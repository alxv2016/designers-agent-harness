---
name: storybook
description: Writes, reviews and sets up a component's Storybook stories so people, tests and coding agents all read them well, carried in the skill (references/storybook.md) with a story file template (templates/component.stories.tsx.tpl) — the layout every story file follows (meta naming the component, shared args, Default first, one concept per story, a story per extra theme); every prop covered as an arg, an argType with the right control, or a story of its own; JSDoc with @summary on the component, each prop and each story; light and dark themes from the design brief, through the preview's theme switch and a story pinning each extra theme with globals; play functions that find elements by role and accessible name; the accessibility test in every theme; autodocs and MDX summaries; curating the manifest with !manifest; and Storybook's MCP server — @storybook/addon-mcp, the components manifest, react-docgen-typescript, registering it in .mcp.json, its dev, docs and test toolsets, and the instructions agents follow; plus story_check.py (SB1–SB7). Portable — the folder works in any repo. Use after creating or changing a component, when asked to write or fix stories, document a component in Storybook, add light and dark stories, review a story file, or set up Storybook's MCP server or manifest.
metadata:
  scope: portable
---

# Storybook

How a component's stories are written, reviewed and served to coding agents. The rules are kept in this skill at
[references/storybook.md](references/storybook.md) (cited `STORYBOOK §n`), the story file's layout at
[templates/component.stories.tsx.tpl](templates/component.stories.tsx.tpl), and the check at
[scripts/story_check.py](scripts/story_check.py); this page holds the rules and the steps. The project's design brief
decides the states, themes and values; the reference wins over this page — fix the page.

**With the other skills.** The `ui-designer` skill designs and builds the component; this skill writes its stories
after it exists, from the component's props and the states its approved draft names. The `accessibility` skill holds
the floors the stories' accessibility test enforces; the `design-system` skill the tokens and themes the preview
loads; the `ux-content` skill the words in a story's args. A React and Vite app set up by the `react-vite-setup` skill
already has Storybook, its preview, its theme switch and its story tests; this skill writes the stories and adds the
MCP server.

**Portable.** This folder is self-contained and links to nothing outside itself; it names the rest of a kit in
backticks. Copy it into any repo's `.agents/skills/` (or `.claude/skills/`) and it works there. In the agent-harness
kit, `verify.py run` runs the story check on the story files under `UI_PATHS`, and the `storybook` agent applies this
skill.

## When to use

- A component was just created or its props changed — its stories follow.
- The person asks for stories for a component, or for all components without them.
- Light and dark stories, or a theme switch in Storybook.
- Reviewing a story file, or a story check that fails.
- Setting up Storybook's MCP server, the components manifest, or agents' instructions for it.

## Rules

### Do

1. **Write every story file from the template's layout** — meta naming the component, shared args, `Default` first,
   one story per concept, a story per extra theme (STORYBOOK §2).
2. **Cover every prop the component declares** — a shared arg, an argType with the right control, or a story of its
   own; a `fn()` for each callback (STORYBOOK §3).
3. **Show one concept per story**, named by the concept; several instances only when they show the same one
   (STORYBOOK §4).
4. **Put a JSDoc comment on the component's export, each prop and each story**, with `@summary` saying why to use it
   (STORYBOOK §5).
5. **Render in the app's tokens and themes** — the preview's theme switch for people, a story pinning each extra theme
   with `globals` and `'!manifest'` for the tests (STORYBOOK §6).
6. **Check behaviour in a play function, finding elements by role and accessible name**; assert every `fn()` is called
   (STORYBOOK §7).
7. **Use the product's real words and the longest translation** for labels and edge cases, never placeholder text
   (STORYBOOK §3).
8. **Curate what agents see** — `'!manifest'` on theme and regression-only stories and people-only pages
   (STORYBOOK §9).
9. **With the MCP server running, read a component's props with `docs-show` before writing its stories, and run
   `test-run` on them after** (STORYBOOK §10.5, §11).
10. **Register the MCP server at project scope in `.mcp.json`**, named `storybook`, at the port the project's script
    uses (STORYBOOK §10.3).

### Never

- **Guess a prop** — read the component's type, or `docs-show` (STORYBOOK §11).
- **Show several concepts in one story** — `SizesAndVariants`, `AllStates` (STORYBOOK §4).
- **Set a colour, a font or a background in a story** — the preview's tokens decide (STORYBOOK §6).
- **Find an element by class name or DOM structure in a play function** (STORYBOOK §7).
- **Parse the manifest in the project's own scripts** — its schema is in preview (STORYBOOK §9).
- **Install the addon or change Storybook's version without the person's yes** — an install is a change to the
  project's dependencies.

## Procedure

`S` is `python3 .agents/skills/storybook/scripts/story_check.py`, from the repo root.

### Writing stories for a component

1. **Read the component** — its props type and their JSDoc, its states and variants; with the MCP server running,
   `docs-show` gives the same. Read the design brief's entry for it and the approved draft's states, if any.
2. **Fill in what the component lacks** — a JSDoc with `@summary` on its export and a line on each prop
   (STORYBOOK §5); that is a change to the component, in the same change.
3. **Copy the template beside it** as `<component>.stories.tsx`, dropping `.tpl`; rename, and fill meta's `args`
   and `argTypes` (STORYBOOK §2, §3).
4. **List the concepts** — each variant, each state, each edge case from the content — and write one story per
   concept, `Default` first, each with its summary (STORYBOOK §4, §5).
5. **Add the play functions** — the default interaction, the keyboard path, every `fn()` asserted (STORYBOOK §7).
6. **Add a story per extra theme** the preview offers (STORYBOOK §6).
7. **Run `S <file>`**, fix each hit; then the project's story tests (`npm run test:stories`, or `test-run` through the
   MCP server); fix what fails, accessibility findings included.
8. **Look at the docs page in each theme**, and show the person the stories that changed.

### Stories for every component without them

1. **Find the components with no story file beside them** — in a `react-vite-setup` app, its check's W4 lists them.
2. **Write each one as above**, one component at a time, each ending in `S <file>` and the story tests.

### Setting up the MCP server

Ask the person first: it adds a dependency and may upgrade Storybook.

1. **Check the Storybook version** in `package.json`; when it is behind the addon's release, `npx storybook@latest
   upgrade` first (STORYBOOK §10.1).
2. `npx storybook add @storybook/addon-mcp` (STORYBOOK §10.1).
3. **Turn on the components manifest and `react-docgen-typescript`** in `.storybook/main.ts` — and
   `experimentalDocgenServer` on `vue3-vite` (STORYBOOK §10.2).
4. **Register the server** as `storybook` in `.mcp.json`, at the port the `storybook` script names (STORYBOOK §10.3).
5. **Add the agents' instructions** to `AGENTS.md` (STORYBOOK §11).
6. **Check it** — start Storybook, open `/mcp`, ask the agent to list the documented components (STORYBOOK §10.7).

### Reviewing a story file (read-only)

1. `S <file>` — SB1–SB7.
2. **Read what the check cannot** — one concept per story, a summary that says why, each prop value that changes the
   screen with its story, play functions that check what a person observes.
3. **Report** each finding with the line, the rule (`STORYBOOK §n`) and the fix.

## Checks

```sh
python3 .agents/skills/storybook/scripts/story_check.py            # every story file, against the baseline
python3 .agents/skills/storybook/scripts/story_check.py FILE …     # some story files
python3 .agents/skills/storybook/scripts/story_check.py --test     # the self-test
```

- [ ] (script) `S` — prints `SB1–SB7 story layout — 0 hits`; baseline 0
- [ ] Every prop the component declares is covered (STORYBOOK §3; SB3)
- [ ] One concept per story, `Default` first, each with a summary saying why (STORYBOOK §4, §5; SB2, SB6)
- [ ] Each theme past the first has its pinned story, tagged `'!manifest'` (STORYBOOK §6; SB5)
- [ ] Play functions find elements by role and name, and every `fn()` is asserted (STORYBOOK §7; SB7)
- [ ] The story tests pass, accessibility included, in every theme story (STORYBOOK §7)
- [ ] With the MCP server: `docs-list` names the component, `docs-show` shows its props (STORYBOOK §10.7)

## Traps

- **An agent invents a prop** → the docs toolset is off or unused → the manifest on, `docs-show` first (Do 9).
- **Contrast fails in dark, and no test saw it** → no dark story → pin each theme (Do 5).
- **A kitchen-sink story copied into a screen** → several concepts in one story → split it (Do 3).
- **The addon will not install** → Storybook is a release behind → upgrade every Storybook package first.
- **The MCP server shows as failed** → Storybook is not running, or on another port → start it; match the URL.
- **A new prop with no story** → the component changed and its stories did not → SB3 names it; add the arg or story.

## Sources

| Topic | Where |
| --- | --- |
| Every rule, the MCP server, the manifest | [references/storybook.md](references/storybook.md) |
| The story file's layout | [templates/component.stories.tsx.tpl](templates/component.stories.tsx.tpl) |
| The check | [scripts/story_check.py](scripts/story_check.py) |
| Storybook's AI best practices, MCP server, manifests | Storybook docs, `/docs/ai/` — version 10.6 |
