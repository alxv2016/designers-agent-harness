---
name: principles
description: The working principles behind every change, carried in the skill (references/principles.md), each a named rule with when it applies, a test and what applying it leaves — Prove it on the real thing, Fix the root cause, Test the behaviour not the implementation (the two imagined edits; tests by role and accessible name), Explain the number, Small steps each checked, Question the premise, Get the data shape first, Model the domain (a screen's states as one value), Check at the boundary and trust inside, Separate before sharing (tasks, interrupts, agents), Make it safe to run twice (settings and OTA on a device), Keep it easy to read, Subtract before you add, Redesign as if it were always there, Move every caller then delete the old way (a token rename in one change), Build the lever, Experience first, Try more than one before committing, Ask only what only the person can answer, Keep the lesson in the structure, Guard the context window — on the web, iOS, Android and embedded ESP-IDF devices with an LVGL screen. Portable — the folder works in any repo. Use before shaping code or data, when debugging, writing or reviewing a test, measuring performance, planning a migration or a multi-step change, after two failed fixes, before declaring a task done, when tempted to ask "should I?", or when the person names a principle — "apply prove it works", "subtract before you add", "test behaviour".
metadata:
  scope: portable
---

# Principles

The rules behind how a change is shaped, sequenced, proved and handed over. They are kept in this skill at
[references/principles.md](references/principles.md) (cited `PRINCIPLES §n`); this page condenses them into one-line
rules and says when each applies. The project's own docs, design brief and the person's recorded decisions win over a
principle; the reference wins over this page — fix the page.

**With the other skills.** The design skills carry the principles of their own field (HCI, accessibility, motion,
layout, type); these are the principles of the work itself. Experience first (PRINCIPLES §18) is the tie-breaker the
`ux-designer` and `ui-designer` skills apply; Try more than one (§19) is how the `ui-designer` skill's first gate offers
drafts.

**Portable.** This folder is self-contained and links to nothing outside itself; it names the rest of a kit in
backticks. It has no script — a principle is applied by judgment, and the checks that enforce one belong to the skills
that own them. Copy it into any repo's `.agents/skills/` (or `.claude/skills/`) and it works there.

## When to use

- Before writing logic, a type, a stored format or a screen's state.
- Debugging a failure, or after a second fix fails for the same reason.
- Writing, reviewing or keeping a test.
- Measuring a speedup, a regression, a frame time or a size.
- Planning a migration, a rename, a refactor or any multi-step change.
- Before declaring a task done, or reporting a result.
- Tempted to ask the person "should I do X?".
- The person names a principle to steer the work.

## Rules

### Do

1. **Read a principle's section before applying it, and name each one that changed a decision, with the decision**
   (PRINCIPLES §1).
2. **Prove it on the real thing** — the running feature, the stored value, the screen on the target; suspect the
   observation before the system (PRINCIPLES §2).
3. **Fix the first place the system went wrong**, after reproducing it; a guard is a fix only when the state it handles
   is legitimate (PRINCIPLES §3).
4. **Keep a test that fails when the behaviour breaks and passes when only the internals change**; find UI elements by
   role and accessible name (PRINCIPLES §4).
5. **Name what limits a measured number and rule out what else it could be measuring** before reporting it
   (PRINCIPLES §5).
6. **End each unit of work in a check, and start the next only when it passes** (PRINCIPLES §6).
7. **After two failed fixes on one assumption, write the assumption down and test it** before a third (PRINCIPLES §7).
8. **Settle the data shape before the logic**, and the groundwork before the features (PRINCIPLES §8).
9. **Encode a repeated rule in one structure** — a screen's states as one value, not booleans that must agree
   (PRINCIPLES §9).
10. **Parse input once where it enters, and trust the types inside** (PRINCIPLES §10).
11. **Give each concurrent writer its own target before adding a lock**; LVGL from one task, never an interrupt
    (PRINCIPLES §11).
12. **Make every state-changing step converge however often it runs and wherever it stopped** (PRINCIPLES §12).
13. **Cut the layers a reader must trace and the state they must hold** (PRINCIPLES §13).
14. **Delete the dead weight first, then make the smallest change that does the job** (PRINCIPLES §14).
15. **Fit a new requirement into the design as if it had always been there** (PRINCIPLES §15).
16. **Migrate every caller of a replaced function, token or component, and delete the old one in the same change** —
    unless it lives outside the code (PRINCIPLES §16).
17. **Build the small script that does or proves non-trivial work** (PRINCIPLES §17).
18. **Choose the person's experience over the builder's convenience** (PRINCIPLES §18).
19. **For a decision with no precedent, compare two or three options** before choosing (PRINCIPLES §19).
20. **Proceed on what is reversible; ask only about cost, taste and direction**, once, with the options and your pick
    (PRINCIPLES §20).
21. **Turn a mistake made twice into a check that fails, before writing it as advice**; prove the check fails on the
    real mistake (PRINCIPLES §21).
22. **Keep bulk out of the conversation** — search, then read the range; long output through a wrapper (PRINCIPLES
    §22).

### Never

- **Cite a principle that changed no decision** — the citation then claims work that was not done (PRINCIPLES §1).
- **Apply a principle over the project's own rule or the person's decision** — raise the conflict instead
  (PRINCIPLES §1).
- **Call a task done on a proxy** — a green build, a compile, a helper's summary (PRINCIPLES §2).
- **Hide a bug behind a guard, a retry, a clamp or a longer timeout** (PRINCIPLES §3).
- **Compute a test's expected value with the code under test** (PRINCIPLES §4).
- **Report a number without its run count, spread and limiter** (PRINCIPLES §5).
- **Leave a compatibility layer behind an internal rename** (PRINCIPLES §16).
- **Ask the person what reading, running or a prototype can answer** (PRINCIPLES §20).

## Procedure

### Applying the principles to a task

1. **Match the task to the When lines** — the index in the reference's contents table; usually two to four apply.
2. **Read each matching section in full.**
3. **Do the work the section asks for**, and keep what it leaves: a test, a script, a written premise, a measurement
   with its spread.
4. **In the hand-over, name each principle that changed a decision**, with the decision — one line each.

### When the person steers by name

1. **Find the section** by its name or its number.
2. **Do what it says on the work in hand**, and say which decision it changed.
3. **If the principle does not fit the task**, say why in one line instead of applying it for show.

## Checks

No script reads a principle; these are read.

- [ ] Each principle named in the hand-over has the decision it changed (PRINCIPLES §1)
- [ ] "Done" rests on the real result, and what was not checked is named (PRINCIPLES §2)
- [ ] Each new or changed test survives both imagined edits (PRINCIPLES §4)
- [ ] A reported number carries its run count, spread and limiter (PRINCIPLES §5)
- [ ] A replaced internal name has no callers and no compatibility layer left (PRINCIPLES §16)
- [ ] A repeated mistake became a check before it became words (PRINCIPLES §21)

## Traps

- **A hand-over cites five principles and changes nothing** → names used as decoration → cite only what changed a
  decision (Do 1).
- **The fix passes the check and the bug comes back** → the symptom was guarded, not the cause → find the state's
  origin (Do 3).
- **Every refactor breaks a dozen tests that check nothing a user sees** → tests pinned to internals → rewrite them
  against the interface (Do 4).
- **A "3× faster" that vanishes on the next run** → noise larger than the effect, or a cached run → measure the spread
  and the limiter (Do 5).
- **A third fix on the same theory** → the premise was never tested → write it down and test it (Do 7).
- **A setting lost on every device after an update** → a stored key renamed as if it were internal → migrate stored
  data (Do 16; PRINCIPLES §12).
- **The agent stops every few minutes to ask** → reversible steps treated as the person's call → proceed and report
  (Do 20).

## Sources

| Topic | Where |
| --- | --- |
| Every principle, its test and its sources | [references/principles.md](references/principles.md) |
| Principles as named rules an agent cites | pstack, a Cursor plugin by Lauren Tan (MIT licence) |
