#!/usr/bin/env bash
# start.sh — the attendee's one command. Run it from the cloned repo and the
# browser control panel opens. That's it.
#
#     ./bin/start.sh
#
# What it does: launches the no-hardware control panel, which opens your default
# browser to a local READ/WRITE GUI for the lock's user-code table. Everything
# runs locally with python3 and the bundled sample dump — no internet, no
# hardware, and NO sudo.
#
# If python3 is missing, or the panel can't start, this prints the bedrock CLI
# one-liners so you always have a way in.
#
# PATH-RELATIVE BY DESIGN: the repo root is resolved from THIS script's own
# location (start.sh lives in bin/, so the root is one level up). Nothing here
# hardcodes a home directory — clone the repo to ~, /tmp, or anywhere and this
# works unchanged.

set -uo pipefail

# ---------------------------------------------------------------------------
# Resolve the repo root from this script's own location. start.sh lives in
# bin/, so the repo root is its parent. Works whether invoked as
# ./bin/start.sh, /abs/path/bin/start.sh, or `bash bin/start.sh`.
# ---------------------------------------------------------------------------
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TOOLS_DIR="${REPO_ROOT}/workshop/kit/tools"
PANEL="${TOOLS_DIR}/lock-panel.py"
LOCK_TOOL="${TOOLS_DIR}/lock-tool.py"
BUNDLED_MINIPRO="${REPO_ROOT}/workshop/kit/bin/minipro"
INSTALL_HELPER="${REPO_ROOT}/workshop/kit/install.sh"

# ---------------------------------------------------------------------------
# Point the bundled minipro at its BUNDLED device database. On a clean machine
# the bundled binary's compiled DB path (/usr/local/share/minipro) does not
# exist, so chip profiling fails with a misleading "reclip" error. Sourcing the
# kit's minipro-env.sh exports an ABSOLUTE MINIPRO_HOME at the bundled share dir
# (REPLACE, not fallback — see that file) so the GUI path's child python (and the
# minipro it spawns) inherit it. The snippet is path-relative, only sets the var
# if the attendee has not already set their own, and no-ops if the share dir is
# absent — so this never fails the launch. The Python CLI/--live path injects the
# same value independently (decode-codes.py minipro_env()); it does NOT rely on
# this having run.
# ---------------------------------------------------------------------------
MINIPRO_ENV_SNIPPET="${REPO_ROOT}/workshop/kit/bin/minipro-env.sh"
if [ -f "$MINIPRO_ENV_SNIPPET" ]; then
    # shellcheck source=/dev/null
    . "$MINIPRO_ENV_SNIPPET"
fi

# ---------------------------------------------------------------------------
# Hardware-readiness note. The browser panel is the no-hardware default and
# needs NO minipro. But the panel ALSO offers an advanced "live chip" path that
# drives a real T48 over minipro, so surface — informationally, never fatally —
# where minipro stands:
#   - on PATH                -> ready (a station that ran install.sh)
#   - bundled in the kit     -> present, but device access still needs the udev
#                               rules; point at the install helper
#   - absent                 -> the kit BUNDLES minipro; point at the helper +
#                               give the Mac/Windows one-liners (the bundled
#                               binary is a Linux ELF and won't run there)
# This is printed once at startup and does not gate the GUI launch.
# ---------------------------------------------------------------------------
# minipro_on_path / bundled_minipro_present — tiny indirections so --self-test
# can drive print_hardware_note's three branches without a real minipro install
# or a real bundled binary on disk. In normal operation they reflect reality.
minipro_on_path() { command -v minipro >/dev/null 2>&1; }
bundled_minipro_present() { [ -x "$BUNDLED_MINIPRO" ]; }

print_hardware_note() {
    echo
    echo "----------------------------------------------------------------------"
    echo "  Advanced live-chip path (optional — the panel works with no hardware):"
    if minipro_on_path; then
        echo "    minipro is on PATH ($(command -v minipro 2>/dev/null || echo minipro)) — the live path is ready."
    elif bundled_minipro_present; then
        echo "    minipro is BUNDLED in this kit (no download/compile needed):"
        echo "      ${BUNDLED_MINIPRO}"
        echo "    Device access still needs the udev rules. Land them (+ minipro on"
        echo "    PATH) with the bundled helper:"
        echo "      sudo ${INSTALL_HELPER}"
        echo "      # or, from a fresh clone:  sudo ./bootstrap.sh"
    else
        echo "    minipro was not found on PATH and the bundled copy is missing."
        echo "    The kit normally BUNDLES a Linux x86-64 minipro; if this is a"
        echo "    Linux station, re-extract the kit, then run:"
        echo "      sudo ${INSTALL_HELPER}     (or, from a clone: sudo ./bootstrap.sh)"
        echo "    Mac:     brew install minipro"
        echo "    Windows: build from https://gitlab.com/DavidGriffith/minipro"
        echo "             (the bundled binary is a Linux ELF and will not run there)"
    fi
    echo "----------------------------------------------------------------------"
}

# ---------------------------------------------------------------------------
# The bedrock fallback. Printed whenever the GUI can't launch. These commands
# run the same no-hardware READ/WRITE the panel drives, straight from the CLI.
# ---------------------------------------------------------------------------
print_fallback() {
    echo
    echo "----------------------------------------------------------------------"
    echo "  CLI fallback — run these from the cloned repo (no browser needed):"
    echo "----------------------------------------------------------------------"
    echo "  READ  the codes:"
    echo "    python3 workshop/kit/tools/lock-tool.py read --all"
    echo
    echo "  WRITE your own code:"
    echo "    python3 workshop/kit/tools/lock-tool.py write --code 246810 --slot 25 --role supervisor"
    echo "----------------------------------------------------------------------"
    echo
}

# ---------------------------------------------------------------------------
# --self-test — hardware-free assertion that print_hardware_note emits the right
# guidance in each minipro-availability branch. Exercised by the kit gate so a
# regression in the live-path pointers fails loudly. Overrides the two tiny
# presence indirections to simulate each branch; never touches real hardware or
# launches the panel. Exits 0 on PASS, non-zero on any failed assertion.
# ---------------------------------------------------------------------------
if [ "${1:-}" = "--self-test" ]; then
    fails=0
    assert_contains() {  # <haystack> <needle> <label>
        if printf '%s' "$1" | grep -qF -- "$2"; then
            echo "    PASS: $3"
        else
            echo "    FAIL: $3 (missing: $2)"; fails=$((fails+1))
        fi
    }
    echo "==> start.sh --self-test — hardware note branches"

    # Branch A: minipro on PATH -> "ready"
    minipro_on_path() { return 0; }
    bundled_minipro_present() { return 1; }
    out_a="$(print_hardware_note)"
    assert_contains "$out_a" "the live path is ready" "PATH-present -> ready"

    # Branch B: not on PATH, bundled present -> install helper pointer
    minipro_on_path() { return 1; }
    bundled_minipro_present() { return 0; }
    out_b="$(print_hardware_note)"
    assert_contains "$out_b" "BUNDLED in this kit" "bundled -> bundled note"
    assert_contains "$out_b" "install.sh" "bundled -> install helper pointer"
    assert_contains "$out_b" "bootstrap.sh" "bundled -> bootstrap pointer"

    # Branch C: neither -> Mac/Windows one-liners
    minipro_on_path() { return 1; }
    bundled_minipro_present() { return 1; }
    out_c="$(print_hardware_note)"
    assert_contains "$out_c" "brew install minipro" "absent -> macOS pointer"
    assert_contains "$out_c" "gitlab.com/DavidGriffith/minipro" "absent -> Windows/upstream pointer"

    echo
    if [ "$fails" -eq 0 ]; then
        echo "  start.sh --self-test: PASS"
        exit 0
    else
        echo "  start.sh --self-test: FAIL (${fails} assertion(s))"
        exit 1
    fi
fi

echo "==> Lock workshop — starting the browser control panel"
echo "    Repo root: ${REPO_ROOT}"

# ---------------------------------------------------------------------------
# python3 is the one hard requirement for the GUI path. If it's missing, we
# can't open the panel — print the (identical) CLI guidance loudly and exit
# cleanly. This is guidance, not a crash: the attendee just needs python3.
# ---------------------------------------------------------------------------
if ! command -v python3 >/dev/null 2>&1; then
    echo
    echo "==> python3 was not found on your PATH."
    echo "    The browser panel needs python3. Install it, then re-run ./bin/start.sh"
    echo "    Install on Debian/Kali/Ubuntu:  sudo apt-get install -y python3"
    echo "    Install on macOS (Homebrew):    brew install python3"
    print_fallback
    exit 0
fi

# ---------------------------------------------------------------------------
# Sanity: the panel script should be present. If the clone is incomplete, fall
# back to the CLI guidance rather than handing python3 a missing path.
# ---------------------------------------------------------------------------
if [ ! -f "$PANEL" ]; then
    echo
    echo "==> Could not find the control panel at:"
    echo "    ${PANEL}"
    echo "    The clone looks incomplete. Use the CLI path below instead."
    print_fallback
    exit 1
fi

# ---------------------------------------------------------------------------
# Launch the panel. By contract, lock-panel.py opens the default browser ITSELF
# when run with no flags. We just exec it. If it exits non-zero (can't bind a
# port, no browser, etc.) we degrade to the CLI one-liners.
# ---------------------------------------------------------------------------
echo "==> Opening the browser control panel (Ctrl-C to stop)..."
echo "    If your browser does not open, use the CLI one-liners shown below."

# Surface the optional live-chip path's minipro readiness (non-fatal).
print_hardware_note

python3 "$PANEL"
rc=$?

if [ "$rc" -ne 0 ]; then
    echo
    echo "==> The control panel exited (code ${rc}) — it could not start or was stopped."
    print_fallback
    exit "$rc"
fi
