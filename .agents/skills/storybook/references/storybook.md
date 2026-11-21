# Storybook

How a component's stories are written so that people, tests and coding agents all read them well: the story file's
layout, covering every prop, one concept per story, the summaries agents read, each theme pinned, play functions and
the accessibility test, docs pages, the manifest agents query, and Storybook's MCP server. People read it to know what
a good story file holds; coding agents read it, through the `storybook` skill, before they write, review or set up
stories.

**Where it lives.** In the `storybook` skill, beside [its SKILL.md](../SKILL.md), with the story file's
[template](../templates/component.stories.tsx.tpl) and the [check](../scripts/story_check.py). The skill folder is
self-contained: copy it into any repo's `.agents/skills/` and these come with it.

**Platforms.** Storybook renders web components; its AI features — the manifest and the MCP server's docs tools — are
in preview, and the components manifest is generated for React frameworks, `@storybook/angular-vite` and
`@storybook/vue3-vite` (§10.6). Native iOS and Android components and LVGL screens have no Storybook; their states are
shown on the target.

**Stability.** Cite this doc as `STORYBOOK §n`. Do not renumber; add new material under the next free number.

| § | Section | Look here for |
| --- | --- | --- |
| 1 | [What a story is for](#1-what-a-story-is-for) | Docs, tests and agents' examples, from one file |
| 2 | [The story file](#2-the-story-file) | The template's layout, meta, naming, where the file sits |
| 3 | [Props](#3-props) | Args, argTypes and controls; covering every prop; what is not storied |
| 4 | [One concept per story](#4-one-concept-per-story) | What a story shows; names; edge cases |
| 5 | [Summaries and descriptions](#5-summaries-and-descriptions) | JSDoc on the component, each prop and each story; `@summary` |
| 6 | [Themes](#6-themes) | Light and dark: the theme switch, a story per theme, tokens |
| 7 | [Play functions and tests](#7-play-functions-and-tests) | Interaction tests by role and name; the accessibility test |
| 8 | [Docs pages and MDX](#8-docs-pages-and-mdx) | Autodocs, MDX summaries, content written in the file |
| 9 | [The manifest](#9-the-manifest) | What agents see; curating it with `!manifest` |
| 10 | [The MCP server](#10-the-mcp-server) | Installing it, the manifest, registering it, toolsets, tools, frameworks |
| 11 | [Agents' instructions](#11-agents-instructions) | What a project tells its agents about the MCP server |
| 12 | [Traps](#12-traps) | Symptom, cause, fix |
| 13 | [Sources](#13-sources) | Storybook's docs pages this rests on |

---

## 1. What a story is for

**A story renders a component in one state, with the args that make it, and that one file serves three readers: the
person browsing the docs, the test runner, and an agent looking for a usage example.**

- **Docs** — each story shows on the component's docs page with its source and controls.
- **Tests** — each story renders in a real browser as a test: its play function checks what the component does, and
  the accessibility addon checks what it is (§7).
- **Agents' examples** — the MCP server hands an agent the component's props and its first stories as usage examples,
  so a story should "demonstrate one concept or use case" and describe why to use it, not only what it shows
  (Storybook, "Best practices for using Storybook with AI").
- **Stories follow the design brief** — a component's states, sizes and variants come from the project's design brief
  and the component's own spec, and every value from a token by role.

---

## 2. The story file

**Every component has a story file beside it — `<component>.stories.tsx` — laid out as the skill's template: imports,
meta, the default story, one story per concept, a story per extra theme.**

- **Meta names the component** — `component: X`, so the docs page, the props table and the manifest find it (check
  SB1); `title` places it in the sidebar (`'UI/Button'`), grouped as the components folder is.
- **Meta's `args` hold what every story shares** — the minimum to render it as people meet it, and a `fn()` for each
  callback (§3).
- **`satisfies Meta<typeof X>`** keeps the args typed against the component's props (TypeScript).
- **The order:** `Default` first — the state people meet most often — then each concept (§4), then the theme stories
  (§6). The first three stories are the ones the MCP server shows an agent in full (§10.5), so put the most useful
  first.
- **Names in PascalCase, by the concept** — `Default`, `Disabled`, `Loading`, `WithIcon`, `LongLabel` — never by the
  value (`BlueBackground`).
- **CSF 3** (`export const Name: Story = { … }`) is the format the template uses; Storybook's preview "CSF Next"
  factory format holds the same rules.
- **The template:** [templates/component.stories.tsx.tpl](../templates/component.stories.tsx.tpl).

---

## 3. Props

**Every prop the component declares appears in the story file — as a shared arg, an argType with a control, or a story
of its own — so the controls can drive it and the docs explain it.**

- **Shared args in meta** — the required props, with realistic content from the product's own words, never "foo" or
  lorem ipsum.
- **Callbacks** — `onX: fn()` from `storybook/test` in meta's args, so the Actions panel logs each call and a play
  function can assert it (§7).
- **argTypes where the control Storybook infers is not the right one** — a union of strings as `inline-radio` or
  `select`, a number with its `min`, `max` and `step`, an icon picked from a `mapping`; a prop that only passes
  through, hidden with `table: { disable: true }`.
- **A story for each value that changes what a person sees or can do** — each variant, each state (`disabled`,
  `loading`, `invalid`, `selected`), each size when sizes are the concept (one `Sizes` story, §4).
- **Edge cases from the content** — the longest label in the longest translation, an empty value, an error message, a
  number at its limit.
- **Not storied:** attributes the component passes straight to its element (`className`, `aria-*` it forwards, native
  HTML attributes) — they are the platform's, documented by the element.
- **Prop types come from the component's TypeScript** — `typescript: { reactDocgen: 'react-docgen-typescript' }` in
  `.storybook/main.ts` gives the fullest props table and manifest; `react-docgen`, the default, is faster and less
  detailed.
- **The check:** SB3 flags a prop the component declares that no story mentions.

---

## 4. One concept per story

**Each story shows one concept; it may render several instances only when they all show that same concept.**

- **Good:** `Default` with no args; `Primary` with `primary: true`; `Disabled` rendering a disabled default and a
  disabled primary button side by side — both show "disabled".
- **Bad:** `SizesAndVariants` rendering three sizes and two variants — "demonstrates too many concepts at once"
  (Storybook, "Best practices for using Storybook with AI"). Split it: `Sizes`, `Outline`, `Text`.
- **A name that joins two concepts is a sign to split** — `…And…`, `All…` (check SB6); a pair that truly is one
  concept carries `story-exception` and its reason.
- **States a person meets, not code paths** — `Loading`, `Empty`, `Error`, `Offline`, taken from the design brief or
  the UX brief's states.
- **The manifest judges the rendered story** — it evaluates the story with every arg and decorator applied, so the
  concept is what shows, not how it is wired.

---

## 5. Summaries and descriptions

**Write a JSDoc comment on the component's export, on each of its props and above each story export — the docs page
shows them, and agents read their summaries to choose a component and an example.**

- **The component** — a JSDoc block above its export: what it is and when to use it; `@summary` for the short
  version agents get, otherwise they get a truncated description. Markdown is allowed (check SB4).

```tsx
/**
 * A button that runs an action on the current screen.
 * @summary for user interactions that do not navigate to another route
 */
export function Button(props: ButtonProps) { … }
```

- **Each prop** — one line on what it does: `/** The icon shown before the label */` (check SB4).
- **Each story** — a JSDoc block above the export saying why to reach for it, not what it shows: `/** @summary for the
  main action in a view */`. Without `@summary`, an agent gets the first 60 characters of the description (check
  SB2).
- **Words follow the project's voice** — sentence case, plain words, the product's names for things.

---

## 6. Themes

**Stories render with the app's own tokens in each theme the design brief gives: a theme switch in the toolbar for
people, and a story per extra theme so the tests run there too.**

- **The preview loads the app's token and global styles**, so a story looks as the app does.
- **A theme switch in the toolbar** sets what the app sets — `data-theme` on `<html>`, or a class — so anything a
  component portals out switches too. Either a toolbar global with a decorator that sets the attribute, or
  `@storybook/addon-themes`' `withThemeByDataAttribute` or `withThemeByClassName`; use the one the project has.
- **Every story renders in the default theme**; the switch shows any story in any theme.
- **A story per theme past the first pins it with `globals`** — `globals: { theme: 'dark' }` — so the accessibility
  test checks contrast in that theme too; tag it `'!manifest'`, since it teaches an agent nothing about usage
  (check SB5).

```tsx
/** The default in the dark theme, for the eye and the accessibility test */
export const Dark: Story = { globals: { theme: 'dark' }, tags: ['!manifest'] }
```

- **A state whose colours are its point** — error, selected, disabled — gets its own dark story when its contrast pair
  differs by theme.
- **No theme switch yet** — add one to the preview from the design brief's themes before writing theme stories; with
  one theme there is nothing to pin.
- **Never a colour in a story** — a background or a border set in a story file hides what the tokens do; a decorator
  for layout padding takes its space from a token.

---

## 7. Play functions and tests

**A play function checks what the component does, the way a person does it; the accessibility addon checks what it
is; both run as tests.**

- **Find elements by role and accessible name** — `canvas.getByRole('button', { name: 'Save' })` — as a person and a
  screen reader find them; a test id only where no role fits.
- **Act as a person** — `userEvent.click`, `type`, `keyboard`, `tab`; then assert what they would see or what reached
  outside: `expect(args.onSave).toHaveBeenCalledWith(…)`, the text shown, the state announced.
- **A callback mocked with `fn()` is checked in a play function** somewhere in the file (check SB7).
- **Keyboard too** — a story for the keyboard path where the component has one: Tab to it, Enter or Space, Escape.
- **The accessibility addon fails the test on any axe violation** when `parameters.a11y.test` is `'error'`, and runs
  in every theme story (§6).
- **The test runner** — `@storybook/addon-vitest` runs each story as a Vitest test in a browser; the MCP server's
  `test-run` tool runs it for an agent (§10.5).
- **A test holds when the internals change** — assert what the person observes, never the component's internal
  state or how it calls its helpers.

---

## 8. Docs pages and MDX

**Every component gets a docs page from its stories and props (`tags: ['autodocs']`), and an MDX page holds what a
story cannot — written out in the file, because agents read only what the file contains.**

- **Autodocs** — the component's summary, its props table and its stories, with source; set once in the preview's
  `tags`.
- **An unattached MDX page has a summary** — `<Meta title="Design tokens/Colours" summary="…" />`, with `Meta` from
  `@storybook/addon-docs/blocks`.
- **Write the content into the MDX itself** — the docs manifest comes from static analysis of the file, so a value
  imported from elsewhere (a `colors` object from the tokens) is not in it.
- **A page for people only** carries `tags={['!manifest']}` on its `Meta`.

---

## 9. The manifest

**The manifest is the JSON an agent reads about the Storybook — each component's props, description and stories, and
the docs pages — so what goes in it is curated: too little context and too much both hurt.**

- **Two manifests** — components, from the story files and the props; docs, from the MDX files.
- **The components manifest is off by default** — `features: { componentsManifest: true }` in `.storybook/main.ts`
  turns it on (§10.2).
- **Where to read it** — `/manifests/components.json` and `/manifests/docs.json` on the dev server (port 6006 by
  default) or a built Storybook; `/manifests/components.html` is the debugger, with generation errors and warnings.
  With `experimentalDocgenServer` on, the dev server returns 404 for the JSON routes — read a built Storybook or the
  debugger.
- **Every story has the `manifest` tag unless it is removed** — `tags: ['!manifest']` on a story leaves it out; on the
  meta, it leaves out the whole file.
- **Leave out what teaches no usage** — theme stories (§6), stories that exist only for a regression test, pages for
  people only.
- **Its schema is in preview** — "not yet stable and should not be considered a public API"; never parse it in a
  project's own scripts.

---

## 10. The MCP server

**Storybook's MCP server lets a coding agent read the components and their docs, find the stories a change affects,
and run the stories' tests, from the running Storybook.**

### 10.1 Installing it

- **The addon:** `npx storybook add @storybook/addon-mcp` — it adds `@storybook/addon-mcp` to the project's
  dependencies and to `addons` in `.storybook/main.ts`.
- **Its version matches Storybook's** — the addon's release requires the same minor release of `storybook` (10.6.8
  needs `^10.6.8`); upgrade every Storybook package together with `npx storybook@latest upgrade` first when it is
  behind.
- **The server runs with the dev server** — at `http://localhost:6006/mcp`, or the port the project's `storybook`
  script names; opened in a browser, it lists its tools and links to the manifest debugger.

### 10.2 The components manifest

- **Turn it on for the docs tools:**

```ts
// .storybook/main.ts
features: {
  componentsManifest: true,
},
typescript: {
  reactDocgen: 'react-docgen-typescript',
},
```

- **`@storybook/vue3-vite` also needs `experimentalDocgenServer: true`** under `features`; `@storybook/angular-vite`
  turns it on itself.

### 10.3 Registering it with the agent

- **Claude Code** — project scope, so every clone gets it: `claude mcp add --transport http storybook
  http://localhost:6006/mcp --scope project`, or in `.mcp.json` at the repo root:

```json
{
  "mcpServers": {
    "storybook": {
      "type": "http",
      "url": "http://localhost:6006/mcp"
    }
  }
}
```

- **Other agents** — Storybook's docs give `npx mcp-add --type http --url "http://localhost:6006/mcp" --scope project`,
  which asks for a server name and writes the agent's own config.
- **The server's name is how its tools are called** — `storybook` makes the tools `mcp__storybook__docs-list` and the
  rest in Claude Code.
- **Another hostname** — an agent that reaches Storybook through a proxy or a container's hostname needs it in
  `core.allowedHosts` in `.storybook/main.ts`.
- **The server answers only while Storybook runs** — start it with the project's `storybook` script; until then, the
  agent's client reports the server as unreachable.

### 10.4 Toolsets

- **Three toolsets, all on by default** — `dev`, `docs` and `test`, each tool appearing once its requirement is met.
- **Turn one off** in the addon's options:

```ts
// .storybook/main.ts
addons: [
  {
    name: '@storybook/addon-mcp',
    options: { toolsets: { dev: true, docs: true, test: true } },
  },
],
```

### 10.5 Tools

| Toolset | Tool | What it does | Needs |
| --- | --- | --- | --- |
| dev | `get-storybook-story-instructions` | How to write useful stories, which props to capture, how to write interaction tests | — |
| dev | `stories-changed` | The stories changed, or possibly affected, by local file changes | Change detection |
| dev | `stories-find-by-component` | The stories that render a component's source file, from a live dependency graph | — |
| dev | `stories-preview` | Previews stories in the agent's chat where it supports MCP Apps; links to them otherwise | — |
| dev | `review-create` | Pushes a review of the current changes and returns its page | The review feature |
| docs | `docs-list` | The index of components and unattached docs pages | A components manifest |
| docs | `docs-show` | A component's docs: props, its first three stories, an index of the rest, extra docs | A components manifest |
| docs | `docs-show-story` | A story's full source and docs, when `docs-show` is not enough | A components manifest |
| test | `test-run` | Runs the tests of the stories named, with accessibility findings where configured, and tells the agent to fix what fails | `@storybook/addon-vitest` |

### 10.6 Frameworks

| Framework | Turn on | Props in `docs-show` |
| --- | --- | --- |
| Every React framework — `react-vite`, `react-webpack5`, `nextjs`, `nextjs-vite`, `tanstack-react`, `react-native-web-vite` | `componentsManifest` | Yes |
| `@storybook/angular-vite` | `componentsManifest` | Yes |
| `@storybook/vue3-vite` | `componentsManifest`, `experimentalDocgenServer` | Yes |
| `@storybook/angular` (Webpack) and every other framework | No manifest | No |

- **The dev and test toolsets work in every Storybook project**; only the docs toolset needs a manifest.
- **A composed Storybook's manifests** are included in the server's answers when it has them.

### 10.7 Checking it works

1. Start Storybook with the project's script.
2. Open `http://localhost:6006/mcp` in a browser — it lists the tools.
3. Ask the agent "list all documented components" — it calls `docs-list` and names the project's components.

---

## 11. Agents' instructions

**A project that runs the MCP server tells its agents, in its agent instructions (`AGENTS.md`, or `CLAUDE.md`), to
build from what the server says rather than from memory.**

```markdown
## Storybook

When the Storybook dev server is running, use the `storybook` MCP server's tools for UI work:

- Never guess a component's props — read them with `docs-show` (find the component with `docs-list` first).
- Before writing or changing stories, read `get-storybook-story-instructions`.
- After changing a component or its stories, run `test-run` on the affected stories (`stories-find-by-component`
  finds them) and fix what fails, accessibility findings included.
- Follow the storybook skill: one concept per story, a summary on each, every prop covered, each theme pinned.
```

---

## 12. Traps

- **An agent invents a prop that does not exist** → it worked from memory, or the docs toolset is off → turn on the
  components manifest and tell agents to read `docs-show` first (§10.2, §11).
- **The props table is thin or empty** → `react-docgen` cannot follow the types → `reactDocgen:
  'react-docgen-typescript'` (§3).
- **`npx storybook add @storybook/addon-mcp` fails on a peer dependency** → the project's Storybook is a release
  behind the addon → `npx storybook@latest upgrade`, then add it (§10.1).
- **The MCP server shows as failed in the agent** → Storybook is not running, or runs on another port → start it, and
  match the URL to the `storybook` script's port (§10.3).
- **Contrast passes in light and fails in dark, unseen** → no story pins the dark theme → add the theme story (§6).
- **An agent copies a kitchen-sink story into a screen** → a story showed every variant at once → one concept per
  story (§4).
- **A docs page an agent reads is missing the token values** → the MDX imported them → write them into the file (§8).
- **A story looks right and the app does not** → the story set its own background or font → take every value from the
  app's tokens through the preview (§6).

---

## 13. Sources

| Topic | Where |
| --- | --- |
| Stories, summaries, prop extraction, MDX summaries, manifest curation | Storybook docs, "Best practices for using Storybook with AI" (`/docs/ai/best-practices`), version 10.6 |
| The MCP server: install, manifest, registering, tools, frameworks, verifying | Storybook docs, "MCP server overview" (`/docs/ai/mcp/overview`) |
| Toolsets and their options | Storybook docs, "MCP server API" (`/docs/ai/mcp/api`) |
| Manifests, their routes, the debugger, the preview schema | Storybook docs, "Manifests" (`/docs/ai/manifests`) |
| The addon's version and its peer dependency | The npm registry, `@storybook/addon-mcp` 10.6.8 |
| Args, argTypes, controls, `fn()`, play functions, globals, tags, autodocs | Storybook docs: Args, ArgTypes, Controls, Interaction tests, Toolbars and globals, Tags, Autodocs |
| The theme switch | Storybook docs and `@storybook/addon-themes` |
| Registering an HTTP MCP server in Claude Code | Claude Code docs, "Connect Claude Code to tools via MCP" |
