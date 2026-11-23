# ui-designer — Spacing rhythm, grouping

What scores of 0, 2 and 4 look like on this dimension, for the `ui-designer` judge. The rhythm of space: what is glued together, what is set apart, and whether every value comes from the scale. Its weight is in `.agents/evals/weights.json`; how it is scored is the judge's rubric, Quality (.agents/HARNESS.md §12).

**The rules it is held to: [LAYOUT §7.1](../../../skills/layout/references/layout.md#71-the-ladder)** — pair gap < inset ≤ group gap < section gap — with the scale (§7.3) and no one-off values (§7.5).

**Measured proxies — not built yet.** `PROXIES` in `.agents/project.py` names the project's screen audit for this judge once it exists (UI_REVIEW_RUBRIC §6 describes the pattern); until then the judge scores this dimension on its reading alone. `verify.py proxies --judge ui-designer` runs it; a value out of its range caps this dimension at 2.

**How to use it.** Find the level the work sits nearest, quote the evidence — a file and line, a screenshot, a measured value — and give 1 or 3 when it sits between two. The person's own examples, under From the person, outrank the ones written here.

## 4 — what good looks like

- Carbon — 16 px padding beside a 32 px gutter (1 : 2), every value a multiple of 2, 4 or 8 on spacing-01 to -13 (carbondesignsystem.com, spacing overview and 2x grid).
- Atlassian — an 8 px base; 0–8 inside small components and between repeated items, 12–24 in cards, 32–80 between sections; spacing named as gap and inset (atlassian.design/foundations/spacing).
- A navigation list — a group's header nearer its first item than the gap between groups; one row rhythm. A transaction list — each name 2–4 px over its category, rows 12–24 apart: proximity does the grouping.
- The ladder: pair gap < inset ≤ group gap < section gap, each a clear step (2–3x) above the one inside it, every value a token on the scale.

## 2 — acceptable, with a clear gap

- Every value on the scale, but two levels too close — a pair's gap equal to the gap between pairs — or one or two one-off values (a 12 or a 20 off a 4, 8, 16, 24 scale).

## 0 — what fails it

- No rhythm: values picked per screen, a group's inside looser than the space around it, nothing tells which text belongs to which control.
