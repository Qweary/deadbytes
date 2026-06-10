#!/usr/bin/env python3
"""
lock-panel.py — Local browser control panel for the workshop read/write actions.

A button-style convenience layer over lock-tool.py: a READ button that shows the
decoded user-code table, and a custom-value INPUT FIELD above a WRITE button that
bakes the attendee's own code into a copy of the sample dump and shows the
re-decoded result. It binds to localhost only and serves a single self-contained
page — no external assets, no internet, no pip. Pure stdlib http.server.

This is the top, most-convenient layer of the workshop's layered tooling. It is a
THIN wrapper: it shells nothing out itself for the decode/encode — it imports
lock-tool.py and calls the same read/write functions the CLI and the menu use, so
all three front-ends agree byte-for-byte. If the panel will not launch (no
browser, port busy, headless box), every action is still available from the
command line; the panel page itself prints those equivalent commands, and so does
this docstring:

    READ  : python3 lock-tool.py read --all
    WRITE : python3 lock-tool.py write --code 246810 --slot 25 --role supervisor

By design the panel exposes ONLY the safe, no-hardware sample-dump-copy path.
The advanced live-chip read/write is deliberately NOT a web button — flashing a
real chip stays on the explicit, confirmation-gated command-line path
(lock-tool.py ... --live) where the operator is in a terminal and can see the
minipro output. The panel page links to those commands rather than running them.

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


def run_read() -> str:
    """Run the READ action (sample dump copy, no hardware) and return its text."""
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            lock_tool.cmd_read(_ns(dump=None, all=True, live=False))
    except SystemExit as e:
        if e.code not in (0, None):
            buf.write(f"\n[read error] {e}\n")
    return buf.getvalue()


def run_write(code: str, slot: str, role: str) -> str:
    """Run the WRITE action (custom value into a copy, no hardware) -> text.

    All validation is delegated to lock-tool.cmd_write; we only convert slot to
    int defensively and surface its error messages as panel text rather than
    crashing the server."""
    buf = io.StringIO()
    code = (code or "").strip()
    role = (role or "normal").strip()
    try:
        slot_i = int((slot or "25").strip())
    except ValueError:
        return f"[write error] slot {slot!r} is not a whole number.\n"
    args = _ns(code=code, slot=slot_i, role=role, out=None,
               baseline_dump=None, live=False, yes=False)
    try:
        with redirect_stdout(buf):
            lock_tool.cmd_write(args)
    except SystemExit as e:
        if e.code not in (0, None):
            buf.write(f"\n[write error] {e}\n")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Page rendering
# ---------------------------------------------------------------------------
def render_page(output_text: str = "", code_val: str = "",
                slot_val: str = "25", role_val: str = "normal") -> str:
    """Render the single-page control panel. output_text is the most recent
    action result (pre-escaped raw text). All values are HTML-escaped."""
    role_options = "".join(
        f'<option value="{r}"{" selected" if r == role_val else ""}>{r}</option>'
        for r in ROLE_CHOICES
    )
    out_block = (
        f'<pre class="out">{html.escape(output_text)}</pre>'
        if output_text else
        '<pre class="out muted">Press READ to decode the sample dump, or enter '
        'a code and press WRITE to bake your own value into a copy.</pre>'
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Lock User-Code Workshop — Control Panel</title>
<style>
  :root {{ color-scheme: light dark; }}
  body {{ font-family: system-ui, sans-serif; max-width: 820px; margin: 2rem auto;
          padding: 0 1rem; line-height: 1.5; }}
  h1 {{ font-size: 1.4rem; margin-bottom: 0.2rem; }}
  .sub {{ color: #666; margin-top: 0; font-size: 0.9rem; }}
  .card {{ border: 1px solid #8884; border-radius: 10px; padding: 1rem 1.2rem;
           margin: 1rem 0; }}
  label {{ display: block; font-weight: 600; margin: 0.6rem 0 0.2rem; }}
  input, select {{ font-size: 1rem; padding: 0.5rem; border-radius: 6px;
                   border: 1px solid #8886; width: 100%; box-sizing: border-box; }}
  .row {{ display: flex; gap: 0.8rem; flex-wrap: wrap; }}
  .row > div {{ flex: 1; min-width: 140px; }}
  button {{ font-size: 1.05rem; font-weight: 600; padding: 0.7rem 1.4rem;
            border-radius: 8px; border: 0; cursor: pointer; margin-top: 0.9rem; }}
  .read-btn {{ background: #2563eb; color: #fff; }}
  .write-btn {{ background: #16a34a; color: #fff; }}
  pre.out {{ background: #0b1020; color: #d7e0ff; padding: 1rem; border-radius: 8px;
             overflow-x: auto; white-space: pre; font-size: 0.85rem; }}
  pre.out.muted {{ color: #9aa3c0; }}
  code {{ background: #8882; padding: 0.1rem 0.3rem; border-radius: 4px; }}
  .note {{ font-size: 0.85rem; color: #777; }}
</style>
</head>
<body>
  <h1>Lock User-Code Workshop — Control Panel</h1>
  <p class="sub">Safe sample-dump path · no hardware needed · localhost only</p>

  <div class="card">
    <h2 style="font-size:1.1rem;margin-top:0">READ</h2>
    <p class="note">Decode the page-0 user-code table from a copy of the bundled
       sample dump and show every slot.</p>
    <form method="POST" action="/read">
      <button class="read-btn" type="submit">READ the lock codes</button>
    </form>
  </div>

  <div class="card">
    <h2 style="font-size:1.1rem;margin-top:0">WRITE your own custom value</h2>
    <p class="note">Type your own 6-digit code, pick a slot and a role, and bake
       it into a <em>copy</em> of the sample dump. The result is re-decoded so you
       see your value land. The original dump and any real chip are never touched
       here.</p>
    <form method="POST" action="/write">
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
          <select id="role" name="role">{role_options}</select>
        </div>
      </div>
      <button class="write-btn" type="submit">WRITE my code into a copy</button>
    </form>
  </div>

  <div class="card">
    <h2 style="font-size:1.1rem;margin-top:0">Result</h2>
    {out_block}
  </div>

  <p class="note">If this panel ever won't open, the same actions are one-liners:<br>
     READ&nbsp;: <code>python3 lock-tool.py read --all</code><br>
     WRITE: <code>python3 lock-tool.py write --code 246810 --slot 25 --role supervisor</code><br>
     The advanced live-chip path stays on the command line:
     <code>python3 lock-tool.py write --code ... --live</code> (confirmation-gated).</p>
</body>
</html>"""


# ---------------------------------------------------------------------------
# HTTP handler
# ---------------------------------------------------------------------------
class PanelHandler(BaseHTTPRequestHandler):
    server_version = "LockPanel/1.0"

    def _send_html(self, body: str, status: int = 200):
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send_html(render_page())
        elif self.path == "/healthz":
            payload = json.dumps({"status": "ok"}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        else:
            self._send_html(render_page("[404] unknown path: " + self.path), 404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(length).decode("utf-8") if length else ""
        form = urllib.parse.parse_qs(raw)

        def get(name, default=""):
            vals = form.get(name)
            return vals[0] if vals else default

        if self.path == "/read":
            out = run_read()
            self._send_html(render_page(out))
        elif self.path == "/write":
            code = get("code")
            slot = get("slot", "25")
            role = get("role", "normal")
            out = run_write(code, slot, role)
            self._send_html(render_page(out, code_val=code,
                                        slot_val=slot, role_val=role))
        else:
            self._send_html(render_page("[404] unknown action: " + self.path), 404)

    def log_message(self, fmt, *args):
        # Quiet by default — the panel is a workshop convenience, not a server we
        # want logging every request to the terminal.
        pass


def run_self_test() -> int:
    """Render the page + exercise the read/write actions in-process, no socket,
    no browser. Confirms the panel's wrapper logic works headless."""
    print("lock-panel.py self-test (no socket, no browser)")
    failures = 0

    def check(label, ok, detail=""):
        nonlocal failures
        print(f"  [{'PASS' if ok else 'FAIL'}] {label} {detail}")
        if not ok:
            failures += 1

    page = render_page()
    check("page renders with READ button", "READ the lock codes" in page)
    check("page has custom-value input field", 'name="code"' in page)
    check("page has WRITE button", "WRITE my code into a copy" in page)
    check("page has role select", 'name="role"' in page)

    read_out = run_read()
    check("READ action decodes slot 0 = 123456", "123456" in read_out,
          f"({len(read_out)} chars)")

    write_out = run_write("135790", "30", "master")
    check("WRITE action bakes + re-decodes the custom code",
          "135790" in write_out and "CONFIRMED" in write_out)

    # zero-digit write exercises the 0xB rule end to end through the panel layer
    z_out = run_write("204060", "12", "supervisor")
    check("WRITE handles a code with zeros (0xB rule)",
          "204060" in z_out and "CONFIRMED" in z_out)

    # invalid code surfaces an error as panel text, not a crash
    bad_out = run_write("12", "5", "normal")
    check("WRITE bad code surfaces an error (no crash)",
          "error" in bad_out.lower() or "must be exactly 6" in bad_out)

    print()
    if failures:
        print(f"  RESULT: FAIL — {failures} panel check(s) failed.")
        return 1
    print("  RESULT: PASS — panel wrapper logic holds.")
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
            "Binds to localhost only and exposes the safe sample-dump-copy path "
            "(READ button + custom-value field + WRITE button). Live-chip flashing "
            "stays on the command line (lock-tool.py ... --live)."
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
    print("  Safe path only: READ + WRITE-into-a-copy. No hardware touched here.")
    print("  Press Ctrl-C to stop. If the browser won't open, the same actions")
    print("  are one-liners:  python3 lock-tool.py read --all")
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
