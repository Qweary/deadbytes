# Dead Bytes Tell No Lies
## DataFlash Decoding and Injection for Access Control Locks — Attendee Card
### ToorCamp 2026 · Qweary

---

## One command

From the cloned repo **root**:

```bash
./bin/start.sh
```

The browser opens to a local control panel in **Practice** mode (a calm-green
"sample copy, no hardware" banner). Click **READ the sample** to decode the lock's
50 code slots; type a code and click **WRITE into a copy (preview)** to bake in your
own. That's it — no hardware, no setup, no `sudo`. (Windows: run `start.ps1` from
the repo root instead.)

Everything runs locally against a bundled sample dump. Nothing touches a real chip
until you switch the panel to **Live lock** mode (or pass `--live` on the CLI) — the
opt-in live path at the very end of this card.

---

## CLI fallback (no browser needed)

If you would rather type, three lines do the whole workshop. Run them **from the
repo root**, with no `sudo`:

```bash
# READ — decode all 50 slots (shows the three baked-in codes)
python3 workshop/kit/tools/lock-tool.py read --all

# WRITE — bake your own code into a copy and watch it land (a PREVIEW — the
#         real chip is never touched without --live)
python3 workshop/kit/tools/lock-tool.py write --code 420420 --slot 32 --role elevated

# RECOVER — restore the code-free baseline if you want a clean slate
python3 workshop/kit/tools/recover-baseline.py
```

`--code` is any six digits (zeros allowed — the tool applies the `0xB`-for-zero rule
for you), `--slot` is `0`–`49`, `--role` is `master`, `elevated`, `supervisor`, or
`normal`. The default `read --all` source already carries three codes (below), so you
see real codes the moment you read — nothing is faked. A `write` without `--live`
prints a loud **PREVIEW ONLY — nothing was written to the lock** banner: it bakes
your code into a *copy* and re-decodes it so you watch your value land, but the real
chip is untouched.

---

## What you're learning

User codes for this lock live in the **DataFlash** chip's first page (file offset 0).
Three facts carry the lesson:

1. **Packed BCD.** Each code byte holds two decimal digits, one per nibble: `0x12`
   decodes to "1","2". A six-digit code is three bytes concatenated.

2. **The `0xB`-for-zero trap.** The digit `0` is stored as the nibble value `0xB` —
   not ASCII `0x30`, not BCD `0x00`. So `420420` encodes as `0x42 0xB4 0x2B`: each
   zero shows up in a hex view as a stray `B`. That is the workshop's trap.

3. **Additive write preserves other slots.** A `write` is a read-modify-write: your
   code stacks on top of whatever is already there and leaves every other slot intact.
   Writing into a slot that's already occupied prints an OVERWRITE warning first;
   writing into an empty slot just adds.

The three codes the default READ shows you:

| Slot | Code | Bytes (packed BCD) | Role | Perm byte |
|---|---|---|---|---|
| 19 | `133769` | `0x13 0x37 0x69` | Master | `0xF1` |
| 32 | `420420` | `0x42 0xB4 0x2B` | Elevated | `0xE1` |
| 49 | `696969` | `0x69 0x69 0x69` | Supervisor | `0xC1` |

Slot 32 (`420420`) is the one to watch — its two zero digits land at nibble `0xB`,
exactly as the re-decode confirms.

**Want the depth?** The full page-0 offset map, the permission-flag table, the slot-0
re-mastering anomaly, and the audit-log structure are in the **decode reference**
(`kit/docs/DATAFLASH-DECODE-REFERENCE.md`). The organizer guide
(`FACILITATOR-GUIDE.md`) covers the live-hardware path station-by-station.

---

## Advanced: the live chip (opt-in)

You do **not** need this to finish the workshop — the panel's Practice mode and the
CLI fallback teach the whole decode/inject lesson on the sample dump. The live path
is for anyone who wants to do it on real hardware, and it is the only place hardware
is touched. Ask an organizer to walk you through it; the short version:

**In the browser:** click the **Live lock** tab. The banner turns red — *"LIVE LOCK
— writes the REAL chip."* **READ the real lock** runs a real read; **FLASH the real
lock…** takes you to a confirmation page that shows exactly what lands on the lock
(your code, plus the 3 demo codes and the `123456` starter) and reminds you the clip
must be seated and the batteries OUT. Only after a second deliberate **Yes, flash the
real lock** does anything get written. Cancel takes you back.

**On the CLI:** the same READ and WRITE gain a `--live` flag that talks to a real
AT45DB041E via a T48 programmer and SOIC-8 clip — `python3 workshop/kit/tools/lock-tool.py
read --all --live` and `… write --code … --slot … --role … --live`. Every live
`minipro` call is `sudo`-free (the bundled udev rule grants your session access
directly). The `--live` write is confirmation-gated: it prints exactly what it will
do and waits for you to type `yes`, then reports **LIVE WRITE OK — landed on the REAL
chip**.

What a live write lands: a copy of the sample dump with your code injected, so every
attendee ends on the same known-good state — your code **plus** the 3 demo codes
(`133769`, `420420`, `696969`) at slots 19/32/49 and the `123456` starter at slot 0.

- After writing, reinstall the lock's batteries and punch each code on the keypad:
  `133769` (Master), `420420` (Elevated — the `0xB`-for-zero proof), `696969`
  (Supervisor), and `123456` (the untouched factory slot) all unlock.
- If anything goes sideways, `recover-baseline.py` flashes the code-free baseline
  back. The AT45DB041E has no OTP fuses; recovery is always available.

**Under the hood** (for the curious — the tools print these so the advertised command
equals the run command): the live read is `minipro -i -p AT45DB041E[Page264]@SOIC8 -c
code -r <file>` and the live write is `minipro -i -p AT45DB041E[Page264]@SOIC8 -c code
-w <file>`. The `-c code` scopes the operation to the chip's main-array `code` region,
where the entire user-code table lives.

**Working with your own dump.** Want to read a *different* lock, see what's on it,
add codes, and write it back? The two raw `minipro` lines above bracket a four-step
loop. Run the `python3` lines **from the repo root**:

```bash
# 1. READ your chip to a file (raw minipro, -c code scoping required on this T48)
minipro -i -p AT45DB041E[Page264]@SOIC8 -c code -r mydump.bin

# 2. DECODE what's on it — every slot, code + role
python3 workshop/kit/tools/lock-tool.py read --dump mydump.bin --all

# 3a. ADD the canonical 3 codes the EASY way — additive, preserves existing codes
python3 workshop/kit/tools/build-injected.py mydump.bin myinjected.bin

# 4. WRITE it back, then re-read + decode to verify it landed
minipro -i -p AT45DB041E[Page264]@SOIC8 -c code -w myinjected.bin
minipro -i -p AT45DB041E[Page264]@SOIC8 -c code -r verify.bin
python3 workshop/kit/tools/lock-tool.py read --dump verify.bin --all
```

`build-injected.py` reads a 540,672-byte dump and writes a copy with the canonical
3-slot patch (`133769`/Master/19, `420420`/Elevated/32, `696969`/Supervisor/49)
applied **additively** — every other slot is preserved, so you only clobber a code
if one of those three slots is already occupied.

**3b. Hand-edit instead.** For full control, open `mydump.bin` in a hex editor
(`xxd`, or ImHex if you want a GUI — same tools the live-hardware stations use) and
write the packed-BCD code and permission bytes yourself. The exact page-0 offset
map, the `0xB`-for-zero encoding, the active-flag offset, and the permission-byte
table are all in the **decode reference** (`kit/docs/DATAFLASH-DECODE-REFERENCE.md`)
— don't guess the offsets, read them there. Then write the file back with step 4.

**No minipro installed?** This kit *bundles* a Linux x86-64 `minipro` binary, so a
Kali/Linux laptop needs no download or compile. `sudo ./workshop/kit/install.sh`
lands it on `PATH` plus the udev rules; the live tools also fall back to the bundled
binary on their own. Mac: `brew install minipro`. Windows: build from the upstream
project, `gitlab.com/DavidGriffith/minipro`. (The bundled binary travels with a GPLv3
attribution notice at `kit/bin/MINIPRO-NOTICE.md`.)

---

## Take-home

By **qweary** — code, dumps, notes, and the "Dead Bytes Tell No Lies" blog series:

- `github.com/qweary`
- `qweary.github.io`
