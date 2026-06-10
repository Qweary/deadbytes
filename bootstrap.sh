#!/usr/bin/env bash
# bootstrap.sh — one-command workshop-station stand-up, from a fresh clone.
#
# This is the single command an attendee/facilitator runs after cloning the
# repo. From the repo root:
#
#     sudo ./bootstrap.sh
#
# It does the whole stand-up end to end:
#   1. Assemble the kit from its source files   (make assemble)
#   2. Verify kit integrity, hardware-free      (make selftest)
#   3. Stand up the station                      (kit/install.sh)
#
# After it finishes the laptop has minipro on PATH, the udev rules installed
# (the uaccess rule grants sudo-free device access — no group change, no
# logout), and ~/workshop/ populated with the docs, the tools (decode/read/write
# + the menu + the panel), and the canonical baseline.
#
# PATH-RELATIVE BY DESIGN: every path is resolved from THIS script's own
# location, so the repo can be cloned anywhere. Nothing here hardcodes a home
# directory. Re-running is safe — assemble and install.sh are both idempotent.
#
# Why sudo: install.sh drops a binary in /usr/local/bin, installs udev rules,
# and reloads udev. It must run as root, and it needs SUDO_USER set so it can
# populate the *invoking* user's ~/workshop/ (not root's). Run it via
# `sudo ./bootstrap.sh` from your normal user shell — do NOT run as a root login
# shell, or SUDO_USER won't be set and install.sh's preflight will stop you with
# a clear message.

set -euo pipefail

# ---------------------------------------------------------------------------
# Resolve the repo root from this script's own location — never a hardcoded
# home path. Works whether invoked as ./bootstrap.sh, /abs/path/bootstrap.sh,
# or `sudo bash bootstrap.sh`.
# ---------------------------------------------------------------------------
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KIT_DIR="${REPO_ROOT}/workshop/kit"
INSTALL_SH="${KIT_DIR}/install.sh"

say() { echo "==> $*"; }
fail() { echo "ERROR: $*" >&2; exit 1; }

say "Workshop station bootstrap"
say "Repo root: ${REPO_ROOT}"

# ---------------------------------------------------------------------------
# Sanity: are we actually in the workshop repo? Check for the kit + installer.
# ---------------------------------------------------------------------------
[ -d "$KIT_DIR" ]      || fail "kit directory not found at ${KIT_DIR}. Run this from the cloned repo root (the dir containing workshop/)."
[ -f "$INSTALL_SH" ]   || fail "installer not found at ${INSTALL_SH}. The clone looks incomplete."
command -v make >/dev/null 2>&1 || fail "'make' is required but not installed. Install with: sudo apt-get install -y make"
command -v python3 >/dev/null 2>&1 || fail "'python3' is required but not installed. Install with: sudo apt-get install -y python3"

# ---------------------------------------------------------------------------
# Step 1+2: assemble + verify the kit. These do not need root, so if we were
# invoked under sudo, run them as the invoking user to keep the build tree
# owned by that user (avoids root-owned files under workshop/kit/). Fall back to
# running them directly when SUDO_USER is unset (e.g. someone ran us un-sudoed
# just to build).
# ---------------------------------------------------------------------------
run_as_builder() {
    if [ "$(id -u)" -eq 0 ] && [ -n "${SUDO_USER:-}" ] && [ "${SUDO_USER}" != "root" ]; then
        sudo -u "${SUDO_USER}" "$@"
    else
        "$@"
    fi
}

say "[1/3] Assembling the kit (make assemble)"
run_as_builder make -C "$KIT_DIR" assemble

say "[2/3] Verifying kit integrity (make selftest, hardware-free)"
if ! run_as_builder make -C "$KIT_DIR" selftest; then
    fail "kit selftest failed — refusing to install a kit that does not verify. See the selftest output above."
fi

# ---------------------------------------------------------------------------
# Step 3: stand up the station. This is the part that needs root.
# ---------------------------------------------------------------------------
if [ "$(id -u)" -ne 0 ]; then
    echo >&2
    echo "==> [3/3] The station installer needs root." >&2
    echo "    The kit is assembled and verified. Finish the stand-up with:" >&2
    echo >&2
    echo "        sudo ${INSTALL_SH}" >&2
    echo >&2
    echo "    Or just re-run this bootstrap under sudo: sudo ./bootstrap.sh" >&2
    exit 0
fi

say "[3/3] Standing up the station (install.sh)"
# install.sh resolves its own KIT_DIR from its location and reads SUDO_USER to
# pick the target home; pass through any extra args (e.g. --resume-from).
bash "$INSTALL_SH" "$@"

say "Bootstrap complete. The station is ready."
echo
echo "  Try the workshop tools (from the invoking user's shell):"
echo "    cd ~/workshop"
echo "    python3 tools/lock-tool.py read --all                 # READ the codes"
echo "    python3 tools/lock-tool.py write --code 246810 --slot 25 --role supervisor"
echo "    python3 tools/lock-menu.py                            # menu front-end"
echo "    python3 tools/lock-panel.py                           # browser control panel"
echo
