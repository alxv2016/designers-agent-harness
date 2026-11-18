# UI Review Rubric

How a review of a UI change is scored — by the `ui-designer` agent in review mode, or anyone following the
`ui-designer` skill's review: the verdict, the evidence each result needs, and one item per rule the review checks.
People read it to know what a UI review will pass or block; coding agents read it before they score one.

**Where it lives.** In the `ui-designer` skill, beside the gates it checks — [its SKILL.md](../SKILL.md) and
[gates.md](gates.md) (DESIGN_GATES). The items cite the rules of the skills the review applies by name: `ui-designer`,
`accessibility`, `design-system`, `layout`, `typography`, `motion`, `touch-and-gesture`. A project may add items it
learned from what the person found on the target; they live with the project (in the agent-harness kit, the Learned
table in `.agents/rubrics/ui-designer.md`), and a review scores them too.

**Stability.** Cite this doc as `UI_REVIEW_RUBRIC §n`; cite an item by its number, `R1`–`R20`. Do not renumber; add an
item under the next free number.

| § | Section | Look here for |
| --- | --- | --- |
| 1 | [Verdict](#1-verdict) | When a review blocks, when it passes, what never blocks |
| 2 | [Evidence](#2-evidence) | What each result must show |
| 3 | [Items](#3-items) | R1–R20, each with the rule it rests on and the review step that scores it |
| 4 | [The report](#4-the-report) | The shape a review returns |

---

## 1. Verdict

**A review blocks when an item fails on an added or changed line, or a gate was skipped; otherwise it passes.**

- **blocking** — an item fails on an added or changed line against a skill's rule or the project's DESIGN.md, or a gate
  was skipped: a screen or component changed with no draft approved by name before the code that built it, or with no
  yes on the built screen — and no recorded "no visible change" or "design given".
- **pass** — every item passes, is n/a or unsure; should-fix findings and notes do not block. A pass never covers the
  walks on the target: they stay on the "Judge on the target" list.
- **The person's recorded decisions are settled** — in the kit, a decision in `verify.py status`; otherwise one in the
  change's record (DESIGN_GATES §3). The review notes it and never blocks on it. A line marked `token-exception` with
  its row in DESIGN.md's exceptions is not a finding.

## 2. Evidence

**A result without evidence counts as unsure.**

| Result | Shows |
| --- | --- |
| fail | The file and line, the line quoted, and the rule (the skill's Do or Never, or the DESIGN.md section) |
| pass | What was read or run: the files and lines checked, the record of yeses, the command and its hits on changed lines |
| unsure | What could not be settled, and what would settle it: the target, the person |
| n/a | Why the item does not touch this change |

## 3. Items

**One item per rule the review checks; the step column is the `ui-designer` skill's review step that scores it.**

The record of yeses is `verify.py status` in the kit, and the change's record otherwise (DESIGN_GATES §3).

| Item | Looks for | Review step |
| --- | --- | --- |
| R1 | Gate 1, the draft: the record shows the person's yes on a draft file unchanged since, given before the code that built the change — or a "design given" or "no visible change"; a request, silence or a reviewer's pass is never the yes (ui-designer Do 2, Never) | 2 |
| R2 | Built from the draft's values: the components, tokens and focus order in `<screen>_mock<n>.md` equal the code; a layout that differs came back as a new draft and a new yes (ui-designer Do 5) | 2 |
| R3 | Gate 2, the built screen: a yes on the side-by-side, the code unchanged since (ui-designer Do 6) | 2 |
| R4 | The script checks: the design check (DESIGN.md's pairs and tokens) at 0, and no hit from the token, accessibility, layout, typography, motion and touch checks or the project's lint on an added or changed line (ui-designer review step 1; design-system Checks) | 1 |
| R5 | Contrast: text 4.5:1, large text and non-text 3:1 against the colour painted, in every theme; only disabled, decorative and logotype exempt; no text dimmed with opacity (accessibility Do 1–3, Never) | 2 |
| R6 | Focus and input: every action reachable by keyboard — or by the device's encoder and keys — focus order follows reading order, a visible focus indicator, no trap; physical controls work without sight, grasping, force or two at once; and the focus model holds — the position apart from the ring, no ring from a tap, the next step from the last place, focus kept in view for the inputs that cannot see, the ring an outline apart from selection, each input one job (accessibility Do 4–5, Do 25–27, Do 29–30, Do 32) | 2 |
| R7 | Names and labels: every control has a name; inputs keep a visible label; images that mean something have a text alternative; headings, landmarks, the screen's title and language in code; where there is no screen reader, what it would say is carried on screen and in sound (accessibility Do 6, Do 11, Do 12, Do 24) | 2 |
| R8 | Target size, colour as the only signal, resize and reflow, reduced motion — travel removed, driven motion and waits still moving; and a device's status light more than colour, said on the screen too, at most three blinks a second (accessibility Do 7–10, Do 34) | 2 |
| R9 | Tokens: every value one of DESIGN.md's tokens, roles at the call site, no literal, every state its token, exceptions registered in DESIGN.md's exceptions; on a fixed panel, values chosen for that panel and every type role a font the product can draw, with the glyphs its strings use (design-system Do 2–8, Do 18–19) | 2 |
| R10 | Components: an existing one reused; a one-off moved to the shared components on its second caller; each control chosen by what it does — an action that cannot be undone is a danger-role button, never a list row, that asks first (design-system Do 10, Do 20; ui-designer Do 8) | 2 |
| R11 | DESIGN.md in the same change: a new token decided there first, a new pair in its contrast pairs, a new component in its components, an exception in its exceptions (design-system Do 4, 6, 8, 10) | 2 |
| R12 | Gate 3, the target: the evidence, a screenshot of each changed screen, the walks handed to the person and never claimed from code; the person's sign-off in the record — unsure while the review runs before it (ui-designer Gate 3) | 4 |
| R13 | Principles: the change follows DESIGN.md's principles — where two options both pass the rules and the brief ranks its principles, the higher-ranked one decides; a principle broken on purpose is the person's recorded decision (ui-designer Do 1; design-system Do 1) | 2 |
| R14 | Alternatives to pointer input: every gesture, drag, long press and hover has a tap or visible control that does the same, and a named screen-reader action where the platform has a reader — on a device with an encoder or keys, a control they reach; actions fire on release; hover and focus content can be dismissed, hovered and kept (accessibility Do 13–16, Never) | 2 |
| R15 | Hidden content, modals and announcements: hidden is inert, a modal returns focus to its opener, a composite widget is one stop (a Tab stop, or a group stop changed in edit mode under an encoder), status changes are announced, time limits pause, fields name their purpose and their errors, checked when the text is committed, both orientations work; media captioned, instructions and links that stand alone, navigation, names and help consistent across screens; no ring on arrival, and focus back or on when an overlay closes; only controls as stops; a toast that takes no focus (accessibility Do 17–23, Do 28, Do 31, Do 33) | 2 |
| R16 | Motion: each move has a frequency and a purpose; curve and duration are the project's tokens, exits shorter; grows from its trigger and near full size; one object on one clock; retargets, never restarts; cheap properties named; a designed reduced variant; the motion study approved before the build; no motion-check hit (M1–M9) on a changed line (motion Do 1–19, Never; ui-designer Do 10) | 2 |
| R17 | Touch and gesture: each gesture has its spec and the person's recorded yes on its prototype on the device; the platform's control, or a reason for a custom one; one axis claimed and the sheet hand-off right; release by distance or speed; system edges left alone; touch feedback kept, pressed delayed in scrolling lists; scroll never taken over; the layout clear of safe areas and the keyboard; on a device, the encoder and buttons an equal input; the throw from the last moments, no scroll taken for an edge swipe, decoration that takes no press; feedback from one vocabulary, after the input is accepted, success only once it happened, a wait shown and its outcome said; no touch-check hit (T1–T10) on a changed line. The input floors are R14 and R15's, never scored twice here (touch-and-gesture Do 1–25, Never) | 2 |
| R18 | Words: each changed string passes the four tests and its element's pattern — the meaning first, plain and short, a button named for its result, an error that says what happened and what to do, an empty state with one next action, success said only once it happened; one name for one thing; accessible names worded as the action; room for the longest translation, and on a device every glyph in the fonts; no string-check hit on a changed line; the person's yes on the copy draft when the words are the change (ux-content Do 1–18, Never) | 2 |
| R19 | Layout: the draft's layout spec tier by tier and the build equal to it; the window read, never the device; screen breakpoints only at the brief's tiers, mobile first; regions in their places and navigation in its tier's form, the same destinations in the same order; panes at or above their minimum width and the pane in use kept on a narrowing; whole columns, the container's cap and margins from the scale; every gap a spacing token, proximity grouping; density by whole steps above the minimum target; running text held to the measure; scroll, selection, input and focus kept through a resize; on a watch or a round or small panel, one purpose per screen, nothing in the curve or the corners, the list's ends reaching the centre; no layout-check hit (G1–G6) on a changed line (layout Do 1–19, Never) | 2 |
| R20 | Type: the draft's type spec and the build equal to it; every text a role from the brief's scale, used for its job, never a size or weight of its own; one top level and three or four sizes, ranked one property at a time, headings in code at their level; the system font or the brief's, at most two families; reading text not tightly set, capitals spaced; running text within the measure, start-aligned, justified only with hyphenation, wrapping before truncating; emphasis by weight, no bold italic, underline only on links, no light weights for reading; tabular figures where numbers change or align; at most one editorial treatment; every role in the platform's scaling unit, the hierarchy intact and nothing clipped at the largest text size; no typography-check hit (Y1–Y8) on a changed line (typography Do 1–17, Never) | 2 |

## 4. The report

**A review returns this shape, beginning with the Verdict line; one Rubric row per item, the project's learned items
included.**

```text
Verdict: pass | blocking — <n> blocking, <n> should-fix, <n> unsure

## Rubric
| Item | Result | Evidence |
| --- | --- | --- |
| R1 … L<n> | pass / fail / unsure / n/a | <quoted line, command output, or why> |

## Findings
- <blocking | should-fix | note> — `file:line` — rule broken (the skill's Do or Never) — fix; most severe first,
  accessibility highest; "No findings" when clean

## Judge on the target
- <the walks with each input, motion and timing, contrast on the real screen, how it feels — a pass never covers them>
```
