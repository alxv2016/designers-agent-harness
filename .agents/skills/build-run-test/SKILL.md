---
name: build-run-test
description: Builds, runs, tests and screenshots this project, and takes evidence from the target — the install, the dev server or simulator, the build through the quiet wrapper (quiet.py prints the result and the errors, not the log), the tests, screenshots at the sizes that matter, and what may run on the target without asking. Use when building, starting the app, running tests, taking a screenshot, setting up a fresh clone, or when the build or the app will not start.
---

# Build, run and test

> **Fill in per project.** The bootstrap prompt (AGENT_HARNESS §17) fills every `<…>` below from the repo and the
> person's answers; the shape and the rules stay.

How to build this project, run it on the target, test it and take evidence from it. The project's tools and versions
are in AGENTS.md → Environment; the checks `verify.py run` runs are `CHECKS` in `.agents/project.py`. The docs win if
this skill and a doc disagree — fix the skill.

## When to use

- A fresh clone: installing the tools and the dependencies.
- Building, starting the dev server or the simulator, running the tests.
- Taking a screenshot of a screen, or other evidence from the target.
- The build fails, the app will not start, or a test fails only on one machine.

## Rules

### Do

1. **Run long commands through the quiet wrapper** — `python3 .agents/skills/build-run-test/scripts/quiet.py --
   <command>`; it prints the result and the error lines and keeps the log in `.cache/harness/logs/`
   (AGENT_HARNESS §7.2).
2. **Run what may run without asking** — building, testing, the dev server, the simulator: `<list>`.
3. **Ask before what the guard asks about** — `<deploys, migrations, paid API calls, the person's accounts>`.
4. **A request to look authorises looking only** — taking a screenshot is not permission to change anything.
5. **Report what was seen apart from what is suspected.**
6. **Mark a temporary debug line with `DEBUG-TEMP`**, and take it out before the hand-over — the pre-commit hook and
   `verify.py finish` refuse it.
7. **On a regression, build the last known-good commit first**, then bisect.

### Never

- **Paste a full build log into the chat** — the wrapper's summary and the log's path.
- **Stop a process you did not start** — the person's dev server may be the one on the port.

## Procedure

### A fresh clone

```sh
<install the toolchain: e.g. nvm use, pyenv install, brew bundle>
<install the dependencies: e.g. npm ci, uv sync, pod install>
git config core.hooksPath .agents/githooks     # the person runs this once per clone
python3 .agents/skills/verify-change/scripts/verify.py doctor
```

### Build and test

```sh
python3 .agents/skills/build-run-test/scripts/quiet.py -- <build command>
python3 .agents/skills/build-run-test/scripts/quiet.py --name test -- <test command>
```

### Run on the target

```sh
<start the dev server or the simulator: e.g. npm run dev -- --port 3000>
<the health check: e.g. curl -sf http://localhost:3000/ >/dev/null && echo up>
```

### Screenshots

Take each changed screen at the sizes that matter — `<the breakpoints or devices: e.g. 375 × 812, 1440 × 900>` — into
the scratchpad, and open each one to say what it shows.

```sh
<the screenshot command: e.g. a headless browser's screenshot, xcrun simctl io booted screenshot <file>,
 adb exec-out screencap -p > <file>>
```

## Checks

- [ ] (script) The build passes through `quiet.py` with no new warning in the project's own sources
- [ ] (script) The tests pass
- [ ] No `DEBUG-TEMP` line left — `verify.py finish` shows none

## Traps

- **`<symptom>`** → `<cause>` → `<fix>` — add each trap the first time it costs time
  (verify-change → Recording what was learned, route `skill`).

## Sources

| Topic | Where |
| --- | --- |
| The loop these steps sit in | [`verify-change`](../verify-change/SKILL.md) |
| Quiet output, token use | [AGENT_HARNESS §7.2, §18](../../../docs/AGENT_HARNESS.md#72-inside-a-skill) |
| What asks the person | [HARNESS §2](../../HARNESS.md#2-the-guard) |
