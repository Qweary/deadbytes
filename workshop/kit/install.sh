#!/usr/bin/env bash
# install.sh — one-command Kali stand-up for a workshop station.
#
# Idempotent: every step checks state before acting and re-running this is
# safe. Run as root (or via sudo) on a fresh Kali-AMD64 install.
#
# Workflow:
#   tar -xzf facilitator-kit-toorcamp-2026.tar.gz
#   cd facilitator-kit-toorcamp-2026
#   sudo ./install.sh
#
# After successful completion the laptop has:
#   - /usr/local/bin/minipro (chmod 755)
#   - /etc/udev/rules.d/{60,61-plugdev,61-uaccess}-minipro.rules + reloaded
#   - ~$SUDO_USER/workshop/ populated with docs/ tools/ dumps/
#   - both Python scripts' self-test modes PASS

set -euo pipefail

# ---------------------------------------------------------------------------
# Step registry — keep in sync with the `run_step` calls in main() below. This
# enables the --resume-from <step> hint on failure (see fail()).
# ---------------------------------------------------------------------------
STEPS=(
    "preflight"
    "install-minipro"
    "install-udev"
    "populate-workshop"
    "smoke-test"
)

# ---------------------------------------------------------------------------
# Config — paths and constants. KIT_DIR resolves to the directory containing
# this script (works whether invoked as ./install.sh, /path/to/install.sh, or
# bash install.sh).
# ---------------------------------------------------------------------------
KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERBOSE=1
RESUME_FROM=""

WORKSHOP_DIRNAME="workshop"
EXPECTED_BASELINE_MD5="eb6acff32ef13b29ac6ebed10d77316d"
EXPECTED_BASELINE_NAME="intact-lock-AT45DB041E-main-2026-05-20.bin"

# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------
say()  { if [ "$VERBOSE" -eq 1 ]; then echo "==> $*"; fi; }
info() { if [ "$VERBOSE" -eq 1 ]; then echo "    $*"; fi; }
warn() { echo "WARN: $*" >&2; }

fail() {
    local step="$1"; shift
    local msg="$*"
    echo >&2
    echo "ERROR [step:${step}]: ${msg}" >&2
    echo >&2
    echo "To re-run from this step after fixing:" >&2
    echo "    sudo ./install.sh --resume-from ${step}" >&2
    exit 1
}

# ---------------------------------------------------------------------------
# CLI parsing
# ---------------------------------------------------------------------------
while [ $# -gt 0 ]; do
    case "$1" in
        --quiet)            VERBOSE=0; shift ;;
        --resume-from)      RESUME_FROM="${2:?--resume-from requires a step name}"; shift 2 ;;
        --resume-from=*)    RESUME_FROM="${1#*=}"; shift ;;
        -h|--help)
            cat <<EOF
install.sh — facilitator-kit stand-up for Kali-AMD64.

Usage:
    sudo ./install.sh [--quiet] [--resume-from STEP]

Options:
    --quiet              Suppress informational output. Errors still print.
    --resume-from STEP   Skip steps until STEP (one of: ${STEPS[*]}).
    -h, --help           This message.

Run as root (or via sudo). The installer is idempotent — safe to re-run.
EOF
            exit 0
            ;;
        *)
            echo "ERROR: unknown argument: $1" >&2
            echo "Run with --help for usage." >&2
            exit 2
            ;;
    esac
done

if [ -n "$RESUME_FROM" ]; then
    valid=0
    for s in "${STEPS[@]}"; do
        if [ "$s" = "$RESUME_FROM" ]; then valid=1; break; fi
    done
    if [ "$valid" -eq 0 ]; then
        echo "ERROR: --resume-from value '${RESUME_FROM}' is not a known step." >&2
        echo "Valid steps: ${STEPS[*]}" >&2
        exit 2
    fi
fi

# ---------------------------------------------------------------------------
# Step dispatcher — skips until $RESUME_FROM matches if set
# ---------------------------------------------------------------------------
RESUME_REACHED=0
should_run() {
    local step="$1"
    if [ -z "$RESUME_FROM" ]; then return 0; fi
    if [ "$RESUME_REACHED" -eq 1 ]; then return 0; fi
    if [ "$step" = "$RESUME_FROM" ]; then RESUME_REACHED=1; return 0; fi
    return 1
}

run_step() {
    local step="$1"
    local fn="$2"
    if should_run "$step"; then
        say "[${step}]"
        "$fn"
    else
        info "[${step}] skipped (--resume-from ${RESUME_FROM})"
    fi
}

# ---------------------------------------------------------------------------
# Step 1: preflight — root check, kit-integrity check, architecture check
# ---------------------------------------------------------------------------
step_preflight() {
    if [ "$(id -u)" -ne 0 ]; then
        fail "preflight" "this installer must be run as root (use sudo)."
    fi
    if [ -z "${SUDO_USER:-}" ] || [ "$SUDO_USER" = "root" ]; then
        fail "preflight" "could not determine the invoking user. Run via 'sudo ./install.sh' from a non-root shell so SUDO_USER is set; the workshop tree must be owned by a real user, not root."
    fi
    info "Running as root, invoking user: ${SUDO_USER}"

    # Architecture gate — bin/minipro is Linux-AMD64 ELF
    local arch
    arch="$(uname -m)"
    if [ "$arch" != "x86_64" ]; then
        fail "preflight" "this kit ships an x86_64 minipro binary; current host is '${arch}'. The kit is Kali-AMD64 only."
    fi
    info "Architecture x86_64 OK"

    # Required source files
    for required in \
            "${KIT_DIR}/bin/minipro" \
            "${KIT_DIR}/tools/build-injected.py" \
            "${KIT_DIR}/tools/recover-baseline.py" \
            "${KIT_DIR}/dumps/${EXPECTED_BASELINE_NAME}" \
            "${KIT_DIR}/MANIFEST.md"; do
        if [ ! -f "$required" ]; then
            fail "preflight" "missing required kit file: ${required}"
        fi
    done
    info "All required kit files present"

    # Baseline MD5 sanity check (cheap; cross-checks the dump before populate)
    local actual_md5
    actual_md5="$(md5sum "${KIT_DIR}/dumps/${EXPECTED_BASELINE_NAME}" | awk '{print $1}')"
    if [ "$actual_md5" != "$EXPECTED_BASELINE_MD5" ]; then
        fail "preflight" "baseline dump MD5 mismatch. Got: ${actual_md5}. Expected: ${EXPECTED_BASELINE_MD5}. The kit tarball is corrupt — re-download."
    fi
    info "Baseline dump MD5 OK (${EXPECTED_BASELINE_MD5})"

    # Python presence
    if ! command -v python3 >/dev/null 2>&1; then
        fail "preflight" "python3 is required but not installed. Install with: apt-get install -y python3"
    fi
    info "python3 found: $(command -v python3)"
}

# ---------------------------------------------------------------------------
# Step 2: install-minipro — copy binary to /usr/local/bin
# ---------------------------------------------------------------------------
step_install_minipro() {
    local src="${KIT_DIR}/bin/minipro"
    local dst="/usr/local/bin/minipro"

    if [ -f "$dst" ]; then
        local existing_md5 src_md5
        existing_md5="$(md5sum "$dst" | awk '{print $1}')"
        src_md5="$(md5sum "$src" | awk '{print $1}')"
        if [ "$existing_md5" = "$src_md5" ]; then
            info "${dst} already at expected MD5; skipping copy"
        else
            info "${dst} exists with different MD5; overwriting (current: ${existing_md5}, kit: ${src_md5})"
            install -m 755 -o root -g root "$src" "$dst"
        fi
    else
        install -m 755 -o root -g root "$src" "$dst"
        info "installed ${dst} (mode 755)"
    fi

    # Sanity: minipro --version (-V) must report a sane line
    if ! "$dst" -V 2>&1 | grep -qi "minipro\|Supported programmers"; then
        # Some minipro builds dump version banner to stderr only; tolerate
        # missing match if exit was clean
        if ! "$dst" -V >/dev/null 2>&1; then
            fail "install-minipro" "${dst} does not appear executable. Architecture mismatch?"
        fi
    fi
    info "$($dst -V 2>&1 | head -1)"
}

# ---------------------------------------------------------------------------
# Step 3: install-udev — drop rules + reload + trigger
# ---------------------------------------------------------------------------
step_install_udev() {
    local src_dir="${KIT_DIR}/etc/udev/rules.d"
    local dst_dir="/etc/udev/rules.d"
    local installed_any=0

    if [ ! -d "$src_dir" ]; then
        fail "install-udev" "kit udev source directory not found: ${src_dir}"
    fi

    for rule in 60-minipro.rules 61-minipro-plugdev.rules 61-minipro-uaccess.rules 50-t48.rules; do
        if [ -f "${src_dir}/${rule}" ]; then
            install -m 644 -o root -g root "${src_dir}/${rule}" "${dst_dir}/${rule}"
            info "installed ${dst_dir}/${rule}"
            installed_any=1
        fi
    done

    if [ "$installed_any" -eq 0 ]; then
        fail "install-udev" "no udev rule files found under ${src_dir}"
    fi

    # Device access is granted by the uaccess rule (61-minipro-uaccess.rules:
    # ENV{ID_MINIPRO}=="1", TAG+="uaccess"), which gives the logged-in user
    # direct access to the programmer with NO group membership and NO logout.
    # That makes minipro runnable sudo-free the moment the T48 is plugged in.
    # We deliberately do NOT add the user to plugdev or require a re-login — the
    # 61-minipro-plugdev.rules file is still installed above (harmless), but the
    # uaccess rule is the load-bearing one.

    # Reload udev
    if command -v udevadm >/dev/null 2>&1; then
        udevadm control --reload-rules
        udevadm trigger
        info "udev rules reloaded + triggered"
    else
        warn "udevadm not found; rules installed but not reloaded — reboot or run 'udevadm control --reload-rules && udevadm trigger' manually"
    fi
}

# ---------------------------------------------------------------------------
# Step 4: populate-workshop — copy docs/ tools/ dumps/ into ~$SUDO_USER/workshop/
# ---------------------------------------------------------------------------
step_populate_workshop() {
    local user_home
    user_home="$(getent passwd "$SUDO_USER" | cut -d: -f6)"
    if [ -z "$user_home" ] || [ ! -d "$user_home" ]; then
        fail "populate-workshop" "could not determine home directory for ${SUDO_USER}"
    fi
    local workshop_dir="${user_home}/${WORKSHOP_DIRNAME}"

    mkdir -p "${workshop_dir}"

    # Copy with --update preserving timestamps (idempotent: copies only newer)
    for sub in docs tools dumps; do
        if [ ! -d "${KIT_DIR}/${sub}" ]; then
            fail "populate-workshop" "kit subdirectory missing: ${KIT_DIR}/${sub}"
        fi
        mkdir -p "${workshop_dir}/${sub}"
        cp -a "${KIT_DIR}/${sub}/." "${workshop_dir}/${sub}/"
        info "populated ${workshop_dir}/${sub}/"
    done

    # Also ship MANIFEST.md so the user can verify their tree later
    cp -a "${KIT_DIR}/MANIFEST.md" "${workshop_dir}/MANIFEST.md"

    # Ownership — everything in ~$SUDO_USER/workshop/ belongs to that user
    chown -R "${SUDO_USER}:${SUDO_USER}" "${workshop_dir}"
    info "ownership set to ${SUDO_USER}:${SUDO_USER} recursively"

    # Ensure Python scripts are executable for the user. Covers the original two
    # tools plus the self-service read/write tooling (decode/lock-tool/menu/panel).
    chmod 755 "${workshop_dir}"/tools/*.py
}

# ---------------------------------------------------------------------------
# Step 5: smoke-test — exercise the original two Python tools' self-test modes.
# build-injected.py has no --self-test flag (it's a non-interactive
# build-from-baseline tool); --help is the contract. recover-baseline.py
# has --self-test which validates the baseline file without hardware access.
# (The self-service read/write tools — decode-codes/lock-tool/lock-menu/lock-
# panel — carry their own --self-test and are exercised by the kit's
# selftest.sh; this installer's smoke gate keeps to the two baseline tools that
# are load-bearing for the recovery path.)
# ---------------------------------------------------------------------------
step_smoke_test() {
    local user_home
    user_home="$(getent passwd "$SUDO_USER" | cut -d: -f6)"
    local workshop_dir="${user_home}/${WORKSHOP_DIRNAME}"

    # build-injected.py --help should exit 0 and print usage
    if ! sudo -u "$SUDO_USER" python3 "${workshop_dir}/tools/build-injected.py" --help >/dev/null; then
        fail "smoke-test" "build-injected.py --help failed. The script is not executable by ${SUDO_USER} or python3 errored."
    fi
    info "build-injected.py --help PASS"

    # recover-baseline.py --self-test validates the canonical baseline path
    # AND its MD5. Since we just copied the baseline to the user's workshop
    # tree, point --self-test at the workshop-installed baseline explicitly
    # (the script's default points to ~/Desktop/toorcamp-2026-dumps/ which
    # this installer doesn't populate — that's the operator's bench location,
    # not the workshop-day location).
    local baseline_in_workshop="${workshop_dir}/dumps/${EXPECTED_BASELINE_NAME}"
    if ! sudo -u "$SUDO_USER" python3 "${workshop_dir}/tools/recover-baseline.py" \
            --self-test --baseline "${baseline_in_workshop}" >/dev/null; then
        fail "smoke-test" "recover-baseline.py --self-test FAIL. The installed baseline at ${baseline_in_workshop} did not validate against MD5 ${EXPECTED_BASELINE_MD5}."
    fi
    info "recover-baseline.py --self-test PASS (baseline ${baseline_in_workshop})"
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
    say "facilitator-kit installer starting (kit: ${KIT_DIR})"
    run_step "preflight"          step_preflight
    run_step "install-minipro"    step_install_minipro
    run_step "install-udev"       step_install_udev
    run_step "populate-workshop"  step_populate_workshop
    run_step "smoke-test"         step_smoke_test
    say "DONE. Workshop laptop is ready."
    info "Workshop tree:    $(getent passwd "$SUDO_USER" | cut -d: -f6)/${WORKSHOP_DIRNAME}/"
    info "minipro on PATH:  $(command -v minipro 2>/dev/null || echo /usr/local/bin/minipro)"
    info ""
    info "Next steps:"
    info "  1. Plug in the T48 programmer over USB."
    info "  2. Verify: lsusb | grep a466:0a53   (T48 vendor:product)"
    info "  3. Device access is sudo-free and immediate — the uaccess udev rule"
    info "     grants ${SUDO_USER} direct access. No group change, no logout needed."
    info "  4. Read ~/${WORKSHOP_DIRNAME}/docs/FACILITATOR-GUIDE.md for the bench-day runbook."
    info ""
    info "Try the self-service tools (safe, no hardware needed):"
    info "  cd ~/${WORKSHOP_DIRNAME}"
    info "  python3 tools/lock-tool.py read --all                 # READ the codes"
    info "  python3 tools/lock-tool.py write --code 246810 --slot 25 --role supervisor"
    info "  python3 tools/lock-menu.py                            # menu front-end"
    info "  python3 tools/lock-panel.py                           # browser control panel"
}

main "$@"
