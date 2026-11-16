# React Vite Setup

How a React, Vite and TypeScript web app is set up with Playwright and Storybook, and why it is shaped as it is: the
Node it runs on and the versions it pins, the web app spec its configuration comes from, the files a project holds,
the app's structure and the rules that keep it, the design tokens as CSS, the three layers of tests, Storybook as the
components' documentation, lint and format, the editor and CI. People read it to know what the setup makes and why;
coding agents read it, through the `react-vite-setup` skill, before they set up an app or add a feature or a
component to one.

**Where it lives.** In the `react-vite-setup` skill, beside the steps, the templates and the script that apply it —
[its SKILL.md](../SKILL.md). The skill folder is self-contained: copy it into any repo's `.agents/skills/` and it
works there. The app's own facts — its name, its ports, its browsers and sizes — live in the project's web app spec
in `docs/`; its design values live in the project's `DESIGN.md`; this doc holds what is true of any such app. Source
of truth: the Vite, Vitest, Storybook and Playwright documentation win for how each tool behaves; `scripts/react_vite.py`
and the templates win for what the setup writes.

**Stability.** Cite this doc as `REACT_VITE_SETUP §n`. Do not renumber; add new material under the next free number.

| § | Section | Look here for |
| --- | --- | --- |
| 1 | [The environment](#1-the-environment) | Node and npm, the versions to pin, Playwright's browsers |
| 2 | [The web app spec](#2-the-web-app-spec) | Where the spec lives, its facts, the defaults and where they come from |
| 3 | [The project](#3-the-project) | The files, what is committed, the scripts, TypeScript, environment variables |
| 4 | [The app's structure](#4-the-apps-structure) | The shell, features, components, `lib/` and `hooks/`; the layering rules W1–W5 |
| 5 | [Styles and tokens](#5-styles-and-tokens) | `tokens.css` from DESIGN.md, CSS modules, themes, type in rem |
| 6 | [Testing](#6-testing) | The three layers, what each proves, the browsers, visual baselines |
| 7 | [Storybook](#7-storybook) | A story file per component, docs pages, the a11y addon, the theme toolbar |
| 8 | [Lint, format and hooks](#8-lint-format-and-hooks) | oxlint, Prettier, and why no Husky in the kit |
| 9 | [Editor and CI](#9-editor-and-ci) | VS Code, the debugger, the CI workflow |
| 10 | [In the agent-harness kit](#10-in-the-agent-harness-kit) | What the setup adds to the project's settings, its build skill and its docs |
| 11 | [Traps](#11-traps) | Symptoms, their causes and their fixes |

---

## 1. The environment

**The app is built with a Node already on the machine: the setup reads its version, pins the spec's major, and never
installs Node or a browser without the person.**

- **Node** — an even-numbered release in active or maintenance LTS. The stack needs 20 or newer (Vite needs 20.19 or
  22.12 and up). `react_vite.py doctor` reads `node --version`, the version managers present (nvm, fnm, volta) and
  `.nvmrc`; with no usable Node it says where to get one and stops. Installing Node is the person's: it changes their
  shell for every project.
- **npm** — the package manager Node ships with; `package-lock.json` is committed, and `npm ci` installs from it.
- **The packages' versions.** `generate --versions latest` (the default) asks the npm registry for each package's
  newest release and writes it as a range — `^` for most, `~` for TypeScript, which changes behaviour in minor
  releases. A package whose newest major is past the set the skill was last proven with together (`TESTED` in the
  script) is named, so its migration notes are read; `--versions tested` takes that set instead. `@types/node`
  follows the spec's Node major. Offline, the tested set is used and said so.
- **Playwright's browsers** are downloads of their own — Chromium, its headless shell, WebKit, Firefox — into a cache
  in the home folder (`~/Library/Caches/ms-playwright` on macOS, `~/.cache/ms-playwright` on Linux). Each Playwright
  release drives one build of each; `doctor` compares the builds the project's Playwright needs with the cache and
  names the missing ones — Chromium always, since the stories run in it. `npx playwright install <browsers>`
  downloads them, with the person's yes: it is hundreds of megabytes outside the repo.

## 2. The web app spec

**The app's configuration comes from a web app spec in `docs/`; `spec --init` writes it with the defaults, each
tagged `[DEFAULT]`, so the person sees what was chosen for them and names anything else.**

- **Which doc it is.** A doc in `docs/` named like a web app spec (`*WEB*APP*SPEC*`, `*WEB*SPEC*`, `*APP*SPEC*`) that
  names a browser engine outside a template's `<…>` placeholders. Its Facts table — `| Fact | Value | Source |` — is
  read by its rows; the first row for a fact wins and a second is reported.
- **The facts, and the defaults.** The defaults are a working app's — its Node, its servers' ports, and the sizes its
  mocks are drawn at, in the engines of Chrome and Safari:

| Fact | Default | Carried by |
| --- | --- | --- |
| Name | The repo folder's name | `package.json` |
| Title | The kit's project name, else the folder's | `index.html`, Storybook's introduction |
| Language | `en` | `<html lang>` (WCAG 3.1.1) |
| Node | `22` | `.nvmrc`, `engines`, CI |
| Dev server, preview and Storybook ports | `5173`, `4173`, `6006` | `vite.config.ts`, the `storybook` script, `.vscode/launch.json` |
| Browsers | `chromium, webkit` | Playwright's projects; CI's browser install, which adds Chromium when the spec has none, since the stories run in it |
| Viewports | `390x844, 1280x800` | Playwright's projects: one per browser and size |

- **A fact the person names** is passed to `spec --init` (`--title`, `--browsers`, `--viewports` …) and tagged
  `[PERSON]`; one they confirm later has its tag changed by hand. A value that is unclear — a browser that is not an
  engine Playwright drives, a Node older than 20, two servers on one port — is asked, never guessed.
- **The spec first, then the config.** A port, a browser or a size changes in the spec, then in the file that carries
  it, so the spec stays true.

## 3. The project

**A React and Vite app is a Node package with its entry page, its source, its configs and its tests; the setup
writes each once and never overwrites a file that exists.**

| File | Holds | Committed |
| --- | --- | --- |
| `package.json`, `package-lock.json` | The scripts, the dependencies, the resolved versions | Yes |
| `.nvmrc` | The Node major | Yes |
| `index.html` | The page: its language, its title, the root element, the entry script | Yes |
| `vite.config.ts` | The React plugin, the `@/` alias, the strict ports | Yes |
| `vitest.config.ts` | The `unit` and `storybook` test projects | Yes |
| `playwright.config.ts`, `e2e/` | The end-to-end tests and their projects | Yes |
| `.storybook/` | Storybook's config and the preview every story renders in | Yes |
| `tsconfig.json`, `tsconfig.app.json`, `tsconfig.node.json` | TypeScript: the app (DOM, JSX, bundler resolution) and the configs and tests run by Node | Yes |
| `src/`, `public/` | The app and its static files | Yes |
| `node_modules/`, `dist/`, `storybook-static/`, `playwright-report/`, `test-results/`, `*.tsbuildinfo` | Installs, builds and reports | No |

- **The scripts.** `dev`, `build` (`tsc -b`, then `vite build`), `preview`, `typecheck`, `lint`, `format`,
  `format:check`, `test` (unit), `test:stories`, `test:e2e`, `storybook`, `build-storybook`, and `check` — the four
  fast ones in a row.
- **Strict ports.** `server.port` and `preview.port` are fixed with `strictPort`, and Storybook runs with
  `--exact-port`: a busy port fails loudly instead of moving to one the tests, the debugger and other agents do not
  know.
- **TypeScript checks, Vite builds.** Vite strips types without checking them; `tsc -b` checks both configs, and the
  build runs it first. `verbatimModuleSyntax` and `erasableSyntaxOnly` keep every file strippable as it is.
- **Environment variables.** Vite exposes a variable to the app only when its name starts with `VITE_`, and compiles
  it into the bundle every visitor downloads — so every `VITE_` variable is public. A secret never gets a `VITE_`
  name: a key the app needs stays on a server (W5). Local values go in `.env.local`, which is never committed and which
  agents never read. The template ships no `.env.example`: the kit's Claude Code settings deny every `.env.*` file to
  the agent, so the person writes one when the app needs it.

## 4. The app's structure

**`main.tsx` mounts the shell, the shell composes features, features use components, and anything may use `lib/` and
`hooks/` — every import points down that list, never up it, and never from one feature into another.**

- **`src/app/`** is the shell: the page's frame, providers, the router once there is a second page, and which feature
  fills which page. It is the one place that knows every feature.
- **`src/features/<name>/`** is one feature — its screens, state, styles and tests. A feature reaches another only
  through the shell, so each can change, be tested and be removed alone. The template's `hello` feature has this
  shape.
- **`src/components/ui/`** holds the design system's components, each with its CSS module and its story file beside
  it. A component knows no feature.
- **`src/lib/`** holds plain functions with their unit tests, and **`src/hooks/`** React hooks; both use no part of
  the app above them.
- **`@/` is `src/`** in every import, so a file's imports read the same wherever it sits.

The layering check, `react_vite.py check`, holds these rules:

| Rule | Fails when |
| --- | --- |
| W1 | A file in `src/components/` imports from `src/features/` or `src/app/` |
| W2 | A file in one feature imports from another feature |
| W3 | A file in `src/lib/` or `src/hooks/` imports a component, a feature or the shell |
| W4 | A component in `src/components/` has no `<name>.stories.tsx` beside it |
| W5 | A `VITE_` variable named like a secret (`SECRET`, `PASSWORD`, `PRIVATE`, `TOKEN`, `KEY`, `AUTH`, `CREDENTIAL`) is in `src/`, `index.html` or a mode's env file a project may commit (`.env.example`, `.env.production`, `.env.development`, `.env.staging`, `.env.test`) — a public one, such as a referrer-locked maps key, carries `secret-exception` and its reason on the line. The check prints the variable's name, never its value, and never reads `.env` or `*.local` |

## 5. Styles and tokens

**Every value a screen paints comes from `DESIGN.md` through `src/styles/tokens.css` — a custom property per role, a
block per theme — and each component styles itself with a CSS module of `var(--…)`.**

- **`tokens.css` is written from the brief.** `react_vite.py tokens` reads every `| Token | … |` table in `DESIGN.md`:
  a `Light` / `Dark` column becomes a theme, a `Value` column one value for every theme, and other columns parts of
  one token (`text.body` → `--text-body-size`, `--text-body-line-height`, `--text-body-weight`). The name is the role
  in CSS spelling (`color.text.secondary` → `--color-text-secondary`), so the design check finds each one.
- **Themes.** The first theme is `:root`; another is `[data-theme='<name>']`; a dark theme also follows the system's
  setting unless the first theme is chosen. Each block sets `color-scheme`, so form controls and scrollbars match.
- **Type in rem.** A type token's size and line height are written in rem, so text follows the browser's text-size
  setting (WCAG 1.4.4); spacing stays in the brief's px.
- **As Prettier writes it.** Hex in lowercase and strings in single quotes, so the format check passes; the design
  check matches a colour in any case.
- **A role the brief lacks** is decided in `DESIGN.md` first. `generate` names every `var(--…)` the app's CSS uses
  that `tokens.css` does not set. A template reaches for a role the starter brief may not have only with a fallback
  (`var(--border-width-focus, 2px)`), never with a colour.
- **The focus ring** is global — `:focus-visible`, the brief's focus colour — so every control has it, and a tap or a
  click shows none.
- **`tokens.css` is never edited by hand.** The brief changes, then `react_vite.py tokens --out src/styles/tokens.css`
  writes it again.

## 6. Testing

**Three layers, each proving what the one below cannot: a function's result in Node, a component's states in a
browser, a person's path through the app in every browser and size the spec names.**

| Layer | Runs | Proves | Command |
| --- | --- | --- | --- |
| Unit | `src/**/*.test.ts(x)`, in Node, with Vitest | A function's result | `npm test` |
| Stories | Every story, in Chromium, with Vitest's browser mode on Playwright | Each state renders, its play function passes, axe finds no violation | `npm run test:stories` |
| End to end | `e2e/*.spec.ts`, with Playwright, in each browser × size | A path works with no error or failed request, no WCAG A or AA violation axe can find, no sideways scroll at 320 px | `npm run test:e2e` |

- **One Vitest config, two projects.** `vitest.config.ts` holds `unit` and `storybook`; it is apart from
  `vite.config.ts` so a test run never takes the dev server's fixed port.
- **Stories are tests.** Storybook's Vitest addon turns each story into a test: it renders the story, runs its play
  function, and — with the a11y addon's `test: 'error'` — fails on any axe violation. Storybook 10 applies the
  preview's annotations itself; no setup file is needed.
- **The smoke test.** `e2e/smoke.spec.ts` is the shape every page's test starts from: no page error, console error or
  failed request; the main heading by its role and name; axe on WCAG 2.0–2.2 A and AA; the page at 320 px wide with
  nothing wider than the viewport (WCAG 1.4.10); and a screenshot attached to the report as evidence.
- **Locally against the dev server, in CI against the build.** Locally Playwright reuses a dev server already on the
  port; in CI it builds the app and tests `vite preview`, so a failure only the build shows is caught.
- **Tests find what a person finds** — by role and accessible name, never by class or test id where a name exists.
- **Visual baselines** (`toHaveScreenshot`) are added per screen once its look is approved. Updating one —
  `--update-snapshots` — accepts a new look, so it is the person's yes, as the built screen is; baselines differ by
  platform, so they are made where CI runs.

## 7. Storybook

**Storybook is the components' documentation: every component in `src/components/` has a story file beside it, each
state a story, rendered with the app's own tokens in each theme, and every story runs as a test.**

- **A story per state.** `button.stories.tsx` holds `Rest`, `Disabled` and the rest of the brief's states for the
  `Button`; a play function checks what the component does.
- **Docs pages are written for every component** (`tags: ['autodocs']`): its props, its stories and their source.
  `src/stories/Introduction.mdx` says where values and code live.
- **The preview loads `tokens.css` and `global.css`**, and its theme toolbar lists the brief's themes, setting
  `data-theme` on `<html>` as the app does, so anything a component portals out switches too.
- **The a11y addon** shows axe's findings in the panel and fails a story's test on any of them.
- **`staticDirs` serves `public/`**, so a story logs no 404 for the favicon.

## 8. Lint, format and hooks

**oxlint finds the bugs and the accessibility misses; Prettier owns the format; the kit's pre-commit hook runs at a
commit, not Husky.**

- **oxlint** with the `react`, `typescript`, `oxc` and `jsx-a11y` plugins: the rules of hooks, components only in a
  component file, and a native element over a role (`<output>` over `role="status"`). A warning is fixed, not kept.
- **Prettier** — no semicolons, single quotes — over everything but the docs, the kit and what tools write.
- **No Husky in the kit.** Husky's `prepare` script points `core.hooksPath` at `.husky/`, which turns off the kit's
  own pre-commit hook. In the kit, the checks run through `verify.py run` and the kit's hook; in a repo without the
  kit, Husky and lint-staged may run `oxlint` and `prettier --write` on the staged files.

## 9. Editor and CI

**The editor formats as Prettier does and debugs in Chrome on the spec's ports; CI runs every check on every pull
request with nothing secret.**

- **VS Code** — `.vscode/settings.json` formats on save with Prettier; `extensions.json` recommends oxc, Prettier,
  Playwright and Vitest; `launch.json` opens Chrome with the debugger on the app's and Storybook's ports.
- **CI** — `.github/workflows/web.yml`: Node from `.nvmrc`, `npm ci`, the spec's browsers with their system
  libraries, then the types, lint, format, unit tests, story tests, end-to-end tests and the Storybook build; the
  Playwright report is kept as an artifact.

## 10. In the agent-harness kit

**In a repo with the kit, the setup also fills in the project's settings, its build skill and its docs; the kit's
own gates for a web app — the hold on a new app with no spec, the browser install, visual baselines, deploys — are
its guard's, set out in its `HARNESS` doc.**

- **`.agents/project.py`** (the guard asks before it is edited) — `generate` prints the block to paste: `CODE_PATHS`,
  `UI_PATHS`, `TOKEN_FILES` (`src/styles/tokens.css`), `UX_STRINGS` with the app's title as a name, the npm and Node
  hosts in `ALLOWED_HOSTS` and `.codex/config.toml`, `CHECKS` for types, lint, format, unit, stories, end to end and
  the build, and `TARGET`.
- **`build-run-test`** is filled in with the commands: `nvm use`, `npm ci`, the browsers with the person's yes,
  `npm run dev` and `npm run storybook` on their ports, the screenshots at the spec's sizes.
- **Docs** — the spec and `APP_ARCHITECTURE` are listed in the README; AGENTS.md's layering line says how the parts
  may import each other (§4).
- **`verify.py run`** runs the layering check when `src/` changes in a React and Vite app.

## 11. Traps

- **`browserType.launch: Executable doesn't exist at …/chromium_headless_shell-<n>`** → the project's Playwright
  drives a newer browser build than the cache holds → `doctor` names the builds; `npx playwright install <browsers>`,
  with the person's yes.
- **The end-to-end tests pass against the wrong app** → another project's dev server holds the port, and Playwright
  reuses whatever answers there → check the port before the run; the app's own ports are the spec's, so two apps on
  one machine get different ones.
- **`Port 5173 is in use`** → a dev server already runs — the person's, or another agent's → use it, never stop a
  process you did not start; or change the port in the spec, then in the config.
- **A story passes that should fail** → its play function never ran, or the a11y addon is not in `.storybook/main.ts`
  → break a story on purpose once and see it fail.
- **`npm run format:check` fails on `tokens.css`** → it was written by hand or by an older script → write it again
  with `react_vite.py tokens --out src/styles/tokens.css`.
- **The editor shows errors in the skill's templates** → they are templates, with no packages installed beside them;
  configs whose placeholders would read as broken carry `.tpl` → judge the generated app, not the templates.
- **The kit's pre-commit hook stopped running** → Husky's `prepare` script moved `core.hooksPath` → `git config
  core.hooksPath .agents/githooks`, and take Husky out (§8).
