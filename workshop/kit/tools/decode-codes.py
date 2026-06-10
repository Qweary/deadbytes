#!/usr/bin/env python3
"""
decode-codes.py — Read and decode the AT45DB041E page-0 user-code table.

The one-command READ for the "Dead Bytes Tell No Lies" workshop. Dumps the
page-0 user-code page into a readable parse and prints it: per active slot the
slot number, the decoded 6-digit code (handling the 0xB-for-zero rule), the
active state, and the permission role name. Empty slots (active flag 0xFF /
permission 0xFF) are rendered as empty rather than crashing or printing garbage.

Two modes:
  - SAMPLE (default): decode the bundled sample dump. Operates on a COPY of the
    bundled baseline so the original is never touched. No hardware required.
  - LIVE (--live, advanced opt-in): read the real chip via `minipro ... -r`
    first, then decode that fresh read. Guarded: a missing programmer fails loud.
    No sudo: the installed uaccess udev rule grants the logged-in user direct
    device access.

STDLIB-ONLY. No pip, no internet, no non-stdlib imports. A fresh offline Kali
laptop runs this with nothing but python3 + the bundled files.

Usage:
    python3 decode-codes.py                       # decode bundled sample (a copy)
    python3 decode-codes.py --dump my-dump.bin    # decode a specific dump file
    python3 decode-codes.py --live                # read real chip, then decode
    python3 decode-codes.py --all                 # also list empty slots
    python3 decode-codes.py --self-test           # decoder self-test, no hardware

This is the safe educational path. Default operates on a copy of a sample dump,
never the original and never live hardware unless you explicitly pass --live.
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile

# ---------------------------------------------------------------------------
# Layout constants — sourced from DATAFLASH-DECODE-REFERENCE.md §3-§5. Kept
# byte-identical to build-injected.py's offset map so the read tool and the
# write tool agree on where every field lives.
# ---------------------------------------------------------------------------
DUMP_SIZE = 540_672          # AT45DB041E main array: 2048 pages * 264 bytes
DUMP_SIZE_WITH_SR = 540_800  # main + 128-byte Security Register (NOT minipro -w scope)

PAGE0_MARKER_LOW_NIBBLE = 0x0D   # byte0 & 0x0F must equal this (§2)
FACTORY_HIGH_NIBBLE = 0xF        # factory-state high nibble; != is informational
NUM_SLOTS = 50                   # slots 0..49

OFF_CODE_BYTE_1 = 0x0001
OFF_CODE_BYTE_2 = 0x0033
OFF_CODE_BYTE_3 = 0x0065
OFF_ACTIVE      = 0x0097
OFF_PERM        = 0x00C9

ACTIVE_FLAG = 0x01
EMPTY_FLAG  = 0xFF

# Permission flag value -> human role name (§4). 0xFF is the empty marker.
PERM_NAMES = {
    0xF1: "Master",
    0xE1: "Elevated User",
    0xC1: "Supervisor",
    0x01: "Normal User",
    0x11: "Role 0x11",
    0x21: "Role 0x21",
    0x31: "Role 0x31",
    0x41: "Role 0x41",
    0xFF: "(empty)",
}

# Bundled sample dump — resolved relative to this script so it works whether the
# tool runs from workshop/src/ (dev) or ~/workshop/tools/ (station). The dump
# lives in a sibling dumps/ directory in both layouts.
#
# This is the TEACHING SAMPLE, deliberately DISTINCT from the recovery baseline:
# it is the canonical baseline with the three default workshop codes injected
# additively at slots 19/32/49 (133769 Master / 420420 Elevated / 696969
# Supervisor). The recovery baseline (intact-lock-...-main-2026-05-20.bin) stays
# code-free so recover-baseline.py's MD5 gate is never corrupted; the tools READ
# this sample by default, so decode shows the three teaching codes out of the box
# and lock-tool's custom writes stack ON TOP of them.
SAMPLE_DUMP_NAME = "workshop-sample-3codes-AT45DB041E-2026-05-20.bin"
EXPECTED_SAMPLE_MD5 = "741dcc79d9975b956d9e1c0a14de0e2b"

DEVICE_NAME = "AT45DB041E[Page264]@SOIC8"   # fully-qualified minipro device entry
MINIPRO_BIN = "minipro"
# No sudo for device access: the installed 61-minipro-uaccess.rules udev rule
# (ENV{ID_MINIPRO}=="1", TAG+="uaccess") grants the logged-in user direct access
# to the programmer, so minipro runs unprivileged. SUDO_BIN is retained only for
# any code that still references it; it no longer prefixes the minipro call.
SUDO_BIN = "sudo"


def find_sample_dump() -> str | None:
    """Locate the bundled sample dump relative to this script.

    Checked, in order:
      - <script-dir>/dumps/<name>            (kit/tools sibling-less; tools at root)
      - <script-dir>/../dumps/<name>         (kit/tools -> kit/dumps; station layout)
      - <script-dir>/../kit/dumps/<name>     (workshop/src -> workshop/kit/dumps; dev)
      - ~/workshop/dumps/<name>              (installed station tree)
    First existing wins; None if nothing found.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(here, "dumps", SAMPLE_DUMP_NAME),
        os.path.join(here, "..", "dumps", SAMPLE_DUMP_NAME),
        os.path.join(here, "..", "kit", "dumps", SAMPLE_DUMP_NAME),
        os.path.expanduser(os.path.join("~", "workshop", "dumps", SAMPLE_DUMP_NAME)),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return os.path.abspath(c)
    return None


def decode_nibble(nibble: int) -> str:
    """Decode one packed-BCD nibble to a single decimal-digit character.

    Per DATAFLASH-DECODE-REFERENCE.md §3a: digit 0 is stored as nibble value
    0xB. Nibbles 0x0-0x9 are their own digit. 0xB is digit 0. Any other nibble
    (0xA, 0xC-0xF) is not a valid code digit — render it as '?' so a garbage or
    partially-erased region is visibly flagged rather than silently mis-decoded.
    """
    if nibble == 0x0B:
        return "0"
    if 0x0 <= nibble <= 0x9:
        return str(nibble)
    return "?"


def decode_code(b1: int, b2: int, b3: int) -> str:
    """Decode three packed-BCD code bytes into a 6-character code string.

    Two digits per byte, high nibble first. Invalid nibbles become '?'.
    """
    out = []
    for b in (b1, b2, b3):
        out.append(decode_nibble((b >> 4) & 0x0F))
        out.append(decode_nibble(b & 0x0F))
    return "".join(out)


def role_name(perm: int) -> str:
    """Human role name for a permission byte; unknown values are labelled."""
    return PERM_NAMES.get(perm, f"Unknown (0x{perm:02X})")


def validate_page0(data: bytes, path: str) -> None:
    """Size + page-0 marker validation. Mirrors build-injected.py tone.

    Non-fatal NOTE when the high nibble is not 0xF (keypad-reprogrammed lock).
    """
    if len(data) != DUMP_SIZE:
        if len(data) == DUMP_SIZE_WITH_SR:
            sys.exit(
                f"ERROR: {path} is {len(data)} bytes; expected {DUMP_SIZE} "
                f"(AT45DB041E main array). Your file includes the 128-byte "
                f"Security Register — trim the trailing 128 bytes first, then "
                f"re-run. The first {DUMP_SIZE} bytes are the main array."
            )
        sys.exit(
            f"ERROR: {path} is {len(data)} bytes; expected {DUMP_SIZE} "
            f"(AT45DB041E main array, 2048 pages * 264 bytes). "
            f"If your dump is {DUMP_SIZE_WITH_SR} bytes, it includes the "
            f"128-byte Security Register — trim the trailing 128 bytes first."
        )
    if (data[0] & 0x0F) != PAGE0_MARKER_LOW_NIBBLE:
        sys.exit(
            f"ERROR: {path} byte 0 = 0x{data[0]:02X}; its low nibble "
            f"0x{data[0] & 0x0F:X} is not the page-0 user-code marker "
            f"0x{PAGE0_MARKER_LOW_NIBBLE:X} (factory locks read 0xFD, "
            f"keypad-reprogrammed locks read e.g. 0x1D — both low-nibble 0xD). "
            f"This does not look like a valid page-0 dump. An all-0x00 (blank) "
            f"or all-0xFF (erased) read fails here — re-read the chip and check "
            f"clip contact."
        )
    if (data[0] >> 4) != FACTORY_HIGH_NIBBLE:
        print(
            f"NOTE: {path} byte 0 = 0x{data[0]:02X} — header high-nibble "
            f"0x{data[0] >> 4:X}, expected 0x{FACTORY_HIGH_NIBBLE:X} for a "
            f"factory-state lock. This lock appears keypad-reprogrammed; "
            f"proceeding (low-nibble 0xD marker is valid)."
        )


def parse_slots(data: bytes) -> list[dict]:
    """Parse all 50 slots into a list of dicts.

    Each entry: slot, active (bool), active_raw, code (str), b1/b2/b3,
    perm (int), role (str), empty (bool). An empty slot is one whose active
    flag is the empty marker (0xFF) — its code is still decoded for display
    completeness but flagged empty so the caller can render it as blank.
    """
    slots = []
    for n in range(NUM_SLOTS):
        b1 = data[OFF_CODE_BYTE_1 + n]
        b2 = data[OFF_CODE_BYTE_2 + n]
        b3 = data[OFF_CODE_BYTE_3 + n]
        active_raw = data[OFF_ACTIVE + n]
        perm = data[OFF_PERM + n]
        is_active = (active_raw == ACTIVE_FLAG)
        # "Empty" = the active flag says empty. A slot with a non-0x01,
        # non-0xFF active byte is neither cleanly active nor cleanly empty;
        # treat it as not-active but surface the raw byte in --all view.
        is_empty = (active_raw == EMPTY_FLAG)
        slots.append({
            "slot": n,
            "active": is_active,
            "active_raw": active_raw,
            "empty": is_empty,
            "b1": b1, "b2": b2, "b3": b3,
            "code": decode_code(b1, b2, b3),
            "perm": perm,
            "role": role_name(perm),
        })
    return slots


def active_state_label(s: dict) -> str:
    if s["active"]:
        return "ACTIVE"
    if s["empty"]:
        return "empty"
    return f"?(0x{s['active_raw']:02X})"


def print_table(slots: list[dict], show_all: bool, source_label: str) -> None:
    """Render the decoded slot table. By default only active slots are listed;
    --all lists every slot including empties (rendered as blank code/role)."""
    print()
    print("=" * 72)
    print(f"  AT45DB041E page-0 user-code table")
    print(f"  Source: {source_label}")
    print("=" * 72)
    print()

    active = [s for s in slots if s["active"]]
    rows = slots if show_all else active

    print(f"  {'slot':>4}  {'code':>8}  {'state':<12}  {'permission / role':<20}")
    print(f"  {'-'*4}  {'-'*8}  {'-'*12}  {'-'*20}")
    if not rows:
        print("  (no active slots)")
    for s in rows:
        if s["active"]:
            code_col = s["code"]
            role_col = f"0x{s['perm']:02X}  {s['role']}"
        elif s["empty"]:
            # Render empty slots as genuinely empty rather than as garbage.
            code_col = "—"
            role_col = "(empty)"
        else:
            code_col = s["code"]
            role_col = f"0x{s['perm']:02X}  {s['role']}"
        print(f"  {s['slot']:>4}  {code_col:>8}  "
              f"{active_state_label(s):<12}  {role_col:<20}")
    print()
    print(f"  Active slots: {len(active)} of {NUM_SLOTS}.")
    if not show_all:
        empties = sum(1 for s in slots if s["empty"])
        print(f"  Empty slots:  {empties} (hidden — pass --all to list them).")
    print()


def read_live_chip() -> str:
    """Read the real chip via minipro into a tempfile; return the path.

    ADVANCED / opt-in only. Reuses recover-baseline.py's minipro invocation
    posture: fully-qualified device name + standing -i flag. Fails LOUD if the
    programmer binary is missing rather than silently degrading.
    """
    if shutil.which(MINIPRO_BIN) is None:
        sys.exit(
            f"ERROR: --live requires the '{MINIPRO_BIN}' programmer on PATH and "
            f"a T48 clipped to the chip. '{MINIPRO_BIN}' was not found.\n"
            f"  This is the ADVANCED live-chip path. For the safe no-hardware "
            f"path, drop --live and the tool decodes the bundled sample dump.\n"
            f"  On a station, minipro installs to /usr/local/bin/minipro via "
            f"install.sh."
        )
    tmpdir = tempfile.mkdtemp(prefix="decode-live-")
    out_path = os.path.join(tmpdir, "live-read.bin")
    # No sudo: the uaccess udev rule grants the logged-in user direct device
    # access, so minipro runs as the unprivileged attendee.
    cmd = [MINIPRO_BIN, "-i", "-p", DEVICE_NAME, "-r", out_path]
    print()
    print("--- LIVE CHIP READ (advanced) ---")
    print(f"  $ {' '.join(cmd)}")
    print("  Clip must be seated on the AT45DB041E; lock batteries OUT.")
    print()
    try:
        rc = subprocess.call(cmd)
    except FileNotFoundError as e:
        sys.exit(f"ERROR: {e}. minipro lives at /usr/local/bin/minipro.")
    except KeyboardInterrupt:
        sys.exit("\nERROR: live read aborted (Ctrl-C). No file written.")
    if rc != 0:
        sys.exit(
            f"ERROR: minipro read returned exit code {rc}. If Chip ID was "
            f"0x0000 the clip did not bite — re-seat it and re-run. "
            f"(FACILITATOR-GUIDE.md 'Clip-bite failure ladder'.)"
        )
    if not os.path.isfile(out_path):
        sys.exit("ERROR: live read reported success but produced no file.")
    print("--- LIVE CHIP READ OK ---")
    return out_path


def load_sample_copy() -> tuple[str, str, bool]:
    """Locate the bundled sample dump and copy it to a tempfile.

    Returns (copy_path, source_label, is_temp). The decoder always operates on
    the COPY so the bundled original is never touched. is_temp=True tells the
    caller to clean the copy up afterward.
    """
    src = find_sample_dump()
    if src is None:
        sys.exit(
            "ERROR: could not locate the bundled sample dump "
            f"'{SAMPLE_DUMP_NAME}'.\n"
            "  Expected it in a sibling dumps/ directory next to this tool "
            "(kit/dumps/ in dev, ~/workshop/dumps/ on a station).\n"
            "  Pass --dump PATH to decode a specific file instead."
        )
    tmpdir = tempfile.mkdtemp(prefix="decode-sample-")
    copy_path = os.path.join(tmpdir, SAMPLE_DUMP_NAME)
    shutil.copy2(src, copy_path)
    label = f"bundled sample dump (working on a copy of {src})"
    return copy_path, label, True


def run_self_test() -> int:
    """Decoder self-test — no hardware, no filesystem dependency.

    Asserts the load-bearing decode contracts:
      1. packed-BCD nibble decode, incl 0xB -> '0'
      2. the worked slot-0 example 0x12/0x34/0x56 -> '123456'
      3. the 0xB-for-zero worked example 0x42/0xB4/0x2B -> '420420'
      4. role-name lookup for each documented permission value
      5. an all-0xFF empty slot decodes/render-flags as empty, not garbage
      6. invalid nibble (0xC) decodes to '?' rather than crashing
    Mirrors the other tools' --self-test discipline.
    """
    print("decode-codes.py decoder self-test")
    failures = 0

    def check(label, got, want):
        nonlocal failures
        ok = (got == want)
        print(f"  [{'PASS' if ok else 'FAIL'}] {label}: got={got!r} want={want!r}")
        if not ok:
            failures += 1

    check("nibble 0xB -> 0", decode_nibble(0x0B), "0")
    check("nibble 0x7 -> 7", decode_nibble(0x07), "7")
    check("nibble 0xC -> ?", decode_nibble(0x0C), "?")
    check("slot-0 worked example 12/34/56", decode_code(0x12, 0x34, 0x56), "123456")
    check("0xB-for-zero example 42/B4/2B", decode_code(0x42, 0xB4, 0x2B), "420420")
    check("role 0xF1", role_name(0xF1), "Master")
    check("role 0xC1", role_name(0xC1), "Supervisor")
    check("role 0xE1", role_name(0xE1), "Elevated User")
    check("role 0x01", role_name(0x01), "Normal User")
    check("role 0xFF", role_name(0xFF), "(empty)")

    # Empty-slot rendering: synthesize a 264-byte page with an all-empty table
    # plus slot 0 = 123456 active, and confirm parse flags exactly one active.
    page = bytearray([0xFF] * DUMP_SIZE)
    page[0] = 0xFD
    page[OFF_CODE_BYTE_1 + 0] = 0x12
    page[OFF_CODE_BYTE_2 + 0] = 0x34
    page[OFF_CODE_BYTE_3 + 0] = 0x56
    page[OFF_ACTIVE + 0] = 0x01
    page[OFF_PERM + 0] = 0x01
    slots = parse_slots(bytes(page))
    actives = [s for s in slots if s["active"]]
    check("synthetic page: exactly 1 active slot", len(actives), 1)
    check("synthetic page: slot 0 code", actives[0]["code"], "123456")
    check("synthetic page: slot 0 role", actives[0]["role"], "Normal User")
    check("synthetic page: slot 1 flagged empty", slots[1]["empty"], True)
    # An empty slot's active flag is the empty marker, not active.
    check("synthetic page: slot 1 not active", slots[1]["active"], False)

    print()
    if failures:
        print(f"  RESULT: FAIL — {failures} decode check(s) failed.")
        return 1
    print("  RESULT: PASS — decode contract holds.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Read and decode the AT45DB041E page-0 user-code table. Defaults to "
            "the bundled sample dump (operating on a copy, no hardware). Pass "
            "--live for the advanced read-the-real-chip path."
        )
    )
    parser.add_argument(
        "--dump", default=None,
        help="decode this specific dump file instead of the bundled sample")
    parser.add_argument(
        "--live", action="store_true",
        help="ADVANCED: read the real chip via minipro first, then decode")
    parser.add_argument(
        "--all", action="store_true",
        help="list every slot including empty ones (default: active slots only)")
    parser.add_argument(
        "--self-test", action="store_true",
        help="run the decoder self-test (no hardware) and exit")
    args = parser.parse_args()

    if args.self_test:
        sys.exit(run_self_test())

    cleanup_dir = None
    if args.live:
        dump_path = read_live_chip()
        source_label = f"LIVE chip read ({dump_path})"
        cleanup_dir = os.path.dirname(dump_path)
    elif args.dump is not None:
        dump_path = args.dump
        if not os.path.isfile(dump_path):
            sys.exit(f"ERROR: dump file not found: {dump_path}")
        source_label = dump_path
    else:
        dump_path, source_label, _is_temp = load_sample_copy()
        cleanup_dir = os.path.dirname(dump_path)

    try:
        with open(dump_path, "rb") as f:
            data = f.read()
        validate_page0(data, dump_path)
        slots = parse_slots(data)
        print_table(slots, show_all=args.all, source_label=source_label)
    finally:
        if cleanup_dir is not None:
            shutil.rmtree(cleanup_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
