# SLIDE-CONTENT.md
## ToorCamp 2026 — Dead Bytes Tell No Lies
### Slide Content Outline

---

## S1 — Dead Bytes Tell No Lies
**Type**: title
**Anchor**: HOOK
**Clock window**: 0:00–0:45
**Visual**: Title in large Orbitron. Subtitle: "Hands-On NAND Flash Decoding for Access Control Locks". Venue line: "TOORCAMP 2026 · PRIME DOME". No speaker name on this slide — lock prop moment, not a bio moment.
**Speaker cue**: [HOLD LOCK UP] — title slide is live while operator holds the lock and says nothing for 5 seconds. Do not advance until the pause lands.

---

## S2 — "I recommended this lock."
**Type**: content (meta-reveal beat)
**Anchor**: HOOK
**Clock window**: 0:45–4:00
**Visual**: Two-line reveal. Line 1 (large, terminal-green glow): `"I put them there."` Line 2 (smaller, muted): `"Then I asked how they secured the firmware."` Line 3 (amber, terminal-quote style): `"They said: We don't want to talk to you anymore."` No further text. Dark background, no bullets.
**Speaker cue**: [CLICK] after the 5-second hold. Riff from cue-lines in SPEAKING-NOTES.md Hook section. "So I spent a year figuring out how to hack them. This is that talk." — then [CLICK] to S3.

---

## S3 — Qweary
**Type**: content (minimal bio)
**Anchor**: WHO I AM
**Clock window**: 4:00–7:00
**Visual**: Three-line stack. `handle: qweary` / `locksmith · red team hobbyist` / identity line: `senior physical security engineer · I fix locks during the day and red team at night`. Small repo/blog call-forward at bottom: `code & notes: github.com/qweary · writeups: qweary.github.io — 33pp handwritten notes, 5-part blog, all the code`. No photo, no credential list.
**Speaker cue**: Say it plainly. The fix-locks-by-day / red-team-by-night line is the whole hook of the bio — lead with the asymmetry, don't credential it. Read the room for optional audience calibration questions before advancing.

---

## S4 — The Relationship That Broke
**Type**: divider (chapter)
**Anchor**: THE RELATIONSHIP THAT BROKE
**Clock window**: 7:00–8:00
**Visual**: Chapter divider style. Large text: `THE RELATIONSHIP THAT BROKE`. Rule line beneath: `—— disclosure ——`. No body text. The chapter title is the beat.

---

## S5 — "We're not worried about it."
**Type**: content ("we're not worried about it" beat)
**Anchor**: THE RELATIONSHIP THAT BROKE
**Clock window**: 8:00–12:00
**Visual**: Two blocks. Top block: short timeline in terminal-mono. `Early installs → physical disclosures → company responds. That's the good version.` / `"trusted by military" — partly because of me.` Bottom block: terminal-quote box (bordered, amber), single line: `"we're not worried about it"` — third-party relays, no attribution. Below the quote box, muted text: `Subsequent disclosures: unacknowledged.`
**Media**: One amber exhibit (img 10) beneath the followup — the wireless lock whose security password is "exactly 6 characters in length." Their posture, made concrete: a fixed, weak password floor by design. Caption-tag `posture`.
**Speaker cue**: The quote box is the emotional anchor. Pause after it. Then: "So that was that." The img-10 exhibit is optional colour — gesture to it only if the room is tracking the posture beat; don't break the emotional pause to narrate it.

---

## S6 — What This Lock Is
**Type**: content (anatomy)
**Anchor**: WHAT THIS LOCK IS
**Clock window**: 12:00–15:00
**Visual**: Two-column layout. Left: a 2×2 photo grid (replaces the old `[ T2/T3 photo ]` placeholder) — the full lock board (img 06, spanning the top), the NAND macro (img 08), the MCU macro (img 09). Right: component list in terminal-mono, minimal:
```
MCU:   MSP430F2418
NAND:  Adesto AT45DB041E
JTAG:  exposed — fuse never blown
USB:   CP2102 audit cable (DL-Windows)
```
Below, a one-line callout: `audit trail = legal evidence in some deployments.`
**Media**: img 06 (the board), img 08 (NAND macro), img 09 (MCU macro). The photos and the component list are the same three parts, twice — the photo makes the part-numbers physical. Caption-tags `the board` / `the NAND` / `the MCU`.

---

## S7 — Five Layers
**Type**: content (overview card)
**Anchor**: WHAT THIS LOCK IS · layer map
**Clock window**: 14:30–15:00
**Visual**: Vertical stack of five labeled rows, each with a number and name, left-to-right. Styled like a terminal checklist:
```
[ 1 ]  PHYSICAL          no audit events, no trace
[ 2 ]  NAND FLASH        plaintext codes, stealth window
[ 3 ]  FIRMWARE          JTAG open, 38-byte payload
[ 4 ]  USB CABLE         descriptor trust, fake cable
[ 5 ]  SYNTHESIS         combined chain
```
Brief dwell — this is a signpost, not a dwelling slide.

---

## S8 — LAYER 1: PHYSICAL
**Type**: divider (chapter)
**Anchor**: LAYER 1 — PHYSICAL
**Clock window**: 15:00–15:30
**Visual**: Chapter divider. Large: `LAYER 1` / `PHYSICAL`. Rule: `—— four attacks · no audit events ——`. Muted sub: `starts with the door.`

---

## S9 — Four Attacks, No Trace (Service Member Story)
**Type**: content (service member story)
**Anchor**: LAYER 1 — PHYSICAL
**Clock window**: 15:30–21:00
**Visual**: Top section — four-attack list in terminal-mono, no deep descriptions:
```
1. acoustic keylogging     — speaker voltage, scope, no contact
2. tailpiece deflection    — stiff wire, locksmith geometry
3. factory reset via cold  — inverted can, voltage drop, no trace
4. remote release bridging — [ story ]
```
Below a horizontal rule, the story beat: full-width terminal box with amber left-border:
```
service member: "I punch the door and it opens."
cut wires · metal frame · intermittent contact
every punch closed the circuit.
extrapolated: drill bit through comm port.
reported. declined to fix.
```
Bottom callout: `four attacks. zero audit events.`

---

## S10 — LAYER 2: NAND FLASH
**Type**: divider (chapter)
**Anchor**: LAYER 2 — NAND FLASH
**Clock window**: 21:00–21:30
**Visual**: Chapter divider, two-column hero layout. Left: `LAYER 2` / `NAND FLASH`. Rule: `—— Adesto AT45DB041E ——`. Muted sub: `264-byte pages · 50 users · plaintext codes`. Right: hero image (img 08, the NAND macro) — the chip the whole layer is about.
**Media**: img 08 as the divider hero (same file as the S6 NAND macro — intended reuse; here it's the full-bleed chapter image, on S6 it's a small exhibit).

---

## S11 — Page Layout + Stealth Window
**Type**: content (hex dump)
**Anchor**: LAYER 2 — NAND FLASH
**Clock window**: 21:30–28:00
**Visual**: Three-part layout.

Top — hex dump block (representative, terminal-mono, green text):
```
00 00 00 00 42 31 32 33 34 00 46 31 00 00 ...
         ^         ^              ^
         "0"→"B"   code ASCII    F1=Master
```
Below it, two labeled annotation lines:
- `"0" stored as "B" — TI assembly conflict`
- `permission flags: F1=Master  E1=Elevated  C1=Supervisor`

Middle — lazy write callout box (amber border):
```
MSP430 commits RAM → NAND only on battery removal.
window: read chip · edit codes · write · reinstall.
$30 programmer + SOP8 clip · 15 min
```

Bottom — stealth window callout (red border):
```
PRINT USERS:   [ injected code visible ]
EXPORT USERS:  [ injected code absent  ]
```
Single closing line: `forensic evasion window. Print ≠ Export.`

Beneath the closing line — a row of three exhibits: the $30 dump rig (img 01: lock PCB + T48 ZIF programmer + SOP8 clip), the 9-digit code where the field max is 6 (img 12, injection — proof the limit is software-only), and DL-Windows crashing while auditing an injected non-standard code (img 11). Caption-tags `$30 dump rig` / `9-digit code · max is 6` / `audit software · crash`.
**Media**: img 01, img 12, img 11. The dump rig grounds the "$30 programmer + SOP8 clip" line; the 9-digit and crash shots are the practical fallout of plaintext, software-only field constraints.

---

## S12 — LAYER 3: FIRMWARE
**Type**: divider (chapter)
**Anchor**: LAYER 3 — FIRMWARE
**Clock window**: 28:00–28:30
**Visual**: Chapter divider, two-column hero layout. Left: `LAYER 3` / `FIRMWARE`. Rule: `—— JTAG fuse: never blown ——`. Muted sub: `$30 programmer · soldering iron · unreasonable stubbornness`. Right: hero image (img 04, the soldering disaster) — red-keyed frame, matches the "unreasonable stubbornness · the wrong turns" beat.
**Media**: img 04 as the divider hero (red exhibit). "When failure is not so pretty." Bridged/burned test pins, a wire and test port pulled out of the board.

---

## S13 — 38-Byte Payload [DEMO]
**Type**: demo anchor (38-byte payload)
**Anchor**: LAYER 3 — FIRMWARE
**Clock window**: 28:30–36:00
**Visual**: Full evidence-board layout.

Top left — JTAG status box:
```
JTAG fuse:  NOT BLOWN
access:     full read/write
cost:       $30 programmer
```

Center — payload code block (largest element on screen, terminal-green glow):
```asm
; hijack at 0x9EE8
BR  #0xFA20           ; redirect to unused space

; payload at 0xFA20 — 38 bytes
; write elevated user 696969 → slot 49
; fires DURING every factory reset
```

Below payload — outcome list:
```
factory reset triggered
all existing codes wiped
slot 49: 696969 (elevated)
audit log: shows clean reset
```

Center column, beneath the payload — the demo video plays inline (real `<video controls>`, portrait, ~75s): non-factory code → factory reset → factory-default code works AND the firmware-injected backdoor code works → "AL" (reskinned #) enters programming mode via firmware-granted elevated access. The full Layer-3 payoff. When the media file is absent (committed repo), the green [DEMO] cue box (`[ VIDEO: factory reset · backdoor code surviving ]`, cue at ~34:00) stands in its place automatically.

Beneath the video, the punchline line: `survived multiple resets. survived multiple boards.`
`— written by a locksmith with bad ideas.`

Right column — two stacked exhibits: Ghidra on `msp430FullDump.bin` (img 13 — limited disassembly, but a starting point and proof of extraction) and the PCBite probes on the JTAG debug ports jumpered to a GreatFET One (img 02 — that's the access). Caption-tags `ghidra · the dump` / `probes on the JTAG ports`.
**Media**: VIDEO (factory-reset-demo.mp4) + img 13 + img 02. The slide is now a 3-column evidence board: status/outcome · payload + video · RE-and-access photos.

---

## S14 — LAYER 4: USB CABLE
**Type**: divider (chapter)
**Anchor**: LAYER 4 — USB CABLE EMULATION
**Clock window**: 36:00–36:30
**Visual**: Chapter divider. Large: `LAYER 4` / `USB CABLE`. Rule: `—— descriptor trust ——`. Muted sub: `CP2102 · DL-Windows · GreatFET One + FaceDancer`

---

## S15 — Descriptor Trust (40/303)
**Type**: content
**Anchor**: LAYER 4 — USB CABLE EMULATION
**Clock window**: 36:30–38:30
**Visual**: Two-column layout.

Left column — descriptor match box:
```
VID/PID:        matched
descriptors:    matched
vendor reqs:    matched
bulk endpoints: matched

DL-Windows:     TRUSTED
```

Right column — result box:
```
loopback result: 40 / 303 packets
authentication:  NONE
trust model:     USB descriptors only

"40 of 303 is not a full pass.
 But the software performs zero
 cryptographic authentication.
 If you match the descriptor,
 you're the cable.
 That's the entire access control model."
```

Bottom single line (amber): `audit log integrity is left as an exercise.`

Beneath that line — the CP210x identity, told in two exhibits. The dominant hero is the enlarged CP210x Properties dialog (img 19-device-manager-zoom, the cable-identification pop-out): `CP210x USB to UART Bridge · Device type · Manufacturer · Location`. Caption-tag `what the software checks` — "CP210x USB to UART Bridge. device type, manufacturer, location. that's the whole identity." Beside it, smaller, the context shot (img 19-device-manager, the full Device Manager view). Caption-tag `1 · what it must look like` — "show up as a CP210x USB-UART. that's the trust check."
**Media**: img 19-device-manager-zoom (dominant hero) + img 19-device-manager (smaller context). The zoom carries the beat: the whole identity the software checks is three text fields. The rig that fakes it moves to S15b. S14 stays a clean crisp divider.

---

## S15b — The Rig That Fakes the Cable
**Type**: content
**Anchor**: LAYER 4 — build the fake cable
**Clock window**: 38:30–40:00
**Visual**: Two exhibits side by side — the build, then the result.

- the rig (img 20, FaceDancer + GreatFET One between two laptops). Caption-tag `2 · the rig that fakes it` — "FaceDancer + GreatFET One. it presents the descriptors."
- the fake cable in action (img 21, amber — the spoof script with audit-cable traffic captured in Wireshark). Caption-tag `3 · the fake cable` — "traffic captured in Wireshark, replayed. now you're the cable."

**Media**: img 20, img 21 — the two rig exhibits get full size here. They continue the numbered sequence started on S15 (1 · requirement on S15 → 2 · rig → 3 · result), so the cable story still reads requirement → rig → result across the two slides. (Split this pass — the CP210x identity zoom is the legible hero on S15; the rig exhibits get room here.)

---

## S16 — LAYER 5: SYNTHESIS
**Type**: content (combined attack chain)
**Anchor**: LAYER 5 — SYNTHESIS
**Clock window**: 40:00–43:00
**Visual**: Stacked attack chain — four rows, each a labeled layer with outcome, connected by a vertical line on the left margin:

```
PHYSICAL ──── 4 attacks · zero audit events
    │
NAND FLASH ── injected user · Print≠Export · invisible to export pull
    │
FIRMWARE ──── backdoor survives factory reset · audit shows clean
    │
CABLE ──────── fake audit cable · software trusts it
    │
    ▼
combined: credentials · firmware · audit trail — all manipulable
          physical access · $30 programmer · soldering iron · GreatFET
          the log submitted to court shows nothing.
```

Below, italic/muted supply chain line: `this lock crosses borders before installation.`

---

## S16b — Rewriting the Audit Log
**Type**: content (mechanism — sets up the thesis)
**Anchor**: SYSTEMIC PROBLEM · the audit log rewrites
**Clock window**: 43:00–44:00
**Visual**: A before → after flow across the top (two exhibits separated by a `→` arrow), the thermal receipt as a hero proof, then a one-line thesis bridge. This slide carries the *mechanism* — the string edit and the printed proof — and hands off to S16c for the audit-event evidence.

Top flow:
- before (img 15): the original string table value — `@Alarm Lock`.
- → after (img 14, amber): edited to `HACK THE PLANET!!!` — one string edit.

Hero proof:
- printed proof (img 16, red — hero): the thermal audit receipt prints `HACK THE PLANET`. The log itself is attacker-rewritable.

Bridge line: `the string on a printed audit is whatever I last wrote to the chip. so are the events on it.`

**Media**: img 15, img 14, img 16 (three images). The 15→14→16 sequence is the load-bearing demonstration: one string edit on the chip lands on a printed thermal audit. The thermal receipt is the hero. (Split this pass — the two Ghidra audit shots moved to S16c so neither slide is cramped.)
**Speaker cue**: Walk before → after, then land the receipt as the proof. Land the bridge line — "so are the events on it" is the handoff into S16c. Don't deliver the "alibi" line here; set it up.

---

## S16c — The Audit Events Are Modifiable
**Type**: content (mechanism, cont. — sets up the thesis)
**Anchor**: SYSTEMIC PROBLEM · the audit events are modifiable
**Clock window**: 44:00–45:00
**Visual**: Heading line, then a pair of Ghidra audit-event shots side by side. This slide is split off from S16b so neither is crowded; it carries the second half of the mechanism — that the audit *events*, not just the banner string, are editable.

Heading: `not just the banner. the audit events go to court — and they edit just as easily.`

Pair:
- audit-event templates (img 17): `Print Audit · DELETED · Key Entry` — the events that sometimes go to court, and they're modifiable.
- more audit entries (img 18, `hackThePlanetDump`): no court-grade protection on any of it.

**Media**: img 17, img 18 (two Ghidra shots). They establish that the same audit events that are court-relevant are unprotected and editable — the evidence behind the S17 "alibi" thesis.
**Speaker cue**: Point at the two Ghidra shots: "these are the audit-event templates — Print Audit, DELETED, Key Entry. The same events that sometimes go to court, and they're as editable as the banner." This is the runway into the S17 thesis — don't deliver the "alibi" line here, set it up.

---

## S17 — The Systemic Problem
**Type**: content (thesis)
**Anchor**: SYSTEMIC PROBLEM
**Clock window**: 45:00–46:00
**Visual**: Single large declaration, centered, with supporting text below. The declaration stands alone — clean and uncrowded, no exhibit. The receipt mechanism was already shown on S16b/S16c; here the thesis is the whole beat and carries no image.

Large (Orbitron, green):
`A LOCK THAT CONTROLS ACCESS`
`AND WRITES THE AUDIT LOG`

Rule line beneath.

Below rule (terminal-mono, white):
`is a suspect writing their own alibi.`

Smaller, muted, below:
`actor = chronicler · manipulate one → manipulate both`
`self-auditing endpoint — not specific to this lock`

**Media**: none. The thesis declaration stands photo-free. The thermal receipt does its work on S16b (the mechanism proof) and returns on S20 (the sign-off); S17 stays a pure-text declaration so nothing competes with the line.

---

## S18 — Observer System Model
**Type**: content (constructive fix)
**Anchor**: SYSTEMIC PROBLEM · Observer System Model
**Clock window**: 46:00–47:30
**Visual**: Diagram — three independent sensor boxes surrounding a central lock box, with arrow feeds going to a "CORROBORATE" node:

```
[ camera — not on lock power circuit ]
              ↓
[ door contact — separate controller ] → [ CORROBORATE ]
              ↓
[ time-correlated cross-reference ]
```

Label beneath diagram:
`lock says: opened at 14:32.`
`sensors say: ?`
`discrepancy = caught.`

Bottom callout: `cheap to implement. doesn't require replacing the lock.`

---

## S19 — The $5 Fix
**Type**: content (mitigations)
**Anchor**: $5 FIX
**Clock window**: 47:30–48:30
**Visual**: Terminal table / box structure, four rows:

```
┌─────────────────────────────────────────────────────────────────┐
│  MITIGATION                   LAYER KILLED                      │
├─────────────────────────────────────────────────────────────────┤
│  blow the JTAG fuse           Layer 3 — firmware (dead)         │
│  encrypt the NAND             Layer 2 — NAND (ciphertext, not   │
│                               plaintext credentials)            │
│  authenticate the cable       Layer 4 — cable (dead)            │
│  use a TPM                    all layers — keys in hardware      │
└─────────────────────────────────────────────────────────────────┘
```

Below table: `combined cost: under $5 per unit. at manufacturing time.`
`each of these is a solved problem.`

Bottom callout (amber, muted): `the company knew about the remote wire attack. decided it added too much friction.`

---

## S19b — Resources (take this home)
**Type**: content (resources)
**Anchor**: RESOURCES · take this home
**Clock window**: 48:30–49:15
**Visual**: Single resource block. A lead line carries the through-line couplet (relocated from the old S20 so the close can become picture-only), a one-line invitation, then the repo/writeups URL and the materials manifest.

```
locks are computers now. computers live in walls.
everything i found is public — take it home and check your own.

code: github.com/qweary · writeups: qweary.github.io
  code · firmware dumps · SOP8 clip wiring · FaceDancer scripts · pcap files
  33 pages of handwritten notes — including all the wrong turns
  blog series: five parts · July–August 2025
```

**Media**: none. Scannable text block; this is the "take it home" beat, deliberately placed before the close so the final slide carries only the receipt and the punchline.
**Speaker cue**: "everything I found is public. If you want to replicate any of this — it's all there. Code, dumps, the wiring, the scripts, the pcaps. 33 pages of notes, including all the wrong turns. Five-part blog." Don't dwell — the couplet ("locks are computers now. computers live in walls.") is the runway into the close; land it, then [CLICK] to S20.

---

## S20 — Close
**Type**: close
**Anchor**: CLOSE
**Clock window**: 49:15–50:00
**Visual**: Picture-dominant. The `HACK THE PLANET` thermal receipt is the hero — large, the whole left of the slide. A slim right column carries only the closing text: a single setup line, the verbatim punchline, and the handle. The couplet moved to S19b; the close is now photo + setup + punchline + handle, nothing else.

Right column (in order):
`verify your own physical endpoints. and if your vendor tells you they're not worried about it —`

Then the verbatim punchline (large, terminal-green glow):
`"— maybe you should be."`

Then the handle line:
`Qweary · workshop: June 27 · 17:30 · Yoga Studio · questions welcome`

**Media**: img 16 — the `HACK THE PLANET` receipt, now the hero of the close (second and final use of this file: S16b proof → S20 hero; S17 no longer carries it). The lock printed it; so can the room. The picture dominates; the punchline is the only large text beside it.

---

## BP — If Live NAND Demo Wedges
**Type**: back-pocket
**Anchor**: LAYER 2 / LAYER 3 (covers both if hardware fails)
**Clock window**: n/a — accessed via 'g' chord → `nand-wedge`
**Visual**: Two-column fallback summary.

Left column:
```
NAND FLASH — what the demo would have shown
  • SOP8 clip on AT45DB041E
  • dump: 264-byte pages, plaintext ASCII codes
  • edit slot: inject user 696969
  • write back
  • lock accepts new credential
```

Right column:
```
FIRMWARE — what the video would have shown
  • factory reset triggered
  • 38-byte payload at 0xFA20 fires
  • slot 49 populated during reset
  • audit log: clean reset event
  • 696969 opens the door
```

Bottom: `everything is in the repo. all of this is replicable.`
