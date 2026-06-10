#!/usr/bin/env bash
# selftest.sh — hardware-free kit-integrity check.
#
# Two phases:
#   1. MD5-verify every file in MANIFEST.md against the on-disk kit.
#      Refuses on any mismatch (corrupt download or local tampering).
#   2. Smoke-run the bundled Python tools' self-test entry points against the
#      bundled baseline (build-injected.py --help, recover-baseline.py
#      --self-test --baseline <bundled-dump>).
#
# Exits 0 on full PASS, non-zero with a line-numbered failure report otherwise.
#
# Designed to run on the build host (after `make tarball` assembly) AND on a
# fresh download before `sudo ./install.sh` so a facilitator can confirm the
# tarball was not corrupted in transit.

set -uo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST="${KIT_DIR}/MANIFEST.md"

# Failure accumulator — script does NOT exit on first failure during MD5 phase;
# we want a complete report.
FAIL_COUNT=0
declare -a FAIL_LINES=()

note_fail() {
    FAIL_COUNT=$((FAIL_COUNT + 1))
    FAIL_LINES+=("$1")
}

echo "==> selftest.sh — facilitator-kit integrity check"
echo "    Kit dir: ${KIT_DIR}"
echo

# -----------------------------------------------------------------------------
# Phase 1: MANIFEST.md present?
# -----------------------------------------------------------------------------
if [ ! -f "$MANIFEST" ]; then
    echo "FAIL: MANIFEST.md not found at ${MANIFEST}" >&2
    echo "      The kit may not have been built — run 'make tarball' to assemble" >&2
    echo "      and generate the manifest, or re-download the tarball." >&2
    exit 1
fi

# -----------------------------------------------------------------------------
# Phase 2: Parse manifest table rows + MD5-verify each file. The table format
# is: | `path` | size | `md5` | role | provenance |. We extract the first two
# backticked fields per row.
# -----------------------------------------------------------------------------
echo "==> Phase 1: MD5-verify every file in MANIFEST.md"
echo

CHECKED=0
while IFS= read -r line; do
    # Skip non-data rows (header, separator, blank, narrative). Data rows
    # look like:  | `path` | SIZE | `md5` | role | provenance |
    # The size column is right-aligned (no leading space guarantee), so we
    # match by structure: backticked-path, pipe-delimited number, backticked-md5.
    if ! echo "$line" | grep -qE '^\| `[^`]+` \|[[:space:]]*[0-9]+[[:space:]]*\| `[a-f0-9]+`'; then
        continue
    fi

    path=$(echo "$line"  | awk -F'`' '{print $2}')
    md5=$(echo "$line"   | awk -F'`' '{print $4}')
    size=$(echo "$line"  | awk -F'|' '{gsub(/^[[:space:]]+|[[:space:]]+$/,"",$3); print $3}')

    if [ -z "$path" ] || [ -z "$md5" ]; then
        continue
    fi

    file_path="${KIT_DIR}/${path}"
    if [ ! -f "$file_path" ]; then
        note_fail "MISSING ${path}"
        echo "    FAIL [${CHECKED}]: ${path} — file not present on disk"
        CHECKED=$((CHECKED + 1))
        continue
    fi

    actual_md5=$(md5sum "$file_path" | awk '{print $1}')
    actual_size=$(stat -c %s "$file_path")

    if [ "$actual_md5" != "$md5" ]; then
        note_fail "MD5 ${path} expected=${md5} got=${actual_md5}"
        echo "    FAIL [${CHECKED}]: ${path} — MD5 mismatch (expected ${md5}, got ${actual_md5})"
    elif [ "$actual_size" != "$size" ]; then
        note_fail "SIZE ${path} expected=${size} got=${actual_size}"
        echo "    FAIL [${CHECKED}]: ${path} — size mismatch (expected ${size}, got ${actual_size})"
    else
        echo "    PASS [${CHECKED}]: ${path}"
    fi
    CHECKED=$((CHECKED + 1))
done < "$MANIFEST"

echo
echo "    Checked: ${CHECKED} files"

if [ "$CHECKED" -eq 0 ]; then
    echo "FAIL: no manifest rows parsed from ${MANIFEST}" >&2
    echo "      The manifest may be malformed. Regenerate with 'make tarball'." >&2
    exit 1
fi

# -----------------------------------------------------------------------------
# Phase 3: smoke-test the bundled Python tools.
# -----------------------------------------------------------------------------
echo
echo "==> Phase 2: smoke-test bundled Python tools"
echo

if ! command -v python3 >/dev/null 2>&1; then
    note_fail "python3 not installed — cannot smoke-test"
    echo "    FAIL: python3 not on PATH"
else
    # build-injected.py — exercise --help (the contract; this script has no
    # --self-test mode because it is a pure build-from-baseline tool. --help
    # exits 0 only if the script parses + imports cleanly.)
    if python3 "${KIT_DIR}/tools/build-injected.py" --help >/dev/null 2>&1; then
        echo "    PASS: tools/build-injected.py --help"
    else
        note_fail "build-injected.py --help nonzero exit"
        echo "    FAIL: tools/build-injected.py --help returned nonzero"
    fi

    # recover-baseline.py --self-test against the bundled baseline. The script
    # validates: file exists, size = 540,672, MD5 = canonical baseline.
    baseline="${KIT_DIR}/dumps/intact-lock-AT45DB041E-main-2026-05-20.bin"
    if python3 "${KIT_DIR}/tools/recover-baseline.py" \
            --self-test --baseline "${baseline}" >/dev/null 2>&1; then
        echo "    PASS: tools/recover-baseline.py --self-test --baseline ${baseline}"
    else
        note_fail "recover-baseline.py --self-test nonzero exit"
        echo "    FAIL: tools/recover-baseline.py --self-test against bundled baseline"
        # Re-run with output captured for the operator
        echo "    --- recover-baseline.py output ---"
        python3 "${KIT_DIR}/tools/recover-baseline.py" \
            --self-test --baseline "${baseline}" 2>&1 | sed 's/^/    /'
        echo "    --- end output ---"
    fi

    # Self-service read/write tooling — each ships a hardware-free --self-test
    # that validates its decode/encode contract against the documented worked
    # examples (slot 0 = 123456, the 0xB-for-zero rule, empty-slot rendering,
    # and a full custom-code write-into-a-copy + re-decode round trip). Exercise
    # all three so a regression in the attendee-facing tooling fails the kit gate
    # exactly like a regression in the two original tools does.
    for tool in decode-codes.py lock-tool.py lock-panel.py; do
        if python3 "${KIT_DIR}/tools/${tool}" --self-test >/dev/null 2>&1; then
            echo "    PASS: tools/${tool} --self-test"
        else
            note_fail "${tool} --self-test nonzero exit"
            echo "    FAIL: tools/${tool} --self-test"
            echo "    --- ${tool} output ---"
            python3 "${KIT_DIR}/tools/${tool}" --self-test 2>&1 | sed 's/^/    /'
            echo "    --- end output ---"
        fi
    done

    # lock-menu.py has no --self-test (it is a pure interactive wrapper with no
    # decode/encode logic of its own); validate it parses + imports cleanly by
    # driving an immediate-quit through it. A broken import would exit nonzero.
    if printf 'q\n' | python3 "${KIT_DIR}/tools/lock-menu.py" >/dev/null 2>&1; then
        echo "    PASS: tools/lock-menu.py (loads + quits cleanly)"
    else
        note_fail "lock-menu.py load/quit nonzero exit"
        echo "    FAIL: tools/lock-menu.py did not load + quit cleanly"
    fi

    # Decode smoke — the default teaching sample must surface the three baked
    # workshop codes (133769 Master @19 / 420420 Elevated @32 / 696969 Supervisor
    # @49). decode-codes.py with no args operates on a copy of the default sample,
    # so a single grep over its output confirms the sample is the 3-codes teaching
    # dump and the read default points at it.
    decode_out="$(python3 "${KIT_DIR}/tools/decode-codes.py" 2>/dev/null)"
    if echo "$decode_out" | grep -q '133769' \
       && echo "$decode_out" | grep -q '420420' \
       && echo "$decode_out" | grep -q '696969'; then
        echo "    PASS: tools/decode-codes.py default decode shows the 3 workshop codes"
    else
        note_fail "decode-codes.py default sample missing the 3 workshop codes"
        echo "    FAIL: tools/decode-codes.py default decode did not show all 3 workshop codes"
        echo "    --- decode-codes.py output ---"
        echo "$decode_out" | sed 's/^/    /'
        echo "    --- end output ---"
    fi
fi

# -----------------------------------------------------------------------------
# Final report
# -----------------------------------------------------------------------------
echo
echo "=================================================================="
if [ "$FAIL_COUNT" -eq 0 ]; then
    echo "  selftest RESULT: PASS — kit integrity verified"
    echo "=================================================================="
    exit 0
else
    echo "  selftest RESULT: FAIL — ${FAIL_COUNT} failure(s) below:"
    echo "------------------------------------------------------------------"
    for f in "${FAIL_LINES[@]}"; do
        echo "  - ${f}"
    done
    echo "=================================================================="
    exit 1
fi
