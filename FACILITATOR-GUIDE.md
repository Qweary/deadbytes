# Dead Bytes Tell No Lies — Facilitator Guide
## ToorCamp 2026 · NightMrkt / Volleyball Court · 90 min
### Qweary + 3 co-facilitators

---

> **How to use this guide:**
> Parse-fast reference document — scan while managing a room.
> `[CHECKPOINT]` = everyone at this station must be at this point before they move on.
> `[TROUBLESHOOT]` = known failure mode with a fix.
> The hands-on block is where time actually goes. 25 minutes per attendee at a programmer station, with rotation.

---

## Station Map

The room runs **four programmer stations** in parallel plus three static stations. One facilitator per programmer station — the operator and three co-facilitators. The two static stations and the drill station are self-directed once an attendee is anchored.

| Station | Type | Facilitator | What happens there |
|---|---|---|---|
| P1 | Programmer station | Qweary | Read → decode → inject → write → verify on a prepped lock board |
| P2 | Programmer station | Co-facilitator A | Same flow as P1 |
| P3 | Programmer station | Co-facilitator B | Same flow as P1 |
| P4 | Programmer station | Co-facilitator C | Same flow as P1 |
| S1 | Standalone lock demo | Self-directed | Remote-release jumper bridge with cut-out window; stiff-wire attack on a fixture; brief defender discussion |
| S2 | Standalone lock demo | Self-directed | Spare attack demos and physical-vulnerability conversation (loose, hacker-camp rhythm) |
| D1 | Drill-open core station | Self-directed | Take a turn drilling a spare core. Cutting lube, safety glasses, gloves, ear protection laid out. Destructive-entry counterpoint to the electronic-attack thread |

Each programmer station serves roughly three attendees across the 90 minutes (25 minutes each, with one rotation cycle of buffer). Four programmer stations × three attendees ≈ **12 attendees through the full hands-on flow.** The standalone and drill stations absorb the rest — anyone waiting for a programmer slot, anyone who already finished, anyone who walked in late.

---

## Pre-Session Setup Checklist

Allow 60 minutes minimum the morning of the workshop, plus ~30 minutes per lock board for the resin-cleaning step done the night before.

### The night before — resin cleaning the SOIC-8 chips

The AT45DB041E on each lock board ships under a layer of conformal-coating resin. The SOIC-8 clip cannot bite through it. **Do this the night before, on all four lock boards, in your tent.** Per board:

- [ ] Identify the AT45DB041E — Adesto markings, 8-pin SOIC, near the MSP430
- [ ] Apply isopropyl alcohol (91 % or higher) to the resin over the chip and the eight leads
- [ ] Let it sit 2–3 minutes; the resin softens
- [ ] Scrape with a wooden toothpick or a plastic spudger — not metal; pin-1 marking is fragile
- [ ] Repeat until all eight leads are clean metal under good light
- [ ] Wipe with a fresh alcohol pad; let dry
- [ ] Bag and label the prepped board with the station letter

If you finish a board and the chip body shows any visible discoloration or the leads bridge solder under the resin you scraped, swap it for a spare. A board you cleaned at midnight under a headlamp is not the time to fight a marginal chip.

### Hardware count (Qweary brings; co-facilitators verify on arrival)

- [ ] **4× lock boards** — resin-cleaned per the step above, factory `123456` confirmed unlocks before resin cleaning began
- [ ] **4× Xgecu T48 programmers** — operator + 3 from the procurement run; serial numbers logged
- [ ] **4× SOIC-8 clips** — 1.27 mm pitch, 8-pin, with the ZIF ICSP adapter that connects clip-flying-leads to the T48's ICSP header
- [ ] **1–2× sets of individual long clips + breakout leads** (operator kit, NOT a per-station item) — ad-hoc-only fallback a facilitator may reach for if a specific board geometry defeats the SOIC-8 clip. **Not a standard station method; do not put it in front of attendees as a documented procedure.** The SOIC-8 clip is the per-station method.
- [ ] **4× Kali laptops** — minipro 0.7.4 pre-installed per `T48-KALI-PLAN.md` Phase 1; udev rules in `/etc/udev/rules.d/`; facilitator users in `plugdev`; the workshop-distribution dump (`intact-lock-AT45DB041E-main-2026-05-20-workshop.bin`) and the injection-payload construction script (`build-injected.py` — see §"Workshop-Distribution Dump Production" below) pre-staged in `~/workshop/`
- [ ] **2× spare T48s** — hot-swap if a programmer flakes
- [ ] **6× spare SOIC-8 clips** — they fail mechanically; 1.5 per station of spare is the right ratio
- [ ] **8× spare AT45DB041E baseline dumps** — `intact-lock-AT45DB041E-main-2026-05-20.bin` on a USB stick at each station, for recovery writes (§"Recovery — write the baseline back")
- [ ] **20+ spare lock cores** — for the drill station
- [ ] **3–4× drill bits sized for the lock core**, sharp; cutting lube; safety glasses; ear protection; nitrile gloves; rags
- [ ] **1–2× cordless drills** with charged batteries plus a spare charged battery
- [ ] **2× standalone lock demos** — one with the cut-out window pre-machined into the body so the jumper-target wire is visible vs the comm-port wire; one for the stiff-wire demo (cover removed, mechanism exposed)
- [ ] **Printed PARTICIPANT-HANDOUT.md** — 30+ copies; double-sided if possible, single-sided fine

### Software verification — at every Kali laptop, before the doors open

Run these at each station laptop:

```bash
# 1. minipro built and on PATH
minipro --version
# expected: minipro version 0.7.4 (or newer)

# 2. udev rules installed for the T48
ls /etc/udev/rules.d/ | grep -i minipro
# expected: three files — 60-minipro.rules, 61-minipro-plugdev.rules, 61-minipro-uaccess.rules

# 3. Plug in the T48; confirm it enumerates
lsusb | grep a466
# expected: Bus xxx Device xxx: ID a466:0a53 Xgecu T48

# 4. Confirm the toolchain opens the programmer
sudo minipro -k
# expected: t48: T48

# 5. Confirm the workshop-distribution dump is on the laptop
md5sum ~/workshop/intact-lock-AT45DB041E-main-2026-05-20-workshop.bin
# expected: the workshop-distribution MD5 you produced in advance per the production note below
```

If any of these fail at any station, swap to a spare laptop or pull the operator. Do not open the doors with an unverified station.

### ToorCamp-specific logistics

- [ ] Power: NightMrkt tent + volleyball court. One power strip per programmer station (T48 USB plus laptop). One strip near the drill station for the drill chargers
- [ ] Wind: handouts will blow. A rock per station, or fold them in half
- [ ] Lighting: workshop runs into late afternoon / early evening; if you are anywhere near sunset by 70:00, have a headlamp per station
- [ ] Table layout: four programmer tables in a row, standalone demos on a separate table, drill station outside the tent with clear floor space and ear-protection visible from the entry — that visual cue alone manages the noise expectation

### Workshop-Distribution Dump Production

The baseline `intact-lock-AT45DB041E-main-2026-05-20.bin` is the operator's intact-lock capture (MD5 `eb6acff32ef13b29ac6ebed10d77316d`, 540,672 bytes). It contains a populated audit log at file offsets `0x42000`–`0x46938` (pages 1024–1094, 71 pages of 6-byte records). Each 6-byte record has byte 5 as the slot/user-id field. Per the dump-validation report §5b, the workshop-distribution dump must zero byte 5 of every audit-log record before any full hex dump goes into the handout or sits on attendee laptops.

Run this once, the night before, on the operator's machine. Output goes onto every station laptop and onto the take-home USB sticks.

```python
#!/usr/bin/env python3
# redact-audit-log.py — produce the workshop-distribution dump
# Zeroes byte 5 of every 6-byte audit-log record in pages 1024–1094.

import sys

SRC = "intact-lock-AT45DB041E-main-2026-05-20.bin"
DST = "intact-lock-AT45DB041E-main-2026-05-20-workshop.bin"

PAGE_SIZE = 264
LOG_FIRST_PAGE = 1024
LOG_LAST_PAGE = 1094            # inclusive
PAYLOAD_BYTES = 252             # each page is 252 record bytes + 8 spare bytes
RECORD_SIZE = 6
SLOT_ID_BYTE_IN_RECORD = 5      # the field that may identify the custodian

with open(SRC, "rb") as f:
    data = bytearray(f.read())

assert len(data) == 540672, f"unexpected source size {len(data)}"

redacted = 0
for page in range(LOG_FIRST_PAGE, LOG_LAST_PAGE + 1):
    page_base = page * PAGE_SIZE
    # Skip the FD page header byte; records run from offset 1 through offset PAYLOAD_BYTES.
    for rec_off in range(1, PAYLOAD_BYTES, RECORD_SIZE):
        target = page_base + rec_off + SLOT_ID_BYTE_IN_RECORD
        if target >= len(data):
            break
        data[target] = 0x00
        redacted += 1

with open(DST, "wb") as f:
    f.write(data)

print(f"wrote {DST} ({len(data)} bytes); zeroed {redacted} slot-id bytes")
```

After running it, sanity-check:

```bash
md5sum intact-lock-AT45DB041E-main-2026-05-20-workshop.bin
ls -l intact-lock-AT45DB041E-main-2026-05-20-workshop.bin
# size must be 540,672 bytes (the redaction does not change length)
```

Record the workshop-distribution MD5 in your facilitator pocket reference. Each station laptop's `~/workshop/` directory should hold this file, the baseline, the injection-payload construction script, and a copy of the handout.

---

## Learning Objectives

By the end of the 90 minutes, an attendee who made it through a programmer station can:

1. **Read** an Adesto AT45DB041E DataFlash chip in-circuit, via a SOIC-8 clip on a Xgecu T48 programmer driven by `minipro` on Kali, and confirm a successful 540,672-byte dump
2. **Navigate** the 264-byte page layout in a hex editor, decode a packed-BCD user code (including the digit-`0`-as-nibble-`0xB` rule), and locate the permission byte for that user
3. **Construct** an injection payload — three codes at three different privilege levels in three scattered slots — and write it back to the chip with `minipro -w`
4. **Demonstrate** that each injected code unlocks the lock when entered on the keypad after the batteries are reinstalled
5. **Discuss** the slot-0 permission anomaly and the programming-mode-fails-for-injected-codes finding, and explain why both matter for the defender

Anyone who only made it through S1/S2/D1 leaves understanding (a) what the flash-write attack does and why it works, (b) what the remote-release jumper bridge looks like inside the lock body, and (c) how destructive entry compares to electronic attack as a threat model.

---

## Equipment List

### Per programmer station (P1–P4)

- 1× prepped Alarm Lock T2/T3 board (resin cleaned per the night-before step)
- 1× Xgecu T48 programmer
- 1× SOIC-8 clip + ZIF ICSP adapter
- 1× Kali laptop, minipro 0.7.4 verified, workshop-distribution dump in `~/workshop/`
- 1× USB-A cable (data, not charge-only)
- 1× headlamp
- 1× clear bench area for the attendee to work alongside the facilitator
- 1× printed handout in the attendee's hand before they sit down

### Per standalone station (S1, S2)

- 1× lock with a pre-machined cut-out window in the body, jumper wire and comm-port wire both visible — S1 only
- 1× lock with the cover off, mechanism visible — S2
- A length of stiff wire for the deflection demo (operator-controlled, not attendee-handled)
- 1× printed handout

### Drill station (D1)

- 20+ spare lock cores
- 3–4× sharp drill bits sized for the core
- Cutting lube
- Safety glasses + ear protection + nitrile gloves at the entry to the station, refused-no-glasses
- 1–2× cordless drills, charged
- A rag for chips and cuttings
- A bucket or tray to catch the cores after they're drilled

### Facilitator-only

- 2× spare T48s
- 6× spare SOIC-8 clips
- 8× USB sticks with the baseline dump + workshop-distribution dump (one per station + spares)
- The pocket reference sheet (§"Facilitator Pocket Reference" at the back of this guide)

---

## Run-of-Show

### [00:00–10:00] Open the doors, anchor everyone, distribute handouts — 10 min

The operator says a sentence and a half. Co-facilitators get attendees seated at the programmer stations on a rolling basis as they walk in.

- "This is a workshop on reading and writing the flash chip inside an Alarm Lock T2/T3. We are going to read user codes off it, modify them, write them back, and watch the lock accept the new codes. We are doing this on real hardware. You will leave knowing how to do it."
- Point to the four programmer stations and the three static stations. Tell the room: if you sit at a programmer station, plan on 25 minutes there. If you finish or are waiting, the standalone demos and the drill station are open the whole time.
- "Everything you need is in the handout. Everything I'm doing is in the repo. We'll get to the questions at the end."

The first four attendees through the entry rotate to P1–P4. The next four anchor at S1/S2/D1 with handouts; the co-facilitator running the static stations cues them on what to look at.

`[CHECKPOINT]` Four attendees seated at programmer stations, three to six at the static stations, handouts distributed, doors closed or signed if you have closed doors.

---

### [10:00–80:00] The hands-on block — 70 min · per-station rotation

This is where the workshop lives. Each programmer station runs the same flow on a rolling basis. As one attendee finishes (~25 minutes in), the next attendee rotates from the static side into the programmer slot.

#### The per-attendee flow at a programmer station (25 min)

Read this whole section before the workshop. During the workshop, walk an attendee through it with the handout in their hand — you are reading from the same pages they are.

**Step 1 — Confirm the lock works as it ships (2 min)**

- Battery is in the lock. Punch `123456`. Confirm it unlocks.
- Punch a wrong code (say, `999999`). Confirm it does not unlock.
- That is the workshop's "before" state. Show them you can prove it.

**Step 2 — Remove the batteries, clip onto the chip (4 min)**

- Pop the battery cover. Pull the batteries. Set them aside on the bench.
- Open the back of the lock so the PCB is exposed. The AT45DB041E is the 8-pin SOIC near the MSP430; the resin is already cleaned off (you did it the night before).
- Align pin 1 of the SOIC-8 clip to pin 1 of the chip (the dot/notch on the chip body). The clip's jaw-1 corresponds to chip pin-1.
- Clamp the clip onto the chip. Wiggle slightly to feel the jaws seat on all eight leads. Do not yank.
- The clip's other end goes into the ZIF ICSP adapter; the adapter sits in the T48's ZIF socket with the lever down. The T48 is plugged into the laptop via USB.

`[TROUBLESHOOT]` If the clip will not bite — go to §"If the clip won't bite" below. Re-seating is the first move every time. Bad clip contact is the workshop's number-one failure mode.

**Step 3 — Read the chip (3 min)**

At the laptop:

```bash
cd ~/workshop
sudo minipro -i -p 'AT45DB041E[Page264]@SOIC8' -r my-dump.bin
```

- The `-i` flag suppresses some interactive prompts; the device name `AT45DB041E[Page264]@SOIC8` is the canonical minipro identifier for the 264-byte-page DataFlash in its SOIC-8 package
- minipro will print a firmware-version warning. **The warning is non-blocking** — let it scroll past
- If chip-ID returns `0x0000`, re-seat the clip (§"If the clip won't bite") and run again. Do **not** add `-y` unless you have already re-clipped twice — `-y` bypasses the chip-ID check and can mask a wiring problem
- A clean read takes ~5 seconds for the main array. Expected output: `Reading Code... OK`, possibly a timeout on `Reading User...` (that's the Security Register, which `-w` does not target; the timeout is benign and the main array is intact)

```bash
ls -l my-dump.bin
md5sum my-dump.bin
```

Confirm `540672` bytes. Note the MD5 — the attendee can compare it to the workshop-distribution dump's MD5 if they want to verify the read is byte-identical to a clean baseline.

`[CHECKPOINT]` Attendee has a 540,672-byte `my-dump.bin` on the laptop. Do not proceed without it.

**Step 4 — Find the user-code page and decode slot 0 (5 min)**

Open the dump in `xxd` (or ImHex, if the attendee prefers a GUI):

```bash
xxd my-dump.bin | head -20
```

- Byte 0 is `0xFD` on a factory/unmodified lock. That is the user-code page header. **The user-code page is page 0 — the very start of the dump.** No hunting required. (Reprogrammed locks may show a different high nibble — e.g. `0x1D` on a lock whose code was changed at the keypad; the **low nibble `0xD` is the marker**. `build-injected.py` accepts any byte 0 whose low nibble is `0xD` and prints a NOTE for the non-factory case. A byte 0 whose low nibble is *not* `0xD`, e.g. all-`00` or all-`FF`, is a bad read — re-read the chip.)
- At file offset `0x0001`, byte = `0x12`. That is code byte 1 for slot 0. Packed BCD: nibbles `1, 2` → digits "1", "2".
- At file offset `0x0033`, byte = `0x34`. Code byte 2 for slot 0. Nibbles `3, 4` → "3", "4".
- At file offset `0x0065`, byte = `0x56`. Code byte 3 for slot 0. Nibbles `5, 6` → "5", "6".
- Concatenate: slot 0's code is **`123456`** — the Alarm Lock factory-default master code.
- At file offset `0x0097`, byte = `0x01`. Active flag for slot 0. The slot is active.
- At file offset `0x00C9`, byte = `0x01`. Permission flag for slot 0. That is **Normal User**, not Master.

**This is the slot-0 anomaly.** Stop and discuss it with the attendee:

> "The code value `123456` is the factory-default master code. But the permission flag here says Normal User, not Master. What does that tell you about how this lock was configured?"

Let them answer. The answer this prompt is reaching for: the lock was re-mastered — someone programmed a new master code, and the new master lives somewhere else on the chip that this validation hasn't located, while the old factory code value `123456` was left behind as a Normal User. The lesson is that the role assignment is decoupled from the slot index and from the code value; the permission flag is its own field and the firmware honors it independently. Land that.

`[CHECKPOINT]` Attendee has decoded slot 0 and can name the slot-0 anomaly.

**Step 5 — Build the injection payload (4 min)**

You are going to inject three codes at three privilege levels in three scattered slots. The handout has the patch table; the script `build-injected.py` in `~/workshop/` will produce the modified dump from the attendee's `my-dump.bin`. (The patch table is also reproduced in the handout for reference — the worked example.)

| Slot | Code | Code bytes (packed BCD) | Permission | Permission byte |
|---|---|---|---|---|
| 19 | `133769` | `0x13 0x37 0x69` | Master | `0xF1` |
| 32 | `420420` | `0x42 0xB4 0x2B` | Supervisor | `0xC1` |
| 49 | `696969` | `0x69 0x69 0x69` | Elevated | `0xE1` |

Walk them through slot 32 specifically: the code `420420` has two zero digits, in the third and sixth positions. Those zeros are encoded as the nibble value `0xB`, not as ASCII `0x30` and not as BCD `0x00`. So code byte 2 for slot 32 = nibbles `B, 4` = `0xB4` (the leading nibble carries the zero digit from position 3). Code byte 3 for slot 32 = nibbles `2, B` = `0x2B` (the trailing nibble carries the zero digit from position 6). This is one of the workshop's payoff moments — show them the bytes, point at where the `0xB` lands in the nibble, and tell them: "If `420420` unlocks the lock, this is the rule for the digit zero. If `420420` is the only one that fails, the rule is something different."

At the laptop:

```bash
python3 ~/workshop/build-injected.py my-dump.bin injected.bin
md5sum injected.bin
xxd injected.bin | sed -n '1,20p'
```

The script applies the 15-byte patch from the table above to the attendee's dump and writes `injected.bin`. The xxd output of the first 264 bytes should show:

- `13` at column `0x14` (slot 19 code byte 1)
- `42` at column `0x21` (slot 32 code byte 1) — visible as `.B..` in the ASCII column
- `69` at column `0x32` (slot 49 code byte 1)
- `37` at column `0x46` (slot 19 code byte 2)
- `b4` at column `0x53` (slot 32 code byte 2 — the digit-zero nibble in plain sight)
- `69` at column `0x64` (slot 49 code byte 2)
- `69` at column `0x78` (slot 19 code byte 3)
- `2b` at column `0x85` (slot 32 code byte 3 — the trailing digit-zero nibble)
- `69` at column `0x96` (slot 49 code byte 3)
- `01` at columns `0xAA`, `0xB7`, `0xC8` (the three active flags)
- `f1` at column `0xDC` (slot 19 Master), `c1` at column `0xE9` (slot 32 Supervisor), `e1` at column `0xFA` (slot 49 Elevated)

If any of those bytes is missing, the script did not run cleanly — re-run it and check the source dump.

`[CHECKPOINT]` Attendee has `injected.bin` on the laptop, 540,672 bytes, with the 15 patch bytes visible in xxd at the expected columns.

**Step 6 — Write the modified dump back to the chip (4 min)**

The clip is still on the chip. The lock batteries are still out. The T48 is powering the chip through the clip.

```bash
sudo minipro -i -p 'AT45DB041E[Page264]@SOIC8' -w injected.bin
```

- This takes about 20 seconds. minipro reports `Verification OK` at the end
- If it aborts with a firmware-mismatch warning, the warning is non-blocking — the attendee may need to add `-y` to bypass the warning on this build. **Only add `-y` for the firmware warning, never to skip the chip-ID check unless you have already re-clipped**
- If verification fails, the clip contact dropped mid-write — re-seat and re-run. The write is idempotent against the same `injected.bin`, so a retry is safe

Read back to confirm:

```bash
sudo minipro -i -p 'AT45DB041E[Page264]@SOIC8' -r post-write.bin
cmp injected.bin post-write.bin && echo "FULL IMAGE MATCH — write took"
```

If `cmp` reports differences only in the audit log band (offsets `0x42000`–`0x46938`) and at pages 1976–1977, that's still a pass — the lock may have logged a power event during the write. The 15 patched bytes in page 0 are what matters; confirm they match `injected.bin`.

`[CHECKPOINT]` Read-back confirms the write took. Attendee sees the `FULL IMAGE MATCH` line, or at minimum the page-0 region matches.

**Step 7 — Unclip, reinstall batteries, demonstrate (3 min)**

- Unclip the SOIC-8 from the chip carefully — the clip is fragile, the chip is now flashed
- Reinstall the lock batteries
- Wait for the lock's boot chirp / LED cycle to complete
- Punch each code in sequence:
  - `133769` → should unlock (slot 19 Master)
  - `420420` → should unlock (slot 32 Supervisor — this validates the `0xB`-for-zero rule)
  - `696969` → should unlock (slot 49 Elevated)
  - `123456` → still unlocks (slot 0, untouched)

`[CHECKPOINT]` All four codes unlock the lock. This is the workshop's central proof. If any code fails, see §"What it means if a code fails" below.

**Step 8 — The advanced-discussion arc — programming-mode-fails-for-injected-codes (optional, 0–3 min)**

If time allows and the attendee is engaged, do this. If the next attendee is waiting, skip and move them in.

Have the attendee enter programming mode with the factory code first — `123456` followed by the programming-mode sequence per the lock's documented procedure. Programming mode opens. Exit programming mode.

Now have them try programming-mode entry with `133769`. It will **not** open programming mode, even though `133769` is set as Master (`0xF1`) on the chip.

Discuss:

> "The flash-write attack is sufficient for unauthorized entry. It is not sufficient for sustained operational control. There is some extra validation the firmware does for programming mode that ordinary unlock does not — possibly a checksum field on the user-code page, possibly a separate code lookup table the firmware consults, possibly something else entirely. We don't know yet. What we do know: the lock's audit log behaves differently for injected codes than for codes that were programmed through the keypad. That difference is the defender's tell."

This is the **defender's takeaway**, not a bug in the attack. Land it that way. The attack works at the level of door entry. The lock retains a subtle integrity property at the programming-mode layer. If your threat model is "someone gets in for ten minutes," the attack is sufficient. If your threat model is "someone owns this lock and can re-program it through normal channels going forward," the attack is not yet sufficient. That is a real, useful distinction — surface it.

**Step 9 — Recovery — write the baseline back (if needed)**

If any code fails (Step 7), or if the lock stops responding entirely, write the baseline back to restore the chip:

```bash
sudo minipro -i -p 'AT45DB041E[Page264]@SOIC8' -w intact-lock-AT45DB041E-main-2026-05-20.bin
```

- The baseline is on the station laptop at `~/workshop/intact-lock-AT45DB041E-main-2026-05-20.bin`
- The AT45DB041E has no OTP fuses and no auto-lock-on-write behavior; the recovery write is unconditionally available
- After recovery, slot 0 is `123456` Normal again, all other slots empty, audit log intact

Recovery is the safety net. The lock cannot be bricked by this attack — only by a power glitch during the write itself, and even then the recovery write usually reseats it.

`[CHECKPOINT]` The lock is either in its injected state with all four codes unlocking, or has been recovered to its baseline state with `123456` unlocking. **Both are valid end states.** The point is that the attendee saw the attack work and saw recovery work.

#### Rotation at programmer stations

As one attendee finishes Step 7 (or Step 8), the facilitator at that station:

1. Recovers the chip to baseline (Step 9) so the next attendee starts from a clean state. The recovery write takes ~20 seconds; do it while the finishing attendee is talking to their friend or grabbing water
2. Unclips the SOIC-8 from the chip, lays the clip on the bench
3. Wipes the laptop's `my-dump.bin`, `injected.bin`, `post-write.bin` from `~/workshop/`
4. Signals to the static-station co-facilitator that a slot is open

The next attendee rotates in. Reset the bench, re-clip (or have the attendee re-clip, depending on their comfort), restart at Step 1.

Each programmer station turns ~3 attendees in 70 minutes. Four stations × 3 = **~12 attendees through the full hands-on flow**. That's the workshop's primary throughput.

---

### [80:00–90:00] Synthesis, room-wide Q&A, wrap — 10 min

Pull the room together. Anyone still at a programmer station is finishing or watching their lock unlock; the static stations wind down naturally.

- Quick poll: hands up — who got all four codes to unlock? Acknowledge the room. Acknowledge anyone whose write didn't take cleanly on the first try; that's also a valid outcome and they saw recovery work
- The synthesis beat: "This was the flash-write attack at the unlock layer. The talk earlier walked through five layers — physical, NAND, firmware, USB cable, audit. You just did one of them, on real hardware, in 25 minutes. The other four are in the repo"
- The slot-0 anomaly — one more public mention. The lock you worked on had been re-mastered before you got here. The role assignment in flash is independent of the code value, and the firmware honors the role
- The programming-mode-fails finding — surface it room-wide if any station ran Step 8. The defender's tell is real
- The mitigations beat (15 seconds): "Encrypt the NAND. Blow the JTAG fuse. Authenticate the cable. Use a TPM. Under $5 per unit at manufacturing time. None of this is exotic."
- One repo link, one social handle. Out.

---

## Troubleshooting Reference

### If the clip won't bite

Bad SOIC-8 clip contact is the workshop's most common failure mode. Before suspecting anything else, work this list:

1. **Re-seat the clip.** Open it fully, re-align pin 1 to pin 1, clamp again. Apply slight downward pressure while running the read
2. **Check pin 1 alignment.** The dot or notch on the chip body marks pin 1; the clip's marked end (usually a triangle or arrow on the body) corresponds to clip jaw 1. Reversed orientation reads as `0x0000` chip ID
3. **Wiggle the chip's leads with a toothpick.** If a lead has cold-solder lift from the resin cleaning, the clip jaw will not seat on it. A toothpick reseat is faster than a re-solder
4. **Swap to a spare SOIC-8 clip.** If the clip itself is the problem, you have spares. Hot-swap, move on
5. **Swap the lock board** for a spare prepped board. A board with a marginal chip is not worth fighting in a 25-minute slot

> Individual long clips + breakout leads are an **operator ad-hoc fallback only** — not part of this ladder and not an attendee procedure. If a specific board geometry truly defeats every SOIC-8 clip, the operator may wire it lead-by-lead off-flow; do not walk an attendee through it.

### `minipro` says "Chip ID 0x0000"

Almost always clip contact. Re-seat (above). If it persists across three re-clips on the same chip, swap the clip. If it persists across two clip swaps, swap the lock board.

**Do not add `-y` to bypass the chip-ID check on the first attempt.** `-y` skips the safety that catches a wiring problem; on a clean clip the chip-ID returns `0x1F24` (the AT45DB041E JEDEC ID) and minipro proceeds. If `-y` is added when the chip is not actually on the SPI bus, you get the all-zeroes failure mode the operator's research documented — minipro reports success while the dump is all `0x00`.

### Read returned all `0x00`

The clip is electrically wired to something but not to the chip — the bus clocks but nothing drives MISO, so every byte reads `0x00`. With the SOIC-8 clip + ZIF ICSP this is rare; the usual cause is a clip jaw that has not seated on a lead. Recover with a re-clip (the failure ladder above). If `-y` was used to force past the chip-ID check, that is what let minipro proceed into the read and clock out an all-zero dump — drop `-y` and let the chip-ID check fire to confirm the chip is actually on the bus.

### minipro firmware-mismatch warning

The T48 ships with firmware 00.1.34; current minipro expects 01.1.38. The warning is non-blocking — it prints, then the operation completes exit=0. Let it scroll past. Do **not** attempt a T48 firmware update during the workshop; the brick risk is non-trivial and there is no symptom to fix.

### Write failed verification

The clip slipped mid-write. Re-seat the clip, re-run the write command. The write is idempotent against the same `injected.bin` file, so re-writing produces the same end state regardless of where the previous attempt stopped.

### Lock does not respond after writing

Reinstall the batteries (it's almost always this). Wait the full boot chirp / LED cycle. Try `123456` first — if `123456` still unlocks, the page-0 patch may not have taken; re-clip and re-read to check `post-write.bin` against `injected.bin`. If no code at all unlocks, run the recovery write (Step 9) — the lock returns to baseline and is fully functional again.

### What it means if a specific code fails

- **All three injected codes fail, `123456` still unlocks.** The write went somewhere but page 0 didn't take. Re-clip, re-read, check the read-back against `injected.bin`. Most likely a clip-contact slip on the write that minipro's verify didn't catch. Re-write
- **`133769` unlocks, `420420` does not, `696969` unlocks.** The `0xB`-for-zero encoding rule is wrong for this firmware revision. That is itself an interesting finding — surface it to the operator. Try `0xA` or `0xC` for the zero digit on a follow-up attempt
- **Only `133769` unlocks.** Permission-flag semantics may differ on this revision; `0xC1` and `0xE1` may not map to "permits door operation" the way `0xF1` does. Another interesting finding; flag to the operator
- **Nothing unlocks, including `123456`.** Page 0 has been corrupted. Run the recovery write (Step 9). The lock will come back

### Drill station — drill stuck in core

Reverse the drill before pulling. Pull straight, not at an angle. If the bit is wedged hard, slide the next core onto the bit and twist the new core to free the old one. Replace the bit if it heats up — a hot bit is a dull bit and a dull bit is what stalls in the core.

### Drill station — attendee without safety gear

Refuse politely. Glasses and ear protection are at the entry to the station for a reason. If they want to watch without drilling, that's fine; if they want to drill, the gear goes on first.

---

## Facilitator Register Notes

### Pacing signals

- The hands-on block is 70 minutes for ~12 programmer-station attendees and however many flow through the static and drill stations. Resist the urge to lecture during the block — every facilitator at a programmer station is one-on-one with the attendee in front of them, with the handout in their hands
- If a station is moving fast (~20 min per attendee), the facilitator can extend Step 8 (the programming-mode-fails discussion) with the current attendee while waiting for the next rotation. Don't rush Step 8 — it's the workshop's intellectually deepest beat
- If a station is moving slow (~30 min per attendee), drop Step 8 for that attendee, get them to the keypad-unlock proof in Step 7, and rotate. Three attendees through Steps 1–7 beats two attendees through Steps 1–8

### Room temperature reads

- Quiet focus around the programmer stations is what you want — circulate silently between stations
- Loud excitement when a lock first unlocks with an injected code: lean in. That's the workshop's payoff moment and the room hears it. Don't shush
- Engagement dropping at the 50:00 mark: stretch break. Tell the room "stretch and re-seat your clip." Physical motion resets attention
- Drill station getting loud: that's fine. The drill station is supposed to be loud. Ear protection is mandatory at the station; the noise itself is part of the destructive-entry counterpoint

### Reading attendees at programmer stations

- An attendee who is following the handout step-by-step without asking questions: leave them alone. Walk them through Step 4's slot-0 discussion at the right moment; otherwise the handout is enough
- An attendee asking deep firmware questions: defer to the talk and the repo. "Five layers, this is one. The other four are in the repo. After the workshop come find me." Don't burn 10 minutes at the programmer station on the MSP430 — there are three other attendees waiting on this slot
- An attendee struggling with the hex editor: switch them to `xxd` with `| less` and have them search by offset (`/ <offset>` in `less`). Don't try to teach a hex editor in 25 minutes

### ToorCamp-specific environment

- Outdoor venue: wind, dust, occasional rain. Cover laptops between rotations if a gust comes through
- Daylight changes: if you start in bright sun and end at golden hour, the handouts get harder to read. Headlamps are at every station for this reason
- Adjacent campsite noise: this is ToorCamp; you cannot do anything about it. Project your voice. The programmer stations are one-on-one so noise affects them less than the wrap-up
- Late arrivals: hand them a handout, point them at the next open static station. The hands-on flow is self-directed enough at the static stations to absorb walk-ins
- Wandering attendees: someone will walk past, peer at a programmer station, and ask what's happening. That's the workshop working. Tell them in one sentence, point them at a static station, and rotate them into a programmer slot when one opens

---

## Facilitator Pocket Reference

Tear this out and put it in your back pocket. Everything you need to drive a programmer station in two columns.

### The minipro commands

```
Read:    sudo minipro -i -p 'AT45DB041E[Page264]@SOIC8' -r my-dump.bin
Build:   python3 ~/workshop/build-injected.py my-dump.bin injected.bin
Write:   sudo minipro -i -p 'AT45DB041E[Page264]@SOIC8' -w injected.bin
Verify:  sudo minipro -i -p 'AT45DB041E[Page264]@SOIC8' -r post-write.bin
         cmp injected.bin post-write.bin
Recover: sudo minipro -i -p 'AT45DB041E[Page264]@SOIC8' -w \
           ~/workshop/intact-lock-AT45DB041E-main-2026-05-20.bin
```

### Baseline + workshop-distribution dump

```
Baseline MD5:    eb6acff32ef13b29ac6ebed10d77316d  (intact in-service lock)
Injected MD5:    47b6faaf1217389afa7a879d93c024dd  (3-slot patch applied)
Workshop-dist:   [your produced MD5]               (baseline + audit-log byte-5 zeroed)
Dump size:       540,672 bytes (main array, 264-byte native page mode)
                 540,800 if a tool also captures the Security Register
```

### The injection patch table

```
Slot 19  code 133769  bytes 0x13 0x37 0x69  perm 0xF1 Master
Slot 32  code 420420  bytes 0x42 0xB4 0x2B  perm 0xC1 Supervisor   ← exercises 0xB-for-zero
Slot 49  code 696969  bytes 0x69 0x69 0x69  perm 0xE1 Elevated
```

### Slot N offset map (apply N from 0 to 49)

```
code byte 1   0x0001 + N
code byte 2   0x0033 + N
code byte 3   0x0065 + N
active flag   0x0097 + N    01 active   FF empty
permission    0x00C9 + N    F1 Master   E1 Elevated   C1 Supervisor   01 Normal
```

### Encoding rules

```
Packed BCD: each byte = two decimal digits, one per nibble
Digit 0:    nibble value 0xB (NOT ASCII 0x30, NOT BCD 0x00)
Example:    420420 → 0x42 0xB4 0x2B
            slot 0 = 123456 → 0x12 0x34 0x56  (no zeros, no 0xB substitution)
```

### Clip-bite failure ladder

```
1. Re-seat the SOIC-8 clip
2. Re-check pin 1 alignment (chip dot ↔ clip jaw 1)
3. Toothpick-poke any chip lead that may have lifted from resin cleaning
4. Swap the SOIC-8 clip itself
5. Swap the T48 (rare)
6. Swap the lock board (last resort)
   (individual long clips = operator ad-hoc only, off-flow — not a station step)
```

### Read-back interpretation

```
cmp full image match               → write fully took, no operational events recorded
cmp page-0 match, diffs elsewhere  → write took (audit log / wear-level shuffle is fine)
cmp page-0 differs                 → write did NOT take; re-clip, re-write
```

---

## Editorial Flag

### attribution_decisions

Operator handle (Qweary) is the only identity surfaced. Co-facilitators are referenced as "co-facilitator A/B/C" — the operator decides whether to drop their handles into the printed facilitator copy on the morning of the workshop. The Alarm Lock T2/T3 is named by manufacturer and model, consistent with the operator's public blog series. No external individuals named. The slot-0-anomaly discussion does not attribute the re-mastering to any party — the framing is "this lock was re-mastered before you got here" without speculating about who or why.

### scope_inclusions_and_omissions

**Included:**

- The full per-attendee programmer-station flow (Steps 1–8 + recovery), grounded in the T+4e operator-bench validation and the Interlock dispatches
- The 4-programmer-station + S1/S2/D1 + drill-station layout with rotation timing
- The slot-0-perm anomaly as a guided-discussion prompt (Step 4)
- The programming-mode-fails-for-injected-codes finding as the advanced-discussion arc (Step 8)
- The workshop-distribution dump production procedure (Python recipe with the audit-log byte-5 zeroing — chosen over `dd`/`xxd` because the audit log is a structured 6-byte-record stream and Python's bytearray indexing reads more cleanly to a facilitator producing the dump the night before than a shell-arithmetic equivalent would)
- The clip-bite failure ladder as the troubleshooting first move
- Recovery via baseline write-back, with the AT45DB041E's no-OTP / no-auto-lock properties as the safety guarantee
- The cut-out window replacement for the originally-considered drill-into-body demo (preserves the lesson, preserves attendee safety)

**Omitted / deferred:**

- The detailed MSP430 firmware reverse-engineering (the 38-byte payload at 0xFA20) — the workshop is the unlock-layer flash-write attack only; firmware work stays in the talk and the repo
- The full audit-log decode — the workshop teaches that the audit log exists and is structured, but the per-byte field semantics (event codes, timestamp encoding) are out of scope for a 90-minute session
- The USB cable emulation layer (CP2102 + FaceDancer) — talk content, repo content, not workshop content
- The CH341A toolchain — explicitly not the workshop toolchain; the operator's procurement is locked on T48. The decommissioned CH341A path is not referenced in the guide
- Desoldering procedures — the workshop is in-circuit-clip throughout; the desolder-resolder skill barrier is removed by toolchain choice

**No must-include workshop-flow steps omitted.**

### audience_calibration

**Primary**: ToorCamp attendees who sat down at a programmer station. Mixed physical and digital security practitioners, hardware hackers, hacker-camp generalists. Per the talk's audience-calibration finding (mostly digital, decent fraction understand hardware, small fraction with locksmith context), the per-station flow assumes:

- Comfort with a Unix shell and a hex editor — yes
- Familiarity with SPI flash chips specifically — no, but they will pick it up
- Locksmith knowledge — no; the lock's mechanical state is narrated in passing where it matters (Step 1 verify, Step 7 re-battery)

**Implicit secondary**: anyone who reads the guide afterward — co-facilitators preparing for a re-run, attendees who took the handout home and want to try this on their own bench. The guide is written so a future co-facilitator can drive a station cold from this document plus the handout, with the operator unavailable.

**Register**: facilitator-instructional. Scannable. Imperative. No anecdotes, no register-bleed from the talk. The "dead bytes tell no lies" framing is locked in title only; the body of the guide is procedural.

### format_compliance

**Target register**: instructional facilitator guide (per Smyth's register catalog), workshop-specific subclass. Length target: 25–35 KB given the four-station layout, the per-station flow detail, the workshop-distribution dump production procedure, and the troubleshooting ladder. This draft lands inside that envelope. Sectioning: Pre-Session Setup → Learning Objectives → Equipment List → Run-of-Show → Troubleshooting Reference → Facilitator Register Notes → Facilitator Pocket Reference → Editorial Flag, with the per-attendee flow nested under Run-of-Show. Pocket Reference at the back is tearable; the operator can print it on the back of the first page for a quick-flip facilitator card.

### quoted_material_handling

Two operator-voice quotes are reproduced verbatim for the discussion prompts:

- The slot-0 discussion prompt — *"The code value `123456` is the factory-default master code. But the permission flag here says Normal User, not Master. What does that tell you about how this lock was configured?"* (Step 4)
- The programming-mode-fails framing — *"The flash-write attack is sufficient for unauthorized entry. It is not sufficient for sustained operational control."* (Step 8)

Both are facilitator-voice cues, not attendee-facing literal quotes from any source. They're operator-styled because the operator authors them on the day; if a co-facilitator drives the station, the words can shift but the beat stays.

### time_relative_phrasing_audit

Scanned for time-relative phrasings that would read false the day after publication. Findings:

- "The night before" / "the morning of" — scene-relative, anchored to the workshop event. PASS
- "Once one attendee finishes (~25 minutes)" — duration estimate, not a calendar reference. PASS
- "Approximately 12 attendees through the full hands-on flow" — population estimate, not time-relative. PASS
- "Per the T+4e operator-bench validation" — internal session reference, not a reader-clock phrasing. PASS

No "last week" / "five days ago" / "recently" detected.

### prose_tic_audit

**Register**: instructional facilitator guide (workshop subclass).

| Signature | Operator baseline | Register target range | This draft (approx) | Status |
|---|---|---|---|---|
| em-dash density | 8–12 / 1000 words | 5–10 / 1000 words (procedural register punishes high density) | ~7 / 1000 | PASS — mid-range |
| parenthetical depth | ~1 per 200 words | 0.8–1.2 per 200 words | ~1.0 per 200 words | PASS |
| hedge-marker frequency | 2–4 / 1000 words | 1.5–4 / 1000 words | ~2.5 / 1000 | PASS |
| zombie-noun density | low | low | low — facilitator-imperative throughout | PASS |
| sentence-length avg | ~18 words, high variance | 12–22 words | ~15 words avg, range 4–32 | PASS |

**A1 (em-dash)**: em-dashes used for the operator's documented pause-before-revelation and appositive-clarification functions. No em-dash-as-default-comma; no zero-out under-correction. Range-fidelity confirmed.

**A2 (negation-pivot)**: scanned for "this isn't X — it's Y" pivot rhetoric. Absent. Accretion construction used throughout. One declarative "X. Y." pair in the programming-mode-fails section ("The flash-write attack is sufficient for unauthorized entry. It is not sufficient for sustained operational control.") — flat declarative pair, not pivot rhetoric.

**A3 (divergence-from-baseline)**: checked against operator's `dead-bytes-tell-no-lies.html` voice baseline. Sharp declarative sentences alternating with longer technical elaborations — present. Hedge markers minimal — present. Technical-anchor moves (byte offsets, command lines, MD5 hashes) — present throughout. Noir-inflected aphorisms absent in body — register-appropriate for facilitator-instructional, which is a procedurally constrained subregister.

Status: PASS across all signatures.

### voice_calibration_set

- **WEB-001** (primary, refreshed at the top of this session): `qweary.github.io/dead-bytes-tell-no-lies.html` — em-dash density per 1000 words, parenthetical patterns, technical-anchor cadence (byte offsets and command names mid-sentence), declarative-first opening structures
- **OWN-001 / OWN-002** (secondary): the engagement's own `SPEAKING-NOTES.md` and `SLIDE-CONTENT.md` from earlier in this arc — workshop-arc voice continuity, the "dead bytes tell no lies" framing as locked title, the audience-calibration findings (mostly digital, decent hardware fraction)
- **OWN-003** (technical-substance grounding): `T+4e-DUMP-VALIDATION-REPORT.md`, `T+4e-INJECTION-PAYLOAD.md`, `DUMP-VALIDATION.md`, `T48-KALI-PLAN.md` — the per-byte facts, the validated MD5s, the in-circuit clip method, the slot-0 anomaly, the programming-mode-fails finding

Register delta from the talk-arc speaking notes: facilitator-instructional register is tighter and more procedural than the talk register; cue-line cadence is replaced with imperative steps; anecdote density drops to near-zero (one operator-voice quote at Step 4, one at Step 8, both serving as facilitator cues rather than attendee-facing stories).

### named_hooks

1. **The slot-0 anomaly as discussion prompt** (Step 4) — the lock has the factory-default code value in slot 0 but the role is Normal User, not Master. The role assignment is decoupled from the code value. This is the workshop's first intellectual payoff moment; the attendee earns the insight by decoding the bytes themselves
2. **The `0xB`-for-zero rule as worked example** (Step 5) — slot 32's `420420` encoded as `0x42 0xB4 0x2B`. The digit zero living at nibble value `0xB` rather than ASCII `0x30` or BCD `0x00` is the workshop's second intellectual payoff. Slot 32 is included in the patch specifically so the attendee sees `0xB4` and `0x2B` in their own xxd output and then sees `420420` unlock the lock at Step 7
3. **The programming-mode-fails-for-injected-codes finding as advanced-discussion arc** (Step 8) — the flash-write attack is sufficient for entry, not for sustained operational control. This is the workshop's third payoff, the operator-bench finding from T+4e that turns a "yes the attack works" outcome into a "and here's where it gets interesting" outcome. Defender's takeaway lives here

### anecdote_flags

The facilitator-instructional register is anecdote-light by convention. The talk-arc anecdotes (ANE-001 through ANE-005) are not eligible for this register — the talk carries them. The guide's only narrative beats are the three discussion prompts above, all sourced from the T+4e operator-bench session and the Interlock dispatches.

No operator-decide flags raised. No must-include omissions to surface.
