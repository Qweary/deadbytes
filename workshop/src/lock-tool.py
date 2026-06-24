#!/usr/bin/env python3
"""
lock-tool.py — One tool for the workshop's two attendee actions: READ and WRITE.

The thin command-line bedrock that the TUI menu and the local control panel wrap.
It does two things, both on the SAFE sample-dump-copy path by default:

  read    Decode the page-0 user-code table and print it in readable form.
          (Delegates to decode-codes.py's decoder so there is exactly one
          decode implementation in the kit.)

  write   Bake an attendee's own custom code into a COPY of the chosen baseline,
          using build-injected.py's packed-BCD / 0xB-for-zero encoding, then
          RE-DECODE the result and show it so the attendee sees their value
          land. Optionally writes that result to the live chip (advanced,
          confirmation-gated opt-in).

          The baseline depends on the mode (this is the load-bearing fix for the
          ToorCamp lock-write defect):

            * --live with no --reset-baseline (the STANDARD live path) —
              ACCUMULATE: the tool FIRST reads the real chip and uses that fresh
              live read as the baseline, then adds the attendee's code on top.
              Every code already on the lock is preserved; the new one is added.
              This is the default because it is what an attendee expects — "add
              my code to the lock", not "wipe the lock and re-seed it".
            * --live --reset-baseline (the explicit RESET path) — flash a COPY of
              the bundled sample dump (the three demo codes + the 123456 starter)
              with the attendee's code injected, so the lock lands on the same
              deterministic known-good state every time. This is the OLD live
              behaviour, now opt-in only.
            * no --live (PRACTICE / preview) — always file-based and
              deterministic: bake into a copy of the bundled sample dump (or
              --baseline-dump) and re-decode. Nothing touches the chip.

STDLIB-ONLY plus the two bundled sibling tools (decode-codes.py,
build-injected.py). No pip, no internet. A fresh offline Kali laptop runs this
with nothing but python3 + the bundled files.

Usage:
    python3 lock-tool.py read [--dump PATH] [--all] [--live]
    python3 lock-tool.py write --code 246810 [--slot 25] [--role supervisor]
                               [--out injected.bin] [--live] [--reset-baseline]
    python3 lock-tool.py --self-test

Default everything is the no-hardware, copy-of-the-sample path. --live is the
advanced, confirmation-gated path that touches the real chip; by default it
ACCUMULATES onto whatever is already on the chip, and --reset-baseline opts back
into the wipe-and-reseed-from-sample behaviour.
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile

# Import the two bundled sibling tools by file path. Both ship next to this one
# (workshop/src/ in dev, ~/workshop/tools/ on a station), so resolve relative to
# this script's own directory and load them as modules. This keeps a single
# decode implementation and a single encode implementation in the kit — no
# reinvented offset map, no reinvented 0xB-for-zero rule.
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

# Do not litter the shipped tools/ dir with __pycache__/*.pyc. These tools are a
# kit file set verified by MD5 manifest; stray bytecode caches would be non-
# manifested, non-deterministic build artifacts. Loading the siblings below
# without writing bytecode keeps the kit clean and reproducible.
sys.dont_write_bytecode = True

import importlib.util


def _load_sibling(module_name: str, file_basename: str):
    """Load a sibling tool (whose filename has a hyphen, so it is not directly
    importable) as a module from this script's directory. Fails loud with a
    clear message if the sibling is missing."""
    path = os.path.join(_HERE, file_basename)
    if not os.path.isfile(path):
        sys.exit(
            f"ERROR: required bundled tool '{file_basename}' not found next to "
            f"lock-tool.py (looked in {_HERE}). The kit is incomplete — re-run "
            f"the kit's selftest, or re-extract the tarball."
        )
    spec = importlib.util.spec_from_file_location(module_name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


decode_codes = _load_sibling("decode_codes_mod", "decode-codes.py")
build_injected = _load_sibling("build_injected_mod", "build-injected.py")

# Role name (case-insensitive) -> permission byte, for the write field. These
# are the documented roles per DATAFLASH-DECODE-REFERENCE.md §4. Master/Elevated/
# Supervisor/Normal cover the workshop; the numeric variants are accepted too.
ROLE_TO_PERM = {
    "master": 0xF1,
    "elevated": 0xE1,
    "elevated user": 0xE1,
    "supervisor": 0xC1,
    "normal": 0x01,
    "normal user": 0x01,
    "user": 0x01,
}
PERM_TO_ROLE_NAME = {
    0xF1: "Master",
    0xE1: "Elevated",
    0xC1: "Supervisor",
    0x01: "Normal User",
}

DEVICE_NAME = decode_codes.DEVICE_NAME
MINIPRO_BIN = decode_codes.MINIPRO_BIN
# Retained for compatibility; no longer prefixes minipro. The installed uaccess
# udev rule grants the logged-in user direct device access, so the live write
# runs unprivileged.
SUDO_BIN = decode_codes.SUDO_BIN
DUMP_SIZE = build_injected.DUMP_SIZE
MAX_SLOT = build_injected.MAX_SLOT

# What an explicit RESET (--reset-baseline) LIVE write lands on the lock. That
# path flashes a copy of the bundled sample dump with the attendee's code
# injected, and that sample already carries the three workshop demo codes (baked
# at slots 19/32/49) plus the 123456 starter code at slot 0. So a RESET write
# ends on the SAME known-good state every time: the three demo codes + 123456 +
# their own code. This is the SAMPLE-flash model (deterministic, repeatable
# across many attendees). It is NO LONGER the default — the default --live path
# ACCUMULATES onto a fresh read of whatever is already on the chip. These constants
# and lands_on_lock_summary() describe the RESET path only; the panel surfaces the
# summary on its RESET button so the browser can tell the attendee exactly what a
# reset ends up putting on the lock.
DEMO_CODES = [
    {"code": "133769", "slot": 19, "role": "Master"},
    {"code": "420420", "slot": 32, "role": "Elevated"},
    {"code": "696969", "slot": 49, "role": "Supervisor"},
]
STARTER_CODE = {"code": "123456", "slot": 0, "role": "Normal User"}


def lands_on_lock_summary(code: str, slot: int, role_display: str) -> str:
    """One-line, panel-displayable summary of exactly what an explicit RESET
    (--reset-baseline) LIVE write puts on the lock: the three workshop demo codes
    + the 123456 starter + the attendee's own code. Pure (no I/O) so the panel
    and the self-test can both consume it.

    This is RESET-specific. It is true ONLY on the reset/sample-flash path; on the
    default --live ACCUMULATE path the lock keeps whatever it already had plus the
    new code, so the post-write surface there is a re-decode of the actual chip,
    not this fixed summary."""
    demos = ", ".join(d["code"] for d in DEMO_CODES)
    return (f"Lands on the lock: your code {code} (slot {slot}, {role_display}) "
            f"+ the 3 demo codes {demos} + the {STARTER_CODE['code']} starter.")


# ---------------------------------------------------------------------------
# READ
# ---------------------------------------------------------------------------
def cmd_read(args) -> int:
    """READ control: decode + print the user-code table. Just drives the shared
    decoder so the panel/TUI 'READ' button and the CLI 'read' agree exactly."""
    if args.live:
        dump_path = decode_codes.read_live_chip()
        source_label = f"LIVE chip read ({dump_path})"
        cleanup_dir = os.path.dirname(dump_path)
    elif args.dump is not None:
        dump_path = args.dump
        if not os.path.isfile(dump_path):
            sys.exit(f"ERROR: dump file not found: {dump_path}")
        source_label = dump_path
        cleanup_dir = None
    else:
        dump_path, source_label, _ = decode_codes.load_sample_copy()
        cleanup_dir = os.path.dirname(dump_path)
    try:
        with open(dump_path, "rb") as f:
            data = f.read()
        decode_codes.validate_page0(data, dump_path)
        slots = decode_codes.parse_slots(data)
        decode_codes.print_table(slots, show_all=args.all, source_label=source_label)
        if not args.live:
            # Depth for advanced users from the safe path: show the exact
            # minipro read command the --live path WOULD run against the real
            # chip. (This decode came from a file/sample copy, not hardware.)
            would_run = " ".join(decode_codes.live_read_command("live-read.bin"))
            print("  Under the hood, the live read path (--live) would run:")
            print(f"    $ {would_run}")
            print()
    finally:
        if cleanup_dir is not None:
            shutil.rmtree(cleanup_dir, ignore_errors=True)
    return 0


# ---------------------------------------------------------------------------
# WRITE
# ---------------------------------------------------------------------------
def resolve_role(role_arg: str | None) -> tuple[int, str]:
    """Map a --role value (name or 0xNN) to (perm_byte, display_name).

    Default role is Normal User (0x01) — the least-privileged, safest default
    for an attendee's first custom code.
    """
    if role_arg is None:
        return 0x01, "Normal User"
    raw = role_arg.strip().lower()
    if raw in ROLE_TO_PERM:
        perm = ROLE_TO_PERM[raw]
        return perm, PERM_TO_ROLE_NAME.get(perm, raw.title())
    # accept a literal 0xNN / NN hex permission byte
    try:
        perm = int(raw, 16) if raw.startswith("0x") else int(raw, 16)
    except ValueError:
        valid = ", ".join(sorted(set(ROLE_TO_PERM)))
        sys.exit(
            f"ERROR: unknown role {role_arg!r}. Use one of: {valid} "
            f"(or a hex permission byte like 0xF1)."
        )
    if perm not in build_injected.VALID_PERMS:
        valid = ", ".join(f"0x{v:02X}" for v in sorted(build_injected.VALID_PERMS))
        sys.exit(f"ERROR: permission 0x{perm:02X} not in valid set ({valid}).")
    return perm, PERM_TO_ROLE_NAME.get(perm, f"0x{perm:02X}")


def live_write_command(injected_path: str, minipro_bin: str = MINIPRO_BIN) -> list[str]:
    """The exact minipro argv that the --live write path runs to flash
    `injected_path` onto the real chip. One definition, shared by the preview
    surfacing (so advanced users see the under-the-hood command from the safe
    path) and by _flash_live (the path that actually runs it). No sudo: the
    installed uaccess udev rule grants the logged-in user direct device access.

    `minipro_bin` defaults to the bare 'minipro' name (so the preview command
    reads as the canonical PATH invocation); _flash_live passes the RESOLVED
    path (PATH minipro, else the bundled bin/minipro) so the actual flash works
    even before install.sh has put minipro on PATH."""
    # Scope the write (erase+program+verify) to the 'code' main-array memory
    # region. The AT45DB041E user-id signature-section read/write times out on
    # T48 firmware 00.1.34 (LIBUSB_ERROR_TIMEOUT; vendor notes "T48 support is
    # not yet complete"), and the write's verify pass would hit that same
    # section. The lock's entire user-code table lives in the 'code' main
    # array, so '-c code' writes exactly the bytes this tool uses and avoids
    # the flaky signature section — robust and exactly-targeted, not a hack.
    return [minipro_bin, "-i", "-p", DEVICE_NAME, "-c", "code", "-w", injected_path]


def occupied_slot_warning(source_bytes: bytes, slot: int) -> str | None:
    """Return the occupied-slot warning string if `slot` is already active in
    `source_bytes`, else None. Pure (no I/O) so the self-test can assert on the
    exact message without capturing stdout. cmd_write calls this and prints the
    result before the write; a None result means a normal additive add (no warn).

    `source_bytes` is the SAME baseline the patch is applied to — on the default
    --live path that is the fresh live chip read, so "all other slots are
    preserved" is now LITERALLY true against the real chip; on the preview/reset
    path it is true against the sample copy. This stays informational (it does not
    gate); the live+accumulate path layers a real confirmation gate on top via
    overwrites_different_code() below.
    """
    source_slots = decode_codes.parse_slots(source_bytes)
    existing = next((s for s in source_slots if s["slot"] == slot), None)
    if existing is not None and existing["active"]:
        return (f"WARNING: slot {slot} is already occupied by code "
                f"{existing['code']} ({existing['role']}) — your write OVERWRITES "
                f"that slot. All other slots are preserved (this is an additive "
                f"read-modify-write).")
    return None


def overwrites_different_code(baseline_bytes: bytes, slot: int, new_code: str) -> bool:
    """True ONLY when writing `new_code` into `slot` would clobber a DIFFERENT
    active code already sitting there. Pure (no I/O) so the self-test asserts on
    it directly.

    The three cases, and why each result is what it is:
      - slot is ACTIVE with a code != new_code  -> True  (a real destructive
        overwrite — the attendee is about to evict someone else's code; on the
        live+accumulate path this arms an explicit confirmation gate)
      - slot is empty / not active              -> False (a clean add, nothing lost)
      - slot is ACTIVE with the SAME code       -> False (an idempotent re-write of
        the attendee's own value — nothing is actually lost, so no gate)

    This is deliberately NARROWER than occupied_slot_warning(): that helper warns
    on ANY occupied slot (informational), while this predicate fires only on the
    case that actually destroys a distinct code, so the confirmation gate it drives
    does not nag on harmless empty-slot or same-code-re-write writes.
    """
    slots = decode_codes.parse_slots(baseline_bytes)
    existing = next((s for s in slots if s["slot"] == slot), None)
    if existing is None or not existing["active"]:
        return False
    return existing["code"] != new_code


def cmd_write(args) -> int:
    """WRITE control with a custom-value field.

    Bakes the attendee's own code (+ slot + role) into a COPY of the chosen
    baseline via build-injected.py's encoder, writes the result file, RE-DECODES
    it, and shows the attendee their value in the same readable form the READ
    control prints. Optionally flashes the result to the live chip (advanced,
    confirmation-gated).

    Baseline selection (the load-bearing ToorCamp fix):
      * --live and NOT --reset-baseline and NO --baseline-dump  -> ACCUMULATE:
        the baseline is a FRESH live read of the real chip (decode_codes.
        read_live_chip()). Existing codes are preserved; the new one is added.
      * --reset-baseline, OR no --live (preview), OR --baseline-dump  -> build
        from the bundled sample (find_sample_dump()) or the passed dump. The
        no-hardware preview path stays file-based and deterministic.
    """
    code = args.code.strip()
    if len(code) != 6 or not code.isdigit():
        sys.exit(f"ERROR: --code {args.code!r} must be exactly 6 decimal digits "
                 f"(e.g. 246810). Zeros are allowed — the tool encodes them with "
                 f"the 0xB-for-zero rule for you.")
    slot = args.slot
    if not (0 <= slot <= MAX_SLOT):
        sys.exit(f"ERROR: --slot {slot} out of range 0..{MAX_SLOT}.")
    perm, role_display = resolve_role(args.role)

    # ACCUMULATE = the new STANDARD live behaviour: write to the real chip with
    # the chip's CURRENT contents as the baseline. It is selected only when this
    # is a live write AND the attendee did not opt into the explicit reset path
    # AND did not name a baseline dump to build from (which is itself an explicit
    # baseline choice). Preview (no --live) is always file-based, so the
    # no-hardware path stays deterministic and never touches hardware.
    reset_baseline = getattr(args, "reset_baseline", False)
    accumulate = (args.live and not reset_baseline and args.baseline_dump is None)

    # Tempdir holding a fresh live read (accumulate path). Registered for cleanup
    # in the existing finally, exactly like read_live_chip()'s callers do.
    live_read_dir = None

    if accumulate:
        # ORDERING IS LOAD-BEARING: read the live chip FIRST, at the TOP of the
        # write, and use that as the injection baseline. A single live read here
        # feeds the occupied-slot notice, the overwrite gate, the apply_patches
        # baseline, AND the post-write re-decode — one read, one source of truth.
        #
        # FAIL-LOUD, NO SILENT FALLBACK: read_live_chip() raises SystemExit on a
        # missing programmer or a clip that did not bite. We deliberately do NOT
        # catch it — a failed read ABORTS the whole write with a loud error, no
        # flash, chip untouched. Falling back to the static sample here would be
        # the original defect (silently wiping the lock to the sample).
        src = decode_codes.read_live_chip()
        live_read_dir = os.path.dirname(src)
    else:
        # PREVIEW / RESET / explicit-baseline path. Locate + copy the baseline.
        # We never touch the bundled original; we build the injected dump from a
        # COPY. This is the unchanged file-based path.
        src = decode_codes.find_sample_dump()
        if src is None:
            sys.exit(
                "ERROR: could not locate the bundled sample dump to build from. "
                "Expected it in a sibling dumps/ directory. Pass --baseline-dump "
                "if you must build from a non-standard path."
            )
        if args.baseline_dump is not None:
            src = args.baseline_dump
            if not os.path.isfile(src):
                sys.exit(f"ERROR: --baseline-dump not found: {src}")

    with open(src, "rb") as f:
        baseline = f.read()
    build_injected.validate_baseline(baseline, src)

    # Occupied-slot pre-write notice. On the accumulate path `baseline` is the
    # live chip, so this reads the REAL occupant; on the preview/reset path it is
    # the sample. The default sample ships the three workshop codes baked at slots
    # 19/32/49, so writing to one of those overwrites a default code rather than
    # adding a fresh one. Informational only — it does not gate, change the
    # successful-write path, or the exit code; an empty target slot produces no
    # warning. The real OVERWRITE CONFIRMATION GATE (below, accumulate path only)
    # is the gate; this stays a notice.
    warn = occupied_slot_warning(baseline, slot)
    if warn is not None:
        print()
        print(f"  {warn}")

    # Real-overwrite confirmation arming. On the live+accumulate path, if the
    # target slot is ACTIVE with a DIFFERENT code, the attendee is about to evict
    # someone else's code from the real lock — require an explicit confirmation
    # before flashing (handled in _flash_live). Empty slot or same-code re-write
    # does not arm the gate (overwrites_different_code() is False there). The
    # preview/reset path keeps informational-only behaviour (no gate).
    overwrite_gate = accumulate and overwrites_different_code(baseline, slot, code)

    patches = [{
        "slot": slot,
        "code": code,
        "perm": perm,
        "perm_name": role_display,
    }]
    build_injected.validate_patches(patches)
    injected, changes = build_injected.apply_patches(baseline, patches)

    # Decide where to write the injected dump. Default to a tempdir copy unless
    # the attendee names --out (so they can keep the artifact / flash it later).
    if args.out is not None:
        out_path = args.out
        out_dir_cleanup = None
    else:
        out_dir_cleanup = tempfile.mkdtemp(prefix="lock-tool-write-")
        out_path = os.path.join(out_dir_cleanup, "injected.bin")

    try:
        with open(out_path, "wb") as f:
            f.write(injected)

        # Name the baseline honestly in the header: a live chip read (accumulate),
        # the sample (preview/reset), or a named dump.
        if accumulate:
            built_from = f"{src}  (a FRESH read of the REAL chip — accumulating)"
        else:
            built_from = f"{src}  (a copy — original untouched)"

        print()
        print("=" * 72)
        if accumulate:
            print("  WRITE — your custom value added on top of the live chip's "
                  "current codes")
        else:
            print("  WRITE — your custom value baked into a copy of the sample dump")
        print("=" * 72)
        print(f"  Code:        {code}")
        print(f"  Slot:        {slot}")
        print(f"  Role:        {role_display} (0x{perm:02X})")
        print(f"  Built from:  {built_from}")
        print(f"  Result file: {out_path}")
        build_injected.print_changes(changes)

        # RE-DECODE the injected result so the attendee sees their value land in
        # the same table the READ control prints.
        with open(out_path, "rb") as f:
            data = f.read()
        decode_codes.validate_page0(data, out_path)
        slots = decode_codes.parse_slots(data)
        print("  Re-decoding the result so you can see your value land:")
        decode_codes.print_table(
            slots, show_all=False,
            source_label=f"your injected dump ({out_path})")

        # Confirm the attendee's slot now reads back what they entered IN THE
        # baseline COPY. This verifies the encode/decode round trip; on the
        # accumulate path it is also a faithful preview of the post-flash chip.
        target = next(s for s in slots if s["slot"] == slot)
        round_trip_ok = (target["code"] == code and target["active"])
        if not round_trip_ok:
            print(f"  WARNING: slot {slot} re-decode = {target['code']!r}, "
                  f"active={target['active']} — expected {code}. "
                  f"This should not happen; flag a facilitator.")
            print()

        if args.live:
            # The --live path actually writes to hardware; its own confirmation
            # banner and post-flash verdict are printed by _flash_live.
            #   - accumulate=True  -> the post-write verdict re-decodes the ACTUAL
            #     injected slot table (lands_on_lock_summary would be FALSE here —
            #     the lock keeps its prior codes plus the new one, not the fixed
            #     3-demos+starter set).
            #   - accumulate=False (reset path) -> the post-write verdict uses
            #     lands_on_lock_summary (the deterministic sample-flash state).
            # overwrite_gate adds a second, slot-specific confirmation when the
            # write evicts a different live code.
            _flash_live(out_path, code, slot, role_display, args.yes,
                        accumulate=accumulate, post_write_slots=slots,
                        overwrite_gate=overwrite_gate, baseline_bytes=baseline)
        else:
            # PREVIEW / PRACTICE PATH — nothing was written to the lock. Say so
            # LOUDLY so it can't be skimmed past. The earlier "CONFIRMED … your
            # value landed" wording was a trap: it read like a hardware success
            # on a path that never touched the chip.
            would_run = " ".join(live_write_command(out_path))
            print("=" * 72)
            print("  PREVIEW ONLY — nothing was written to the lock.")
            print("=" * 72)
            if round_trip_ok:
                print(f"  Your code {code} decodes correctly in slot {slot} "
                      f"({role_display}) — but only in this COPY of the dump.")
            print("  This built a copy of the dump so you can see your code")
            print("  decode; the real chip is untouched.")
            print("  To actually flash this onto the lock: re-run with --live.")
            print("  --live reads the REAL chip first and ADDS your code to "
                  "whatever")
            print("  is already on it (your existing codes are kept). Add "
                  "--reset-baseline")
            print("  to instead wipe-and-reseed the lock to the sample state "
                  "(3 demo")
            print("  codes + 123456 + your code). The browser panel's Live-lock "
                  "mode")
            print("  mirrors both.")
            print("  Under the hood, the live path would run:")
            print(f"    $ {would_run}")
            print("=" * 72)
            print()

    finally:
        if out_dir_cleanup is not None:
            shutil.rmtree(out_dir_cleanup, ignore_errors=True)
        # Clean up the fresh-live-read tempdir (accumulate path) the same way the
        # read command does, so we never leak a /tmp/decode-live-* dir.
        if live_read_dir is not None:
            shutil.rmtree(live_read_dir, ignore_errors=True)
    return 0


def _flash_live(injected_path: str, code: str, slot: int,
                role_display: str, assume_yes: bool,
                accumulate: bool = False,
                post_write_slots: list[dict] | None = None,
                overwrite_gate: bool = False,
                baseline_bytes: bytes | None = None) -> None:
    """ADVANCED: flash the injected dump to the real chip. Confirmation-gated,
    reusing recover-baseline.py's safety posture (loud-fail on missing
    programmer, explicit gate, fully-qualified device string).

    `accumulate` chooses the post-write verdict: True (default --live path) means
    the lock kept its prior codes and gained the new one, so the verdict
    RE-DECODES the actual injected slot table (`post_write_slots`); False (the
    explicit --reset-baseline path) means the deterministic sample-flash state, so
    the verdict uses lands_on_lock_summary().

    `overwrite_gate` (accumulate path only) adds a SECOND, slot-specific
    confirmation when the write would evict a DIFFERENT live code from `slot` —
    the existing occupant is shown (reusing occupied_slot_warning's formatting off
    `baseline_bytes`) and an explicit yes is required before flashing. --yes /
    assume_yes honours the panel's pre-granted confirmation on both gates."""
    minipro_bin = decode_codes.resolve_minipro()
    if minipro_bin is None:
        # Shared, actionable message (bundled binary + install helper + Mac/Win).
        # The injected dump is already saved, so note that before the message.
        sys.exit(
            f"  (Your injected dump was still built and saved at {injected_path}; "
            f"the SAFE path stops here.)\n"
            + decode_codes.minipro_not_found_message("live write")
        )
    # No sudo: the uaccess udev rule grants the logged-in user direct device
    # access, so minipro runs as the unprivileged attendee. Same command the
    # preview path advertises (live_write_command), now actually run with the
    # RESOLVED binary (PATH minipro, else the bundled bin/minipro).
    cmd = live_write_command(injected_path, minipro_bin)
    print("=" * 72)
    print("  LIVE CHIP WRITE — advanced, confirmation gate")
    print("=" * 72)
    print(f"  This will ERASE + REPROGRAM the real lock's page-0 with your")
    print(f"  custom code {code} in slot {slot} ({role_display}).")
    if accumulate:
        print(f"  ACCUMULATE: the chip's CURRENT codes were read first and are "
              f"preserved;")
        print(f"  your code is ADDED to them (all other slots kept).")
    else:
        print(f"  RESET: the lock is re-seeded to the sample state "
              f"(3 demo codes + 123456)")
        print(f"  with your code added — any other codes currently on the chip "
              f"are wiped.")
    print(f"  Clip must be seated on the AT45DB041E; lock batteries OUT.")
    print(f"  Recovery is always available: recover-baseline.py restores the")
    print(f"  canonical baseline (MD5-gated).")
    print(f"  Command:")
    print(f"    {' '.join(cmd)}")
    print("=" * 72)

    # Real-overwrite confirmation gate. Only fires on the accumulate path when the
    # target slot holds a DIFFERENT active code; an empty slot or a same-code
    # re-write never reaches here. Show exactly whose code is about to go, reusing
    # occupied_slot_warning's formatting, then require an explicit yes (honouring
    # --yes / assume_yes for the panel's pre-granted path).
    if overwrite_gate and baseline_bytes is not None:
        occupant = occupied_slot_warning(baseline_bytes, slot)
        print()
        print(f"  OVERWRITE — slot {slot} already holds a DIFFERENT live code.")
        if occupant is not None:
            print(f"  {occupant}")
        if not assume_yes:
            try:
                ans = input(f"  Overwrite slot {slot}'s existing code with {code}? "
                            f"[yes/N]: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                sys.exit("\nERROR: overwrite confirmation aborted — no live write "
                         "performed.")
            if ans not in ("yes", "y"):
                sys.exit("ERROR: overwrite declined — no live write performed. "
                         "Pick an empty slot and re-run.")
        print()

    if not assume_yes:
        try:
            answer = input("  Proceed with LIVE write? [yes/N]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            sys.exit("\nERROR: confirmation aborted — no live write performed.")
        if answer not in ("yes", "y"):
            sys.exit("ERROR: confirmation declined — no live write performed.")
    print()
    print(f"  $ {' '.join(cmd)}")
    print()
    try:
        rc = subprocess.call(cmd)
    except FileNotFoundError as e:
        sys.exit(f"ERROR: {e}. minipro lives at /usr/local/bin/minipro.")
    except KeyboardInterrupt:
        sys.exit("\nERROR: live write aborted (Ctrl-C). The chip may be in a "
                 "partially-written state — run recover-baseline.py to restore.")
    if rc != 0:
        sys.exit(
            f"ERROR: minipro write returned exit code {rc}. Re-seat the clip "
            f"and re-run, or run recover-baseline.py to restore the baseline."
        )
    print()
    if accumulate and post_write_slots is not None:
        # ACCUMULATE verdict: the lock kept whatever it had and gained the new
        # code. lands_on_lock_summary would be FALSE here, so print the ACTUAL
        # post-write slot table (the same one re-decoded above) instead.
        print(f"  LIVE WRITE OK — landed on the REAL chip. Your code {code} "
              f"(slot {slot}, {role_display}) was ADDED to the lock's existing "
              f"codes.")
        decode_codes.print_table(
            post_write_slots, show_all=False,
            source_label="the REAL chip after your accumulate write")
    else:
        # RESET verdict: the deterministic sample-flash state is on the chip.
        print(f"  LIVE WRITE OK — landed on the REAL chip. "
              f"{lands_on_lock_summary(code, slot, role_display)}")
    print("  Reinstall the lock batteries and try your code on the keypad.")
    print("  If anything is wrong, run recover-baseline.py.")
    print()


# ---------------------------------------------------------------------------
# Panel-callable entry points (programmatic, no input() deadlock)
# ---------------------------------------------------------------------------
def _ns(**kw):
    """Build a SimpleNamespace args object the cmd_* functions accept. Fills the
    optional fields cmd_read/cmd_write read so the panel doesn't have to."""
    from types import SimpleNamespace
    return SimpleNamespace(**kw)


def read_live(show_all: bool = True) -> int:
    """LIVE READ entry point for the browser panel (or any programmatic caller).

    Reads the real chip via minipro and prints the decoded user-code table to
    stdout. No input() anywhere on this path, so it is safe to call from inside
    an HTTP handler with stdout captured. Loud-fails (SystemExit) if minipro is
    missing or the clip did not bite — the caller surfaces that text. Returns 0
    on success.
    """
    return cmd_read(_ns(dump=None, all=show_all, live=True))


def flash_attendee_live(code: str, slot: int = 25, role: str | None = None,
                        out: str | None = None,
                        reset_baseline: bool = False) -> int:
    """LIVE WRITE entry point for the browser panel — confirmation PRE-GRANTED.

    The panel does its own confirmation in the browser, then calls this. Two
    flavours, picked by `reset_baseline`:

      * reset_baseline=False (the STANDARD panel ADD button) — ACCUMULATE: read
        the real chip first and ADD the attendee's `code` at `slot`/`role` on top,
        preserving every code already on the lock.
      * reset_baseline=True (the explicit panel RESET button) — flash the
        canonical SAMPLE-flash state: a copy of the bundled sample dump (the three
        demo codes at slots 19/32/49 + the 123456 starter at slot 0) with the
        attendee's code injected. Deterministic, repeatable; see
        lands_on_lock_summary() for the exact contents to display.

    yes=True is passed through to cmd_write -> _flash_live(assume_yes=True), so
    NO input() is ever reached on EITHER gate (the overwrite gate honours it too):
    this will not deadlock in an HTTP handler. The loud-fail-on-missing-minipro
    guard, the loud-fail-on-bad-read guard (accumulate path), and the
    recover-baseline.py safety language are preserved. Returns 0 on a successful
    flash; raises SystemExit (with operator-facing text) on any failure the
    caller can show.
    """
    return cmd_write(_ns(code=code, slot=slot, role=role, out=out,
                         baseline_dump=None, live=True, yes=True,
                         reset_baseline=reset_baseline))


# ---------------------------------------------------------------------------
# Self-test — no hardware. Exercises a full write-into-a-copy + re-decode round
# trip for a custom code (including a zero digit, to hit the 0xB rule) and
# confirms the re-decode reads back exactly what was written.
# ---------------------------------------------------------------------------
def run_self_test() -> int:
    print("lock-tool.py self-test")
    failures = 0

    def check(label, ok, detail=""):
        nonlocal failures
        print(f"  [{'PASS' if ok else 'FAIL'}] {label} {detail}")
        if not ok:
            failures += 1

    # Role resolution
    perm, name = resolve_role("supervisor")
    check("role 'supervisor' -> 0xC1", perm == 0xC1, f"(got 0x{perm:02X} {name})")
    perm, name = resolve_role(None)
    check("default role -> Normal User 0x01", perm == 0x01, f"(got 0x{perm:02X} {name})")
    perm, name = resolve_role("0xF1")
    check("role '0xF1' -> Master", perm == 0xF1, f"(got 0x{perm:02X} {name})")

    # Full encode -> apply -> re-decode round trip on a synthetic baseline, with
    # a zero digit to exercise the 0xB-for-zero path end to end.
    page = bytearray([0xFF] * DUMP_SIZE)
    page[0] = 0xFD
    # seed slot 0 = 123456 Normal so the baseline validates + has a known slot
    page[build_injected.OFF_CODE_BYTE_1] = 0x12
    page[build_injected.OFF_CODE_BYTE_2] = 0x34
    page[build_injected.OFF_CODE_BYTE_3] = 0x56
    page[build_injected.OFF_ACTIVE] = 0x01
    page[build_injected.OFF_PERM] = 0x01
    baseline = bytes(page)
    test_code = "240680"   # contains zeros -> exercises 0xB nibble
    patches = [{"slot": 25, "code": test_code, "perm": 0xC1, "perm_name": "Supervisor"}]
    build_injected.validate_patches(patches)
    injected, _changes = build_injected.apply_patches(baseline, patches)
    slots = decode_codes.parse_slots(injected)
    s25 = next(s for s in slots if s["slot"] == 25)
    check("write 240680 -> slot 25 re-decodes to 240680",
          s25["code"] == test_code and s25["active"],
          f"(got {s25['code']!r}, active={s25['active']})")
    check("slot 25 role is Supervisor", s25["role"] == "Supervisor",
          f"(got {s25['role']!r})")
    # untouched slot 0 still reads 123456
    s0 = next(s for s in slots if s["slot"] == 0)
    check("untouched slot 0 still 123456", s0["code"] == "123456",
          f"(got {s0['code']!r})")

    # Occupied-slot warning: slot 0 is active in `baseline`, so writing to it
    # must emit the warning; an empty slot (25) must NOT. Assert on the pure
    # helper so the contract holds without capturing cmd_write's stdout.
    warn_occupied = occupied_slot_warning(baseline, 0)
    check("occupied slot 0 emits warning",
          warn_occupied is not None and "already occupied" in warn_occupied
          and "123456" in warn_occupied,
          f"(got {warn_occupied!r})")
    check("empty slot 25 emits no warning",
          occupied_slot_warning(baseline, 25) is None,
          f"(got {occupied_slot_warning(baseline, 25)!r})")

    # Real-overwrite gate predicate (overwrites_different_code). This drives the
    # live+accumulate confirmation, so its three cases are load-bearing. `baseline`
    # has slot 0 = 123456 active; slot 25 empty. Pure logic, hardware-free.
    check("overwrite gate: occupied slot 0 with a DIFFERENT code -> True",
          overwrites_different_code(baseline, 0, "999999") is True,
          f"(got {overwrites_different_code(baseline, 0, '999999')!r})")
    check("overwrite gate: EMPTY slot 25 -> False (clean add)",
          overwrites_different_code(baseline, 25, "999999") is False,
          f"(got {overwrites_different_code(baseline, 25, '999999')!r})")
    check("overwrite gate: occupied slot 0 with the SAME code -> False (idempotent)",
          overwrites_different_code(baseline, 0, "123456") is False,
          f"(got {overwrites_different_code(baseline, 0, '123456')!r})")

    # D2: the live minipro write command surfacing is exact + copy-pasteable.
    wcmd = live_write_command("/tmp/injected.bin")
    check("live write command is the minipro -c code -w invocation",
          wcmd == [MINIPRO_BIN, "-i", "-p", DEVICE_NAME, "-c", "code",
                   "-w", "/tmp/injected.bin"],
          f"(got {' '.join(wcmd)!r})")
    rcmd = decode_codes.live_read_command("/tmp/live-read.bin")
    check("live read command is the minipro -c code -r invocation",
          rcmd == [decode_codes.MINIPRO_BIN, "-i", "-p", decode_codes.DEVICE_NAME,
                   "-c", "code", "-r", "/tmp/live-read.bin"],
          f"(got {' '.join(rcmd)!r})")

    # D4: the RESET-path 'what lands on the lock' summary names the attendee code
    # + all three demo codes + the starter, so the panel's RESET button can
    # display it verbatim. (The default --live ACCUMULATE path does NOT use this
    # summary — it re-decodes the actual chip; that path is hardware-gated, so the
    # accumulate baseline-selection / overwrite-gate logic is covered above by the
    # pure overwrites_different_code() checks, not by a live read here.)
    summary = lands_on_lock_summary("246810", 25, "Normal User")
    check("RESET-path lands-on-lock summary names attendee code + 3 demos + starter",
          "246810" in summary and "133769" in summary and "420420" in summary
          and "696969" in summary and "123456" in summary,
          f"(got {summary!r})")

    # Preview (no-hardware, file-based) cmd_write end-to-end through stdout
    # capture. This exercises the NON-live cmd_write branch — baseline selection
    # must stay file-based (accumulate must NOT engage without --live), and the
    # reworded PREVIEW banner must state the live path reads the chip first.
    # Skips cleanly if the bundled sample dump isn't reachable from this layout
    # (still hardware-free; never touches a chip).
    import io
    from contextlib import redirect_stdout
    if decode_codes.find_sample_dump() is not None:
        buf = io.StringIO()
        pv_args = _ns(code="246810", slot=25, role="supervisor", out=None,
                      baseline_dump=None, live=False, yes=False,
                      reset_baseline=False)
        with redirect_stdout(buf):
            try:
                cmd_write(pv_args)
            except SystemExit:
                pass
        pv = buf.getvalue()
        check("preview write shows PREVIEW-ONLY banner + decodes the custom code",
              "PREVIEW ONLY — nothing was written to the lock." in pv
              and "246810" in pv,
              f"({len(pv)} chars)")
        check("preview banner states --live reads the REAL chip first + adds to it",
              "reads the REAL chip first" in pv
              and "ADDS your code" in pv,
              "(reworded banner)")
        check("preview banner names the explicit --reset-baseline opt-in",
              "--reset-baseline" in pv)
    else:
        check("preview write check skipped (no bundled sample reachable here)",
              True, "(SKIP — file-based path only)")

    # Roll the bundled-tool self-tests in so a regression in either sibling also
    # fails lock-tool --self-test.
    print()
    print("  --- decode-codes.py decoder self-test ---")
    rc_dec = decode_codes.run_self_test()
    if rc_dec != 0:
        failures += 1

    print()
    if failures:
        print(f"  RESULT: FAIL — {failures} lock-tool check(s) failed.")
        return 1
    print("  RESULT: PASS — read/write round trip holds.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Read or write the AT45DB041E lock user-code table. READ decodes the "
            "page-0 table; WRITE bakes your own custom code into a copy of the "
            "sample dump and shows you the result. Safe sample-dump-copy path by "
            "default; --live is the advanced real-chip path."
        )
    )
    parser.add_argument("--self-test", action="store_true",
                        help="run the read/write round-trip self-test and exit")
    sub = parser.add_subparsers(dest="command")

    p_read = sub.add_parser("read", help="decode + print the user-code table")
    p_read.add_argument("--dump", default=None,
                        help="decode this dump file instead of the bundled sample")
    p_read.add_argument("--all", action="store_true",
                        help="list every slot including empty ones")
    p_read.add_argument("--live", action="store_true",
                        help="ADVANCED: read the real chip first, then decode")

    p_write = sub.add_parser("write", help="bake a custom code into a copy + re-decode")
    p_write.add_argument("--code", required=True,
                         help="your 6-digit code, e.g. 246810 (zeros allowed)")
    p_write.add_argument("--slot", type=int, default=25,
                         help=f"slot 0..{MAX_SLOT} to write into (default 25)")
    p_write.add_argument("--role", default=None,
                         help="master | elevated | supervisor | normal "
                              "(or a hex perm byte; default normal)")
    p_write.add_argument("--out", default=None,
                         help="write the injected dump here (default: a tempfile)")
    p_write.add_argument("--baseline-dump", default=None,
                         help="build from this baseline instead of the bundled sample")
    p_write.add_argument("--live", action="store_true",
                         help="ADVANCED: flash the result to the real chip "
                              "(confirmation-gated). By default ACCUMULATES: reads "
                              "the chip first and adds your code, keeping existing "
                              "codes")
    p_write.add_argument("--reset-baseline", "--from-sample", action="store_true",
                         dest="reset_baseline",
                         help="with --live: do NOT accumulate — wipe-and-reseed "
                              "the chip to the bundled sample (3 demo codes + "
                              "123456) plus your code. Ignored without --live")
    p_write.add_argument("--yes", action="store_true",
                         help="skip the live-write confirmation (batch only)")

    args = parser.parse_args()

    if args.self_test:
        sys.exit(run_self_test())
    if args.command == "read":
        sys.exit(cmd_read(args))
    if args.command == "write":
        sys.exit(cmd_write(args))
    parser.print_help()
    sys.exit(2)


if __name__ == "__main__":
    main()
