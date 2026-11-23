# UX Content Review Rubric

How a review of an interface's words is scored — by the `ux-content-writer` agent in review mode, or anyone following
the `ux-content` skill's review: the verdict, the evidence each result needs, one item per step of the review, the
report's shape, and the quality score beside the verdict. People read it to know what a content review will pass or
block; coding agents read it before they score one.

**Where it lives.** In the `ux-content` skill, beside [its SKILL.md](../SKILL.md) and the rules it scores, in
[ux-content.md](ux-content.md) (UX_CONTENT). A project may add items it learned from what the person found on the
target; they live with the project (in the agent-harness kit, the Learned and Taste tables in
`.agents/rubrics/ux-content-writer.md`), and a review scores them too.

**Stability.** Cite this doc as `UX_CONTENT_RUBRIC §n` and an item by its number, `C1`–`C6`. Never renumber an item; a new one takes the next free number.

| § | Section | Look here for |
| --- | --- | --- |
| 1 | [Verdict](#1-verdict) | When a review blocks, when it passes, what never blocks |
| 2 | [Evidence](#2-evidence) | What each result must show |
| 3 | [Items](#3-items) | C1–C6, each with the rule it rests on and the review step that scores it |
| 4 | [The report](#4-the-report) | The shape a review returns |
| 5 | [Quality](#5-quality) | The score beside the verdict: dimensions, anchors, proxies, the Score block |

---

## 1. Verdict

**A review blocks when a changed string breaks a floor or misleads; everything else is advice.**

- **blocking** — a string check hit on a changed line, or a control with no accessible name. Also an error or a
  status that says nothing the person can act on, or claims success before it happened. Also a string cut off or
  drawn with a glyph the font does not hold, and words shipped without the person's yes where the words are the change.
- **pass** — every item passes, is n/a or unsure; a should-fix finding or a note does not block.
- **Never blocking** — a decision the person recorded (in the kit, `verify.py status`); the product's voice and case
  convention as its design brief sets them; the control or layout around the words, which are the `ui-designer`
  review's.

## 2. Evidence

**A result without evidence counts as unsure.**

| Result | Shows |
| --- | --- |
| fail | The file and line, the string quoted, the rule (`UX_CONTENT §n`, or `ACCESSIBILITY §n` for a floor) and a rewrite |
| pass | What was read or run: the strings checked, the string check's command and its count |
| unsure | What could not be settled, and what would settle it: the target, a screen reader, the person |
| n/a | Why the item does not touch this change |

## 3. Items

**One item per step of the `ux-content` skill's review.**

| Item | Looks for | Review step |
| --- | --- | --- |
| C1 | The string check: no hit (U1–U14) on a changed line (ux-content Checks) | 1 |
| C2 | The four tests: each changed string purposeful, short, human and of one meaning, the important words first (UX_CONTENT §2) | 2 |
| C3 | The element's pattern: a button named for its result, an error that says what happened and what to do, an empty state with one next action, success said only once it happened (UX_CONTENT §5) | 2 |
| C4 | Consistency: one name for one thing, one verb for one action, across the product and its word list (UX_CONTENT §4) | 3 |
| C5 | Accessible content: every icon-only control named as its action, every status read alone, inclusive and translatable (UX_CONTENT §6) | 4 |
| C6 | Room: the longest translation fits and wraps rather than cuts; on a device, every character in the font's glyph range (UX_CONTENT §2.4, §3.4) | 4 |

## 4. The report

**A review returns this shape: the Verdict line first, then one Rubric row per item, learned items included.**

```text
Verdict: pass | blocking — <n> blocking, <n> should-fix, <n> unsure

## Rubric
| Item | Result | Evidence |
| --- | --- | --- |
| C1 … L<n> | pass / fail / unsure / n/a | <the string quoted, the command and its count, or why> |

## Findings
- <blocking | should-fix | note> — `file:line` — "<string>" — rule (UX_CONTENT §n) — rewrite; most severe first;
  "No findings" when clean

## Judge on the target
- <voice and tone, how the words read on the real screen, what a screen reader speaks>
```

## 5. Quality

**Beside its verdict, a review scores how good the words are: each quality dimension 0–4 against its anchors,
weighted to a score of 0–100.** The verdict says whether a string breaks a floor; the score says how far the words are
from what the person calls good. The hand-over holds the score to the project's bar; below it the person raises the
words or accepts the score by name.

| Dimension | What it scores | Starting weight |
| --- | --- | --- |
| `clear` | Clear, one meaning: the important words first, in the person's words (C2, C4) | 30 |
| `short` | Short: as few words as hold the meaning, within the room (C2, C6) | 20 |
| `human` | Human, the product's voice: plain and calm, speaking to the person, never blaming (C2) | 20 |
| `next-step` | Says what happened and what to do next (C3) | 30 |

- **The ux-content-writer's scoring follows the kit's HARNESS §12**, with the dimensions above. Outside the kit, the project keeps the ux-content-writer's weights, anchors and taste beside its rubric.
- A ux-content-writer review scores what the change touches; `verify.py audit` scores the whole product.
- Evidence for the ux-content-writer is the strings quoted. `na` fits a dimension the change cannot touch, such as `next-step` for a change that touches only labels.

The ux-content-writer's report ends with this block, after the Rubric table. In the kit, `verify.py review ux-content-writer <verdict> --score
dim=n,… --note "dim: why; …"` records it and computes the score.

```text
## Score — quality <n>/100 (bar <bar>)
| Dimension | Weight | Score | Evidence |
| --- | --- | --- | --- |
| clear … next-step | <weight> | 0–4 / na (capped: <metric>) | <the strings quoted; the anchor held against> |

To raise: <dimension> — <what would lift it>   (below the bar only)
```
