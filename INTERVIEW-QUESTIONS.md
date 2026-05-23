# Interview Questions — ToorCamp 2026
## Smyth Ghostwriter Engagement

I've read the ToorCamp Talk and Workshop submission screenshots, the T2-T3 Lock Exploitation Research repo (README + writeup), and three blog posts from qweary.github.io. I have a solid picture of the technical research — the full Alarm Lock T2/T3 attack chain is well-documented — and a strong voice baseline from the blog corpus. These questions are filling the gaps I can't infer from grounding: the stories, the logistics, and the framing choices that will determine the structure of both the talk artifacts and the workshop materials.

---

## Talk Questions

**1. Who recommended this lock?**
The research makes clear the T2/T3 is marketed as a higher-security product deployed in banks, schools, and government buildings — but the talk title says "the Recommended Lock" (capital R, capital L, definite article). That framing implies a specific recommendation source. Is it LockPickingLawyer? A YouTube channel? A physical security trade publication? A government procurement spec? A locksmith industry certification? The recommendation source is the load-bearing word in the title — knowing who recommended it tells the audience why they should care that a locksmith hacked it.

**2. How did your locksmith work lead you here?**
The repo documents what you found and how you exploited it, but not how you found the target in the first place. Did you encounter the T2/T3 on a job — installing it, servicing it, cutting keys for a building using it? Did a client ask your professional opinion about it? Did you notice something as a locksmith about how it was installed that tipped you off to a physical attack vector before you ever opened it up? The locksmith-to-researcher path is the distinctive hook of this talk; the repo doesn't have that story.

**3. What did the locksmith lens see that a digital researcher alone would have missed?**
You identified physical attack vectors — tailpiece latch deflection, thermal battery interruption via compressed air, remote unlock wire bridging. Some of those require knowing how locks are actually installed and used in the field. Did your professional experience give you physical intuition that shaped the research direction? Is there a specific observation — something you saw on a job site, or knew from locksmith training — that a firmware-first researcher wouldn't have noticed?

**4. What does the demo look like on stage?**
The research produced a complete attack chain: read NAND flash, dump credentials, modify firmware via JTAG, inject a backdoor code, manipulate audit logs. Which parts of this are live on stage, which are recorded, and which are just described? Will you have the physical lock with you? If there's a live component, what's the single most compelling moment you're building toward — the credential dump, the backdoor surviving factory reset, the audit log showing nothing happened?

**5. What's the payoff for the audience?**
After the talk, what should a ToorCamp attendee think or do differently? Is the conclusion specific to this lock (don't trust T2/T3), about a class of electronic locks (self-auditing systems have a structural problem), or about something bigger (physical and digital security need to be reviewed together, not separately)? The research identifies a "self-auditing problem" — the lock controls access AND records its own behavior — as the design flaw that makes the individual vulnerabilities systemic. Is that the thesis, or is there a sharper version?

**6. Talk slot: how long and what's the room like?**
Standard ToorCamp talks run 25–45 minutes depending on the track; I want to pace the speaking notes to your actual slot. Also: projector, outdoor screen, or tent setup? Will you have a table for hardware, and does the venue work for a live demo involving a lock, a laptop, and a JTAG debugger? Any known constraints I should factor into how the demo and slide structure are sequenced?

**7. Who's in the room, and what do they already know?**
ToorCamp runs from "this is my first DEF CON" to people who have been hacking hardware since before you were born. When you picture the front row for this talk, what's your mental model of the audience? Mostly physical security people who know locks but not firmware? Mostly digital people who know JTAG but not tailpieces? A general hacker-camp mix? How much of the digital attack surface (NAND flash, JTAG fuse, MSP430 architecture) do you plan to explain versus assume?

---

## Workshop Questions

**8. What hardware does a participant work with, and what do they bring or receive?**
The submission references hands-on RFID flash encoding for access control locks. What is the specific equipment in a participant's hands — a Proxmark3, a Flipper Zero, a custom board? Does the workshop supply it, or do participants bring their own? What's the rough cost if someone is coming in cold and needs to acquire the toolchain? (ToorCamp audience will want to know before they show up.)

**9. What can a participant DO after that they couldn't do before?**
I want to write a facilitator guide around a specific capability transfer, not around general awareness. After 90 minutes (or however long) of your workshop, can a participant independently perform a credential clone on an RFID access control lock in a sanctioned test environment? Or is the goal closer to: they understand how flash encoding works, they can read and write with their tool, they know what to look for? There's a big difference between "you leave with hands-on skills you can go practice tonight" and "you leave with a conceptual framework and the toolchain set up."

**10. What experience level are you assuming?**
Do participants need to know what RFID is before they walk in? Should they have used a Proxmark before, or does the workshop include a quick tool orientation? Is this aimed at practitioners who already do physical pen testing and want to add RFID to their kit, or is it genuinely accessible to someone who's never held a card reader?

**11. Duration, participant cap, and take-home artifact?**
Three logistics questions in one: (a) How long is the workshop? (b) How many people can participate effectively — is this limited by hardware sets, by your ability to walk the room, or by the space? (c) Is there a take-home artifact — a cloned card they encoded themselves, a printed reference sheet, a configured tool? If yes, what is it? The answer shapes both the facilitator guide (what to time-box, when to push vs. slow down) and the handout (what it needs to scaffold vs. what it can leave as a take-home reference).

**12. What does "Don't Blink" reference?**
The workshop title is "Don't Blink Tell No Lies: Hands-On RFID Flash Encoding for Access Control Locks." I want to make sure I understand the title's resonance before writing any header copy or workshop intro framing. Is "Don't Blink" a reference to the encoding speed (it happens fast, you'll miss it if you're not watching), to a specific lock or vendor name, or to something else? Knowing the source of the phrase tells me how much weight to put on it in the facilitator intro and participant handout.

---

Your answers will unlock Phase 3: I'll draft SPEAKING-NOTES.md, a reveal.js slide deck, FACILITATOR-GUIDE.md, and PARTICIPANT-HANDOUT.md. The more specific you can be about the demo moment, the recommendation source, and the workshop capability transfer, the sharper those deliverables get.
