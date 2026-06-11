# Dead Bytes Tell No Lies: Hands-On NAND Flash Decoding for Access Control Locks
## ToorCamp 2026 — Speaking Notes
### Prime Dome | 45–50 min | Qweary

---

> **How to use these notes:**
> Cue-lines only — these are anchors, not a script. Each bullet is a beat you riff from.
> `[PAUSE]` = breath and let it land. `[CLICK]` = advance slide. `[VIDEO: ...]` = roll the video.
> `[HOLD LOCK UP]` = physical prop moment. `[AUDIENCE]` = genuine question, wait for answers.
> Timing estimates assume conversational hacker-camp pace with Q&A overlap at the end.
> If you're running long, the "Five Layers Fast" section can compress — cut the JTAG depth first.

---

## Hook [0:00–4:00]

[HOLD LOCK UP]

- Hold it up. Let people see it.
- Don't say anything yet. Just hold it.

[PAUSE — 5 seconds]

- "This is an Alarm Lock T2/T3."
- "It's in pharmacies. Government buildings. Banks."
- "Military installations."

[PAUSE]

- "I know this because I put them there."

[PAUSE — let that land]

- "I'm a locksmith. I've installed hundreds of these."
- "Other locksmiths asked me what lock the base I work at was running."
- "I said: this one. Fast disclosure response, cooperative company, military-grade."
- "Word spread. The company advertised themselves as 'trusted by military installations.'"
- "That's partly because of me."

[PAUSE]

- "Then I asked them how they secured the firmware and user codes."
- "They said: 'We don't want to talk to you anymore.'"

[PAUSE — this is the pivot]

[CLICK — "Dead Bytes Tell No Lies" title slide]

- "So I spent a year figuring out how to hack them."
- "This is that talk."

---

## Who I Am [4:00–7:00]

[CLICK — minimal bio slide or keep it visual, don't dwell]

- "Qweary. Locksmith by trade. Red team hobbyist by COVID-era life choices."
- Brief: had degrees, didn't use them, learned what red teaming was during the pandemic
- Decided the move was: become the best locksmith possible AND teach myself security on the side
- CTFs for a couple years. Then this.
- "Senior physical security engineer. I fix locks during the day and red team at night."
- [PAUSE] — lead with the asymmetry, say it plainly; the day-job/night-job split is the whole credential
- "I've been sitting on this research for over a year. Five-part blog series. Phrack submission — they passed. GitHub repo with everything: code, dumps, 33 pages of handwritten notes."
- "Today I want to walk you through why the locksmith angle matters — not just for this research, but for what it means when physical and digital security share the same attack surface."

[AUDIENCE question — optional, read the room]
- "How many of you have worked on physical access control professionally?"
- "Hardware hacking background? JTAG, NAND, flash programmers?"
- "Just here because it sounded interesting?"
- Use the read to calibrate depth in the middle sections

---

## The Relationship That Broke [7:00–12:00]

[CLICK — background context slide; photo of a T2/T3 installed if available]

- The base I work at was an early adopter
- Through sheer volume of installs and repairs — I had handled a lot of these
- Found physical vulnerabilities first. Reported them.
- Company responded fast, fixed them. That's rare. That's the good version of this story.
- "I thought we had a relationship."

[PAUSE]

- Other locksmiths at tradeshows, at classes: "what are you running?"
- "Alarm Lock T2/T3. They respond to disclosures."
- Lock started showing up everywhere — pharmacies, more government buildings, banks
- The company leaned into the "trusted by military" marketing

[CLICK]

- "Then I asked a different question."
- "Not 'what happens when someone gets in through the door.' I asked: what happens when someone gets in through the firmware? How do you secure user codes? What's on the chip?"
- "They said they didn't want to talk to me anymore."
- Subsequent disclosures: unacknowledged
- Third-party relays: "we're not worried about it"

[PAUSE — this is the emotional anchor]

- [On-slide, optional colour: they also sell a wireless lock whose security password is "exactly 6 characters in length." A fixed floor, not a minimum. Gesture to it only if the room is tracking the posture beat — don't break this pause to narrate the photo.]
- "So that was that."
- "The lock I recommended was now in critical infrastructure. The company wouldn't talk to me. And I had a year of locksmith context, some CTF practice, and a really bad idea."
- "Let's talk about what I found."

---

## What This Lock Is [12:00–15:00]

[CLICK — lock anatomy slide; board + NAND macro + MCU macro on the left, component list on the right]

- The photos are the same three parts as the list — board, NAND, MCU. The picture makes the part numbers physical; point at the board when you say "exposed JTAG."
- Physical rundown: standalone electronic lock, keypad, RFID option, audit trail output
- Marketed as high-security, used where you care about access logging
- The audit trail is load-bearing — it gets used as legal evidence in some deployments
- Internal architecture: MSP430F2418 microcontroller, Adesto AT45DB041E NAND flash chip
- JTAG interface: exposed on the board, fuse never blown
- USB audit cable: proprietary, CP2102 chip, used to pull logs into DL-Windows software

[PAUSE]

- "The audit cable is how you know who entered the building and when."
- "This becomes important later."

---

## Layer 1 — Physical [15:00–21:00]

[CLICK — Layer 1 slide]

- "I'm a locksmith. We start with the door."
- "Before any chip reading, before any firmware, there are four physical attacks — all of them leave little or no trace, none of them generate audit events."

[CLICK — attack list, not deep-dived]

**Attack 1: Acoustic keylogging**
- Speaker voltage leakage — each key produces a distinct voltage signature
- Capture with a scope. Decode the code. No contact with the lock.
- "I wasn't planning to find this. It was just there."

**Attack 2: Tailpiece deflection**
- Improperly installed unit + stiff wire through the gap
- Deflect the tailpiece, retract the latch, door opens
- "This is pure locksmith intuition. If you've ever shimmed a lock you know the geometry."

**Attack 3: Factory reset via cold**
- Freezing battery leads with inverted compressed air can
- Induces a voltage drop that triggers factory reset behavior
- "No damage. No trace. Cheap."

**Attack 4: Remote release wire bridging** — this is the one with a story

[PAUSE — set up the story]

- "Let me tell you about a service member who could punch a door open."

[PAUSE]

- The T2/T3 has two wires — the remote release wires — that normally sit open
- A proprietary dongle closes them when it receives a remote signal
- Correct installation: route them through the door
- What a different locksmith did: cut them short and cap them inside the frame

[PAUSE]

- "One day I got a call. Service member said they'd punch the door and the lock would unlock."
- "Everyone laughed. I didn't laugh."
- "I asked: 'Did you recently do work on that door? Is it metal? Were the wires cut?'"
- "Yes, yes, yes."
- "Cut wires, inside a metal frame, jostling on impact — intermittent contact. Every punch closed the circuit. Lock read it as a remote release signal."

[PAUSE — let the image settle]

- "So I thought: what if you did that on purpose?"
- "External comm port on the T2/T3. Drill bit through it. Bridge the wires."
- "Door opens. Comm port still functional — you can still audit it."
- "I reported this."
- "Company said fixing it would add too much friction for customers using remotes."

[PAUSE]

- "That's four physical attacks, no audit events, no trace, no $5 chip."
- "And I hadn't touched the firmware yet."

[CLICK]

---

## Layer 2 — NAND Flash [21:00–28:00]

[CLICK — Layer 2 slide; photo of the NAND chip or SOP8 clip if available]

- "Now we go digital."
- "The Adesto AT45DB041E is the NAND flash chip that stores everything: user codes, permission flags, audit data."

**The page layout**
- 264-byte pages. 50 users per page.
- Took a while to reverse engineer — the layout isn't documented
- "I dumped the chip, I stared at hex for a long time, I started seeing patterns."

[CLICK — hex dump slide if available; show the structure]

- Codes stored as ASCII nibbles, plain decimal
- One quirk: "0" is substituted with "B" — TI assembly conflict, the microcontroller's representation bleeds into the storage format
- Permission flags: F1 for Master, E1 for Elevated, C1 for Supervisor

**The lazy write**
- MSP430 only commits RAM to NAND on battery removal
- "Which means: between battery pull and storage, there's a window."
- Practically: you can read the chip, modify user codes, write them back, reinstall — and the lock has a new user with your credentials

**What this looks like in practice**
- $30 programmer, SOP8 clip, 15 minutes
- Extract chip. Read. Edit. Write. Replace.
- "You've just given yourself master access to a lock in a pharmacy."
- [On-slide photos: the $30 dump rig (T48 + SOP8 clip) is the whole read. Then the practical fallout — a 9-digit code where the field max is 6 (the limit is software-only), and DL-Windows crashing when you feed it a code it never expected. Point at the crash: "the auditor chokes on its own injected data."]

[PAUSE]

- The stealth detail: injected codes appear in "Print Users" but NOT in "Export Users"
- "That's a forensic evasion window. Print is on-screen; Export goes to a file. If investigators pull the export, they don't see your user."
- "I don't know if this was intentional. I don't think it matters."

[CLICK]

---

## Layer 3 — Firmware [28:00–36:00]

[CLICK — Layer 3 slide]

- "This is the part where things got embarrassing. In a good way."

[PAUSE]

- "I'm not a firmware engineer. I'm a locksmith."
- "I bricked a lot of boards."
- "I filled a notebook with bad hypotheses."
- "I eventually taught myself enough TI MSP430 assembly to write a 38-byte payload."
- "Thirty-eight bytes. That's what I needed."
- "$30 programmer. Soldering iron. Unreasonable stubbornness."
- [The divider hero is the soldering disaster — bridged pins, a wire pulled clean out of the board. "When failure is not so pretty." Let the photo carry the "I bricked a lot of boards" line; you don't have to enumerate.]

[PAUSE — this is the self-deprecating beat that lands]

**Why the JTAG was accessible**
- JTAG fuse: never blown
- On most commercial devices this is a production oversight — you blow it before shipping
- "They didn't."
- Full read/write access to firmware through the JTAG interface

**What I found in the firmware**
- SetMasterCode() at 0x9ECA — the function that writes master credentials during factory reset
- "Factory reset is supposed to wipe all codes and set you back to a clean state."
- Traced the execution flow around it

**The payload**
- Hijacked execution at 0x9EE8 using a BR opcode
- Redirect to unused space at 0xFA20
- 38-byte payload: write elevated user code 696969 to slot 49 during every factory reset
- "Not before reset. Not after. During. The reset triggers the write."

[PAUSE]

- "Which means: I factory reset the lock. All existing codes are wiped. The lock appears clean."
- "Slot 49 has a new code. Code is 696969. User appears in the Print list, not in the Export list."
- "The lock thinks it reset. The audit log shows a reset event. A ghost user with master privileges is now in the lock."

[VIDEO — plays inline on this slide (center column, beneath the payload). Real `<video controls>`; hit play, or roll your own copy manually. If the media is absent the green [DEMO] cue box stands in its place — describe it instead.]

- "Watch this."
- [Hit play — let it run, narrate lightly or stay quiet depending on audio. The video walks: non-factory code → factory reset → factory-default code works AND 696969 works → press "AL" (reskinned #) to enter programming mode via firmware-granted elevated access.]
- "Factory reset. Enters 696969. Opens."
- "Survived multiple resets. Multiple boards."
- [Right column has the receipts: Ghidra on the dump (proof of extraction) and the PCBite probes on the JTAG ports jumpered to a GreatFET — "that's the access." Gesture to them while the video plays or right after.]

[PAUSE after video]

- "That's 38 bytes of TI assembly. Written by a locksmith. With a $30 programmer and bad ideas."

[CLICK]

---

## Layer 4 — USB Cable Emulation [36:00–38:30]

[CLICK — Layer 4 divider, then S15 cable-trust slide]

- "The audit cable is the thing that makes this lock worth deploying in legal-evidence contexts."
- "It's how you pull the audit log. It's proprietary — Alarm Lock's DL-Windows software, their cable, their format."
- "I built a fake one."

**The cable**
- Silicon Labs CP2102 USB-to-UART bridge
- Specific VID/PID, device descriptors, vendor requests, bulk endpoints
- DL-Windows recognizes devices by USB descriptor match — if the descriptors match, it trusts the device

[PAUSE]

- "40 of 303 is not a full pass. I'm not going to tell you I broke the cable protocol entirely."
- "But here's what that result means: the software performs zero cryptographic authentication."
- "Trust is entirely USB descriptors."
- "If you match the descriptor, you're the cable. That's the entire access control model."

[PAUSE]

- "A device that costs less than the lock itself can present itself as the audit cable."
- "What that means for audit log integrity is left as an exercise."
- [On-slide, the CP210x identity is the hero: the enlarged Properties dialog. Point at it.] "This is the whole identity the software checks — device type, manufacturer, location. Three text fields. Show up as a CP210x USB-UART and you've passed the trust check."

[CLICK — S15b, the rig]

---

## Layer 4 (cont.) — The Rig That Fakes the Cable [38:30–40:00]

[CLICK — S15b rig slide]

**The emulator**
- GreatFET One + FaceDancer library
- Match the VID/PID and device descriptors exactly
- DL-Windows recognizes it as the audit cable
- Loopback test: ~40 of 303 packets pass

- [Point at the rig.] "Here's the rig. FaceDancer + GreatFET One between two laptops. It presents the descriptors DL-Windows wants to see."
- [Point at the second shot.] "And here's the traffic captured in Wireshark, replayed by the script. That's the cable answering. Now you're the cable."

[PAUSE]

[CLICK]

---

## Layer 5 — Audit Trail Subversion [40:00–43:00]

[CLICK — Layer 5 slide — the synthesis]

- "Let me put this together."
- "You have a lock deployed in a hospital. Or a court building. Or a bank."
- "The audit trail from this lock has been submitted as legal evidence in access control disputes."

[PAUSE]

- "Here's what you can do with physical access and modest tools:"
- NAND flash: inject a user. Appears in Print, not in Export. Invisible to standard forensic pull.
- Firmware: plant a backdoor code that survives factory reset. Lock appears clean after reset.
- Cable emulation: present a fake audit cable. Software trusts it. Log data is now interceptable.
- Physical: four attacks, no audit events. The log doesn't know you were there.

[PAUSE — let the synthesis settle]

- "Combined: a lock whose credentials, firmware, and audit trail can all be manipulated."
- "With physical access. With a $30 programmer. A soldering iron. A GreatFET."
- "And the log that gets submitted to court shows nothing."

[PAUSE]

- "This lock was shipped internationally before installation. It crosses borders before it goes in a door."
- "If the firmware is compromised in the supply chain, the JTAG fuse is not blown, and you can clone credentials from a chip in the trash — what's the threat model for the supply chain?"
- "I don't have a complete answer. But I think the question is worth asking."

[CLICK]

---

## Rewriting the Audit Log [43:00–44:00]

[CLICK — S16b audit-rewrite slide: before → after, then the thermal receipt as the hero proof]

- "Let me show you the audit log isn't just incomplete. It's writable."
- [Point at the flow, left to right.] "Here's the original string the lock stores: '@Alarm Lock.'"
- "I changed one string on the chip to 'HACK THE PLANET.'"
- "And here's the thermal audit receipt the lock printed." [the red hero exhibit]

[PAUSE — let the receipt land]

- "The banner is whatever I last wrote to the chip. So are the events on it."

[CLICK — S16c]

---

## The Audit Events Are Modifiable [44:00–45:00]

[CLICK — S16c: the two Ghidra audit-event shots]

- [Point at the two Ghidra shots.] "It's not just the banner. These are the audit-event templates — Print Audit, DELETED, Key Entry. The same events that sometimes go to court."
- "There's no court-grade protection on any of it. They edit just as easily as the banner did."

[PAUSE — this is the runway into the thesis; don't deliver the 'alibi' line yet]

[CLICK]

---

## The Systemic Problem [45:00–46:00]

[CLICK — self-auditing endpoint slide; declaration stands alone, no image — the receipt already did its work on S16b/S16c]

- "I want to step back from the specific lock."
- "Because this is the argument I actually want to make."

[PAUSE]

- "A lock that controls access AND writes the audit log is a suspect writing their own alibi."
- "That's not a metaphor. That's the architecture."
- "The same device that decides who gets in is the same device that records who got in."
- "If you can manipulate one, you can manipulate both."

[PAUSE]

- "We call this a self-auditing endpoint. And it's everywhere — not just in access control locks."
- "Any endpoint that is both the actor and the chronicler of its own actions has this problem."

---

## The Observer System Model [46:00–47:30]

[CLICK — Observer System Model slide]

- "The fix doesn't have to be expensive."
- "Independent sensors that verify what the lock claims."
- "Camera that's not on the lock's power circuit. Door contact sensor on a separate controller. Time-correlated cross-reference."
- "The lock says it was opened at 14:32. Does the sensor agree? Does the camera agree?"
- "If the lock is lying, the independent sensors catch the discrepancy."
- "That's the Observer System Model. Cheap to implement. Doesn't require replacing the lock."

[PAUSE]

---

## The $5 Fix [47:30–48:30]

[CLICK — mitigations slide]

- "While I have your attention: here are the mitigations that would have stopped every layer of this chain."

- **Blow the JTAG fuse.** Firmware is now read-only. Layer 3 dead.
- **Encrypt the NAND.** Chip reading gives you ciphertext, not plaintext credentials. Layer 2 dead.
- **Authenticate the cable.** Challenge-response handshake between the lock and the audit cable. Layer 4 dead.
- **Use a TPM.** Store keys in hardware, not in a chip accessible by a $30 programmer.

[PAUSE]

- "Combined cost: under $5 per unit. At manufacturing time."
- "Each of these is a solved problem. Off-the-shelf solutions exist."
- "This isn't an exotic attack chain. This is what happens when a manufacturer decides security is friction."

[PAUSE]

- "And I know — because I was told — that the company knew the remote wire bridging attack was possible, and decided fixing it would add too much friction for customers."
- "So."

[CLICK]

---

## Resources — Take This Home [48:30–49:15]

[CLICK — S19b resources slide]

- "Everything I found is public."
- GitHub repo: code, firmware dumps, SOP8 clip wiring, FaceDancer scripts, pcap files
- 33 pages of handwritten notes — including all the wrong turns
- Five-part blog series, July–August 2025
- "If you want to replicate any of this: it's all there. Take it home and check your own."

[PAUSE]

- "One thing I want to leave you with."
- "The locksmith and the digital researcher were looking at the same lock."
- "The locksmith saw wires that shouldn't be cut. The locksmith knew what a factory reset meant mechanically. The locksmith knew the volume of these units in the field — because the locksmith installed them."
- "The digital researcher might have found the JTAG. Might have found the NAND layout. Might not have thought to ask about the remote release wires."
- "The intersection of physical and digital security isn't coming. It's here. It's been here."
- "Locks are computers now. Computers live in walls." — this couplet lives on the S19b slide; land it as the runway into the close, then [CLICK] to S20.

[PAUSE]

[CLICK — S20]

---

## Close [49:15–50:00]

[CLICK — S20: picture-dominant close. The HACK THE PLANET receipt is the hero; a slim right column carries only the setup line, the punchline, and the handle.]

- The receipt the lock printed is the hero of this slide now — large, the whole left. "The lock printed that. So can you. It's in the repo." Let the picture carry the weight; the only big text beside it is the punchline.

[PAUSE]

- "Verify your own physical endpoints. And if your vendor tells you they're not worried about it — "

[PAUSE]

- "— maybe you should be."

[PAUSE — hold it]

- "I'm Qweary. Workshop is June 27 at 17:30 in the Yoga Studio if you want to get hands-on with a flash programmer."
- "Questions? I'll be here after."

---

## Q&A Seeds [if it goes cold] [50:00+]

Use these if the room goes quiet after first question:

1. "Someone is going to ask me: did I notify the company? Yes. Multiple times. Through a third party. Their position is documented."

2. "Someone is going to ask: can this be patched? The physical attacks — some yes, some no. The JTAG? Blow the fuse. The NAND? Encrypt it. These aren't hard problems. They're priority problems."

3. "Here's one I find interesting: why did the forensic evasion window exist? Print vs. Export divergence. I genuinely don't know if it was intentional. Would be curious if anyone here has theories."

4. "The supply chain question is the one I keep coming back to. This lock crosses international waters before installation. If you're interested in that thread — the repo has the full attack chain, and the question I'm sitting with is: at what point in the chain does this become actionable for a nation-state?"

---

## Demo Timing Notes

**If running live NAND read/write on stage:**
- Set up before the talk; don't let the setup eat into Layer 2 time
- SOP8 clip on the chip: confirm connection before audience sees it
- Terminal output: font size up, dark terminal on projector
- Have backup video ready — the ToorCamp tent environment can be unforgiving to live hardware

**Video: factory reset + backdoor code surviving**
- Now embedded inline on the Layer 3 slide (center column, beneath the payload) — real `<video controls>`. Hit play on the slide, or roll your own copy manually; either works.
- Cue around the ~34:00 mark inside Layer 3 (after "the lock thinks it reset")
- Narrate over it or let it run silent — your call; the video is self-explanatory if the setup is clean
- The clip walks: non-factory code → factory reset → factory-default works AND 696969 works → "AL" (reskinned #) enters programming mode via firmware-granted elevated access
- If the media file is absent (e.g. the committed repo, before rehydrate): the green [DEMO] cue box stands in its place automatically — describe it verbally, hit the punchline ("Survived every reset. Survived multiple boards."), move on — the story still lands

**Physical lock on stage:**
- Hold it up at the Hook, keep it on the table in view throughout
- Pick it up again at Layer 1 when you describe tailpiece deflection — the physical object anchors the abstract

---

## Timing Summary

| Section | Clock | Notes |
|---|---|---|
| Hook (meta reveal) | 0:00–4:00 | Do not rush the pauses |
| Who I Am | 4:00–7:00 | Brief; don't over-dwell on bio |
| The Relationship That Broke | 7:00–12:00 | Emotional anchor; "we're not worried about it" |
| What This Lock Is | 12:00–15:00 | Technical scaffold; set up the five layers |
| Layer 1 — Physical | 15:00–21:00 | Service member story is here; 6 min is right |
| Layer 2 — NAND Flash | 21:00–28:00 | 7 min; page layout + stealth window |
| Layer 3 — Firmware | 28:00–36:00 | 8 min; factory reset video at ~34:00 |
| Layer 4 — USB Cable (S15) | 36:00–38:30 | divider + descriptor-trust beat; 40/303, "you're the cable"; CP210x identity zoom is the hero |
| Layer 4 (cont.) — The Rig (S15b) | 38:30–40:00 | the rig that fakes it; FaceDancer + GreatFET One, Wireshark replay; keep it crisp |
| Layer 5 — Synthesis | 40:00–43:00 | 3 min; let the combined picture hit |
| Rewriting the Audit Log (S16b) | 43:00–44:00 | 1 min; before→after→thermal receipt hero; the banner is rewritable |
| The Audit Events Are Modifiable (S16c) | 44:00–45:00 | 1 min; two Ghidra audit shots; runway into the thesis |
| Systemic Problem | 45:00–46:00 | The argument; the "alibi" thesis lands here, clean |
| Observer System Model | 46:00–47:30 | The cheap fix; independent sensors corroborate |
| $5 Fix | 47:30–48:30 | Mitigations; don't rush the list |
| Resources — Take This Home (S19b) | 48:30–49:15 | Repo, notes, blog; couplet is the runway into the close |
| Close (S20) | 49:15–50:00 | Picture-dominant: receipt hero + the punchline, then done |
| Q&A | 50:00+ | Use seeds if needed |
