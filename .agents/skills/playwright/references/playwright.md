# Playwright

How end-to-end tests are written, kept and debugged with Playwright so that each proves a person's path through the
product and fails only when that path breaks: what a spec file holds, locators by role and name, assertions that
wait, isolation and state, what the project does not control, the accessibility floors, reflow, themes and the
keyboard, visual baselines, traces and fixing a failing test, CI and browsers, and Playwright's MCP server and test
agents. People read it to know what a good end-to-end test is; coding agents read it, through the `playwright`
skill, before they write, fix or review one.

**Where it lives.** In the `playwright` skill, beside [its SKILL.md](../SKILL.md), with the spec file's
[template](../templates/feature.spec.ts.tpl) and the [check](../scripts/e2e_check.py). The skill folder is
self-contained: copy it into any repo's `.agents/skills/` and these come with it.

**Platforms.** Playwright drives web apps in Chromium, Firefox and WebKit, on desktop sizes and emulated phones. A
native iOS or Android app and an LVGL screen are walked on the target instead; their logic is tested on the host.

**Stability.** Cite this doc as `PLAYWRIGHT §n`. Do not renumber; add new material under the next free number.

| § | Section | Look here for |
| --- | --- | --- |
| 1 | [What an end-to-end test is for](#1-what-an-end-to-end-test-is-for) | The person's path; what unit tests and stories cover instead |
| 2 | [The spec file](#2-the-spec-file) | The template's layout; one file per feature; names as tasks |
| 3 | [Locators](#3-locators) | Role and name first; chaining and filtering; no CSS or XPath; generating them |
| 4 | [Assertions and actions](#4-assertions-and-actions) | Web-first assertions, awaited; no fixed waits; no forced actions; soft assertions |
| 5 | [Isolation and state](#5-isolation-and-state) | Each test on its own; setup in hooks; signing in once; parallel runs |
| 6 | [What the project does not control](#6-what-the-project-does-not-control) | Stubbing third parties and errors with `page.route`; test data |
| 7 | [Accessibility, reflow, themes and the keyboard](#7-accessibility-reflow-themes-and-the-keyboard) | axe, 320 px, colour scheme and reduced motion, the keyboard path |
| 8 | [Visual baselines](#8-visual-baselines) | `toHaveScreenshot`, where baselines are made, the person's yes |
| 9 | [Debugging and fixing a failing test](#9-debugging-and-fixing-a-failing-test) | Traces, UI mode, the inspector; the app or the test; never weakening |
| 10 | [CI, browsers and upkeep](#10-ci-browsers-and-upkeep) | Linux, the browsers needed, sharding, linting, keeping Playwright current |
| 11 | [Agents: the MCP server and test agents](#11-agents-the-mcp-server-and-test-agents) | `@playwright/mcp`, its safe settings; the planner, generator and healer |
| 12 | [Traps](#12-traps) | Symptom, cause, fix |
| 13 | [Sources](#13-sources) | Playwright's docs pages this rests on |

---

## 1. What an end-to-end test is for

**An end-to-end test walks one task a person does in the running app, in a real browser, and checks what they would
see; it is the slowest layer, so it covers paths, not every state.**

- **Test what the person sees and does** — "avoid relying on implementation details" such as function names, data
  shapes or CSS classes (Playwright, Best practices).
- **Each layer proves what the one below cannot** — a unit test a function's result; a story a component's states,
  their interaction and their accessibility; an end-to-end test a path through pages, with routing, data and the
  whole app's markup.
- **Cover the top tasks and their failures** — the paths the UX brief or the product names first, each with the
  error a person is likely to meet; a state that lives inside one component belongs in its story.
- **A test fails when the path breaks and only then** — it passes when the markup, the styles or the internals change
  and the person's path does not.

---

## 2. The spec file

**One spec file per feature or flow, laid out as the template: a `describe` for the feature, setup in `beforeEach`,
then a test per task, its failure, the keyboard path, axe in each theme and reflow.**

- **Where it sits** — the project's test folder (`e2e/` in a `react-vite-setup` app), named for the feature:
  `checkout.spec.ts`.
- **Test names say the task in the person's words** — `pays for the basket`, `shows an error when the card is
  declined`; never `test 1` or a function name.
- **Each test reads alone** — its setup in `beforeEach` or a fixture, its own data, no reliance on another test's
  result (§5).
- **A new page starts from the project's smoke shape** — no page error, console error or failed request; its main
  heading by role and name; axe; reflow; a screenshot attached as evidence.
- **The template:** [templates/feature.spec.ts.tpl](../templates/feature.spec.ts.tpl).

---

## 3. Locators

**Find elements the way a person and a screen reader do — by role and accessible name first — so a test survives a
redesign and fails when the interface stops making sense.**

- **The order:** `getByRole` with its `name`, then `getByLabel` for a form field, `getByPlaceholder`, `getByText`,
  `getByAltText`, `getByTitle`; `getByTestId` only where nothing a person perceives tells the element apart — an
  explicit contract.
- **Prefer user-facing attributes to XPath or CSS selectors** — `page.locator('button.buttonIcon.episode-actions-later')`
  breaks when a class changes; `page.getByRole('button', { name: 'submit' })` does not (Playwright, Best practices)
  (check PW2).
- **Chain and filter to narrow** — `page.getByRole('listitem').filter({ hasText: 'Product 2' }).getByRole('button',
  { name: 'Add to cart' })`.
- **A locator that cannot be found by role and name is a finding about the interface** — a button with no accessible
  name fails a person on a screen reader too; fix the name, not the test.
- **Generate them** — `npx playwright codegen <url>` and the VS Code extension pick role, text and test-id locators
  and make one more specific when several elements match.
- **Locators are strict and lazy** — an action on a locator that matches two elements fails; each action finds the
  element again, so a re-render does not leave a stale handle.

---

## 4. Assertions and actions

**Assert with web-first assertions, awaited, which wait and retry until the page reaches the state; never wait a fixed
time, never check a value once.**

- **Web-first:** `await expect(page.getByText('welcome')).toBeVisible()`. **Manual:** `expect(await
  page.getByText('welcome').isVisible()).toBe(true)` — `isVisible()` returns at once and does not wait (Playwright,
  Best practices) (check PW3).
- **Await every web-first assertion** — `expect(locator).toBeVisible()` without `await` floats: the test ends before
  it settles and never fails on it (check PW4). Lint for it with the floating-promises rule where the project's
  linter has one (§10).
- **Never a fixed wait** — `waitForTimeout` is slow when the app is fast and flaky when it is slow; wait for the state
  the person would see (check PW1).
- **Actions wait for actionability** — visible, stable, enabled, receiving events. `force: true` skips those checks
  and hides a real problem — an overlay over the button, a control still disabled (check PW8).
- **Soft assertions** — `await expect.soft(locator).toHaveText('Success')` lets a test go on and lists every failure
  at the end; use them for a page's several independent checks, not for a step the next one depends on.
- **Assert the outcome, not the mechanism** — the text shown, the URL, the status announced, the request that reached
  the server (`page.waitForRequest`), not a component's internal state.

---

## 5. Isolation and state

**Each test runs on its own — its own cookies, storage and data — so it can run alone, in any order, in parallel.**

- **Each test gets a fresh browser context** — local storage, session storage and cookies are its own; isolation
  "improves reproducibility, makes debugging easier and prevents cascading test failures" (Playwright, Best
  practices).
- **Repeat setup in `beforeEach` or a fixture** — a little duplication beats tests that depend on each other.
- **Sign in once, not per test** — a setup project signs in and saves the storage state, and the tests that need it
  start from that file (Playwright, Authentication). The saved state holds a session: keep it out of git.
- **Never depend on another test's leftovers** — a record another test created, the order tests run in.
- **Tests run in parallel** — files across workers; `test.describe.configure({ mode: 'parallel' })` runs one file's
  tests in parallel too.

---

## 6. What the project does not control

**Test only what the project controls: stub third parties, and the errors they return, at the network.**

- **Stub a third party with `page.route`** — `await page.route('**/api/fetch_data_third_party_dependency', route =>
  route.fulfill({ status: 200, body: testData }))` (Playwright, Best practices).
- **Never visit a site the project does not own** — its outage or redesign fails the build; test the app from
  `baseURL` (check PW7).
- **Stub the failures too** — a 500, a timeout, an empty list, a slow response — so the error and empty states the UX
  brief designs are each walked.
- **Control the data** — a seeded database or a staging environment whose data does not change between runs.
- **A secret never sits in a test** — credentials come from the environment, and a saved session stays out of git.

---

## 7. Accessibility, reflow, themes and the keyboard

**Every page a test visits meets the accessibility floors axe can find, reflows at 320 px, holds in each theme, and
its main task works from the keyboard.**

- **axe on WCAG 2.0 to 2.2 A and AA** — `new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a',
  'wcag21aa', 'wcag22aa']).analyze()`, its violations expected empty; once per page and state, not after every
  click. axe finds part of the floors; the rest are the person's walk.
- **Reflow at 320 px** — `page.setViewportSize({ width: 320, height: 640 })`, then the document no wider than the
  viewport (WCAG 1.4.10).
- **Each theme** — `page.emulateMedia({ colorScheme: 'dark' })` where the app follows the system's scheme, or the
  app's own theme switch where it has one; axe again in that theme.
- **Reduced motion** — `page.emulateMedia({ reducedMotion: 'reduce' })` for a path whose motion changes.
- **The keyboard path** — `page.keyboard.press('Tab')` to the control, `Enter` or `Space` to act, `Escape` to close;
  `toBeFocused()` where focus must land.
- **Evidence** — a screenshot attached to the report with `testInfo.attach`, for the person to look at.

---

## 8. Visual baselines

**A visual baseline is the approved look of a screen: added once the person said yes to it, made where CI runs, and
updated only with their yes on the new picture.**

- **`await expect(page).toHaveScreenshot()`** compares the page with its baseline, pixel by pixel within a threshold.
- **Keep the operating system and browser the same** — baselines differ by platform, so they are made and updated
  where CI runs (Playwright, Visual comparisons).
- **Updating a baseline accepts a new look** — `--update-snapshots` is the person's yes, the same as their yes on the
  built screen; never run to make a failure go away.
- **Mask what changes every run** — a clock, an avatar, an ad, with `mask: [locator]`.

---

## 9. Debugging and fixing a failing test

**Read the trace before touching the test, decide whether the app or the test is wrong, and fix that one — never
weaken an assertion to make it pass.**

- **Traces on the first retry in CI** — `trace: 'on-first-retry'`; "We don't recommend setting this to `on`", which
  is heavy (Playwright, Best practices) (check PW6). Locally: `npx playwright test --trace on`, then `npx playwright
  show-report`.
- **Step through** — `npx playwright test <file>:<line> --debug` opens the inspector; UI mode (`--ui`) gives time
  travel and watch mode; the VS Code extension runs a test in debug from the gutter.
- **The app or the test?** Replay the failing steps, look at the page at the failing moment, and ask whether a person
  would succeed. If they would not, the app is broken: report or fix the app, and keep the test failing. If they
  would, the test is wrong: a locator that no longer names the element, a missing wait for a state, data it assumed.
- **Never weaken** — no looser assertion, no `force: true`, no longer timeout, no skipped test, to turn red green;
  a test skipped because the feature is broken says so and names the issue.
- **Flaky is a bug** — a test that passes on retry has a race: a missing web-first wait, shared state, unstubbed
  network; find it in the trace.

---

## 10. CI, browsers and upkeep

**Run every test on every commit and pull request, on Linux, in the browsers the product supports, with Playwright kept
current.**

- **Each commit and pull request** — and "Use Linux when running your tests on CI as it is cheaper" (Playwright, Best
  practices).
- **Install only the browsers needed** — `npx playwright install chromium --with-deps` for Chromium alone.
- **A project per browser and size** — `devices['Desktop Chrome']`, `devices['Desktop Firefox']`,
  `devices['Desktop Safari']`, and the phone sizes the product supports.
- **No focused test reaches CI** — `forbidOnly: !!process.env.CI` in the config fails a run with `.only` left in
  (check PW5).
- **Shard a long suite** — `npx playwright test --shard=1/3` across machines.
- **Lint and type-check the tests** — the floating-promises rule (`@typescript-eslint/no-floating-promises`, or the
  project linter's own) catches a missing `await`; `tsc --noEmit` in CI.
- **Keep Playwright current** — `npm install -D @playwright/test@latest`, then the browsers again; read the release
  notes; `npx playwright --version` says what is installed.

---

## 11. Agents: the MCP server and test agents

**Playwright's MCP server lets a coding agent drive a browser by its accessibility tree; Playwright's test agents
plan, generate and heal tests. Use the server with safe settings; borrow the agents' loop.**

### 11.1 The MCP server

- **The package:** `@playwright/mcp`, run with `npx @playwright/mcp@latest`; it needs Node.js 20 or newer.
- **It reads pages as accessibility snapshots**, not pixels — the same roles and names the tests use; a screenshot
  tool exists for visual checks.
- **Register it in Claude Code** at project scope — `claude mcp add playwright npx @playwright/mcp@latest`, then the
  flags below — or in `.mcp.json`:

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest", "--headless", "--isolated"]
    }
  }
}
```

- **Safe settings for an agent** — `--headless` (it opens a visible browser by default); `--isolated`, a fresh
  profile each session, instead of the persistent one it keeps by default; `--allowed-origins` limited to the app's
  local origins where the agent should go nowhere else.
- **Leave `browser_run_code_unsafe` off** — it runs arbitrary JavaScript in the server's process; the README calls it
  equivalent to remote code execution.
- **Extra tools by capability** — `--caps=testing` adds tools that generate a locator and verify an element, text or
  value; `vision`, `pdf`, `devtools`, `network` and `storage` add others.
- **What it is for here** — looking at the running app the way the tests do, finding the role and name of an element
  before writing its locator, and replaying a failing test's steps.

### 11.2 Test agents

- **Three agents** — the planner explores the app and writes a Markdown test plan in `specs/`; the generator turns
  the plan into tests, checking locators and assertions live; the healer replays a failing test and patches it, or
  skips it when it judges the feature broken (Playwright, Agents).
- **Set up by** `npx playwright init-agents --loop=claude` (also `vscode`, `codex`, `opencode`); the definitions are
  regenerated after each Playwright update.
- **Here, borrow the loop rather than install them** — the `playwright` skill's Writing procedure names the tasks
  before writing, and its Fixing procedure replays and decides; the generated definitions would sit outside a kit's
  own agents and its scope labels. A project without a kit can install them.
- **A healer that skips a test is a finding** — the skill's Fixing procedure reports the broken feature instead (§9).

---

## 12. Traps

- **A test passes and the feature is broken** → an assertion with no `await`, or a manual check that ran once → await
  a web-first assertion (§4).
- **Tests fail after a restyle, with no change a person would notice** → CSS selectors → locators by role and name
  (§3).
- **A test fails only in CI, or only sometimes** → a fixed wait, shared state or an unstubbed request → the trace
  shows which (§4, §5, §9).
- **The suite goes red when a vendor's site is down** → a third party visited, not stubbed → `page.route` (§6).
- **A failing test turned green by `force: true` or a longer timeout** → the test weakened instead of the cause fixed
  → find what covers or delays the element (§9).
- **Every screenshot test fails on a new machine** → baselines made on another platform → make and update them where
  CI runs (§8).
- **The agent's browser keeps state between runs** → the MCP server's persistent profile → `--isolated` (§11.1).
- **A green suite and a page a screen reader cannot use** → no axe and no role-based locators → both, on every page
  (§3, §7).

---

## 13. Sources

| Topic | Where |
| --- | --- |
| Testing philosophy, locators, web-first assertions, isolation, third parties, debugging, traces, CI, browsers, linting, parallelism, soft assertions | Playwright docs, "Best practices" (`/docs/best-practices`) |
| Locator order, strictness, filtering | Playwright docs, "Locators" |
| Actionability | Playwright docs, "Auto-waiting" |
| Signing in once with a setup project | Playwright docs, "Authentication" |
| Stubbing requests | Playwright docs, "Mock APIs" and "Network" |
| Visual comparisons | Playwright docs, "Visual comparisons" |
| Colour scheme and reduced motion | Playwright docs, `page.emulateMedia` |
| axe in Playwright | Playwright docs, "Accessibility testing"; `@axe-core/playwright` |
| The test agents | Playwright docs, "Agents" (`/docs/test-agents`) |
| The MCP server, its flags and tools | Playwright docs, "Getting started — MCP"; the `microsoft/playwright-mcp` README |
| Reflow at 320 px | WCAG 2.2, Success Criterion 1.4.10 Reflow |
