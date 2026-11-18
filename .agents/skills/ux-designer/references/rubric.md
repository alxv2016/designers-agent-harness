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
