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
# Phase 3: bundled minipro device-database (share/minipro/*.xml).
#
# The kit ships its own version-matched minipro device DB so a clean attendee
# machine resolves chip profiles with zero setup. Two guards:
#   (a) version-match guard — the two XML are present and their MD5s equal the
#       values pinned to the bundled binary's commit (fd6b56af). A mismatch here
#       means the DB drifted from the binary (the version-pin/drift rule) — the
#       kit MUST re-bundle both XML from the SAME commit on any binary rebuild.
#   (b) clean-env DB-resolution proof — a hardware-free DIFFERENTIAL: point
#       MINIPRO_HOME at the bundled share dir vs. an empty tmp dir, from a
#       SCRUBBED cwd (no stray ./logicic.xml — minipro checks cwd BEFORE
#       MINIPRO_HOME), and assert the bundled case yields the device profile
#       while the empty case yields the DB-missing error. The differential is
#       the proof and it needs no T48.
#
# CRITICAL: minipro's exit code is NOT a health signal — `minipro -L <device>`
# prints the DB-missing error but still exits 0. Every assertion below is on
# STDOUT/STDERR CONTENT, never on $? alone.
# -----------------------------------------------------------------------------
echo
echo "==> Phase 3: bundled minipro device database (share/minipro)"
echo

# Pinned to bin/minipro commit fd6b56af. Re-pin (and re-bundle the XML from the
# SAME commit) on any binary rebuild — see MANIFEST.md device-db rows.
PINNED_INFOIC_MD5="81e41770ff5ccde8da9344cc91894159"
PINNED_LOGICIC_MD5="54e0c050e5f2e0e9b7d2179de5ec7be8"
SHARE_DIR="${KIT_DIR}/share/minipro"
MINIPRO_BIN="${KIT_DIR}/bin/minipro"
# DB-only lookup target: a device whose profile lives in infoic.xml. minipro -L
# lists matching devices from the DB with no chip attached and no programmer.
PROBE_DEVICE="AT45DB041E"

# (a) version-match guard — present + pinned MD5.
for xml_pin in "infoic.xml:${PINNED_INFOIC_MD5}" "logicic.xml:${PINNED_LOGICIC_MD5}"; do
    xml="${xml_pin%%:*}"
    pin="${xml_pin#*:}"
    xml_path="${SHARE_DIR}/${xml}"
    if [ ! -f "$xml_path" ]; then
        note_fail "share/minipro/${xml} missing"
        echo "    FAIL: share/minipro/${xml} not present — kit DB is not self-contained"
        continue
    fi
    got_md5=$(md5sum "$xml_path" | awk '{print $1}')
    if [ "$got_md5" = "$pin" ]; then
        echo "    PASS: share/minipro/${xml} present + matches pinned MD5 (${pin})"
    else
        note_fail "share/minipro/${xml} MD5 drift expected=${pin} got=${got_md5}"
        echo "    FAIL: share/minipro/${xml} MD5 drift (expected ${pin}, got ${got_md5})"
        echo "          The device DB has drifted from binary commit fd6b56af — re-bundle"
        echo "          both XML from the SAME commit (the version-pin/drift rule)."
    fi
done

# (b) clean-env DB-resolution differential. Hardware-free, stdout-asserted.
if [ ! -x "$MINIPRO_BIN" ]; then
    note_fail "bin/minipro not executable — cannot run DB-resolution proof"
    echo "    FAIL: bin/minipro not present/executable; skipping DB-resolution differential"
else
    # Scrubbed cwd with NO stray XML — minipro reads a bare ./logicic.xml BEFORE
    # $MINIPRO_HOME, so the differential is only honest from a clean dir.
    _scrub_cwd="$(mktemp -d)"
    _empty_home="$(mktemp -d)"
    # Bundled-DB branch: MINIPRO_HOME -> bundled share. Expect the device profile.
    bundled_out="$(cd "$_scrub_cwd" && MINIPRO_HOME="$SHARE_DIR" "$MINIPRO_BIN" -L "$PROBE_DEVICE" 2>&1)"
    # Empty-DB branch: MINIPRO_HOME -> empty tmp. Expect the DB-missing error
    # (and NOT the device profile). This is the teeth of the test — it MUST fail
    # to resolve when the DB is absent, or the bundled branch proves nothing.
    empty_out="$(cd "$_scrub_cwd" && MINIPRO_HOME="$_empty_home" "$MINIPRO_BIN" -L "$PROBE_DEVICE" 2>&1)"
    rm -rf "$_scrub_cwd" "$_empty_home"

    # Assert on CONTENT, never on $?. Bundled branch: device name surfaces in the
    # device-list output. Empty branch: device name does NOT surface (the DB is
    # gone), and the DB-missing diagnostic ("No such file" / "infoic"/"logicic")
    # does.
    bundled_resolves=0
    echo "$bundled_out" | grep -qi "$PROBE_DEVICE" && bundled_resolves=1
    empty_resolves=0
    echo "$empty_out" | grep -qi "$PROBE_DEVICE" && empty_resolves=1

    if [ "$bundled_resolves" -eq 1 ] && [ "$empty_resolves" -eq 0 ]; then
        echo "    PASS: clean-env DB-resolution differential — bundled DB resolves '${PROBE_DEVICE}', empty DB does not"
    else
        note_fail "DB-resolution differential failed (bundled_resolves=${bundled_resolves} empty_resolves=${empty_resolves})"
        echo "    FAIL: clean-env DB-resolution differential"
        echo "          bundled-DB branch resolved '${PROBE_DEVICE}': $( [ "$bundled_resolves" -eq 1 ] && echo yes || echo NO )"
        echo "          empty-DB  branch resolved '${PROBE_DEVICE}': $( [ "$empty_resolves" -eq 0 ] && echo no || echo YES-LEAK )"
        echo "    --- bundled-DB branch output ---"
        echo "$bundled_out" | sed 's/^/    /'
        echo "    --- empty-DB branch output ---"
        echo "$empty_out" | sed 's/^/    /'
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
