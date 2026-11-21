---
name: blast-radius
description: Finds what a change could break outside its own diff before it ships, and proves the one fact the change is safe because of by running real code — not by writing a convincing account. Looks where a search for callers stops — a design token used across components and themes, a component on every screen, a string in a narrow label or a longer translation, a stored key or format on devices and browsers already in use (localStorage, NVS), an API's JSON, a URL, a feature flag, CSS that cascades, shared state between tasks or an interrupt, a partition table, a library's pinned version — and rates each step of its evidence from "said so" to "seen on the target". Read-only on the code; probes run in a scratch folder. Portable — the folder works in any repo. Use when asked "what could this break?", "blast radius of X", "is this safe to merge?", before renaming a token, a component, a setting or a stored key, or reviewing a small diff you do not trust.
metadata:
  scope: portable
---

# Blast radius

Finds what a change breaks somewhere else, before it ships. Listing the callers is not the job — a search does that in
a second. The job is the breakage a search will not show, and proof of the one fact that makes the change safe. A
written account of why a change is safe reads as convincing whether or not it is true, so the account is not the
deliverable; the proof is.

**With the other skills.** The `teach` skill explains what the code does and why; a code reviewer scores the diff
against the project's rules; this skill hunts what the diff touches outside itself. A token's or a component's roles
come from the project's design brief and the `design-system` skill.

**Portable.** This folder is self-contained and links to nothing outside itself; it names the rest of a kit in
backticks. It has no script — each probe is written for the change in hand. Copy it into any repo's `.agents/skills/`
(or `.claude/skills/`) and it works there.

## When to use

- "What could this break?", "blast radius of X", "is this safe to merge?"
- Before renaming or changing a design token, a component's props, a setting, a stored key or a file format.
- A small diff you do not trust, in code you did not write.
- A dependency bump, a config change, a change to shared state between tasks.

## Rules

### Do

1. **Read the whole change first** — the diff, the symbols it adds, changes and removes, and what it now does
   differently that the diff does not spell out.
2. **Find the one fact the change is safe because of** — most risky-looking changes are safe because of a single fact
   ("this only drops cache entries that are already dead"); when it holds, most risks clear at once.
3. **Look where a search stops** — the places in Where a search stops, below, for each platform the change touches.
4. **Rate each fact's evidence on the ladder, and say where it stopped** — Evidence, below.
5. **Prove the one fact by running real code** — a probe that imports the code the app ships and calls the exact
   function in question, and fails loudly if you are wrong; paste what it printed.
6. **Give each risk how it breaks, where, how likely, how bad and how to check** — keep the confirmed risks apart from
   the ones checked and cleared.
7. **Cite a real file and symbol for every claim** — a search that finds nothing is an answer too; say what you
   searched.
8. **End with the cheapest check that would catch the real bug before merge** — the probe itself, a test, a run on
   the target.

### Never

- **Hand back a list of callers as the result.**
- **Invent a caller, an API or a behaviour of a library** — read its source at the pinned version.
- **Call a fact proven that you did not run** — write "unproven" and the step it reached.
- **Edit the change or the repo** — probes go in a scratch folder; one worth keeping becomes a test in its own change.
- **Pad the risks with maybes** — each needs a real way to break and a real cost.

## Procedure

### Evidence

Take each fact the change's safety depends on as far down this ladder as is cheap, and say where it stopped.

| Step | Evidence | Worth |
| --- | --- | --- |
| 1 | Said so | Nothing on its own |
| 2 | Pointed at the line — a real file and symbol, or the library's own source | A claim that can be checked |
| 3 | Walked the bad case step by step and showed it cannot be reached | Reasoning, still unrun |
| 4 | Ran it — a probe or a test that calls the real code and fails loudly when wrong | Proof in isolation |
| 5 | Saw it on the target — the running app, the device, the browser | Proof where it ships |

### Where a search stops

- **Design tokens** — every component and screen that uses the token by role, in every theme; the contrast pairs it
  takes part in; the token files on each platform generated from the brief; a hard-coded value elsewhere that copied
  it.
- **Components** — every screen that renders it, its stories and tests, props passed through spread, a default prop
  callers rely on without passing it.
- **Strings** — the narrowest place the string appears, its longest translation, a label with a fixed width on a
  small panel, an accessible name built from it, a test or a script that matches its text.
- **Stored data** — a key or format already written on people's devices and browsers: `localStorage`, cookies, a
  database column, a settings file, NVS on a device. Renaming it loses their data unless the change migrates it.
- **Wire formats** — an API's JSON, a URL people saved or another site links to, a message on a bus or a socket,
  another language reading the same bytes.
- **Timing and order** — effects and cleanup, unmount and teardown, a promise resolved after its screen closed,
  boot order, a watchdog.
- **Web** — CSS that cascades to other selectors, a global style, a breakpoint, a bundle split, a service worker's
  cache serving the old file.
- **iOS, Android** — an asset or string resource referenced by name, a deep link, a permission string, state restored
  after the app is killed.
- **Embedded (ESP-IDF, LVGL)** — state shared between tasks or with an interrupt, stack sizes, a Kconfig option
  another component reads, the partition table, an LVGL object deleted while a timer or an animation still holds it,
  the pinned version of a managed component.
- **Libraries** — the source at the version the lockfile pins, any local patch, and what a "dry run" or "safe" option
  actually skips.
- **Flags and config** — a feature flag on in one environment, a build option, an environment variable read
  elsewhere.

### Running it

1. **Read the change** (Do 1) — the diff, the commits, and any doc or design-brief section it touches.
2. **Find the one fact** (Do 2) and write it as one sentence.
3. **Look where a search stops** for each place the change reaches (Do 3); note each risk with its file and symbol.
4. **Rate and prove** — take the one fact to step 4 with a probe in a scratch folder, run it, and keep its output; take
   it to step 5 when the target is cheap to reach (Do 4, Do 5).
5. **Write it up** in the shape below.

### What to hand back

- **What it does** — what changed, including the part that is not obvious.
- **The one fact it is safe because of** — stated, the ladder step it reached, and the proof; or "unproven".
- **Risks** — each with how it breaks, the file and symbol, how likely, how bad and how to check; the proof pasted for
  the ones that matter.
- **Cleared** — what was checked and why it is fine.
- **Before you merge** — the cheapest check that catches the real bug, including the probe.

## Checks

No script reads a blast radius; these are read.

- [ ] The one fact is stated, with its ladder step and its proof or "unproven" (Do 2, Do 4)
- [ ] The probe ran against the real code, and its output is pasted (Do 5)
- [ ] Every risk names a real file and symbol, how it breaks, its likelihood and cost (Do 6, Do 7)
- [ ] Confirmed risks and cleared ones are listed apart (Do 6)
- [ ] Stored data and wire formats the change reaches were checked (Where a search stops)
- [ ] Nothing in the repo was edited (Never)

## Traps

- **A tidy page of risks, none of them real** → maybes listed instead of the one fact → find the fact and prove it
  (Do 2).
- **"Safe — nothing else calls it"** → a search for the symbol, not for the stored key, the JSON field or the string →
  look where a search stops (Do 3).
- **A token renamed and every theme but one updated** → only the default theme checked → check every theme and pair.
- **Saved settings gone after an update** → a stored key renamed as if it were internal → migrate it or keep it.
- **A library assumed to behave as its name says** → its source never read → read it at the pinned version (Never).
- **The probe passed and the bug shipped** → the probe called a copy of the logic, not the shipped function → import
  the real one (Do 5).

## Sources

| Topic | Where |
| --- | --- |
| The one fact, the evidence ladder, looking where a search stops | pstack's `blast-radius` skill, a Cursor plugin by Lauren Tan (MIT licence), rewritten for this kit |
| Stored data on a device | ESP-IDF Programming Guide: Non-Volatile Storage |
| Stored data in a browser | MDN: Window.localStorage |
