---
name: ux-designer
description: Decides and reviews how an experience works — the people, their tasks, the flow, the structure, the interaction model, states and errors — from the principles of human–computer interaction, carried in the skill — references/hci.md (usability in a context of use, ISO 9241-11; Nielsen's ten heuristics; Shneiderman's eight golden rules; ISO 9241-110's seven interaction principles; Norman's visibility, affordances, signifiers, mapping, feedback, constraints and conceptual model; the seven stages and the gulfs of execution and evaluation; direct manipulation; GOMS and the keystroke-level model; mental models; perception and attention; memory and cognitive load; decisions and complexity; movement and time; motivation and the peak-end rule; slips and mistakes; and every law on Laws of UX — Aesthetic-Usability, Choice Overload, Chunking, Cognitive Bias, Cognitive Load, Doherty Threshold, Fitts's, Flow, Goal-Gradient, Hick's, Jakob's, Common Region, Prägnanz, Proximity, Similarity, Uniform Connectedness, Mental Model, Miller's, Occam's Razor, Paradox of the Active User, Pareto, Parkinson's, Peak-End, Postel's, Selective Attention, Serial Position, Tesler's, Von Restorff, Working Memory, Zeigarnik — each with the decision it informs), references/methods.md (human-centred design, the Double Diamond, choosing a research method, interviews, personas and jobs to be done, journey maps, task analysis, card sorting, tree testing, heuristic evaluation, cognitive walkthrough, usability testing with five people, severity ratings 0–4, task success, SEQ and SUS, what an agent can and cannot do) and references/rubric.md (X1–X14); plus the UX brief template — on the web, phones, watches and embedded devices alike. Writes the UX brief the person approves before the ui-designer skill drafts the screen, plans research, and reviews a brief, a flow or a built experience. Portable — the folder works in any repo. Use when designing a new flow, feature or screen, deciding how something should work, structuring navigation or content, choosing an interaction model, handling states and errors, onboarding, planning a usability test or other research, running a heuristic evaluation or walkthrough, or asked "does this flow make sense?", "which law applies?" or "how should this work?".
metadata:
  scope: portable
---

# UX designer

How an experience works, decided before its screens are drawn and checked after they are built. The principles,
models and laws are kept in this skill at [references/hci.md](references/hci.md) (cited `HCI §n`), the research and
evaluation methods at [references/methods.md](references/methods.md) (`UX_METHODS §n`) and the review items at
[references/rubric.md](references/rubric.md) (`UX_REVIEW_RUBRIC`); this page holds the rules and the steps. The
product's own principles in its `DESIGN.md` win over this skill where they rank two good options; the references win
over this page.

**With the `ui-designer` skill.** This skill decides the task, the flow, the structure, the interaction model, the
states and the behaviour — the UX brief; the `ui-designer` skill draws the screen that carries them, in the project's
tokens and components, and builds it. For a new flow, feature or screen, the person's yes on the UX brief comes first,
and the `ui-designer` skill's draft follows it; a change to how an existing screen looks skips the brief. Each
reviews its own half: this skill the experience, the `ui-designer` skill the screen. The words are the `ux-content`
skill's; the floors the `accessibility` skill's; the layout, type, motion and gestures the `layout`, `typography`,
`motion` and `touch-and-gesture` skills'.

**Platforms.** The principles are about people and hold on every platform — the web, iOS, Android, a watch, an
embedded device with a screen, an encoder and buttons; the brief names the platform, its inputs and its setting.

**Portable.** This folder is self-contained and links to nothing outside itself (it names the rest of a kit in
backticks): the three references and the [UX brief template](templates/ux-brief.md). It has no script — an experience
is judged by reasoning and by people, not by a pattern in code. Copy it into any repo's `.agents/skills/` (or
`.claude/skills/`) and it works there. In the agent-harness kit, `verify.py approve <file> --kind ux` records the
person's yes on a brief, and the `ux-designer` agent applies this skill.

## When to use

- A new flow, feature or screen — before its screen is drafted: the UX brief.
- Deciding how something should work: the interaction model, the steps, the defaults, what can be undone.
- Structuring navigation or content: where things live and what they are called.
- States and errors: empty, loading, error, success, offline; what to prevent and how to recover.
- Onboarding, help, progress and the end of a task.
- Planning a usability test or other research; analysing what the person brings back.
- Reviewing a brief, a flow or a built experience — "does this make sense?", "which law applies?".

## Rules

### Do

1. **Start from named people, their task and their context** — who, what job, where, on what device and input
   (HCI §1; UX_METHODS §3, §4).
2. **Write the UX brief before the screen for a new flow, feature or screen**, from the template, and stop for the
   person's yes naming it (UX_METHODS §10).
3. **Map the whole flow** — every entry, step, decision, exit and back path; no dead ends; the top tasks shortest
   (HCI §2 H3).
4. **Choose the interaction model by the task, and state the conceptual model in one sentence** (HCI §4, §5.2).
5. **Follow conventions people already know; break one only with a reason written down** (HCI §6, §9 Jakob's law).
6. **Answer every action, within 400 ms or with a visible wait, in the person's terms** — a press sooner still, as the
   `touch-and-gesture` skill holds (HCI §2 H1, §10).
7. **Give every state a way out, undo where it can be, and an end that says the task is done** (HCI §3 S4–S7).
8. **Prevent slips with constraints, defaults and forgiving input; prevent mistakes with conventions and previews;
   ask first only for what cannot be undone** (HCI §12).
9. **Make the system carry the memory and the complexity** — recognition over recall, information carried across
   steps, chunks, defaults, at most two levels of disclosure (HCI §8, §9).
10. **Reduce choices where speed matters, and recommend one** (HCI §9 Hick's law, choice overload).
11. **Put frequent actions near and large, and offer experts accelerators novices never need** (HCI §2 H7, §10).
12. **Group what belongs together and make one primary action distinct** (HCI §7).
13. **Design the peak and the end; show progress honestly** (HCI §11).
14. **Put help where it is needed, in context** (HCI §11, paradox of the active user).
15. **Cite the principle behind each decision and each finding** — `HCI §2 H6`, `HCI §9 Tesler's law`.
16. **Label every claim about people as research or assumption, and name the research that would settle it**
    (UX_METHODS §11).
17. **Rate review findings 0 to 4, and say one agent is one rater** (UX_METHODS §8).

### Never

- **Draw or style the screen** — the look, tokens and components are the `ui-designer` skill's.
- **State what people do, think or feel as a finding without research** — write it as a prediction or an assumption.
- **Use a law against the person's interest** — artificial urgency, hidden costs, defaults that serve only the
  product, confirmations designed to wear people down (HCI §1).
- **Treat Miller's "seven, plus or minus two" as a limit on items** (HCI §8).
- **Add a confirmation where undo would do** (HCI §12).
- **Hide the only way to do something behind a gesture, a hover or a long press** — the `accessibility` skill's
  alternatives hold.
- **Take a request to build, a silence or a judge's pass as the person's yes on a brief.**

## Procedure

### Framing a flow — the UX brief

Input: a feature, a flow or a screen to design. Everything here is written in the scratchpad.

1. **Read what exists** — the product's principles in `DESIGN.md`, the flows and screens around this one, any
   research, analytics or support issues; the person's own words about the problem.
2. **Name the outcome, the people, their job and context**; mark each as research or assumption (UX_METHODS §3).
3. **List the top tasks with their frequency and risk** (UX_METHODS §4).
4. **Map the flow** — entries, steps, decisions, exits, back; a Mermaid flowchart when it branches.
5. **Place it in the structure** — where it lives, how people reach it, what things are called (UX_METHODS §5).
6. **Choose the interaction model and the defaults**, and write the conceptual model (HCI §4–§6).
7. **Design every state and error** — empty, loading, partial, error, success, offline; slips, mistakes, undo
   (HCI §12).
8. **Check the brief against the laws and heuristics** — write each decision with its principle; the rubric's X1–X14
   are the checklist (UX_REVIEW_RUBRIC §3).
9. **Write the open questions with concrete options**, and the research that would settle each.
10. **Show the brief and stop.** The person's yes names `<flow>_ux<n>.md` — with the kit, `verify.py approve
    <flow>_ux<n>.md --kind ux`. A change is a new draft and a new yes. Then the `ui-designer` skill drafts the screen
    from it.

### Planning research

1. **Write the question** — what decision it informs.
2. **Choose the method by the question** — say or do, why or how many, the stage (UX_METHODS §2).
3. **Name the people** — who, how many (five per group for a qualitative test), how to reach them (UX_METHODS §7).
4. **Write the tasks and the script** — realistic tasks, no leading words; for a test, what success is.
5. **Hand the plan to the person** — the agent does not recruit, observe or speak to participants.
6. **Analyse what comes back** — group the findings, rate severity, tie each to a principle, and update the brief.

### Reviewing an experience (read-only)

Input: a UX brief, a flow, a prototype, a built screen or a diff.

1. **Read the brief and the record first** — the person's decisions are settled and never block.
2. **Walk the top tasks as a new user** — the cognitive walkthrough's four questions at each step (UX_METHODS §6.2).
3. **Inspect against the heuristics and the laws** — X1–X14 (UX_REVIEW_RUBRIC §3), each finding with its step, what a
   person would experience, the principle, a severity and a fix.
4. **Return the report** in the rubric's shape, most severe first, with the research that would settle what
   inspection cannot.

## Checks

No script reads an experience; these are read.

- [ ] The brief names people, job, context, top tasks — each as research or assumption (Do 1, Do 16)
- [ ] The flow has every entry, step, decision, exit and back path; no dead end (Do 3)
- [ ] The interaction model and the conceptual model are stated (Do 4)
- [ ] Every state and error is designed; undo where it can be; confirmation only where it cannot (Do 7, Do 8)
- [ ] Each decision cites its principle or law (Do 15)
- [ ] The person's yes on the brief, naming the file, recorded before the screen was drafted (Do 2)
- [ ] A review's findings carry severity, step, principle and fix; the research to settle named (Do 17)

## Traps

- **The screen is drawn before anyone agreed how it works** → the brief was skipped for a new flow → write the brief,
  take the yes, then draft (Do 2).
- **The flow works on the happy path and nowhere else** → only the main path was mapped → map every state, error and
  exit (Do 3, Do 7).
- **"Users want X" with nobody asked** → an assumption written as a finding → label it, and name the study (Do 16).
- **A confirmation on every action, clicked through by habit** → confirmation used in place of undo → undo, and ask
  first only for what cannot be undone (Do 8).
- **A seven-item limit on a menu "because of Miller's law"** → the law is about memory span, not menus → chunk and
  order by use (HCI §8).
- **An onboarding tour nobody finishes** → help placed before the task → help in context, at the moment of need
  (Do 14).
- **A clever pattern people do not recognise** → a convention broken without a reason → follow the convention, or
  test the new one (Do 5).

## Sources

| Topic | Where |
| --- | --- |
| Principles, models, laws | [references/hci.md](references/hci.md) |
| Process, methods, measures, the brief | [references/methods.md](references/methods.md) |
| How a UX review is scored | [references/rubric.md](references/rubric.md) |
| The UX brief | [templates/ux-brief.md](templates/ux-brief.md) |
| Heuristics, mental models, errors, research methods, testing, severity | Nielsen Norman Group |
| The golden rules; direct manipulation | Ben Shneiderman, "The Eight Golden Rules of Interface Design"; *Designing the User Interface* |
| Affordances, signifiers, mapping, the seven stages, the gulfs | Don Norman, *The Design of Everyday Things* |
| The laws of UX | Laws of UX (Jon Yablonski), each law's page and its origins |
| Usability, interaction principles | ISO 9241-11 and -110, as described on Wikipedia |
| Human-centred design's principles and activities | ISO 9241-210:2019 — its introduction and table of contents, in ISO's free preview |
| The Double Diamond | Design Council |
| The keystroke-level model | Card, Moran and Newell, Communications of the ACM 23(7), 1980; its times and rules as given on Wikipedia, "Keystroke-level model" |
| GOMS, the cognitive walkthrough, SUS | Wikipedia — "GOMS", "Cognitive walkthrough", "System usability scale" |
