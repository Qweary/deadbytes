#!/usr/bin/env python3
"""
lock-panel.py — Local browser control panel for the workshop read/write actions.

A button-style convenience layer over lock-tool.py. It has TWO clearly-separated
modes so an attendee can never confuse practising on a sample copy with writing
the real lock:

  * PRACTICE (default, calm/blue-green, NO hardware) — a READ that decodes a copy
    of the bundled sample dump, and a WRITE that bakes the attendee's own code
    into a COPY and re-decodes it (a PREVIEW — nothing is written to the lock).

  * LIVE LOCK (amber/red warning, the REAL chip) — a READ that runs the real
    minipro read, and TWO writes, each after an explicit in-browser confirmation:
      - ADD my code (the STANDARD button) — reads the real chip first and ADDS the
        attendee's code on top, preserving every code already on the lock.
      - RESET + add my code (the explicit reset button) — wipes the chip and
        re-seeds it to the sample state (3 demo codes + 123456) with the
        attendee's code injected. The old deterministic sample-flash behaviour,
        now opt-in.

It binds to localhost only and serves a single self-contained page — no external
assets, no internet, no pip. Pure stdlib http.server.

This is the top, most-convenient layer of the workshop's layered tooling. It is a
THIN wrapper: it shells nothing out itself for the decode/encode — it imports
lock-tool.py and calls the same read/write functions the CLI and the menu use, so
all three front-ends agree byte-for-byte. If the panel will not launch (no
browser, port busy, headless box), every action is still available from the
command line; the panel page itself prints those equivalent commands, and so does
this docstring:

    PRACTICE READ  : python3 lock-tool.py read --all
    PRACTICE WRITE : python3 lock-tool.py write --code 246810 --slot 25 --role supervisor
    LIVE READ      : python3 lock-tool.py read --all --live
    LIVE WRITE ADD : python3 lock-tool.py write --code 246810 --slot 25 --role supervisor --live
    LIVE WRITE RST : python3 lock-tool.py write --code 246810 --slot 25 --role supervisor --live --reset-baseline

The LIVE LOCK write is gated TWICE: a deliberate two-click in-browser
confirmation here (which states exactly what lands on the lock), and the
confirmation built into lock-tool.py. From an HTTP handler the panel calls the
non-blocking entry points (read_live / flash_attendee_live, confirmation
pre-granted) so the server never deadlocks on input(). A missing programmer or a
clip that does not bite surfaces as panel text, never a crash.

STDLIB-ONLY. No pip, no internet, no non-stdlib imports.

Usage:
    python3 lock-panel.py                 # serve on 127.0.0.1:8765 + open browser
    python3 lock-panel.py --port 9000     # pick a port
    python3 lock-panel.py --no-browser    # serve only, don't auto-open a browser
    python3 lock-panel.py --self-test     # render the page in-process, no socket
"""

import argparse
import html
import io
import json
import os
import sys
import threading
import types
import urllib.parse
import webbrowser
from contextlib import redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Load lock-tool.py (hyphenated filename) as a module from this script's dir.
_HERE = os.path.dirname(os.path.abspath(__file__))
# Keep the shipped tools/ dir free of __pycache__ bytecode (see lock-tool.py).
sys.dont_write_bytecode = True
import importlib.util

_LT_PATH = os.path.join(_HERE, "lock-tool.py")
if not os.path.isfile(_LT_PATH):
    sys.exit(
        f"ERROR: lock-tool.py not found next to lock-panel.py (looked in {_HERE}).\n"
        f"  The panel is only a convenience wrapper. Run the kit selftest or "
        f"re-extract the tarball. The command-line path still works without "
        f"the panel: python3 lock-tool.py read --all"
    )
_spec = importlib.util.spec_from_file_location("lock_tool_mod", _LT_PATH)
lock_tool = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lock_tool)

decode_codes = lock_tool.decode_codes
MAX_SLOT = lock_tool.MAX_SLOT
ROLE_CHOICES = ["normal", "supervisor", "elevated", "master"]

HOST = "127.0.0.1"   # localhost only — never bind to a routable interface
DEFAULT_PORT = 8765


# ---------------------------------------------------------------------------
# Action helpers — capture lock-tool's printed output as text for the panel.
# ---------------------------------------------------------------------------
def _ns(**kw):
    return types.SimpleNamespace(**kw)


def _role_display(role: str) -> str:
    """Resolve a role string to its human display name via lock-tool, never
    crashing the panel — fall back to the raw role on an unknown value."""
    try:
        return lock_tool.resolve_role(role)[1]
    except SystemExit:
        return (role or "normal").strip() or "normal"


def _parse_slot(slot: str):
    """Return (slot_int, error_text). error_text is None on success."""
    try:
        return int((slot or "25").strip()), None
    except ValueError:
        return None, f"slot {slot!r} is not a whole number."


# --- PRACTICE (sample-copy, no hardware) -----------------------------------
def run_read() -> str:
    """PRACTICE READ — sample dump copy, no hardware. Returns its printed text."""
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            lock_tool.cmd_read(_ns(dump=None, all=True, live=False))
    except SystemExit as e:
        if e.code not in (0, None):
            buf.write(f"\n[read error] {e}\n")
    return buf.getvalue()


def run_write(code: str, slot: str, role: str) -> str:
    """PRACTICE WRITE — bake the custom value into a COPY, no hardware. -> text.

    All validation is delegated to lock-tool.cmd_write; we only convert slot to
    int defensively and surface its error messages as panel text rather than
    crashing the server. The output now carries the PREVIEW-ONLY banner."""
    buf = io.StringIO()
    code = (code or "").strip()
    role = (role or "normal").strip()
    slot_i, err = _parse_slot(slot)
    if err is not None:
        return f"[write error] {err}\n"
    args = _ns(code=code, slot=slot_i, role=role, out=None,
               baseline_dump=None, live=False, yes=False, reset_baseline=False)
    try:
        with redirect_stdout(buf):
            lock_tool.cmd_write(args)
    except SystemExit as e:
        if e.code not in (0, None):
            buf.write(f"\n[write error] {e}\n")
    return buf.getvalue()


# --- LIVE LOCK (the real chip) ---------------------------------------------
def run_live_read() -> str:
    """LIVE READ — real minipro read of the actual chip. Catches the SystemExit
    that read_live raises on missing-minipro / clip-fail and returns it as panel
    text so the server never crashes and the no-hardware laptop degrades cleanly."""
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            lock_tool.read_live(show_all=True)
    except SystemExit as e:
        if e.code not in (0, None):
            buf.write(f"\n{e}\n")
    except Exception as e:  # never leak a traceback to the attendee
        buf.write(f"\n[live read error] {e}\n")
    out = buf.getvalue()
    return out or "[live read produced no output]\n"


def run_live_write(code: str, slot: str, role: str, reset: bool = False) -> str:
    """LIVE WRITE — flash the REAL chip. Two flavours, picked by `reset`:
      * reset=False (STANDARD) — ACCUMULATE: read the chip first and ADD the
        attendee's code, preserving every existing code.
      * reset=True  (explicit) — wipe-and-reseed to the sample state (3 demo codes
        + 123456) with the attendee's code injected.
    The browser confirmation gate has already fired by the time we get here; the
    lock-tool confirmation is pre-granted (yes=True) so there is no input()
    deadlock — and yes=True also pre-grants the accumulate path's overwrite gate.
    Catches SystemExit (missing-minipro / bad-read / write failure) and surfaces
    it as panel text rather than crashing the server."""
    buf = io.StringIO()
    code = (code or "").strip()
    role = (role or "normal").strip()
    slot_i, err = _parse_slot(slot)
    if err is not None:
        return f"[flash error] {err}\n"
    try:
        with redirect_stdout(buf):
            lock_tool.flash_attendee_live(code=code, slot=slot_i, role=role,
                                          reset_baseline=reset)
    except SystemExit as e:
        if e.code not in (0, None):
            buf.write(f"\n{e}\n")
    except Exception as e:  # never leak a traceback to the attendee
        buf.write(f"\n[flash error] {e}\n")
    return buf.getvalue() or "[flash produced no output]\n"


# ---------------------------------------------------------------------------
# Page rendering
# ---------------------------------------------------------------------------
_PAGE_CSS = """
  :root {
    color-scheme: light dark;
    --practice: #16a34a;        /* calm green   */
    --practice-blue: #2563eb;   /* calm blue    */
    --live: #b91c1c;            /* strong red   */
    --live-amber: #d97706;      /* warning amber*/
  }
  * { box-sizing: border-box; }
  body { font-family: system-ui, sans-serif; max-width: 860px; margin: 1.5rem auto;
         padding: 0 1rem; line-height: 1.5; }
  h1 { font-size: 1.4rem; margin-bottom: 0.2rem; }
  .sub { color: #666; margin-top: 0; font-size: 0.9rem; }

  /* Mode tab switcher */
  .tabs { display: flex; gap: 0.6rem; margin: 1rem 0 0.4rem; }
  .tab { flex: 1; text-align: center; text-decoration: none; font-weight: 700;
         font-size: 1.05rem; padding: 0.8rem 0.5rem; border-radius: 10px 10px 0 0;
         border: 2px solid #8884; border-bottom: 0; color: #555; background: #8881; }
  .tab small { display: block; font-weight: 500; font-size: 0.72rem; opacity: 0.85; }
  .tab.practice.active { background: var(--practice); color: #fff;
                         border-color: var(--practice); }
  .tab.live.active { background: var(--live); color: #fff; border-color: var(--live); }

  /* Persistent mode banner */
  .mode-banner { border-radius: 0 0 10px 10px; padding: 0.7rem 1rem; font-weight: 700;
                 display: flex; align-items: center; gap: 0.6rem; }
  .mode-banner .what { font-weight: 500; font-size: 0.9rem; }
  .mode-banner.practice { background: var(--practice); color: #fff; }
  .mode-banner.live { background: var(--live); color: #fff;
                      border: 2px solid var(--live-amber); }
  .badge { font-size: 0.7rem; letter-spacing: 0.08em; text-transform: uppercase;
           background: #fff3; padding: 0.15rem 0.5rem; border-radius: 999px; }

  .card { border: 1px solid #8884; border-radius: 10px; padding: 1rem 1.2rem;
          margin: 1rem 0; }
  .card.live-card { border-color: var(--live-amber); }
  label { display: block; font-weight: 600; margin: 0.6rem 0 0.2rem; }
  input, select { font-size: 1rem; padding: 0.5rem; border-radius: 6px;
                  border: 1px solid #8886; width: 100%; }
  .row { display: flex; gap: 0.8rem; flex-wrap: wrap; }
  .row > div { flex: 1; min-width: 140px; }
  button { font-size: 1.05rem; font-weight: 700; padding: 0.7rem 1.4rem;
           border-radius: 8px; border: 0; cursor: pointer; margin-top: 0.9rem; }
  .read-btn { background: var(--practice-blue); color: #fff; }
  .write-btn { background: var(--practice); color: #fff; }
  .live-read-btn { background: var(--live-amber); color: #fff; }
  .flash-btn { background: var(--live); color: #fff; }
  /* RESET is the more destructive of the two live writes (it wipes the lock
     first), so it reads as a hollow/outlined danger button — present, but visibly
     secondary to the solid ADD button. */
  .reset-btn { background: #fff; color: var(--live); border: 2px solid var(--live); }
  .cancel-btn { background: #8883; color: inherit; }
  pre.out { background: #0b1020; color: #d7e0ff; padding: 1rem; border-radius: 8px;
            overflow-x: auto; white-space: pre; font-size: 0.85rem; }
  pre.out.muted { color: #9aa3c0; }
  code { background: #8882; padding: 0.1rem 0.3rem; border-radius: 4px; }
  .note { font-size: 0.85rem; color: #777; }

  /* Live-write confirmation panel */
  .confirm { border: 3px solid var(--live); border-radius: 10px; padding: 1rem 1.2rem;
             margin: 1rem 0; background: #b91c1c14; }
  .confirm h2 { color: var(--live); margin-top: 0; }
  .confirm .lands { font-weight: 700; background: #fff4; padding: 0.6rem 0.8rem;
                    border-radius: 6px; border-left: 4px solid var(--live-amber); }
  .confirm ul { margin: 0.6rem 0; }
  .confirm .danger { color: var(--live); font-weight: 700; }
"""


def _mode_banner(mode: str) -> str:
    if mode == "live":
        return (
            '<div class="mode-banner live" role="status">'
            '<span class="badge">Live lock</span>'
            '<span>LIVE LOCK — writes the REAL chip.</span>'
            '<span class="what">Reads and flashes the actual AT45DB041E over the '
            'programmer clip. Real hardware.</span>'
            '</div>'
        )
    return (
        '<div class="mode-banner practice" role="status">'
        '<span class="badge">Practice</span>'
        '<span>PRACTICE — sample copy, no hardware.</span>'
        '<span class="what">Everything happens on a copy of the bundled sample '
        'dump. Nothing touches a real lock.</span>'
        '</div>'
    )


def _tabs(mode: str) -> str:
    p_active = " active" if mode != "live" else ""
    l_active = " active" if mode == "live" else ""
    return (
        '<div class="tabs" role="tablist">'
        f'<a class="tab practice{p_active}" href="/?mode=practice" '
        f'role="tab" aria-selected="{"false" if mode == "live" else "true"}">'
        'PRACTICE<small>sample copy · no hardware</small></a>'
        f'<a class="tab live{l_active}" href="/?mode=live" '
        f'role="tab" aria-selected="{"true" if mode == "live" else "false"}">'
        'LIVE LOCK<small>writes the REAL chip</small></a>'
        '</div>'
    )


def _role_select(role_val: str) -> str:
    return "".join(
        f'<option value="{r}"{" selected" if r == role_val else ""}>{r}</option>'
        for r in ROLE_CHOICES
    )


def _footer() -> str:
    return (
        '<p class="note">If this panel ever won\'t open, the same actions are '
        'one-liners:<br>'
        'PRACTICE READ&nbsp;: <code>python3 lock-tool.py read --all</code><br>'
        'PRACTICE WRITE (preview): '
        '<code>python3 lock-tool.py write --code 246810 --slot 25 --role supervisor</code>'
        '<br>'
        'LIVE READ (real chip)&nbsp;: '
        '<code>python3 lock-tool.py read --all --live</code><br>'
        'LIVE WRITE — ADD (real chip, keeps existing codes, confirmation-gated): '
        '<code>python3 lock-tool.py write --code 246810 --slot 25 --role supervisor '
        '--live</code><br>'
        'LIVE WRITE — RESET (real chip, wipe + reseed to sample): '
        '<code>python3 lock-tool.py write --code 246810 --slot 25 --role supervisor '
        '--live --reset-baseline</code></p>'
    )


def _out_block(output_text: str, placeholder: str) -> str:
    if output_text:
        return f'<pre class="out">{html.escape(output_text)}</pre>'
    return f'<pre class="out muted">{html.escape(placeholder)}</pre>'


def _practice_body(output_text: str, code_val: str, slot_val: str,
                   role_val: str) -> str:
    placeholder = ("Press READ the sample to decode the sample dump, or enter a "
                   "code and press WRITE into a copy (preview) to bake your own "
                   "value into a copy — nothing is written to any lock.")
    return f"""
  <div class="card">
    <h2 style="font-size:1.1rem;margin-top:0">READ the sample</h2>
    <p class="note">Decode the page-0 user-code table from a copy of the bundled
       sample dump and show every slot. No hardware touched.</p>
    <form method="POST" action="/read?mode=practice">
      <button class="read-btn" type="submit">READ the sample</button>
    </form>
  </div>

  <div class="card">
    <h2 style="font-size:1.1rem;margin-top:0">WRITE into a copy (preview)</h2>
    <p class="note">Type your own 6-digit code, pick a slot and a role, and bake
       it into a <em>copy</em> of the sample dump. The result is re-decoded so you
       see your value land. This is a PREVIEW — the original dump and any real
       chip are never touched here.</p>
    <form method="POST" action="/write?mode=practice">
      <label for="code">Custom code (6 digits — zeros allowed)</label>
      <input id="code" name="code" inputmode="numeric" pattern="[0-9]{{6}}"
             maxlength="6" placeholder="246810" value="{html.escape(code_val)}">
      <div class="row">
        <div>
          <label for="slot">Slot (0–{MAX_SLOT})</label>
          <input id="slot" name="slot" inputmode="numeric"
                 value="{html.escape(slot_val)}">
        </div>
        <div>
          <label for="role">Role</label>
          <select id="role" name="role">{_role_select(role_val)}</select>
        </div>
      </div>
      <button class="write-btn" type="submit">WRITE into a copy (preview)</button>
    </form>
  </div>

  <div class="card">
    <h2 style="font-size:1.1rem;margin-top:0">Result</h2>
    {_out_block(output_text, placeholder)}
  </div>
"""


def _live_body(output_text: str, code_val: str, slot_val: str,
               role_val: str) -> str:
    placeholder = ("LIVE LOCK mode. Press READ the real lock to read the actual "
                   "chip, or enter a code and press ADD my code to the lock to "
                   "write it — flashing asks you to confirm first. ADD keeps every "
                   "code already on the lock; RESET wipes the lock back to the "
                   "sample state first. If no programmer is attached, this reports "
                   "it and you can switch to Practice.")
    # ONE shared input form with TWO submit buttons. Both POST to /flash-confirm;
    # the button's own formaction carries the ?reset= flag, so the confirmation
    # page (and ultimately flash_attendee_live) knows which path the attendee
    # picked. ADD is the standard/default action; RESET is the explicit opt-in.
    return f"""
  <div class="card live-card">
    <h2 style="font-size:1.1rem;margin-top:0">READ the real lock</h2>
    <p class="note">Run a real minipro read of the actual chip over the clip and
       decode it. Needs the programmer attached and the clip seated.</p>
    <form method="POST" action="/read?mode=live">
      <button class="live-read-btn" type="submit">READ the real lock</button>
    </form>
  </div>

  <div class="card live-card">
    <h2 style="font-size:1.1rem;margin-top:0">Write your code to the real lock</h2>
    <p class="note danger" style="color:#b91c1c;font-weight:700">
       This erases and reprograms the REAL chip. You will be asked to confirm
       before anything is written.</p>
    <form method="POST" action="/flash-confirm?mode=live">
      <label for="lcode">Your code (6 digits — zeros allowed)</label>
      <input id="lcode" name="code" inputmode="numeric" pattern="[0-9]{{6}}"
             maxlength="6" placeholder="246810" value="{html.escape(code_val)}">
      <div class="row">
        <div>
          <label for="lslot">Slot (0–{MAX_SLOT})</label>
          <input id="lslot" name="slot" inputmode="numeric"
                 value="{html.escape(slot_val)}">
        </div>
        <div>
          <label for="lrole">Role</label>
          <select id="lrole" name="role">{_role_select(role_val)}</select>
        </div>
      </div>
      <div class="row">
        <button class="flash-btn" type="submit"
                formaction="/flash-confirm?mode=live&amp;reset=0">
          ADD my code to the lock…</button>
        <button class="reset-btn" type="submit"
                formaction="/flash-confirm?mode=live&amp;reset=1">
          RESET + add my code…</button>
      </div>
      <p class="note"><strong>ADD</strong> reads the lock first and keeps every
         code already on it (the standard choice). <strong>RESET</strong> wipes
         the lock back to the sample state (3 demo codes + 123456) before adding
         your code — use it only to return a station to a known state.</p>
    </form>
  </div>

  <div class="card live-card">
    <h2 style="font-size:1.1rem;margin-top:0">Result</h2>
    {_out_block(output_text, placeholder)}
  </div>
"""


def render_page(output_text: str = "", code_val: str = "",
                slot_val: str = "25", role_val: str = "normal",
                mode: str = "practice") -> str:
    """Render the single-page control panel for the given mode. output_text is the
    most recent action result (raw text). All values are HTML-escaped here."""
    mode = "live" if mode == "live" else "practice"
    body = (_live_body(output_text, code_val, slot_val, role_val) if mode == "live"
            else _practice_body(output_text, code_val, slot_val, role_val))
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Lock User-Code Workshop — Control Panel</title>
<style>{_PAGE_CSS}</style>
</head>
<body>
  <h1>Lock User-Code Workshop — Control Panel</h1>
  <p class="sub">Two modes · localhost only · stdlib http.server</p>
  {_tabs(mode)}
  {_mode_banner(mode)}
{body}
  {_footer()}
</body>
</html>"""


def render_flash_confirm(code: str, slot: str, role: str,
                         reset: bool = False) -> str:
    """Render the LIVE-WRITE confirmation page — the in-browser gate. It states
    exactly what lands on the lock and requires a second deliberate click before
    /flash fires. The copy is mode-aware:
      * reset=False (ADD/accumulate) — the lock's current codes are read first and
        KEPT; the attendee's code is added on top. We cannot enumerate the kept
        codes here (we have not read the chip yet), so we say so honestly.
      * reset=True  (RESET) — the deterministic sample-flash state lands, so we
        show lands_on_lock_summary() (attendee code + 3 demo codes + starter).
    All form values are HTML-escaped."""
    code = (code or "").strip()
    role = (role or "normal").strip()
    slot_i, err = _parse_slot(slot)
    role_disp = _role_display(role)
    slot_for_summary = slot_i if err is None else slot
    bad_code = not (code.isdigit() and len(code) == 6)
    warn = ""
    if bad_code:
        warn = ('<p class="danger">Heads up: <code>'
                + html.escape(code or "(empty)")
                + '</code> is not a 6-digit code. Go back and fix it before '
                  'flashing.</p>')
    if err is not None:
        warn += ('<p class="danger">Heads up: ' + html.escape(err)
                 + ' Go back and fix the slot before flashing.</p>')

    code_disp = html.escape(code or "??????")
    slot_disp = html.escape(str(slot_for_summary))
    role_html = html.escape(role_disp)
    if reset:
        # RESET: the fixed sample-flash state. Enumerable up front.
        summary = lock_tool.lands_on_lock_summary(code or "??????",
                                                  slot_for_summary, role_disp)
        lead = ('This will <span class="danger">erase and reprogram the real '
                'AT45DB041E chip</span> back to the sample state — any codes '
                'currently on the lock are <span class="danger">wiped</span> and '
                'replaced by:')
        lands_block = f'<p class="lands">{html.escape(summary)}</p>'
        detail = (
            f'<li>Your code <code>{code_disp}</code> goes into slot '
            f'<code>{slot_disp}</code> as <code>{role_html}</code>.</li>'
            f'<li>The <strong>3 demo codes (133769, 420420, 696969)</strong> and '
            f'the <strong>123456 starter</strong> are flashed alongside it.</li>'
        )
    else:
        # ADD / accumulate: keep whatever is on the lock, add this code. We have
        # not read the chip yet, so we describe the effect, not a fixed list.
        lead = ('This will <span class="danger">add your code to the real '
                'AT45DB041E chip</span>. The lock is read first, so every code '
                'already on it is <strong>kept</strong>:')
        lands_block = (
            f'<p class="lands">Adds your code {code_disp} (slot {slot_disp}, '
            f'{role_html}) to the lock — existing codes preserved.</p>')
        detail = (
            f'<li>Your code <code>{code_disp}</code> is added at slot '
            f'<code>{slot_disp}</code> as <code>{role_html}</code>.</li>'
            f'<li>Every code already on the lock is <strong>preserved</strong> '
            f'(this reads the chip and writes it back with your code added).</li>'
            f'<li>If slot <code>{slot_disp}</code> already holds a DIFFERENT code, '
            f'the flash step shows you whose code it is before overwriting it.</li>'
        )
    reset_q = "1" if reset else "0"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Confirm LIVE flash — Lock Workshop</title>
<style>{_PAGE_CSS}</style>
</head>
<body>
  <h1>Lock User-Code Workshop — Control Panel</h1>
  {_tabs("live")}
  {_mode_banner("live")}

  <div class="confirm">
    <h2>Confirm: {"RESET and flash" if reset else "add your code to"} the REAL lock?</h2>
    <p>{lead}</p>
    {lands_block}
    <ul>
      {detail}
    </ul>
    <p class="danger">Before you click: make sure the programmer clip is seated on
       the chip and the lock's batteries are OUT.</p>
    {warn}
    <form method="POST" action="/flash?mode=live&amp;reset={reset_q}" style="display:inline">
      <input type="hidden" name="code" value="{html.escape(code)}">
      <input type="hidden" name="slot" value="{html.escape(str(slot))}">
      <input type="hidden" name="role" value="{html.escape(role)}">
      <button class="{"reset-btn" if reset else "flash-btn"}" type="submit">{
        "Yes, RESET and flash the real lock" if reset
        else "Yes, add my code to the real lock"}</button>
    </form>
    <form method="POST" action="/read?mode=live" style="display:inline">
      <button class="cancel-btn" type="submit">Cancel — back to Live mode</button>
    </form>
  </div>

  {_footer()}
</body>
</html>"""


# ---------------------------------------------------------------------------
# HTTP handler
# ---------------------------------------------------------------------------
class PanelHandler(BaseHTTPRequestHandler):
    server_version = "LockPanel/2.0"

    def _send_html(self, body: str, status: int = 200):
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    @staticmethod
    def _route(path: str):
        """Split a request path into (route, mode, reset). mode comes from
        ?mode=live; reset (the explicit wipe-and-reseed live write) comes from
        ?reset=1 — False for everything else."""
        parsed = urllib.parse.urlsplit(path)
        qs = urllib.parse.parse_qs(parsed.query)
        mode = "live" if qs.get("mode", ["practice"])[0] == "live" else "practice"
        reset = qs.get("reset", ["0"])[0] == "1"
        return parsed.path, mode, reset

    def do_GET(self):
        route, mode, _reset = self._route(self.path)
        if route in ("/", "/index.html"):
            self._send_html(render_page(mode=mode))
        elif route == "/healthz":
            payload = json.dumps({"status": "ok"}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        else:
            self._send_html(
                render_page("[404] unknown path: " + route, mode=mode), 404)

    def do_POST(self):
        route, mode, reset = self._route(self.path)
        length = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(length).decode("utf-8") if length else ""
        form = urllib.parse.parse_qs(raw)

        def get(name, default=""):
            vals = form.get(name)
            return vals[0] if vals else default

        if route == "/read":
            if mode == "live":
                out = run_live_read()
            else:
                out = run_read()
            self._send_html(render_page(out, mode=mode))
        elif route == "/write":
            # PRACTICE preview write (no hardware).
            code = get("code")
            slot = get("slot", "25")
            role = get("role", "normal")
            out = run_write(code, slot, role)
            self._send_html(render_page(out, code_val=code, slot_val=slot,
                                        role_val=role, mode="practice"))
        elif route == "/flash-confirm":
            # Step 1 of the LIVE write gate: show the confirmation page. `reset`
            # (from ?reset=1) selects ADD-vs-RESET copy and carries through.
            code = get("code")
            slot = get("slot", "25")
            role = get("role", "normal")
            self._send_html(render_flash_confirm(code, slot, role, reset=reset))
        elif route == "/flash":
            # Step 2 of the LIVE write gate: the deliberate second click. Only
            # here does the real flash actually fire. `reset` picks the path:
            # False = ACCUMULATE (read-and-add), True = wipe-and-reseed-from-sample.
            code = get("code")
            slot = get("slot", "25")
            role = get("role", "normal")
            out = run_live_write(code, slot, role, reset=reset)
            self._send_html(render_page(out, code_val=code, slot_val=slot,
                                        role_val=role, mode="live"))
        else:
            self._send_html(
                render_page("[404] unknown action: " + route, mode=mode), 404)

    def log_message(self, fmt, *args):
        # Quiet by default — the panel is a workshop convenience, not a server we
        # want logging every request to the terminal.
        pass


def run_self_test() -> int:
    """Render both modes + the live-write confirmation page, and exercise the
    PRACTICE wrapper logic in-process — no socket, no browser, NO hardware. The
    live read/flash entry points are deliberately NOT called (they touch the real
    chip); we only assert that their UI/markup renders."""
    print("lock-panel.py self-test (no socket, no browser, no hardware)")
    failures = 0

    def check(label, ok, detail=""):
        nonlocal failures
        print(f"  [{'PASS' if ok else 'FAIL'}] {label} {detail}")
        if not ok:
            failures += 1

    # --- PRACTICE-mode page renders -----------------------------------------
    page = render_page(mode="practice")
    check("practice page renders READ-the-sample button",
          "READ the sample" in page)
    check("practice page has custom-value input field", 'name="code"' in page)
    check("practice page renders preview WRITE button",
          "WRITE into a copy (preview)" in page)
    check("practice page has role select", 'name="role"' in page)

    # --- Mode UI: both controls present + clearly distinct ------------------
    check("page exposes a PRACTICE mode control",
          'href="/?mode=practice"' in page and "PRACTICE" in page)
    check("page exposes a LIVE mode control",
          'href="/?mode=live"' in page and "LIVE LOCK" in page)
    check("practice mode banner states no-hardware",
          "PRACTICE — sample copy, no hardware." in page)

    live_page = render_page(mode="live")
    check("live page renders READ-the-real-lock button",
          "READ the real lock" in live_page)
    check("live page renders the ADD (accumulate) live-write button",
          "ADD my code to the lock" in live_page)
    check("live page renders the explicit RESET live-write button",
          "RESET + add my code" in live_page)
    check("live page ADD button posts reset=0; RESET button posts reset=1",
          "reset=0" in live_page and "reset=1" in live_page)
    check("live mode banner warns it writes the real chip",
          "LIVE LOCK — writes the REAL chip." in live_page)

    # --- ADD (accumulate) confirmation: keeps existing codes, no fixed list -
    add_confirm = render_flash_confirm("246810", "25", "supervisor", reset=False)
    check("ADD confirmation renders + asks to add the code",
          "add your code to the REAL lock?" in add_confirm
          and "Yes, add my code to the real lock" in add_confirm)
    check("ADD confirmation states existing codes are preserved",
          "preserved" in add_confirm and "246810" in add_confirm)
    check("ADD confirmation does NOT promise the fixed sample-flash demo set",
          not ("133769" in add_confirm and "420420" in add_confirm
               and "696969" in add_confirm))
    check("ADD confirmation posts to the accumulate flash (reset=0)",
          "/flash?mode=live&amp;reset=0" in add_confirm)

    # --- RESET confirmation: the deterministic sample-flash state -----------
    reset_confirm = render_flash_confirm("246810", "25", "supervisor", reset=True)
    check("RESET confirmation renders + asks to reset",
          "RESET and flash the REAL lock?" in reset_confirm
          and "Yes, RESET and flash the real lock" in reset_confirm)
    check("RESET confirmation shows the lands-on-lock summary",
          "Lands on the lock:" in reset_confirm and "246810" in reset_confirm)
    check("RESET confirmation reflects the 3 demo codes are pushed too",
          "133769" in reset_confirm and "420420" in reset_confirm
          and "696969" in reset_confirm)
    check("RESET confirmation reflects the 123456 starter is pushed too",
          "123456" in reset_confirm)
    check("RESET confirmation posts to the reset flash (reset=1)",
          "/flash?mode=live&amp;reset=1" in reset_confirm)
    check("both confirmations warn clip seated / batteries out",
          "clip is seated" in add_confirm and "batteries are OUT" in add_confirm
          and "clip is seated" in reset_confirm
          and "batteries are OUT" in reset_confirm)

    # --- Footer reflects the practice + BOTH live one-liners ----------------
    check("footer shows the practice (preview) one-liner",
          "PRACTICE WRITE (preview)" in page)
    check("footer shows the live ADD one-liner",
          "LIVE WRITE — ADD" in page and "--live" in page)
    check("footer shows the live RESET --reset-baseline one-liner",
          "LIVE WRITE — RESET" in page and "--reset-baseline" in page)

    # --- PRACTICE wrapper logic (in-process, no hardware) -------------------
    read_out = run_read()
    check("READ action decodes slot 0 = 123456", "123456" in read_out,
          f"({len(read_out)} chars)")

    write_out = run_write("135790", "30", "master")
    check("WRITE action bakes + re-decodes the custom code, shows PREVIEW banner",
          "135790" in write_out
          and ("PREVIEW ONLY" in write_out
               or "nothing was written to the lock" in write_out))

    # zero-digit write exercises the 0xB rule end to end through the panel layer
    z_out = run_write("204060", "12", "supervisor")
    check("WRITE handles a code with zeros (0xB rule), still PREVIEW",
          "204060" in z_out
          and ("PREVIEW ONLY" in z_out
               or "nothing was written to the lock" in z_out))

    # invalid code surfaces an error as panel text, not a crash
    bad_out = run_write("12", "5", "normal")
    check("WRITE bad code surfaces an error (no crash)",
          "error" in bad_out.lower() or "must be exactly 6" in bad_out)

    print()
    if failures:
        print(f"  RESULT: FAIL — {failures} panel check(s) failed.")
        return 1
    print("  RESULT: PASS — panel wrapper logic + mode UI hold.")
    return 0


def _open_browser(url: str) -> None:
    """Best-effort auto-open of the default browser to the panel URL.

    Fired from a short-lived daemon timer just after the server starts accepting,
    so the very first browser request lands on a listening socket. NEVER crashes
    the panel: webbrowser.open returning False (headless, no DISPLAY, no browser
    registered) or raising is treated as "couldn't auto-open" — the printed URL
    and the CLI one-liners are still on screen for the attendee to use."""
    try:
        opened = webbrowser.open(url)
    except Exception:
        opened = False
    if not opened:
        print(f"  (couldn't auto-open a browser — open this URL yourself: {url})")


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Local browser control panel for the workshop read/write actions. "
            "Binds to localhost only. Two modes: PRACTICE (safe sample-dump copy, "
            "no hardware) and LIVE LOCK (real chip read + confirmation-gated "
            "flash). The command-line path mirrors both: lock-tool.py ... [--live]."
        )
    )
    parser.add_argument("--port", type=int, default=DEFAULT_PORT,
                        help=f"localhost port to serve on (default {DEFAULT_PORT})")
    parser.add_argument("--self-test", action="store_true",
                        help="render + exercise the panel in-process and exit")
    parser.add_argument("--no-browser", action="store_true",
                        help="serve only; do not auto-open the default browser")
    args = parser.parse_args()

    if args.self_test:
        sys.exit(run_self_test())

    try:
        httpd = ThreadingHTTPServer((HOST, args.port), PanelHandler)
    except OSError as e:
        sys.exit(
            f"ERROR: could not bind {HOST}:{args.port} ({e}).\n"
            f"  Try a different --port, or just use the command line — the panel "
            f"is only a convenience:\n"
            f"    python3 lock-tool.py read --all\n"
            f"    python3 lock-tool.py write --code 246810 --slot 25 --role supervisor"
        )
    url = f"http://{HOST}:{args.port}/"
    print("=" * 72)
    print("  Lock User-Code Workshop — control panel is running")
    print(f"  Open this in a browser on this laptop:  {url}")
    print("  Two modes: PRACTICE (sample copy, no hardware) and LIVE LOCK (real")
    print("  chip — confirmation-gated flash). Defaults to PRACTICE.")
    print("  Press Ctrl-C to stop. If the browser won't open, the same actions")
    print("  are one-liners:  python3 lock-tool.py read --all   (add --live for real)")
    print("=" * 72)
    # Auto-open the default browser just after serve_forever() starts accepting,
    # so the first request hits a listening socket. A short daemon timer keeps the
    # open off the main thread and never blocks shutdown. --no-browser skips it.
    if not args.no_browser:
        opener = threading.Timer(0.5, _open_browser, args=(url,))
        opener.daemon = True
        opener.start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nPanel stopped.")
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
