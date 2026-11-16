---
name: react-vite-setup
description: Sets up a React, Vite and TypeScript web app with Playwright for testing and Storybook for component documentation, from the web app spec in docs/, carried in the skill (references/react-vite.md) — checking the Node and Playwright browsers already installed and the builds the project's Playwright needs, and advising an install when there is none; writing the web app spec with the defaults of a working app (Node 22, npm, strict ports 5173, 4173 and 6006, Chromium and WebKit at 390x844 and 1280x800), each tagged [DEFAULT] so the person sees what was chosen and names anything else; generating the app — the shell, a hello-world feature, a Button with its stories, tokens.css written from DESIGN.md with a block per theme, CSS modules, oxlint and Prettier, three test layers (Vitest unit tests, every story run as a test in Chromium with the a11y addon, Playwright end-to-end tests with axe, a 320 px reflow check and screenshots in each browser and size), the editor's settings, a CI workflow and APP_ARCHITECTURE — pinning the newest package releases and naming any newer major than the set the skill was proven with; the layering rules W1–W5 and adding a feature or a component; plus react_vite.py (doctor, spec, generate, tokens, check). Portable — the folder works in any repo. Use when asked to set up, create or scaffold a React, Vite or TypeScript web app or dev environment, Playwright tests or Storybook, when adding a feature or a component to an app with src/features/ and src/components/ui/, when the design tokens' CSS must be written from DESIGN.md again, or when Node, Playwright's browsers or the app's layering are in question.
metadata:
  scope: portable
---

# React and Vite setup

How a React, Vite and TypeScript web app is set up with Playwright and Storybook from the web app spec, and how a
feature or a component is added to it. The principles and their reasons are kept in this skill at
[references/react-vite.md](references/react-vite.md) (cited `REACT_VITE_SETUP §n`); this page indexes them in one-line
rules and holds the steps. The app's facts come from the project's web app spec in `docs/` and its values from
`DESIGN.md`, which win over the reference, and the reference over this page.

**Portable.** This folder is self-contained and links to nothing outside itself: the reference, the templates
([templates/](templates/)) and the script ([scripts/react_vite.py](scripts/react_vite.py)). Copy it into any repo's
`.agents/skills/` (or `.claude/skills/`) and it works there: the script reads the doc prefix and the project's name
from `.agents/project.py` when the repo has one, and needs neither. It needs git, Python 3.9+, and Node 20 or newer to
run what it makes. In the agent-harness kit, the guard holds a new app's configs until docs/ has a spec, asks before
a browser install or a visual baseline update, and `verify.py run` runs the layering check (REACT_VITE_SETUP §10).

## When to use

- The person asks to set up, create or scaffold a React, Vite or TypeScript web app, Playwright tests or Storybook.
- A feature or a component is added to an app with `src/features/` and `src/components/ui/`.
- `DESIGN.md` changed and `src/styles/tokens.css` must be written again.
- Node, Playwright's browsers or a change across the app's layers is in question.

## Rules

### Do

1. **Check Node and the browsers first, and install neither without the person** — `react_vite.py doctor`; no usable
   Node: say where to get one and stop; missing browser builds: ask before `npx playwright install` (REACT_VITE_SETUP
   §1).
2. **Write the spec before anything else, with the defaults** — `spec --init`; tell the person each `[DEFAULT]` fact
   and pass the ones they name (REACT_VITE_SETUP §2).
3. **Ask about a fact that is unclear, never guess it** — a browser that is not an engine, an old Node, a shared port
   (REACT_VITE_SETUP §2).
4. **Pin the newest releases, and read the migration notes of any newer major `generate` names** — or pass
   `--versions tested` (REACT_VITE_SETUP §1).
5. **Keep the app's shape**: the shell composes, features never import each other, components know no feature, `lib/`
   and `hooks/` use no part above them (REACT_VITE_SETUP §4).
6. **Take every value from a token in `tokens.css`**, and decide a missing role in `DESIGN.md` first; write
   `tokens.css` again with `tokens --out`, never by hand (REACT_VITE_SETUP §5).
7. **Give every component a story file beside it**, a story per state with a play function — it is its docs and its
   test (REACT_VITE_SETUP §7).
8. **Find controls in tests by role and name**, as a person and a screen reader do (REACT_VITE_SETUP §6).
9. **Change a port, a browser or a size in the spec first**, then in the config that carries it (REACT_VITE_SETUP §2).

### Never

- **Generate before the spec exists.**
- **Overwrite a file that exists** — the script keeps it and says so; a change to it is a change of its own.
- **Break a layering rule, W1–W5** — features meet only in `src/app/` (REACT_VITE_SETUP §4).
- **Give a secret a `VITE_` name** — it ships in the bundle (REACT_VITE_SETUP §3).
- **Update a visual baseline, deploy, or install a browser without the person** — each is theirs to approve.
- **Add Husky in a repo with the kit** — it turns off the kit's pre-commit hook (REACT_VITE_SETUP §8).
- **Stop a dev server you did not start** — the person's may be the one on the port.

## Procedure

`R` is `python3 .agents/skills/react-vite-setup/scripts/react_vite.py`, from the repo root.

### Setting up an app

1. **Node.** `R doctor --latest`. No Node, or older than 20: tell the person how to install an LTS release and stop.
2. **The spec.** `R spec`. No spec: `R spec --init`, with `--title`, `--browsers` … for anything the person already
   named; tell them each `[DEFAULT]` fact; list the spec in the README. Facts missing or unclear: ask, write the answer
   to the spec, `R spec` again until nothing is missing.
3. **The brief.** No `DESIGN.md`: write one first with the design-system skill — `tokens.css` is written from it.
4. **Generate.** `R generate --dry-run` to show the person what it will write, then `R generate`. It writes the app,
   `src/styles/tokens.css`, `docs/<PREFIX>_APP_ARCHITECTURE.md`, and merges `.gitignore`; it never overwrites. Read
   each `note:` and `warning` line: a newer major to read up on, a role the brief lacks.
5. **Install.** `npm install`, then `R doctor`: the browser builds the project's Playwright needs. Missing: ask the
   person, then `npx playwright install <the spec's browsers>`.
6. **Check every layer.** `npm run check`, `npm run test:stories`, `npm run test:e2e`, `npm run build`, `npm run
   build-storybook`; read the first error, fix it, run again.
7. **In the agent-harness kit**, paste the settings block `generate` printed into `.agents/project.py` with the
   person's yes, fill in `build-run-test` and AGENTS.md's layering line, and list `APP_ARCHITECTURE` in the README
   (REACT_VITE_SETUP §10).
8. **On the target**: `npm run dev`, then each screen at the spec's sizes, in light and dark; what it looks like is
   the person's to judge.

### Adding a feature

1. `src/features/<name>/<name>.tsx` and its CSS module, shaped like `src/features/hello/`; its controls from
   `src/components/ui/`.
2. Render it from `src/app/` — never from another feature.
3. Its path through the app in `e2e/<name>.spec.ts`; `R check`, then the three test layers.

### Adding a component

1. In `DESIGN.md`'s components first when it is new to the product.
2. `src/components/ui/<name>.tsx`, `<name>.module.css` (every value a token) and `<name>.stories.tsx` — a story per
   state, a play function for what it does.
3. `R check`, then `npm run test:stories`.

## Checks

```sh
python3 .agents/skills/react-vite-setup/scripts/react_vite.py doctor --latest   # Node, browsers, newest releases
python3 .agents/skills/react-vite-setup/scripts/react_vite.py spec              # the spec's facts, and what it lacks
python3 .agents/skills/react-vite-setup/scripts/react_vite.py check             # the layering, W1–W5
python3 .agents/skills/react-vite-setup/scripts/react_vite.py --test            # the script's own cases
```

- [ ] (script) Node 20 or newer, and the browser builds the project's Playwright needs — `doctor`
- [ ] (script) The spec has every fact — `spec` exits 0
- [ ] (script) The layering rules **W1–W5** (REACT_VITE_SETUP §4) — `check` reports 0 hits
- [ ] `npm run check`, `npm run test:stories` and `npm run test:e2e` pass; `npm run lint` shows no warning
- [ ] `generate` named no `var(--…)` that `tokens.css` lacks
- [ ] The person heard each `[DEFAULT]` fact, and said yes before any browser install

## Traps

- **`generate` refuses with "No web app spec in docs/"** → no spec, or one that names no browser → `spec --init`
  (Do 2).
- **`Executable doesn't exist at …/chromium_headless_shell-<n>`** → the project's Playwright needs a newer browser
  build → `doctor`, then the install with the person's yes (Do 1).
- **The end-to-end tests pass against the wrong app** → another app's dev server holds the port → check the port
  first; give each app its own in its spec.
- More traps — a story that never fails, `tokens.css` and Prettier, the editor and the templates, Husky — in
  REACT_VITE_SETUP §11.

## Sources

| Topic | Where |
| --- | --- |
| The principles, the spec's facts, the app's structure, the rules | [references/react-vite.md](references/react-vite.md) |
| Vite's config, env variables, the dev server and preview | Vite documentation: Config, Env Variables and Modes |
| Vitest's projects and browser mode on Playwright | Vitest documentation: Projects, Browser Mode |
| Stories as tests, the a11y addon, docs pages | Storybook documentation: Vitest addon, Accessibility tests, Autodocs |
| Projects, `webServer`, browsers, screenshots | Playwright documentation: Test configuration, Browsers, Visual comparisons |
| axe's rules and tags | `@axe-core/playwright` README; Deque's axe-core rule descriptions |
| oxlint's rules and plugins | oxc documentation: Linter |
| Node's releases and LTS | nodejs.org, Previous Releases |
