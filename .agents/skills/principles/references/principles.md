# Principles

The working principles behind every change: what counts as proof, how code and data are shaped, how a change is
sequenced, what the product's experience asks of the work, and when to stop for the person. Each is a named rule with
when it applies, a test to run in your head, and what applying it leaves behind. People read it to steer an agent in a
few words ("apply prove it works"); coding agents read it, through the `principles` skill, before they shape, debug,
test, measure or hand over a change.

**Where it lives.** In the `principles` skill, beside [its SKILL.md](../SKILL.md). The skill folder is
self-contained: copy it into any repo's `.agents/skills/` and this comes with it.

**Platforms.** The principles hold on every platform. Where the practice differs, a bullet is labelled **Web**,
**iOS**, **Android** or **Embedded (ESP-IDF, LVGL)**.

**Stability.** Cite this doc as `PRINCIPLES §n`. Do not renumber; add a new principle under the next free number. A
principle's name is part of its address too: people steer with it, so a name changes only with every place that uses
it.

| § | Section | Look here for |
| --- | --- | --- |
| 1 | [Using the principles](#1-using-the-principles) | Naming the decision a principle changed, steering by name, what wins over a principle |
| 2 | [Prove it on the real thing](#2-prove-it-on-the-real-thing) | Checking the result itself, never a proxy; suspecting the observation first |
| 3 | [Fix the root cause](#3-fix-the-root-cause) | Tracing a symptom to the first wrong decision; the ways a bug gets hidden |
| 4 | [Test the behaviour, not the implementation](#4-test-the-behaviour-not-the-implementation) | The two imagined edits; tests by role and name; a test before a bug fix |
| 5 | [Explain the number](#5-explain-the-number) | What limits a measurement, and what else it could be measuring |
| 6 | [Small steps, each checked](#6-small-steps-each-checked) | Units that end in a check; delivery in the order that proves itself |
| 7 | [Question the premise](#7-question-the-premise) | Two failed fixes on one assumption; testing the assumption first |
| 8 | [Get the data shape first](#8-get-the-data-shape-first) | Core types and structures before logic; groundwork before features |
| 9 | [Model the domain](#9-model-the-domain) | One structure for a repeated rule; a screen's states as one value |
| 10 | [Check at the boundary, trust inside](#10-check-at-the-boundary-trust-inside) | Parse input once where it enters; types for values that differ in meaning |
| 11 | [Separate before sharing](#11-separate-before-sharing) | Concurrent writers; tasks, interrupts, agents; a lock as the last resort |
| 12 | [Make it safe to run twice](#12-make-it-safe-to-run-twice) | Steps that converge after a crash or a retry; settings and OTA on a device |
| 13 | [Keep it easy to read](#13-keep-it-easy-to-read) | Layers to trace and state to hold; collapsing one-caller wrappers |
| 14 | [Subtract before you add](#14-subtract-before-you-add) | Deleting first; the smallest change; deciding a thing once |
| 15 | [Redesign as if it were always there](#15-redesign-as-if-it-were-always-there) | Fitting a new requirement into the design instead of bolting it on |
| 16 | [Move every caller, then delete the old way](#16-move-every-caller-then-delete-the-old-way) | Renaming a token or replacing a component in one change; when not to |
| 17 | [Build the lever](#17-build-the-lever) | A script, a codemod or a check that does or proves the work |
| 18 | [Experience first](#18-experience-first) | The person's experience over the builder's convenience; fewer things, finished |
| 19 | [Try more than one before committing](#19-try-more-than-one-before-committing) | Two or three options for a decision with no precedent |
| 20 | [Ask only what only the person can answer](#20-ask-only-what-only-the-person-can-answer) | Proceeding on what is reversible; stopping for cost, taste and direction |
| 21 | [Keep the lesson in the structure](#21-keep-the-lesson-in-the-structure) | A repeated mistake turned into a failing check, before words |
| 22 | [Guard the context window](#22-guard-the-context-window) | Keeping bulk out of the conversation |
| 23 | [Sources](#23-sources) | Where each principle comes from |

---

## 1. Using the principles

**A principle is a named rule that changes a decision; name each one that did, with the decision.**

- **Read the section before applying it** — the name is a pointer; the section is the rule.
- **Name each principle that changed a decision, and the decision** — "Subtract before you add (PRINCIPLES §14):
  deleted the two unused adapters before adding the third." A name with no decision behind it means the rule was
  named, not applied.
- **People steer with the names** — "apply prove it works" points at §2; answer by doing what the section says, and
  say which decision it changed.
- **The project's own rules win** — its docs, its design brief and the person's recorded decisions rank above a
  principle here. A principle that conflicts with one is raised with the person, never applied over it.
- **Proof is never traded away** — a smaller or cleaner change that cannot be shown to work loses to one that can
  (§2–§7).
- **Experience sets the target; the shape and change principles decide how to reach it** (§18 with §8–§17).
- **Apply a principle only where its "When" holds** — plain code that is clear, local and unlikely to grow stays
  plain.

---

## 2. Prove it on the real thing

**Check the result itself — the running feature, the stored value, the screen on the target, the diff — never a proxy
for it.**

- **When:** before saying a task is done, and before reporting any result.
- **Proxies do not count** — a passing build, a compile, a file's timestamp, a helper agent's summary, a cached output,
  a log line that says "done". Each shows that something ran, not that it did the right thing.
- **Suspect the observation before the system** — when a check fails, or passes too easily, first confirm it looked at
  the right build, file, device and moment: a stale bundle, a cached screenshot, the wrong board on the port.
- **Script the check when you can** — a command that reruns the comparison beats one look; show its output to the
  person.
- **Say what was not checked** — an unchecked part is named as unchecked, never folded into "done".
- **Web:** the page in a browser at the sizes that matter, the request on the network and the value stored.
- **iOS, Android:** the app on a simulator or a phone, not a preview canvas alone.
- **Embedded (ESP-IDF, LVGL):** the build flashed, the board's serial log and its screen — not the build's exit code.
- **The test:** could this "done" be true while the feature is broken? If so, check the feature.
- **In the kit:** `verify.py target` and `signoff`; `finish` refuses a hand-over without them where the change needs
  the target.

---

## 3. Fix the root cause

**Fix the first place the system did something it should not, not the place the symptom surfaced.**

- **When:** debugging any failure — a crash, a wrong value, a screen that looks wrong, a device that resets.
- **Reproduce first**, then ask "why" until the answer is a decision in the code.
- **Ask whether the triggering state is legitimate** — if it is, handle it where the code broke; if it should never
  exist, a check at the symptom hides the bug, so find what produced the state.
- **Know the ways a bug gets hidden** — a guard, a retry, a swallowed error, a clamped value, a default that covers
  missing data, a longer timeout, a one-off override at the width where a layout breaks.
- **Fix the pattern, not the instance** — search for every place with the same fault.
- **When stuck, read the actual state** — a temporary log line marked for removal, a debugger, the device's serial
  log — instead of reasoning about it.
- **Leave a cheap signal** — when the cause took a long dig, propose the always-on log line, assertion or check that
  would have shown it at first look.
- **The test:** name the line where the system first went wrong. Until you can, the cause is not found.

---

## 4. Test the behaviour, not the implementation

**A test claims what users of the code can observe: it fails when that breaks, and keeps passing when only the
internals change.**

- **When:** writing, changing, reviewing or keeping a test.
- **Observable** — return values, the errors callers branch on, state they can read back, and what reaches outside: a
  request sent, a record written, what the screen shows and says. **Implementation** — private helpers, internal call
  order, intermediate data, a component's internal state.
- **The two imagined edits:**
  - **Break the behaviour** — a wrong value, a skipped or doubled effect. A test that still passes proves nothing. The
    usual causes: a loose assertion, an expected value computed by the code under test, an assertion on data the test
    built itself.
  - **Change the internals and keep every observable result.** A test that now fails is pinned to the implementation.
- **Keep a test that catches the first edit and survives the second**; rewrite or delete the rest.
- **Derive the expected value from the requirement**, never from running the code.
- **Pair "this never happens" with a case where it would.**
- **Assert the error type callers branch on**, not its message text.
- **Before a bug fix, a test that fails for the right reason** — then the fix, then the same test passing. Where no
  cheap test path exists, use the closest repeatable check (a script, a screenshot comparison) and say why; no new
  test beats a test that mostly tests mocks or timing.
- **A screenshot test is behaviour for the look** — its baseline changes only with the person's yes on the new
  picture.
- **Web:** find elements by role and accessible name — how a person and a screen reader find them — not by class
  name, and by test id only where no role fits.
- **iOS, Android:** query by accessibility label and trait (XCUITest), or by semantics (Espresso, Compose).
- **Embedded (ESP-IDF, LVGL):** assert what the device emits — the screen's state, the log, the bytes on the bus — or
  test the pure logic on the host; a test that reads a module's private struct is pinned.
- **The test:** run both imagined edits in your head; mutation testing runs the first one for real.

---

## 5. Explain the number

**Before trusting or reporting a measured number, name what limits it and rule out that it measured something else.**

- **When:** a speedup, a regression, frame time, memory, battery, binary size, load time, an eval score.
- **Write the decision before the run** — the result that would change it, and the run-to-run noise. Stop when the
  noise is larger than the effect.
- **Ask "why not twice as fast?"** — name the resource that bounds the result, from a profile or counters taken during
  the run, not from reading the code.
- **List what else the number could be measuring** — errors, skipped or cached work, code that never ran, a debug
  build, a warm cache against a cold one, the logging itself — and rule each out with evidence.
- **Keep the run count, the spread and the limiter with the number.**
- **Web:** a production build, the CPU and network throttling named, the browser's performance panel.
- **iOS, Android:** a release build on a device, Instruments or the Android Studio profiler.
- **Embedded (ESP-IDF, LVGL):** a release build, measured on the panel (LVGL's performance monitor, a timer around the
  flush), with the bus speed and the draw buffers named.

---

## 6. Small steps, each checked

**Order work as small units that each end in a state you can check, and do not start the next until this one
passes.**

- **When:** multi-step work — a migration, a sweep of similar edits, a feature built in parts — and how commits are
  stacked.
- **Each unit is a bracket** — a known-good state, one change, the check, then on.
- **Run the check per unit even when a script made the edit.**
- **Deliver in the order that proves itself** — the failing test before the fix, the removal before the rebuild, the
  baseline before the change.
- **The test:** if this unit is wrong, will you know before starting the next?
- **In the kit:** `verify.py run` after each unit.

---

## 7. Question the premise

**When two fixes built on the same assumption have failed the same check, test the assumption before writing a
third.**

- **When:** a second fix fails for the same reason as the first; the retry limit is near or reached.
- **Write the premise down** — the one sentence every failed fix assumed ("the value is stale because of the cache").
- **Find an observation that would come out differently if the premise were false**, and make it.
- **Look at how the failures are distributed**, not only how large they are — always the same screen, the same board,
  the first run after boot.
- **If the evidence contradicts the premise**, look for what the failures share that it did not predict.
- **Write no further fix until the premise is written down and tested.**
- **In the kit:** the retry limit (`verify.py run` exits 3) is where this happens; the premise and the observation
  that tests it go to the person with the report, and into `verify.py finding`.

---

## 8. Get the data shape first

**Settle the core types and data structures before writing the logic; the right shape makes the code that follows
obvious.**

- **When:** before writing logic — a new feature, a screen's state, a module, a stored format.
- **Define the core types early and trace every access** — who reads, who writes, how often — and pick the structure
  that fits the main path.
- **Remove repetition in the structure**, not every repeated line.
- **Ask what concurrent actors share** before sharing anything (§11).
- **Groundwork first** — what helps every later step (shared types, the test setup, the check) goes in before the
  features, after dead code is removed (§14).
- **Design:** the same order holds for a design system — roles before values — and for a screen — its content model
  before its layout.

---

## 9. Model the domain

**Encode a repeated rule in one structure — a state machine, a typed model, a table — instead of conditionals
scattered across files.**

- **When:** stateful logic, code that branches a lot, or one shape assumption repeated across files.
- **A screen's states are one value** — empty, loading, loaded, error, offline — with one case each, not three
  booleans that must agree. Each state a UX brief designs is one case.
- **Reach for** a state machine instead of flags, a typed model instead of loose parameters, a table or registry
  instead of a branch in every file, a reducer instead of scattered mutation.
- **Make illegal states unrepresentable** — "loading and failed" cannot be written when the status is one value.
- **Keep plain code** when the shape is clear, local and unlikely to grow; distrust an abstraction that adds a layer
  without removing a branch or an invalid state.
- **The sign it was skipped:** a feature that adds one more branch to an if-else chain, or a second boolean that must
  stay in step with the first.
- **Web:** a discriminated union for a component's status.
- **iOS, Android:** a Swift enum with associated values; a Kotlin sealed interface.
- **Embedded (ESP-IDF, LVGL):** an enum and one switch in the app layer that owns the screen's state; the LVGL widgets
  show it and hold none of it.

---

## 10. Check at the boundary, trust inside

**Validate and parse data where it enters — input, files, the network, storage, a sensor — and trust the types
inside.**

- **When:** validation, error handling, framework adapters, a new input.
- **Parse, don't validate** — turn raw input into a typed value once, at the edge; the code behind it takes the typed
  value and checks nothing again.
- **External data is untyped until parsed** — JSON, API responses, URL parameters, settings files, environment
  variables, stored values, what a person types, a sensor reading.
- **A check deep inside means the boundary missed something** — fix the boundary, then remove the inner check.
- **Keep the logic in pure functions** — the shell that calls the framework, the network or the hardware stays thin.
- **Give values that share a primitive but differ in meaning their own types** — millimetres and pixels, a user ID
  and a device ID.
- **Derive types from the schema that owns the shape**, rather than a second copy written by hand.
- **Embedded (ESP-IDF, LVGL):** validate at the driver and where settings are read from flash — a value an older
  firmware stored — not in every screen.
- **The test:** is this data crossing a boundary here? If not, the check is redundant. Can this be a pure function the
  shell calls? If so, extract it.

---

## 11. Separate before sharing

**When two actors might write the same thing, give each its own before adding a lock.**

- **When:** concurrent writers — threads, tasks, processes, agents, an interrupt and a task.
- **Ask whether they need one shared object or each publishes its own fact** — default to each its own (file, key,
  branch, buffer, queue), and merge where it is read.
- **Two writers of their own field in one shared file is still shared mutation.**
- **Serialize by structure, only where one shared target is a real invariant** — one writer, a queue, a lock,
  sequential phases, compare-and-swap. An instruction not to write at the same time is not concurrency control.
- **Embedded (ESP-IDF, LVGL):** tasks pass data by queue to the one task that owns it; LVGL is called from one task,
  or behind its lock, and never from an interrupt; an interrupt hands its work to a task.
- **Web:** one owner per piece of state; derived values are computed, not kept in step.
- **Agents:** each parallel agent works in its own worktree or branch.

---

## 12. Make it safe to run twice

**A step that changes state reaches the same end state however many times it runs, and wherever the last run
stopped.**

- **When:** commands, migrations, setup scripts, sync, a device's boot sequence, firmware updates, retries.
- **Read the current state, compare it with the goal, and apply only the difference.**
- **Make whatever a run leaves behind recognisable as stale** — a lock, a temporary file, a half-written record.
- **Write to a temporary file and rename it into place**, so a crash leaves the old file or the new one, never half
  of each.
- **Embedded (ESP-IDF, LVGL):** a settings write commits as one unit (NVS's commit) and the reader tolerates a missing
  key; an OTA update writes the other slot and switches only after it verifies; a reset mid-boot boots again cleanly.
- **Web:** a submit retried by the network or pressed twice creates one record — an idempotency key, with the button
  disabled while it is pending.
- **The test:** what happens if it runs twice? If it crashes at every point it could?

---

## 13. Keep it easy to read

**Count what a reader must trace and hold in mind to answer a question about the code, and cut both.**

- **When:** reviewing or shaping code that is hard to follow.
- **Two measures** — the layers between the question and the answer, and the hidden or changeable state the reader
  must keep in mind.
- **Collapse layers that only forward** — a wrapper with one caller, an adapter with one implementation, a method that
  passes its arguments through.
- **Shrink the reach of state** — a return value over a mutation, a local over a field, a field over module state,
  module state over a global; derive a value instead of keeping two copies in step.
- **State an invariant once, where it is enforced**, not in every consumer.
- **The test:** can a new reader answer "where does X come from?" and "what can change X?" in half a minute?

---

## 14. Subtract before you add

**Remove what is dead or redundant first, then build on the simpler base, with the smallest change that does the
job.**

- **When:** sequencing an addition, a refactor or a rewrite; sizing a diff; tempted to add a layer, an option or a
  flag.
- **Delete first** — dead code, unused options, duplicate components, stale docs a reader would copy.
- **Make the smallest change that solves the problem** — fewer lines beat elegant scaffolding.
- **Decide a thing once** — one source of truth, passed on as a plain value, never the same choice repeated in several
  places.
- **Design for observed use** — no option, validator or setting for a case nobody has.
- **Leave the system a little simpler than you found it.**
- **Design:** a new component only when the existing ones cannot do the job; a new token only when no role fits.

---

## 15. Redesign as if it were always there

**Fit a new requirement into the design as if it had been known from the start, instead of bolting it on.**

- **When:** a new requirement meets an existing design.
- **Read every affected file**, then ask: writing this today with this requirement, what would we build?
- **Carry the change through every reference** — types, docs, examples, the reasons in a doc's Decisions.
- **Think through the whole redesign, then deliver it in small checked steps** (§6).
- **Docs follow the same rule** — they state the current design, not the history of how it got there.

---

## 16. Move every caller, then delete the old way

**When a new internal function, token or component replaces an old one, migrate every caller and delete the old one in
the same change.**

- **When:** renaming a token, replacing a component, changing an internal function's contract — where nobody outside
  the codebase depends on the old one.
- **Leave no compatibility layer behind** — with two ways to do one thing, the next agent copies the wrong one.
- **Rewrite the tests to assert the new contract**; delete the tests that guarded only the old implementation.
- **Breakage inside a planned migration is fine** when it is scoped and the whole is checked at the end.
- **It does not apply to what lives outside the code** — a public API, a URL people saved, a stored key or file format
  on devices already in use. Those need a migration path (§12), and removing them is the person's decision.
- **Embedded (ESP-IDF, LVGL):** an NVS key renamed without a migration loses every device's saved setting on update.

---

## 17. Build the lever

**For work that is not trivial, build the small tool that does it or proves it — a script, a codemod, a check —
instead of working by hand.**

- **When:** any edit, migration, analysis or check beyond a couple of obvious edits — the bar is triviality, not
  repetition.
- **Do the first unit by hand**, then build the tool and prove it by running it on that unit; make it safe to rerun
  (§12).
- **A deterministic script beats several agents working by judgment** — save agents for the judgment calls.
- **Build the smallest script that does the job**, never a framework.
- **Have it print its result, not its work.**
- **Applying this leaves a file** — a script, a check or a codemod in the diff; commit it when the work outlives the
  session.

---

## 18. Experience first

**When the builder's convenience and the person's experience conflict, choose the experience.**

- **When:** product, UX or scope trade-offs.
- **Every feature, control and option earns its place** — fewer things, finished, beat more things, rough.
- **Get the details right** — states, feedback, transitions, alignment, error messages.
- **Serve the core task** — what does not serve it gets out of the way.
- **The person is whoever uses the work** — the end user of a screen, the developer who imports a module, the
  engineer who maintains it next.
- **Explain impact from their side** — what they see, wait for or lose.
- **This sets the work's target; getting the data shape first (§8) sets its order.**
- **In the kit:** the `ux-designer` and `ui-designer` skills hold how; this principle breaks ties.

---

## 19. Try more than one before committing

**For a decision with no precedent, build two or three small options and compare them before choosing.**

- **When:** a new interaction, a visual direction or an architecture the codebase has no example of; a decision that
  depends on feel.
- **Make the options differ in kind**, not in one value.
- **Compare them side by side, on the target where feel matters**, show the person and recommend one with the
  evidence.
- **Settle by prototype what a prototype can settle**; leave to the person what only taste or product direction can.
- **Keep prototypes cheap** — a scratch page, a branch, a story, a sketch on the board.
- **Follow the precedent where one exists** — consistency beats novelty.
- **In the kit:** offer two or three drafts at the `ui-designer` skill's first gate.

---

## 20. Ask only what only the person can answer

**Proceed on what is reversible and yours to decide; stop for what costs the person if it is wrong.**

- **When:** tempted to ask "should I do X?".
- **Ask before** anything irreversible or outward-facing — a deploy, a push, deleting data, flashing a board, a message
  sent; before building what the person must like — draft it, then ask; at a fork where the options cost differently
  and only their priorities decide.
- **Do not ask** what you can find out by reading, running or prototyping, or about a reversible step inside the task
  they gave you — do it, and say what you did and why.
- **Ask once, with the options, what each costs and your pick.**
- **"No" is an answer** — asked whether something is worth doing, give your judgment, not agreement by default.
- **In the kit:** the guard's asks and the design gates are where the person decides; between them, keep working.

---

## 21. Keep the lesson in the structure

**Turn a mistake that happened twice into something that fails when it happens again, before writing it down as
advice.**

- **When:** correcting the same mistake a second time; the person corrects you; a judge keeps missing the same thing.
- **Fix it at the highest level that works:**
  1. **Architecture** — make it impossible: one owner per piece of state, one supported way, the wrong import fails.
  2. **Types** — the bad state cannot be written.
  3. **A check whose error names the fix** — a lint, a script in CI; on a pattern already common, fail only on new
     hits.
  4. **A test of the behaviour** (§4).
  5. **Words, last** — a doc rule, a skill line, a rubric item — for what needs judgment; nothing fails when an agent
     skips them.
- **Prove a new check fails on the real past mistake**, then passes on the fix, before trusting it.
- **When a lesson can only be words, make it prominent** and give an example of the failure.
- **When the fix is structural, remove the words it replaces** — the instruction was the symptom.
- **In the kit:** `verify.py finding --route test|rubric|guard|skill|doc`, highest route first.

---

## 22. Guard the context window

**Keep bulk out of the conversation: send large reading to a helper and keep the findings, not the raw output.**

- **When:** long files, big logs, wide searches, repeated reads, planning a fan-out.
- **Read the part you need** — search, then read the range.
- **Run long commands through a wrapper** that prints the result and the errors, not the log.
- **Hand broad reading to a read-only helper agent** and keep its conclusion.
- **Cap each phase** — the files it reads, the turns it takes.
- **Write what must survive compaction into a file** — the task's state — not only the chat.

---

## 23. Sources

| Principle | Source |
| --- | --- |
| The idea of principles as short named rules an agent cites with the decision each changed; most of the rules here, rewritten for this kit | pstack, a Cursor plugin by Lauren Tan (MIT licence): its `principle-*` skills |
| §3 asking "why" until the cause | The five whys, Toyota Production System (Taiichi Ohno) |
| §4 tests that resemble use; queries by role and name | Testing Library's guiding principles and query priority (Kent C. Dodds) |
| §4 the first imagined edit, run by a tool | Mutation testing |
| §5 finding the limiter during a run | Brendan Gregg, "Active Benchmarking" |
| §8 data structures before logic | Fred Brooks, *The Mythical Man-Month*, ch. 9: show the tables and the flowchart becomes obvious |
| §9 illegal states unrepresentable | Yaron Minsky, "Effective ML" |
| §10 parse, don't validate | Alexis King, "Parse, don't validate" |
| §12 write, then rename into place | POSIX `rename()`, atomic within one file system |
| §12, §16 settings and updates on a device | ESP-IDF Programming Guide: Non-Volatile Storage, Over The Air Updates |
| §11 LVGL from one task | LVGL documentation: using LVGL with an operating system and interrupts |
