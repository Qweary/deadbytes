# start.ps1 — the attendee's one command on Windows. Run it from the cloned
# repo and the browser control panel opens. That's it.
#
#     .\start.ps1
#
# What it does: launches the no-hardware control panel, which opens your default
# browser to a local READ/WRITE GUI for the lock's user-code table. Everything
# runs locally with Python and the bundled sample dump — no internet, no
# hardware. (The live-chip path is Linux-only; Windows is the no-hardware lane.)
#
# If Python is missing, or the panel can't start, this prints the bedrock CLI
# one-liners so you always have a way in.
#
# PATH-RELATIVE BY DESIGN: the repo root is resolved from this script's own
# location ($PSScriptRoot), so the repo can be cloned anywhere.

$ErrorActionPreference = 'Continue'

# ---------------------------------------------------------------------------
# Resolve the repo root from this script's own location. start.ps1 lives at the
# repo root, so $PSScriptRoot IS the repo root.
# ---------------------------------------------------------------------------
$RepoRoot = $PSScriptRoot
$ToolsDir = Join-Path $RepoRoot 'workshop\kit\tools'
$Panel    = Join-Path $ToolsDir 'lock-panel.py'

function Write-Fallback {
    Write-Host ''
    Write-Host '----------------------------------------------------------------------'
    Write-Host '  CLI fallback — run these from the cloned repo (no browser needed):'
    Write-Host '----------------------------------------------------------------------'
    Write-Host '  READ  the codes:'
    Write-Host '    python workshop\kit\tools\lock-tool.py read --all'
    Write-Host ''
    Write-Host '  WRITE your own code:'
    Write-Host '    python workshop\kit\tools\lock-tool.py write --code 246810 --slot 25 --role supervisor'
    Write-Host '----------------------------------------------------------------------'
    Write-Host ''
}

Write-Host '==> Lock workshop — starting the browser control panel'
Write-Host "    Repo root: $RepoRoot"

# ---------------------------------------------------------------------------
# Find a Python launcher. Prefer 'python'; fall back to the 'py' launcher that
# ships with the python.org Windows installer.
# ---------------------------------------------------------------------------
$PyExe = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $PyExe = 'python'
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $PyExe = 'py'
}

if (-not $PyExe) {
    Write-Host ''
    Write-Host '==> Python was not found on your PATH.'
    Write-Host '    The browser panel needs Python 3. Install it from https://www.python.org/downloads/'
    Write-Host '    (check "Add python.exe to PATH" in the installer), then re-run .\start.ps1'
    Write-Fallback
    exit 0
}

# ---------------------------------------------------------------------------
# Sanity: the panel script should be present.
# ---------------------------------------------------------------------------
if (-not (Test-Path -LiteralPath $Panel)) {
    Write-Host ''
    Write-Host '==> Could not find the control panel at:'
    Write-Host "    $Panel"
    Write-Host '    The clone looks incomplete. Use the CLI path below instead.'
    Write-Fallback
    exit 1
}

# ---------------------------------------------------------------------------
# Launch the panel. By contract, lock-panel.py opens the default browser itself
# when run with no flags. If it exits non-zero we degrade to the CLI one-liners.
# ---------------------------------------------------------------------------
Write-Host '==> Opening the browser control panel (Ctrl-C to stop)...'
Write-Host '    If your browser does not open, use the CLI one-liners shown below.'

& $PyExe $Panel
$rc = $LASTEXITCODE

if ($rc -ne 0) {
    Write-Host ''
    Write-Host "==> The control panel exited (code $rc) — it could not start or was stopped."
    Write-Fallback
    exit $rc
}
