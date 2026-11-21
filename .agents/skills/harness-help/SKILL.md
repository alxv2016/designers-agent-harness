---
name: harness-help
description: Answers questions about this repo's agent harness and hands back a prompt to send — which skill or agent fits a task, how the verify loop works and what comes next on the current task, why the guard blocked or asked, how to set up a fresh clone or adapt the template, how to steer with a principle's name, how to add a skill or an agent, and what to do when a run went wrong (exit 3, a refused hand-over, a skill that did not load, the stop reminder). Reads the repo's state first — the git hooks path, placeholders left in AGENTS.md and project.py, the demo DESIGN.md, the specs in docs/, verify.py status — and mentions it only where it changes the answer; links the file each answer came from; never starts the work. Use when the person asks "which skill do I use for…", "how do I…", "what's next?", "why was this blocked?", "how do I set this up?", "what can this harness do?", or types /harness-help.
disable-model-invocation: true
metadata:
  scope: project
---

# Harness help

Answers the person's question about this harness, hands them a prompt they can send, and links the file the answer
came from. For a help question it does not start the work: the person asked how, and a run spends real time and
tokens, so they send the prompt. A message that asks for work — "add a settings screen" — is not a help question: do
the work under [`verify-change`](../verify-change/SKILL.md), and say once that `/harness-help` answers questions
about the kit.

This page is a map to the files that hold the answers: [AGENTS.md](../../../AGENTS.md) (the rules and the index),
[.agents/README.md](../../README.md) (the kit in plain words), [HARNESS](../../HARNESS.md) (the guard, the checks, the
gate) and [AGENT_HARNESS](../../../docs/AGENT_HARNESS.md) (how a harness works). Read the file an answer routes to
before quoting it; where it and this page disagree, it wins — fix this page.

## When to use

- "Which skill or agent do I use for…?"
- "How do I…?" — set up, start a task, approve a mock, sign off, commit, add a skill.
- "What's next?" or "where does my task stand?"
- "Why did the guard block this?" or "why won't it hand over?"
- "What can this harness do?" — an overview for someone new.

## Rules

### Do

1. **Infer the need from the message and the conversation**; if it is still unclear, ask one multiple-choice question
   — get set up, start a task, pick a skill or agent, fix a run that went wrong, make the kit my own — and answer only
   the part they pick.
2. **Read the state that changes the answer, and mention it only when it does** (State, below).
3. **Lead with the answer**, then at most one example prompt in a code block, then the link to the file it came from.
4. **Read the file you route to before quoting it** — skills, agents and docs own the details.
5. **Make every file, doc section and URL a link the person can click**
   ([AGENT_HARNESS §10.4](../../../docs/AGENT_HARNESS.md#104-the-hand-over)).
6. **Keep it short** unless the person asked for the whole map.

### Never

- **Start the work a help question asks about** — hand over the prompt instead.
- **Run anything that writes state** — of `verify.py`, only `status`; `doctor` only when the person asks for it.
- **Tell the person to work round the guard** — a block is a rule from AGENTS.md; they approve it or run it themselves
  ([HARNESS §2](../../HARNESS.md#2-the-guard)).
- **Answer from this page alone when the file it routes to says otherwise.**

## Procedure

### State

Read only what the question needs; each line is read-only.

| Read | Command | Changes the answer when |
| --- | --- | --- |
| The git hooks | `git config core.hooksPath` | Not `.agents/githooks` — the pre-commit hook is not wired; the person runs `git config core.hooksPath .agents/githooks` once |
| The template filled in | `grep -c '<[A-Z][^>]*>' AGENTS.md .agents/project.py` | Placeholders remain — the bootstrap has not run ([AGENT_HARNESS §17](../../../docs/AGENT_HARNESS.md#17-bootstrap-prompt)) |
| The design brief | `head -5 DESIGN.md` | It still says DEMO — every value is an example to replace ([`design-system`](../design-system/SKILL.md)) |
| The specs | `ls docs/` | No hardware spec or web app spec — the setup skills write one first ([`esp-idf-setup`](../esp-idf-setup/SKILL.md), [`react-vite-setup`](../react-vite-setup/SKILL.md)) |
| The task | `python3 .agents/skills/verify-change/scripts/verify.py status` | A task is open — what it waits on: a run, a judge, the person's yes, the target, a sign-off |

### Get set up

1. Wire the git hooks once: `git config core.hooksPath .agents/githooks`.
2. Check the wiring: `python3 .agents/skills/verify-change/scripts/verify.py doctor`.
3. A fresh template: run the bootstrap prompt, which fills AGENTS.md and `project.py` from the repo and the person's
   answers ([AGENT_HARNESS §17](../../../docs/AGENT_HARNESS.md#17-bootstrap-prompt)).
4. Replace the demo DESIGN.md with the product's own brief ([`design-system`](../design-system/SKILL.md)).
5. Start a real task with its goal and how to tell it is done.

### Start a task

Every change runs through [`verify-change`](../verify-change/SKILL.md): `start`, a draft and the person's yes for
anything they must like, the edit, `run`, the judges it names, the target, the sign-off, `finish`. A good prompt states
the goal, how to tell it is done, and the proof to show; it does not list skills — the agent loads them by the task.

### Pick a skill or an agent

The skills load by their description; name one only to insist on it. The full index is
[AGENTS.md → Skills](../../../AGENTS.md#skills) and [→ Agents](../../../AGENTS.md#agents).

| The person wants to | Skill or agent |
| --- | --- |
| Decide how a new flow, feature or screen works | [`ux-designer`](../ux-designer/SKILL.md) — the UX brief, before the mock |
| Design, build or review a screen or component | [`ui-designer`](../ui-designer/SKILL.md) skill and agent — the three gates |
| Write stories for a component, or set up Storybook's MCP server | [`storybook`](../storybook/SKILL.md) skill and agent |
| Write the words on a screen | [`ux-content`](../ux-content/SKILL.md), the [`ux-content-writer`](../../agents/ux-content-writer.md) |
| Decide or change a design token | [`design-system`](../design-system/SKILL.md) |
| Meet the accessibility floors | [`accessibility`](../accessibility/SKILL.md) |
| Lay out a screen, set type, add motion or a gesture | [`layout`](../layout/SKILL.md), [`typography`](../typography/SKILL.md), [`motion`](../motion/SKILL.md), [`touch-and-gesture`](../touch-and-gesture/SKILL.md) |
| Set up a React and Vite app, or ESP-IDF firmware | [`react-vite-setup`](../react-vite-setup/SKILL.md), [`esp-idf-setup`](../esp-idf-setup/SKILL.md) |
| Understand how something works and why | [`teach`](../teach/SKILL.md) — type `/teach` |
| Know what a change could break beyond its diff | [`blast-radius`](../blast-radius/SKILL.md) |
| Steer the work with a rule — "apply prove it works" | [`principles`](../principles/SKILL.md) |
| Write or fix a doc | [`docs-authoring-and-sync`](../docs-authoring-and-sync/SKILL.md), the [`doc-writer`](../../agents/doc-writer.md) |
| Handle users' secrets in the product | [`secrets-handling`](../secrets-handling/SKILL.md) |
| Build, run, test, take a screenshot | [`build-run-test`](../build-run-test/SKILL.md), the [`target-runner`](../../agents/target-runner.md) |
| Commit | [`commit-message`](../commit-message/SKILL.md) — only when the person asks |
| Find the answers to the docs' open items | The [`open-items-curator`](../../agents/open-items-curator.md) |

Close calls:

- **`ux-designer` decides how it works; `ui-designer` decides how it looks** and builds it.
- **`teach` explains; `blast-radius` hunts breakage outside the diff; the `code-reviewer` scores the diff** against the
  project's rules.
- **`verify.py finding` is a lesson to route; `decision` is the person's word on this task; `dispute` is a judge's
  false alarm** ([`verify-change`](../verify-change/SKILL.md)).
- **The design skills hold their field's principles; [`principles`](../principles/SKILL.md) holds the work's** —
  proof, shape, sequencing, when to ask.

### Fix a run that went wrong

| Symptom | What it means, and what to do |
| --- | --- |
| The guard blocked or asked | A rule from AGENTS.md; approve it, or run it yourself — never reworded ([HARNESS §2](../../HARNESS.md#2-the-guard)) |
| `verify.py run` exited 3 | Three failed builds or tests in a row: the plan is wrong; the agent reports the shared premise and the failures, and you choose the next approach ([`verify-change`](../verify-change/SKILL.md) Do 3) |
| `finish` exits 1 | Something is open; it lists what — a judge, a yes, the target, a lesson ([HARNESS §5](../../HARNESS.md#5-the-hand-over-gate)) |
| "the file changed since the yes" | The approved mock was redrawn; look at the new one and say yes again ([`verify-change`](../verify-change/SKILL.md) Traps) |
| "came after the first run that built it" | The mock was approved after the code was built; the draft comes first ([`ui-designer`](../ui-designer/SKILL.md)) |
| The stop reminder asks about unrun changes | Edits no run has seen; the agent runs `verify.py run` or says why not ([HARNESS §10](../../HARNESS.md#10-the-stop-reminder)) |
| A skill did not load | Its description did not match the request; name the skill, or tune its description ([AGENT_HARNESS §7.1](../../../docs/AGENT_HARNESS.md#71-format)) |
| The reply claims success from a green build | Ask for the real result — "apply prove it works" ([`principles`](../principles/SKILL.md)) |

### Make the kit your own

- **A new skill or agent** — the agent asks whether it is `portable` or `project` first, and the guard holds the file
  until it carries `metadata: scope:` ([AGENT_HARNESS §7.3](../../../docs/AGENT_HARNESS.md#73-the-harnesss-skills)).
- **A lesson** — `verify.py finding --route …` turns it into a check, a rubric item, a guard rule, a skill line or a doc
  rule ([AGENT_HARNESS §9.2](../../../docs/AGENT_HARNESS.md#92-recording-what-was-learned)).
- **The project's own facts** — the checks, judges, UI paths and gates live in [project.py](../../project.py).

### Prompts worth copying

Swap in the real names; informal wording works.

- New screen: `add a <screen> where people can <task>. start with the UX brief, then a mock for my yes.`
- Bug: `<symptom> on <screen or board>. reproduce it first, then fix the cause and show me it on the target.`
- Stories: `write stories for <component>: its props, light and dark, one concept per story.`
- Understand: `/teach how <module> works and why it is built this way.`
- Risk: `what could this change break outside the diff? prove the one fact it's safe because of.`
- Steer: `apply prove it works. show me the screen on the target, not the build log.`
- Status: `where does my task stand, and what's waiting on me?`

## Checks

No script reads a help answer; these are read.

- [ ] The answer leads, with at most one prompt and the link to its source (Do 3)
- [ ] Any state mentioned changes the answer (Do 2)
- [ ] Nothing was started or written (Never)

## Traps

- **"How do I add a screen?" turned into a screen** → a help question read as work → answer and hand over the prompt.
- **A setup answer that skips the hooks** → the hooks path never read → read the state first (Do 2).
- **An answer that contradicts AGENTS.md** → this page drifted → the file wins; fix this page (Do 4).

## Sources

| Topic | Where |
| --- | --- |
| The rules and the index | [AGENTS.md](../../../AGENTS.md) |
| The kit in plain words | [.agents/README.md](../../README.md) |
| The guard, the checks, the gate | [HARNESS](../../HARNESS.md) |
| How a harness works | [AGENT_HARNESS](../../../docs/AGENT_HARNESS.md) |
| A help skill that routes and hands back a prompt | pstack's `poteto-help` skill, a Cursor plugin by Lauren Tan (MIT licence), rewritten for this kit |
