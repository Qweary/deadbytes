# Dead Bytes Tell No Lies
## DataFlash Decoding and Injection for Access Control Locks — Attendee Card
### ToorCamp 2026 · Qweary

---

## One command

From the cloned repo root:

```bash
./bin/start.sh
```

The browser opens to a local control panel. Click **READ** to decode the lock's 50
code slots; type a code and click **WRITE** to inject your own. That's it — no
hardware, no setup, no `sudo`. (Windows: run `start.ps1` from the repo root instead.)

Everything runs locally against a bundled sample dump. Nothing touches a real chip
until you opt into the live path at the very end of this card.

---

## CLI fallback (no browser needed)

If you would rather type, three lines do the whole workshop — straight from the
clone, from any directory, with no `sudo`:

```bash
# READ — decode all 50 slots (shows the three baked-in codes)
python3 workshop/kit/tools/lock-tool.py read --all

# WRITE — bake your own code into a copy and watch it land
python3 workshop/kit/tools/lock-tool.py write --code 420420 --slot 32 --role elevated

# RECOVER — restore the code-free baseline if you want a clean slate
python3 workshop/kit/tools/recover-baseline.py
```

`--code` is any six digits (zeros allowed — the tool applies the `0xB`-for-zero rule
for you), `--slot` is `0`–`49`, `--role` is `master`, `elevated`, `supervisor`, or
`normal`. The default `read --all` source already carries three codes (below), so you
see real codes the moment you read — nothing is faked.

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

You do **not** need this to finish the workshop — the GUI and the CLI fallback teach
the whole decode/inject lesson on the sample dump. The live path is for anyone who
wants to do it on real hardware, and it is the only place hardware is touched. Ask an
organizer to walk you through it; the short version:

- The same READ and WRITE gain a `--live` flag that talks to a real AT45DB041E via a
  T48 programmer and SOIC-8 clip. The clip-read is `sudo`-free (the bundled udev rule
  grants your session access directly). The `--live` write is confirmation-gated — the
  tool prints exactly what it will do and waits for you to type `yes`.
- After writing, reinstall the lock's batteries and punch each code on the keypad:
  `133769` (Master), `420420` (Elevated — the `0xB`-for-zero proof), `696969`
  (Supervisor), and `123456` (the untouched factory slot) all unlock.
- If anything goes sideways, `recover-baseline.py --live` flashes the code-free
  baseline back. The AT45DB041E has no OTP fuses; recovery is always available.

---

## Take-home

By **qweary** — code, dumps, notes, and the "Dead Bytes Tell No Lies" blog series:

- `github.com/qweary`
- `qweary.github.io`
