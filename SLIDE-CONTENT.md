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
**Anchor**: HOOK · ANE-001
**Clock window**: 0:45–4:00
**Visual**: Two-line reveal. Line 1 (large, terminal-green glow): `"I put them there."` Line 2 (smaller, muted): `"Then I asked how they secured the firmware."` Line 3 (amber, terminal-quote style): `"They said: We don't want to talk to you anymore."` No further text. Dark background, no bullets.
**Speaker cue**: [CLICK] after the 5-second hold. Riff from cue-lines in SPEAKING-NOTES.md Hook section. "So I spent a year figuring out how to hack them. This is that talk." — then [CLICK] to S3.

---

## S3 — Qweary
**Type**: content (minimal bio)
**Anchor**: WHO I AM
**Clock window**: 4:00–7:00
**Visual**: Three-line stack. `handle: qweary` / `locksmith · red team hobbyist` / `first conference talk.` Small repo/blog call-forward at bottom: `github.com/qweary/dead-bytes — 33pp handwritten notes, 5-part blog, everything`. No photo, no credential list.
**Speaker cue**: Say it plainly. Don't apologize for "first talk." The locksmith + CTF + "this" sentence arc is the entire bio. Read the room for optional audience calibration questions before advancing.

---

## S4 — The Relationship That Broke
**Type**: divider (chapter)
**Anchor**: THE RELATIONSHIP THAT BROKE
**Clock window**: 7:00–8:00
**Visual**: Chapter divider style. Large text: `THE RELATIONSHIP THAT BROKE`. Rule line beneath: `—— disclosure ——`. No body text. The chapter title is the beat.

---

## S5 — "We're not worried about it."
**Type**: content (ANE-003 beat)
**Anchor**: THE RELATIONSHIP THAT BROKE · ANE-003
**Clock window**: 8:00–12:00
**Visual**: Two blocks. Top block: short timeline in terminal-mono. `Early installs → physical disclosures → company responds. That's the good version.` / `"trusted by military" — partly because of me.` Bottom block: terminal-quote box (bordered, amber), single line: `"we're not worried about it"` — third-party relays, no attribution. Below the quote box, muted text: `Subsequent disclosures: unacknowledged.`
**Speaker cue**: The quote box is the emotional anchor. Pause after it. Then: "So that was that."

---

## S6 — What This Lock Is
**Type**: content (anatomy)
**Anchor**: WHAT THIS LOCK IS
**Clock window**: 12:00–15:00
**Visual**: Two-column layout. Left: photo placeholder — `[ T2/T3 photo ]` — or diagram label block if no photo. Right: component list in terminal-mono, minimal:
```
MCU:   MSP430F2418
NAND:  Adesto AT45DB041E
JTAG:  exposed — fuse never blown
USB:   CP2102 audit cable (DL-Windows)
```
Below, a one-line callout: `audit trail = legal evidence in some deployments.`

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
**Type**: content (ANE-002)
**Anchor**: LAYER 1 — PHYSICAL · ANE-002
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
**Visual**: Chapter divider. Large: `LAYER 2` / `NAND FLASH`. Rule: `—— Adesto AT45DB041E ——`. Muted sub: `264-byte pages · 50 users · plaintext codes`

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

---

## S12 — LAYER 3: FIRMWARE
**Type**: divider (chapter)
**Anchor**: LAYER 3 — FIRMWARE
**Clock window**: 28:00–28:30
**Visual**: Chapter divider. Large: `LAYER 3` / `FIRMWARE`. Rule: `—— JTAG fuse: never blown ——`. Muted sub: `$30 programmer · soldering iron · unreasonable stubbornness`

---

## S13 — 38-Byte Payload [DEMO]
**Type**: demo anchor (ANE-005)
**Anchor**: LAYER 3 — FIRMWARE · ANE-005
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

Bottom — [DEMO] callout box (green border, large):
`[ VIDEO: factory reset · backdoor code surviving ]`

Beneath video cue, the punchline line: `survived multiple resets. survived multiple boards.`
`— written by a locksmith with bad ideas.`

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
**Clock window**: 36:30–40:00
**Visual**: Two-column layout.

Left column — descriptor match box:
```
VID/PID:     matched
descriptors: matched
vendor reqs: matched
bulk endpts: matched

DL-Windows:  TRUSTED
```

Right column — result box:
```
loopback result: 40 / 303 packets
authentication:  NONE
trust model:     USB descriptors only

"If you match the descriptor,
 you're the cable."
```

Bottom single line (amber): `audit log integrity is left as an exercise.`

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

## S17 — The Systemic Problem
**Type**: content (thesis)
**Anchor**: SYSTEMIC PROBLEM
**Clock window**: 43:00–44:30
**Visual**: Single large declaration, centered, with supporting text below:

Large (Orbitron, green):
`A LOCK THAT CONTROLS ACCESS`
`AND WRITES THE AUDIT LOG`

Rule line beneath.

Below rule (terminal-mono, white):
`is a suspect writing their own alibi.`

Smaller, muted, below:
`actor = chronicler · manipulate one → manipulate both`
`self-auditing endpoint — not specific to this lock`

---

## S18 — Observer System Model
**Type**: content (constructive fix)
**Anchor**: SYSTEMIC PROBLEM · Observer System Model
**Clock window**: 44:30–46:00
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
**Clock window**: 46:00–48:00
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

## S20 — Close
**Type**: close
**Anchor**: CLOSE
**Clock window**: 48:00–50:00
**Visual**: Two sections.

Top section — resources:
```
github.com/qweary/dead-bytes
  code · firmware dumps · SOP8 wiring · FaceDancer scripts · pcaps
  33 pages of handwritten notes (including the wrong turns)
  blog: five parts, July–August 2025
```

Below rule, the closing argument in descending size:
`locks are computers now.`
`computers live in walls.`

Then the verbatim punchline (large, terminal-green glow):
`"— maybe you should be."`

Bottom: `Qweary · workshop: [TIME/LOCATION]`

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

---

## Editorial Flag

### attribution_decisions

No real names or handles applied to any individual in the slide content beyond the operator's own handle (Qweary). Alarm Lock / Trilogy referenced by company name, consistent with the operator's public blog series and GitHub repo.

ANE-002 (service member story): "service member" — role only, no identifying detail. "A different locksmith" — unnamed, unidentifiable. Both match the locked operator-decide dispositions from SPEAKING-NOTES.md.

ANE-003 ("we're not worried about it"): rendered as a terminal-style quote block on S5 with "third-party relays" as attribution — no role description, consistent with the ANE-003 locked flag (LEAVE GENERIC). No name, no role label beyond "third-party."

ANE-005 (38-byte payload): all technical specifics (function addresses 0x9ECA, 0x9EE8, 0xFA20; opcode BR; slot 49; code 696969) are from the operator's own public repo. No external attribution required.

### scope_inclusions_and_omissions

**ANE-001 (Meta Reveal)** — CONF-SLIDES-REVEALJS: must-include. Present on S2. The reversal ("I recommended this lock") is the entire structural hook of S2 and drives the S20 closing callback ("verify your own physical endpoints" / "maybe you should be").

**ANE-002 (Service Member Story)** — CONF-SLIDES-REVEALJS: preferred. Present on S9. Rendered as a terminal-style story block beneath the four-attack list. Carries the "locksmith lens finds what a digital researcher wouldn't" argument without stating it explicitly.

**ANE-003 ("We're Not Worried About It")** — CONF-SLIDES-REVEALJS: preferred. Present on S5 as a bordered terminal quote box. Attribution per locked flag: "third-party relays." No role description per ANE-003 disposition.

**ANE-004 (Career Path)** — CONF-SLIDES-REVEALJS: not a flagged eligible anecdote for slides (per ANECDOTE-MANIFEST registration). Present on S3 as minimal compressed bio only: `handle: qweary / locksmith · red team hobbyist / first conference talk.` Consistent with ANE-004 locked flag (KEEP COMPRESSED). Not expanded on any slide.

**ANE-005 (38-Byte Payload)** — CONF-SLIDES-REVEALJS: must-include. Present on S13 as the demo anchor slide. Payload assembly block, JTAG status, outcome list, [DEMO] callout, and video cue all present. Factory-reset video cue rendered explicitly on-screen per brief requirement.

**No must-include omissions.**

Workshop content correctly separated to the workshop deliverable; no workshop procedural detail appears in these slides. Full FaceDancer packet trace breakdown omitted from slides (repo reference only, consistent with SPEAKING-NOTES.md treatment).

### anecdote_flags

No new operator-decide flags generated for slides. All three locked flags from SPEAKING-NOTES.md baked in:
- ANE-004 (career path): KEEP COMPRESSED — S3 bio is three lines, no expansion.
- ANE-003 ("we're not worried about it"): LEAVE GENERIC — S5 quote box uses "third-party relays," no role description.
- ANE-002 (different locksmith): FINE AS WRITTEN — S9 uses "a different locksmith," unnamed, unidentifiable.

### prose_tic_audit

**Slide titles** measured against operator diction (declarative, no superlatives, no passive voice, no "Introduction to..." framing):

| Slide | Title | Assessment |
|---|---|---|
| S1 | Dead Bytes Tell No Lies | Declarative — PASS |
| S2 | "I recommended this lock." | Quote-form, direct — PASS |
| S3 | Qweary | Handle only, no framing — PASS |
| S4 | The Relationship That Broke | Declarative, active past — PASS |
| S5 | "We're not worried about it." | Verbatim quote — PASS |
| S6 | What This Lock Is | Declarative — PASS |
| S7 | Five Layers | Minimal noun — PASS |
| S8 | LAYER 1: PHYSICAL | Layer label — PASS |
| S9 | Four Attacks, No Trace | Declarative — PASS |
| S10 | LAYER 2: NAND FLASH | Layer label — PASS |
| S11 | Page Layout + Stealth Window | Declarative noun pair — PASS |
| S12 | LAYER 3: FIRMWARE | Layer label — PASS |
| S13 | 38-Byte Payload [DEMO] | Declarative + demo callout — PASS |
| S14 | LAYER 4: USB CABLE | Layer label — PASS |
| S15 | Descriptor Trust (40/303) | Declarative + data — PASS |
| S16 | LAYER 5: SYNTHESIS | Layer label — PASS |
| S17 | The Systemic Problem | Declarative — PASS |
| S18 | Observer System Model | Named concept — PASS |
| S19 | The $5 Fix | Declarative, cost-anchored — PASS |
| S20 | Close | Section label — PASS |
| BP | If Live NAND Demo Wedges | Conditional declarative — PASS |

No superlatives detected. No "Introduction to" framing. No passive voice in titles. All titles match declarative or question-form operator diction.

**Prohibited tics scan** (visual field / speaker cue text):
- "This isn't X — it's Y" pivot rhetoric: not detected.
- Zombie-noun softeners: not detected. Visual fields are verb-active or noun-precise.
- Credential-first framing: absent. S3 bio leads with role and decision, not degrees.
- Vendor superlatives: absent.
- Summary-as-close: absent. S20 closes on the punchline line, not a recap list.

Status: PASS.

### operator_decide_flags_status

All three locked flags from SPEAKING-NOTES.md confirmed baked in across all slides:

1. **ANE-004 (career path — KEEP COMPRESSED)**: S3 is three lines. No expansion anywhere in the deck.
2. **ANE-003 ("we're not worried about it" — LEAVE GENERIC)**: S5 quote box attributes to "third-party relays." No role description. Flag confirmed closed.
3. **ANE-002 (different locksmith — FINE AS WRITTEN)**: S9 story block uses "a different locksmith." No name, no further identifying detail. Flag confirmed closed.
