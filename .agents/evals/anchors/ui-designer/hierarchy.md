# ui-designer — Hierarchy, type pairing

What scores of 0, 2 and 4 look like on this dimension, for the `ui-designer` judge. Which text leads and which follows, and how a title pairs with its description, a label with its value. Its weight is in `.agents/evals/weights.json`; how it is scored is the judge's rubric, Quality (.agents/HARNESS.md §12).

**The rules it is held to: [TYPOGRAPHY §17](../../../skills/typography/references/typography.md#17-pairing-type-in-a-component)** — a pair's size step, its weights, the secondary never heavier, and hierarchy without colour or fine sizes (§17.3).

**Measured proxies — not built yet.** `PROXIES` in `.agents/project.py` names the project's screen audit for this judge once it exists (UI_REVIEW_RUBRIC §6 describes the pattern); until then the judge scores this dimension on its reading alone. `verify.py proxies --judge ui-designer` runs it; a value out of its range caps this dimension at 2.

**How to use it.** Find the level the work sits nearest, quote the evidence — a file and line, a screenshot, a measured value — and give 1 or 3 when it sits between two. The person's own examples, under From the person, outrank the ones written here.

## 4 — what good looks like

- A balance card — the hero is big by size alone (about 44 px, **regular**); a key and its value share one size, told apart by weight (value semibold) and side (value right, tabular).
- A transaction list — a title about 18 medium over its description about 15 regular, 1.2 : 1; each row's name medium over its category regular; the amount the one heavy thing in the row.
- An editorial empty state — the eyebrow the smallest, quietest text; the heading 1.75x body at medium weight on a tight line.
- What they share: two or three sizes per component; hierarchy from weight first and size last; the secondary text never heavier than the primary. On a display where the smallest size step is coarse and colour cannot carry it, a 4 is one top level per screen and every pair told apart by one property the display can draw (TYPOGRAPHY §17.3).

## 2 — acceptable, with a clear gap

- Readable, with one top level, but some pairs jump a full size step with nearly the same weight, or a description is as heavy as its title; four sizes on one screen.

## 0 — what fails it

- No order: every text one size and weight, a description larger than its title, or five or more sizes on one screen.
