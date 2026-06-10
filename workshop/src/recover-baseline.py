#!/usr/bin/env python3
"""
recover-baseline.py — Write the canonical workshop baseline back to a chip.

Defensive wrapper around `minipro -i -p 'AT45DB041E[Page264]@SOIC8' -w
<baseline>` that recovers a lock-board AT45DB041E from a botched workshop write.
Refuses to run unless the baseline file matches the bench-validated MD5 of the
intact-lock golden master, and unless the file is exactly 540,672 bytes (the
minipro main-array-only read scope, confirmed by bench validation). Defaults to
verifying the write with a read-back-and-compare; skip with --skip-verify if
workshop time pressure demands.

Baseline location is auto-detected so a facilitator on a workshop station need
not pass --baseline under live time pressure. When --baseline is NOT given, the
script walks an ordered candidate list — the operator bench path first, then the
workshop-station install path — and uses the first that EXISTS. The chosen path
is printed as auto-detected before the confirmation gate so the facilitator sees
exactly which baseline is about to be written. Passing --baseline explicitly
honors that path verbatim and the candidate list is not consulted. Whatever path
resolves, the size + MD5 gates run on it unchanged — those gates, not the path,
are the safety net.

Intended for the ToorCamp 2026 "Dead Bytes Tell No Lies" workshop.

Usage:
    python3 recover-baseline.py [--baseline PATH] [--yes] [--skip-verify]
    python3 recover-baseline.py --self-test
"""

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile

# ---------------------------------------------------------------------------
# Constants — load-bearing, sourced from bench validation.
#
# DUMP_SIZE — AT45DB041E main array, 2048 pages * 264 bytes. minipro's -w on
#   the device entry 'AT45DB041E[Page264]@SOIC8' round-trips exactly this scope
#   (confirmed by bench validation). Same constant used by build-injected.py.
#
# CANONICAL_BASELINE_MD5 — the bench-validated MD5 of the intact in-service lock
#   capture. Two independent reads byte-identical to this MD5 on the bench; the
#   same MD5 is the basis for build-injected.py's expected post-build MD5
#   (741dcc79d9975b956d9e1c0a14de0e2b) when the canonical 3-slot patch is
#   applied. FACILITATOR-GUIDE.md Pocket Reference also names this MD5 as
#   "Baseline MD5" — the workshop convention is one baseline per station, and
#   that one baseline IS this canonical master.
#
# CANONICAL_BASELINE_PATH — the operator-bench location of the baseline on the
#   bench machine where the golden master was first validated. This is the FIRST
#   candidate path when --baseline is not given.
#
# WORKSHOP_STATION_BASELINE_PATH — the location the facilitator-kit installer
#   (install.sh step 'populate-workshop') copies the byte-identical baseline to
#   on every station laptop (per FACILITATOR-GUIDE.md "Software verification" and
#   "Per programmer station"). This is the SECOND candidate path.
#
# CANONICAL_BASELINE_CANDIDATES — the ordered auto-detect list, used ONLY when
#   --baseline is not supplied. Order is additive: bench path first (preserves
#   the historical default so an operator running on the bench sees no behavior
#   change), then station path (so a facilitator on a station laptop no longer
#   needs --baseline). First path that EXISTS wins. The two files are MD5-
#   identical, so order is a tie-break-by-locality convenience, not a safety
#   decision — the MD5 + size gates run on whichever resolves and are the actual
#   safety net. An explicit --baseline bypasses this list entirely.
#
# DEVICE_NAME — the fully-qualified, page-mode-qualified, package-suffixed
#   device string. Bare 'AT45DB041E' returns 'Device AT45DB041E not found!'
#   (bench finding).
#
# MINIPRO_FLAGS — '-i' is the standing skip-ID-check flag. The dry probe is the
#   once-per-session ID-check confirmation; subsequent operations use -i to avoid
#   intermittent Chip-ID 0x0000 stalls on this AT45DB041E sample against T48
#   firmware 00.1.34 (standing rule from bench testing).
# ---------------------------------------------------------------------------
DUMP_SIZE = 540_672
DUMP_SIZE_WITH_SR = 540_800    # main + 128-byte Security Register — NOT minipro -r scope
CANONICAL_BASELINE_MD5 = "eb6acff32ef13b29ac6ebed10d77316d"
CANONICAL_BASELINE_PATH = os.path.expanduser(
    "~/Desktop/toorcamp-2026-dumps/intact-lock-AT45DB041E-main-2026-05-20.bin"
)
WORKSHOP_STATION_BASELINE_PATH = os.path.expanduser(
    "~/workshop/dumps/intact-lock-AT45DB041E-main-2026-05-20.bin"
)
# Ordered auto-detect list — bench first (historical default preserved), then
# station. Consulted ONLY when --baseline is not given. First existing wins.
CANONICAL_BASELINE_CANDIDATES = [
    CANONICAL_BASELINE_PATH,
    WORKSHOP_STATION_BASELINE_PATH,
]
DEVICE_NAME = "AT45DB041E[Page264]@SOIC8"
MINIPRO_BIN = "minipro"
# Retained for compatibility; no longer prefixes minipro. The installed uaccess
# udev rule grants the logged-in user direct device access, so the live
# write/read runs unprivileged.
SUDO_BIN = "sudo"


def md5_of_file(path: str) -> str:
    """Stream-hash a file with MD5. Stdlib only; no pip deps."""
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve_baseline_path(explicit: str | None) -> tuple[str, bool]:
    """Resolve which baseline file to use. Single source of truth for path
    selection — --self-test, preflight, and main all route through here so the
    bench/station behavior is identical everywhere.

    Returns (path, auto_detected):
      - If `explicit` is not None, the operator passed --baseline. Honor it
        verbatim, do NOT consult the candidate list, and report it as not
        auto-detected (auto_detected=False). Existence/size/MD5 are still
        gated downstream — an explicit path that does not exist is the
        operator's mistake to see, exactly as before this change.
      - If `explicit` is None, walk CANONICAL_BASELINE_CANDIDATES in order and
        return the first that EXISTS, flagged auto_detected=True so the caller
        can tell the facilitator which one was chosen before a destructive
        write.
      - If `explicit` is None and NO candidate exists, exit cleanly listing
        every candidate path checked so the facilitator knows where to stage
        the file or what --baseline to pass.

    The two candidate files are MD5-identical by construction, so first-existing
    is a locality convenience, not a safety decision; the MD5 + size gates that
    run afterward are the real safety net regardless of which path wins.
    """
    if explicit is not None:
        return explicit, False
    for candidate in CANONICAL_BASELINE_CANDIDATES:
        if os.path.isfile(candidate):
            return candidate, True
    checked = "\n".join(f"    - {c}" for c in CANONICAL_BASELINE_CANDIDATES)
    sys.exit(
        f"ERROR: no baseline file found and --baseline was not given.\n"
        f"  Auto-detect checked these candidate paths, none existed:\n"
        f"{checked}\n"
        f"  Stage the canonical baseline at one of the above (per "
        f"FACILITATOR-GUIDE.md it ships on the station USB stick), or pass "
        f"--baseline PATH explicitly."
    )


def validate_baseline_size(data_len: int, path: str) -> None:
    """Size pre-flight — mirrors build-injected.py validate_baseline() tone.

    The 540,800-byte case gets its own explicit error message because that is
    the Xgpro/vendor-utility full-read scope (main + Security Register) per
    bench validation; an attendee who staged the wrong baseline file from a
    non-minipro source will hit this and need the 'trim the trailing 128 bytes'
    guidance.
    """
    if data_len == DUMP_SIZE:
        return
    if data_len == DUMP_SIZE_WITH_SR:
        sys.exit(
            f"ERROR: {path} is {data_len} bytes; expected {DUMP_SIZE} "
            f"(AT45DB041E main array, 2048 pages * 264 bytes). "
            f"Your file is {DUMP_SIZE_WITH_SR} bytes — that includes the "
            f"128-byte Security Register, which minipro's -w does not "
            f"round-trip on this device entry. Trim the trailing 128 bytes "
            f"first, then re-run."
        )
    sys.exit(
        f"ERROR: {path} is {data_len} bytes; expected {DUMP_SIZE} "
        f"(AT45DB041E main array, 2048 pages * 264 bytes). "
        f"If your dump is {DUMP_SIZE_WITH_SR} bytes, it includes the 128-byte "
        f"Security Register — trim the trailing 128 bytes first."
    )


def validate_baseline_md5(md5: str, path: str) -> None:
    """MD5 pre-flight — refuse to write anything other than the canonical
    baseline. Prevents accidentally writing a wrong-baseline file."""
    if md5 == CANONICAL_BASELINE_MD5:
        return
    sys.exit(
        f"ERROR: {path} has MD5 {md5}; expected {CANONICAL_BASELINE_MD5} "
        f"(the canonical intact-lock baseline). Refusing to write a "
        f"wrong-baseline file to the chip. Confirm you are pointing at the "
        f"workshop-shipped baseline at {CANONICAL_BASELINE_PATH}."
    )


def preflight(baseline_path: str) -> str:
    """Run size + MD5 pre-flight; return the validated MD5.

    `baseline_path` here has already been resolved by resolve_baseline_path —
    an auto-detected path is guaranteed to exist, so this not-found branch only
    fires for an explicit --baseline that points at a missing file. (The
    no-candidate-found case is handled, with a full candidate-list message, in
    resolve_baseline_path.)
    """
    if not os.path.isfile(baseline_path):
        candidates = "\n".join(f"    - {c}" for c in CANONICAL_BASELINE_CANDIDATES)
        sys.exit(
            f"ERROR: baseline file not found at {baseline_path}.\n"
            f"  You passed this path with --baseline; it does not exist. "
            f"Drop the flag to auto-detect from these candidate locations:\n"
            f"{candidates}\n"
            f"  Per FACILITATOR-GUIDE.md the baseline ships on the station USB "
            f"stick at every station."
        )
    data_len = os.path.getsize(baseline_path)
    validate_baseline_size(data_len, baseline_path)
    md5 = md5_of_file(baseline_path)
    validate_baseline_md5(md5, baseline_path)
    return md5


def build_minipro_cmd(baseline_path: str, output_path: str | None = None,
                      mode: str = "write") -> list[str]:
    """Construct the minipro argv. mode ∈ {'write','read'}.

    Read mode targets `output_path` (for the post-write verify); write mode
    targets `baseline_path` (the canonical baseline). Both use the standing
    -i flag and the fully-qualified device name (per bench validation).

    No sudo: the uaccess udev rule grants the logged-in user direct device
    access, so minipro runs as the unprivileged facilitator/attendee.
    """
    if mode == "write":
        return [MINIPRO_BIN, "-i", "-p", DEVICE_NAME, "-w", baseline_path]
    if mode == "read":
        assert output_path is not None
        return [MINIPRO_BIN, "-i", "-p", DEVICE_NAME, "-r", output_path]
    raise ValueError(f"unknown mode {mode!r}")


def confirm_or_exit(baseline_path: str, baseline_md5: str, do_verify: bool) -> None:
    """Interactive confirmation gate. --yes bypasses this."""
    cmd = build_minipro_cmd(baseline_path, mode="write")
    print()
    print("=" * 72)
    print("  RECOVERY-BASELINE WRITE — confirmation gate")
    print("=" * 72)
    print(f"  Target chip:         AT45DB041E (in-circuit, SOIC-8 clip, via T48)")
    print(f"  Baseline file:       {baseline_path}")
    print(f"  Baseline MD5:        {baseline_md5}")
    print(f"                       (matches canonical baseline — OK)")
    print(f"  Baseline size:       {DUMP_SIZE:,} bytes")
    print(f"  Expected post-write: {baseline_md5}")
    print(f"                       (read-back of main array should match baseline)")
    print(f"  Post-write verify:   {'ON  (read-back + cmp, ~20s extra)' if do_verify else 'OFF (--skip-verify)'}")
    print(f"  Command to execute:")
    print(f"    {' '.join(cmd)}")
    print("=" * 72)
    print()
    print("  This will erase + reprogram the chip's main array. The clip must")
    print("  be seated on the AT45DB041E and the lock batteries must be OUT.")
    print()
    try:
        answer = input("  Proceed with recovery write? [yes/N]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        sys.exit("\nERROR: confirmation gate aborted — no write performed.")
    if answer not in ("yes", "y"):
        sys.exit("ERROR: confirmation declined — no write performed.")


def run_streaming(cmd: list[str], label: str) -> None:
    """Run a subprocess, streaming stdout/stderr to the operator in real time.

    No capture — minipro's ~20-second write needs to be visible at the
    workshop so the facilitator can see progress and the verification line.
    Silence during the write would be terrifying.
    """
    print()
    print(f"--- {label} ---")
    print(f"  $ {' '.join(cmd)}")
    print()
    try:
        rc = subprocess.call(cmd)
    except FileNotFoundError as e:
        sys.exit(f"ERROR: {e}. Is minipro installed and on PATH? "
                 f"The binary lives at /usr/local/bin/minipro.")
    except KeyboardInterrupt:
        sys.exit(f"\nERROR: {label} aborted by operator (Ctrl-C). The chip "
                 f"may now be in a partially-written state. Re-run this "
                 f"script to complete the recovery.")
    if rc != 0:
        sys.exit(f"ERROR: {label} returned exit code {rc}. The recovery "
                 f"write did not complete cleanly. Check clip contact "
                 f"(FACILITATOR-GUIDE.md Pocket Reference 'Clip-bite failure "
                 f"ladder') and re-run.")
    print()
    print(f"--- {label} OK ---")


def verify_write(baseline_path: str, baseline_md5: str) -> None:
    """Read the chip back to a tempfile and MD5-compare against the baseline.

    Adds ~20 seconds. Default-on (recommended) because workshop time pressure
    is real but silent corruption is worse — an attendee leaves the station
    believing the recovery took when in fact the chip is still in a bad state.
    --skip-verify is the opt-out for facilitators who would rather rotate the
    next attendee in and trust minipro's built-in 'Verification OK' line.
    """
    tmpdir = tempfile.mkdtemp(prefix="recover-verify-")
    readback_path = os.path.join(tmpdir, "post-recovery.bin")
    try:
        cmd = build_minipro_cmd(baseline_path, output_path=readback_path, mode="read")
        run_streaming(cmd, "POST-WRITE VERIFY READ")
        actual_size = os.path.getsize(readback_path)
        if actual_size != DUMP_SIZE:
            sys.exit(
                f"ERROR: post-write read-back is {actual_size} bytes; "
                f"expected {DUMP_SIZE}. The chip may not be in the expected "
                f"page mode. Re-run this script."
            )
        actual_md5 = md5_of_file(readback_path)
        print()
        print(f"  Baseline MD5:    {baseline_md5}")
        print(f"  Read-back MD5:   {actual_md5}")
        if actual_md5 != baseline_md5:
            sys.exit(
                f"ERROR: read-back MD5 does not match the baseline. The "
                f"recovery write reported success but the chip's contents "
                f"differ from the baseline. Re-seat the clip "
                f"(FACILITATOR-GUIDE.md Pocket Reference 'Clip-bite failure "
                f"ladder') and re-run this script. Read-back saved at "
                f"{readback_path} for diagnostics."
            )
        print()
        print("  POST-WRITE VERIFY: PASS — chip MD5 matches baseline MD5.")
    finally:
        # Clean up the verify tempfile unless we exited via a sys.exit above
        # that bypassed this block; we leave a partial readback in place on
        # error (the sys.exit message tells the operator where to find it).
        shutil.rmtree(tmpdir, ignore_errors=True)


def self_test_resolution() -> int:
    """Exercise resolve_baseline_path without touching hardware or the filesystem
    layout. Asserts the three contract branches:
      1. explicit path given  -> returned verbatim, auto_detected=False
      2. some candidate exists -> first existing returned, auto_detected=True
      3. no candidate exists   -> clean exit listing every candidate checked

    Mirrors build-injected.py's internal self-test discipline. Pure in-process
    checks: branch (2) is driven against this very source file (guaranteed to
    exist) by temporarily swapping the module candidate list, and branch (3)
    against a guaranteed-absent path; the real CANONICAL_BASELINE_CANDIDATES is
    restored in a finally so the live config is never left mutated.
    """
    global CANONICAL_BASELINE_CANDIDATES
    print(f"recover-baseline.py resolution self-test")
    saved = CANONICAL_BASELINE_CANDIDATES
    failures = 0
    try:
        # Branch 1 — explicit path is honored verbatim, list not consulted.
        explicit = "/some/operator/supplied/path.bin"
        path, auto = resolve_baseline_path(explicit)
        ok1 = (path == explicit and auto is False)
        print(f"  [1] explicit honored:      {'PASS' if ok1 else 'FAIL'} "
              f"(path={path!r}, auto={auto})")
        failures += 0 if ok1 else 1

        # Branch 2 — first existing candidate wins, flagged auto-detected.
        # Use an absent path ahead of a guaranteed-present one (this script
        # itself) to also prove ORDER: the missing first entry is skipped.
        present = os.path.abspath(__file__)
        CANONICAL_BASELINE_CANDIDATES = ["/no/such/baseline-A.bin", present]
        path, auto = resolve_baseline_path(None)
        ok2 = (path == present and auto is True)
        print(f"  [2] auto-detect first-hit: {'PASS' if ok2 else 'FAIL'} "
              f"(path={path!r}, auto={auto})")
        failures += 0 if ok2 else 1

        # Branch 3 — no candidate exists -> clean SystemExit listing candidates.
        CANONICAL_BASELINE_CANDIDATES = ["/no/such/baseline-A.bin",
                                         "/no/such/baseline-B.bin"]
        try:
            resolve_baseline_path(None)
            ok3 = False
            msg = "(did not exit)"
        except SystemExit as e:
            text = str(e)
            ok3 = all(c in text for c in CANONICAL_BASELINE_CANDIDATES)
            msg = "(exited, listed all candidates)" if ok3 else \
                  "(exited but candidate list incomplete)"
        print(f"  [3] no-candidate clean exit:{'PASS' if ok3 else 'FAIL'} {msg}")
        failures += 0 if ok3 else 1
    finally:
        CANONICAL_BASELINE_CANDIDATES = saved

    if failures:
        print(f"  RESULT:              FAIL — {failures} resolution check(s) failed.")
        return 1
    print(f"  RESULT:              PASS — path resolution contract holds.")
    return 0


def self_test(baseline_path: str, auto_detected: bool) -> int:
    """Validate the baseline file without touching hardware. Exits 0 on PASS.

    Mirrors build-injected.py's self-test discipline. The workshop facilitator-
    kit packaging exercises this as a stand-up check before the doors open. Runs
    the path-resolution contract gate first, then validates the resolved baseline
    file's size + MD5.
    """
    rc = self_test_resolution()
    print()
    print(f"recover-baseline.py self-test")
    if auto_detected:
        print(f"  Baseline path:       {baseline_path}  (auto-detected)")
    else:
        print(f"  Baseline path:       {baseline_path}")
    if not os.path.isfile(baseline_path):
        print(f"  RESULT:              FAIL — baseline file not found.")
        return 1
    data_len = os.path.getsize(baseline_path)
    print(f"  Baseline size:       {data_len:,} bytes (expected {DUMP_SIZE:,})")
    if data_len != DUMP_SIZE:
        print(f"  RESULT:              FAIL — size mismatch.")
        return 1
    md5 = md5_of_file(baseline_path)
    print(f"  Baseline MD5:        {md5}")
    print(f"  Expected MD5:        {CANONICAL_BASELINE_MD5}")
    if md5 != CANONICAL_BASELINE_MD5:
        print(f"  RESULT:              FAIL — MD5 mismatch.")
        return 1
    print(f"  RESULT:              PASS — baseline is the canonical master.")
    # Roll the earlier resolution-gate result into the overall exit code so a
    # resolution-contract regression also fails --self-test.
    return rc


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Write the canonical workshop baseline back to a lock-board "
            "AT45DB041E. Recovers from a botched attendee injection write. "
            "When --baseline is omitted, auto-detects the baseline from an "
            "ordered candidate list (bench path first, then workshop-station "
            "path); first existing wins and the chosen path is announced as "
            "auto-detected before the write."
        )
    )
    parser.add_argument(
        "--baseline", default=None,
        help=(f"path to the baseline dump to write back. If given, this exact "
              f"path is used (auto-detect is skipped). If omitted, auto-detect "
              f"checks, in order: {CANONICAL_BASELINE_PATH} then "
              f"{WORKSHOP_STATION_BASELINE_PATH}; the first that exists is used.")
    )
    parser.add_argument(
        "--yes", action="store_true",
        help="skip the interactive confirmation gate (batch operation)"
    )
    parser.add_argument(
        "--skip-verify", action="store_true",
        help=("skip the post-write read-back + MD5 compare (saves ~20s; "
              "default-on per workshop safety preference)")
    )
    parser.add_argument(
        "--self-test", action="store_true",
        help="validate the baseline file without touching hardware, then exit"
    )
    args = parser.parse_args()

    # Resolve the baseline path once, through the single source of truth.
    # `args.baseline is None` means the operator passed nothing -> auto-detect;
    # a concrete value means honor it verbatim. self-test, preflight, and the
    # write path all consume this same resolved pair.
    baseline_path, auto_detected = resolve_baseline_path(args.baseline)

    if args.self_test:
        sys.exit(self_test(baseline_path, auto_detected))

    # TRANSPARENCY — for a destructive write, the facilitator must see which
    # baseline was chosen and that it was auto-detected, BEFORE the gate below.
    if auto_detected:
        print()
        print(f"  Baseline auto-detected (no --baseline given):")
        print(f"    {baseline_path}")
        print(f"  Pass --baseline PATH to override.")

    # Pre-flight gates (size + MD5) — refuse before any hardware action. These
    # run on whatever path resolved; they, not the path, are the safety net.
    baseline_md5 = preflight(baseline_path)

    do_verify = not args.skip_verify

    if not args.yes:
        confirm_or_exit(baseline_path, baseline_md5, do_verify)

    # The write itself. Stream output so the operator sees minipro's progress
    # lines and the 'Verification OK' line minipro prints internally.
    write_cmd = build_minipro_cmd(baseline_path, mode="write")
    run_streaming(write_cmd, "RECOVERY WRITE")

    if do_verify:
        verify_write(baseline_path, baseline_md5)
    else:
        print()
        print("  --skip-verify set; trusting minipro's built-in verification.")
        print(f"  To verify manually:")
        print(f"    minipro -i -p '{DEVICE_NAME}' -r post-recovery.bin")
        print(f"    md5sum post-recovery.bin  # expect: {baseline_md5}")

    print()
    print("Recovery complete. The chip is back to the canonical baseline.")
    print("Unclip the SOIC-8, reinstall the lock batteries, and confirm")
    print("`123456` unlocks the lock (FACILITATOR-GUIDE.md Step 7).")
    print()


if __name__ == "__main__":
    main()
