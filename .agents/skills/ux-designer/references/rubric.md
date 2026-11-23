# UX Review Rubric

How an experience is scored in a UX review: when a review blocks and when it passes, what each result must show, one
item per principle the review checks, and the shape of the report. People read it to know what a UX review will pass
or block; coding agents read it, through the `ux-designer` skill and agent, before they review a UX brief, a flow or a
built experience.

**Where it lives.** In the `ux-designer` skill, beside [its SKILL.md](../SKILL.md), the principles in
[hci.md](hci.md) (HCI) and the methods in [methods.md](methods.md) (UX_METHODS). A project may add items it learned
from what people found in testing or on the target; they live with the project (in the agent-harness kit, the Learned
table in `.agents/rubrics/ux-designer.md`), and a review scores them too.

**Stability.** Cite this doc as `UX_REVIEW_RUBRIC §n`; cite an item by its number, `X1`–`X14`. Do not renumber; add an
item under the next free number.

| § | Section | Look here for |
| --- | --- | --- |
| 1 | [Verdict](#1-verdict) | When a review blocks, when it passes, what never blocks |
| 2 | [Evidence](#2-evidence) | What each result must show |
| 3 | [Items](#3-items) | X1–X14, each with the principle it rests on |
| 4 | [The report](#4-the-report) | The shape a review returns |
| 5 | [Quality](#5-quality) | The score beside the verdict: dimensions, anchors, proxies, the Score block |

---

## 1. Verdict

**A review blocks on a problem rated 3 or 4, or on a claim about people with no evidence; everything else is advice.**

- **Blocking** — a problem of severity 3 (major) or 4 (catastrophe) (UX_METHODS §8); a flow with no way out of a
  state (HCI §2 H3); an action that cannot be undone and does not ask first; a finding about what people do stated as
  fact with no research behind it.
- **Should-fix** — a problem of severity 2.
- **Note** — severity 1, and missed opportunities.
- **Never blocking** — a decision the person recorded; a trade-off the brief names with its reason; the screen's look,
  tokens and components, which are the `ui-designer` review's.

## 2. Evidence

**Every result names the step of the flow, the principle and what a person would experience.**

- **Pass** — the step or screen checked, and why it meets the item.
- **Fail** — the step, what happens there, the heuristic or law broken (`HCI §2 H6`, `HCI §9 Hick's law`), the
  severity, the fix.
- **Unsure** — what would settle it: a test with people, a device, a measure (UX_METHODS §2).
- **n/a** — the item does not apply to this change, and why.

## 3. Items

**One item per principle the review checks; each is scored on the brief, the flow or the built experience.**

| Item | Looks for |
| --- | --- |
| X1 | People and task: the brief names who, their job, the top tasks and the context of use — device, input, setting — and the change serves them (HCI §1; UX_METHODS §3, §4) |
| X2 | The flow is complete: every entry point, step, decision, exit and back path; no dead end; the top tasks take the fewest steps (HCI §2 H3; UX_METHODS §10) |
| X3 | Status and feedback: every action answered, within 400 ms or with a visible wait, a press sooner still (the `touch-and-gesture` skill's timing); the result shown in the person's terms; the gulf of evaluation narrow (HCI §2 H1, §5.1, §10) |
| X4 | Mental model and conventions: the conceptual model in one sentence, matching what people expect from similar products; a broken convention has its reason (HCI §6, §9 Jakob's law) |
| X5 | Control and closure: a way out of every state, undo where it can be, a clear end that says the task is done (HCI §2 H3, §3 S4, S6, S7) |
| X6 | Consistency: the same action, word and place for the same thing across the flow and the platform (HCI §2 H4, §3 S1) |
| X7 | Errors: slips prevented by constraints, defaults and forgiving input; mistakes by conventions and previews; confirmation only for what cannot be undone; recovery that keeps the input (HCI §12, §10 Postel's law) |
| X8 | Memory and load: recognition over recall, information carried across steps, content chunked, extraneous load removed (HCI §8) |
| X9 | Choices and complexity: few choices where speed matters, a recommended option, progressive disclosure at most two levels deep, complexity carried by the system (HCI §8, §9 Hick's, Tesler's laws) |
| X10 | Efficiency: frequent actions near and large, defaults and autofill, accelerators for experts that novices never need (HCI §2 H7, §10 Fitts's, Parkinson's laws) |
| X11 | Attention and grouping: related things grouped, one primary action distinct, nothing important styled like an ad, a change that matters cued (HCI §7) |
| X12 | Motivation and the ending: progress shown honestly, the peak and the end designed, no pressure against the person's interest (HCI §1, §11) |
| X13 | Help in context: guidance at the moment of need, never an up-front tour to sit through (HCI §2 H10, §11 paradox of the active user) |
| X14 | Evidence: each claim about people backed by research or labelled an assumption; the research that would settle each open question named; one agent's severity labelled as one rater's (UX_METHODS §11) |

## 4. The report

**A review returns this shape, beginning with the Verdict line; one Rubric row per item, the project's learned items
included.**

```text
Verdict: pass | blocking — <n> blocking, <n> should-fix, <n> unsure

## Rubric
| Item | Result | Evidence |
| --- | --- | --- |
| X1 … L<n> | pass / fail / unsure / n/a | <the step, and why> |

## Findings
- <severity 0–4> — <step or screen> — <what a person would experience> — <heuristic or law, HCI §n> — <fix>;
  most severe first; "No findings" when clean

## Research to settle
- <the open question> — <method, people, tasks> (UX_METHODS §2)
```

## 5. Quality

**Beside its verdict, a review scores how good the experience is: each quality dimension 0–4 against its anchors,
weighted to a score of 0–100.** The verdict says whether a problem is severe enough to block; the score says how far
the experience is from what the person calls good. The hand-over holds the score to the project's bar; below it the
person raises the work or accepts the score by name.

| Dimension | What it scores | Starting weight |
| --- | --- | --- |
| `flow` | Task flow: the top tasks in the fewest steps, no dead end (X2, X10) | 25 |
| `learnability` | Learnability: the next step obvious without being told; recognition over recall (X4, X8, X13) | 20 |
| `errors` | Error prevention and recovery: slips prevented, mistakes recovered with the input kept (X5, X7) | 20 |
| `feedback` | Feedback and status: every action answered, every wait shown, the result in the person's terms (X3) | 15 |
| `model` | Consistency with the product's model: one concept, word and key meaning one thing everywhere (X4, X6) | 20 |

- **The ux-designer's scoring follows the kit's HARNESS §12**, with the dimensions above. Outside the kit, the project keeps the ux-designer's weights, anchors and taste beside its rubric.
- A ux-designer review scores what the change touches; `verify.py audit` scores the whole product.
- Evidence for the ux-designer is the step of the flow and what a person would experience there.

The ux-designer's report ends with this block, after the Rubric table. In the kit, `verify.py review ux-designer <verdict> --score
dim=n,… --note "dim: why; …"` records it and computes the score.

```text
## Score — quality <n>/100 (bar <bar>)
| Dimension | Weight | Score | Evidence |
| --- | --- | --- | --- |
| flow … model | <weight> | 0–4 / na (capped: <metric>) | <the step, what a person would experience; the anchor held against> |

To raise: <dimension> — <what would lift it>   (below the bar only)
```
