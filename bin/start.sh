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

python3 "$PANEL"
rc=$?

if [ "$rc" -ne 0 ]; then
    echo
    echo "==> The control panel exited (code ${rc}) — it could not start or was stopped."
    print_fallback
    exit "$rc"
fi
