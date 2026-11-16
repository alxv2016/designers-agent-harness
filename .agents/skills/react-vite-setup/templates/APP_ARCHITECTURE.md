# {{arch_title}}

How the web app is put together: `src/main.tsx` mounts the app shell, the shell composes the features, features build
their screens from the components in `src/components/ui/`, and every value comes from the design tokens. People read
it to know where new code goes; coding agents read it before they add a feature, a component or a dependency. Source
of truth: the code in `src/`; this doc says why it is shaped so. The ports, browsers and sizes are the web app spec's
({{spec_link}}).

**Stability.** Code comments cite this doc's `§n`. Do not renumber; add new material under the next free number.

| § | Section | Look here for |
| --- | --- | --- |
| 1 | [The shape](#1-the-shape) | The parts, and which may import which |
| 2 | [Rules](#2-rules) | Where code goes, and what never goes where |
| 3 | [Testing](#3-testing) | The three layers, and which one a change needs |
| 4 | [Adding a feature or a component](#4-adding-a-feature-or-a-component) | The steps for each |
| 5 | [Dependencies and versions](#5-dependencies-and-versions) | Node, the packages, the lock file |
| 6 | [Decisions](#6-decisions) | Why features never import each other, why a story is a test |

---

## 1. The shape

**`main.tsx` mounts the shell, the shell composes features, features use components, and everything may use `lib/`
and `hooks/` — every import points down this list, never up it, and never from one feature into another.**

| Part | Holds | May import |
| --- | --- | --- |
| `src/main.tsx` | The entry: the tokens and global styles, then the shell | `src/app/` |
| `src/app/` | The shell: the page's frame, providers, the router once there are pages, which feature fills which page | Features, components, `lib/`, `hooks/` |
| `src/features/<name>/` | One feature: its screens, its state, its styles, its tests | Components, `lib/`, `hooks/` — never another feature |
| `src/components/ui/` | The design system's components, each with its story file beside it | Other components, `lib/`, `hooks/` |
| `src/hooks/` | React hooks any part may use | `lib/` |
| `src/lib/` | Plain functions any part may use, with their unit tests | Nothing of the app's |
| `src/styles/` | `tokens.css`, written from `DESIGN.md`, and `global.css` — what every screen shares | — |
| `e2e/` | The end-to-end tests, which drive the app through a browser | Nothing of the app's |

`@/` is `src/` in every import (`vite.config.ts`, `vitest.config.ts`, `tsconfig.app.json`).

## 2. Rules

**Each part keeps to its job; `verify.py run` (or the `react-vite-setup` skill's check) fails the layering rules
W1–W5.**

### Do

1. **Take every colour, size and duration from a token** — `var(--color-text-secondary)`, never a literal; a role
   the brief lacks is decided in `DESIGN.md` first.
2. **Style a component with its own CSS module** beside it — `button.module.css` for `button.tsx`.
3. **Give every component in `src/components/` a story file beside it** — `<name>.stories.tsx`, one story per state
   (W4).
4. **Build a feature's controls from `src/components/ui/`**; a control made a second time becomes a component.
5. **Name a role and a label for every control** a test reaches — the tests find it as a person does.

### Never

- **Import a feature, or the shell, from a component** (W1).
- **Import one feature from another** — features meet in `src/app/` (W2).
- **Import a component, a feature or the shell from `src/lib/` or `src/hooks/`** (W3).
- **Give a secret a `VITE_` name** — every `VITE_` variable ships in the bundle, to every visitor (W5).
- **Edit `src/styles/tokens.css` by hand** — change `DESIGN.md`, then write it again.

## 3. Testing

**Three layers, each proving what the one below cannot: a function's result, a component's states, a person's
path through the app.**

| Layer | Runs | Proves | Command |
| --- | --- | --- | --- |
| Unit | `src/**/*.test.ts(x)`, in Node | A function's result | `npm test` |
| Stories | Every story, in Chromium | A component renders in each state, its play function passes, axe finds no violation | `npm run test:stories` |
| End to end | `e2e/*.spec.ts`, in each browser and size of the spec | A path through the app works, with no error, no axe violation and no sideways scroll at 320 px | `npm run test:e2e` |

## 4. Adding a feature or a component

**A feature is a folder in `src/features/` that the shell renders; a component is a file in `src/components/ui/`
with its story file.**

- **A feature**: `src/features/<name>/<name>.tsx` with its CSS module, shaped like `src/features/hello/`; render it
  from `src/app/`; give its path through the app an `e2e/<name>.spec.ts`.
- **A component**: `src/components/ui/<name>.tsx`, `<name>.module.css` and `<name>.stories.tsx` — a story per state,
  a play function for what it does; first in `DESIGN.md`'s components when it is new to the product.
- **The hello feature goes when the first real one lands**, with the smoke test's lines that name it.

## 5. Dependencies and versions

**Node is pinned to the spec's major; packages are declared in `package.json` and resolved once into
`package-lock.json`.**

- **Node** — `.nvmrc` and `engines`, from the spec. A new major is adopted on purpose: the spec first, then here.
- **Packages** — `npm install <package>` adds one and updates the lock; `package-lock.json` is committed and never
  edited by hand. A new major of Vite, Vitest, Storybook, Playwright or TypeScript is a change of its own, with its
  migration notes read.
- **Playwright's browsers** match the `@playwright/test` version: after it moves, `npx playwright install` again.

## 6. Decisions

- **Features never import each other.** A feature that reaches into another couples their release and their tests;
  the shell is the one place that knows them all, so a change to how two features meet is made there, in review.
- **A story is a test.** The Storybook addon for Vitest renders every story in a real browser, so documenting a
  component's state and testing it are one act, and the docs cannot drift from what the component does.
- **The end-to-end tests run against the production build in CI**, so a failure that only the build shows is caught.
