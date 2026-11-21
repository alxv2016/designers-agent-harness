---
name: playwright
description: Writes, fixes and reviews Playwright end-to-end tests so each proves a person's path through a web app and fails only when that path breaks, carried in the skill (references/playwright.md) with a spec file template (templates/feature.spec.ts.tpl) — one spec per feature with the task, its likely failure, the keyboard path, axe in light and dark and reflow at 320 px; locators by role and accessible name, chained and filtered, never CSS or XPath; web-first assertions, always awaited, never a fixed wait or a forced action; each test isolated, signing in once with a setup project; third parties and their errors stubbed with page.route; visual baselines only with the person's yes; traces on the first retry, and fixing a failing test by deciding whether the app or the test is wrong, never weakening it; CI on Linux with only the browsers needed, sharding, linting for floating promises; and Playwright's MCP server (@playwright/mcp, headless and isolated) and its planner, generator and healer agents; plus e2e_check.py (PW1–PW8). Portable — the folder works in any repo. Use after adding a feature, a page or a flow to a web app, when asked to write, fix or review an end-to-end test, when a Playwright test is failing or flaky, or to set up Playwright's MCP server.
metadata:
  scope: portable
---

# Playwright

How end-to-end tests are written, fixed and reviewed with Playwright. The rules are kept in this skill at
[references/playwright.md](references/playwright.md) (cited `PLAYWRIGHT §n`), the spec file's layout at
[templates/feature.spec.ts.tpl](templates/feature.spec.ts.tpl), and the check at
[scripts/e2e_check.py](scripts/e2e_check.py); this page holds the rules and the steps. The project's own test setup
and its UX brief's tasks decide what is tested; the reference wins over this page — fix the page.

**With the other skills.** A unit test covers a function, a story a component's states (the `storybook` skill), an
end-to-end test a person's path through pages — this skill. The `accessibility` skill holds the floors axe checks
here; the `ux-designer` skill's brief names the top tasks and their errors. A React and Vite app set up by the
`react-vite-setup` skill already has Playwright, its config, its browsers, CI and a smoke test; this skill writes the
tests for each feature after it, fixes them and adds the MCP server.

**Portable.** This folder is self-contained and links to nothing outside itself; it names the rest of a kit in
backticks. Copy it into any repo's `.agents/skills/` (or `.claude/skills/`) and it works there. In the agent-harness
kit, `verify.py run` runs the check on the Playwright files, and the `playwright` agent applies this skill.

## When to use

- A feature, a page or a flow was just added — its end-to-end test follows.
- The person asks for an end-to-end test, or for the tests a feature lacks.
- A Playwright test fails or is flaky.
- Reviewing a spec file, or a check that fails.
- Setting up Playwright's MCP server for agents.

## Rules

### Do

1. **Write each spec from the template** — the task, its likely failure, the keyboard path, axe in each theme, reflow
   (PLAYWRIGHT §2, §7).
2. **Find elements by role and accessible name**, chained and filtered to narrow; a test id only where nothing a person
   perceives tells it apart (PLAYWRIGHT §3).
3. **Assert with web-first assertions, and await every one** (PLAYWRIGHT §4).
4. **Keep each test isolated** — setup in `beforeEach` or a fixture, sign in once with a setup project (PLAYWRIGHT §5).
5. **Stub what the project does not control, and its failures, with `page.route`** (PLAYWRIGHT §6).
6. **Name each test as the person's task, in their words** (PLAYWRIGHT §2).
7. **Read the trace before changing a failing test, and decide whether the app or the test is wrong** (PLAYWRIGHT §9).
8. **Add or update a visual baseline only with the person's yes on the picture**, made where CI runs (PLAYWRIGHT §8).
9. **Run the MCP server headless and isolated**, with its unsafe code tool off (PLAYWRIGHT §11.1).

### Never

- **Wait a fixed time** — `waitForTimeout` (PLAYWRIGHT §4; PW1).
- **Select by CSS class, DOM structure or XPath** (PLAYWRIGHT §3; PW2).
- **Check a value once instead of waiting for it** — `expect(await x.isVisible())` (PLAYWRIGHT §4; PW3).
- **Force an action past its checks, or loosen an assertion, a timeout or a skip, to turn a test green**
  (PLAYWRIGHT §4, §9; PW8).
- **Visit a site the project does not own** (PLAYWRIGHT §6; PW7).
- **Leave `.only` in, or traces always on** (PLAYWRIGHT §9, §10; PW5, PW6).
- **Put a credential or a saved session in a test or in git** (PLAYWRIGHT §5, §6).
- **Install a package or a browser, or update baselines, without the person's yes.**

## Procedure

`E` is `python3 .agents/skills/playwright/scripts/e2e_check.py`, from the repo root.

### Writing the tests for a feature

1. **Name the tasks** — from the UX brief, the feature's spec or the person: the top tasks, and the error each is
   likely to meet. With the MCP server, walk the feature in the browser first and note each control's role and name.
2. **Copy the template** into the project's test folder as `<feature>.spec.ts`, dropping `.tpl` (PLAYWRIGHT §2).
3. **Write the setup** — the page, the stubs for third parties, the signed-in state if the feature needs it
   (PLAYWRIGHT §5, §6).
4. **Write a test per task, then its failure**, each asserting what the person sees, awaited (PLAYWRIGHT §3, §4).
5. **Keep the keyboard, axe-in-each-theme and reflow tests** (PLAYWRIGHT §7).
6. **Run `E <file>`**, fix each hit; then the tests (`npm run test:e2e`, or `npx playwright test <file>`); a failure
   goes through Fixing a failing test.
7. **Show the person** the report's screenshots and anything only they can judge.

### Fixing a failing test

1. **Read the trace** — `npx playwright show-report`, or rerun with `--trace on` (PLAYWRIGHT §9).
2. **Replay the steps** — with the MCP server, or `--debug` — and look at the page at the failing moment.
3. **Decide** — would a person succeed here? No: the app is broken — report it, or fix the app in its own change, and
   keep the test. Yes: the test is wrong — a locator, a missing wait for a state, data it assumed.
4. **Fix that cause**, never by weakening (PLAYWRIGHT §9); run the test several times to show it no longer flakes.

### Setting up the MCP server

Ask the person first: it downloads a package and opens a browser.

1. **Add the `playwright` entry** to `.mcp.json` with `--headless` and `--isolated`, and `--allowed-origins` for the
   app's local origins where the agent should go nowhere else (PLAYWRIGHT §11.1).
2. **Check it** — ask the agent to open the app's local URL and list the page's headings; it answers from an
   accessibility snapshot.

### Reviewing a spec file (read-only)

1. `E <file>` — PW1–PW8.
2. **Read what the check cannot** — each test a task with its failure, isolation, stubs for third parties, axe and
   reflow on each page, names in the person's words, nothing asserted about internals.
3. **Report** each finding with the line, the rule (`PLAYWRIGHT §n`) and the fix.

## Checks

```sh
python3 .agents/skills/playwright/scripts/e2e_check.py            # every Playwright file, against the baseline
python3 .agents/skills/playwright/scripts/e2e_check.py FILE …     # some files
python3 .agents/skills/playwright/scripts/e2e_check.py --test     # the self-test
```

- [ ] (script) `E` — prints `PW1–PW8 Playwright patterns — 0 hits`; baseline 0
- [ ] Each test is a task in the person's words, with its likely failure (PLAYWRIGHT §2)
- [ ] Locators by role and name; no CSS or XPath (PLAYWRIGHT §3; PW2)
- [ ] Every web-first assertion awaited; no fixed wait, no forced action (PLAYWRIGHT §4; PW1, PW3, PW4, PW8)
- [ ] Each test isolated; third parties stubbed (PLAYWRIGHT §5, §6; PW7)
- [ ] axe in each theme, reflow at 320 px, the keyboard path (PLAYWRIGHT §7)
- [ ] The tests pass, more than once for a test that flaked (PLAYWRIGHT §9)

## Traps

- **A test passes and the feature is broken** → an assertion not awaited → await it (Do 3; PW4).
- **Tests break on a restyle** → CSS selectors → role and name (Do 2; PW2).
- **Red only in CI, or only sometimes** → a fixed wait, shared state or an unstubbed request → read the trace (Do 7).
- **A fix that turned red green with `force: true`** → the cause was hidden → find what covers the element (Never).
- **A test the healer skipped** → the feature is broken → report it, keep the test (PLAYWRIGHT §11.2).
- **The agent's browser remembers the last session** → the MCP server's persistent profile → `--isolated` (Do 9).

## Sources

| Topic | Where |
| --- | --- |
| Every rule, the MCP server, the test agents | [references/playwright.md](references/playwright.md) |
| The spec file's layout | [templates/feature.spec.ts.tpl](templates/feature.spec.ts.tpl) |
| The check | [scripts/e2e_check.py](scripts/e2e_check.py) |
| Best practices, agents, the MCP server | Playwright docs: Best practices, Agents, Getting started — MCP |
