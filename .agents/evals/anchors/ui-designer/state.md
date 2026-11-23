# ui-designer — Clarity of state and feedback

What scores of 0, 2 and 4 look like on this dimension, for the `ui-designer` judge. Whether the person can tell, at a glance, what is chosen, focused, disabled, pending or done — and why. Its weight is in `.agents/evals/weights.json`; how it is scored is the judge's rubric, Quality (.agents/HARNESS.md §12).

**Measured proxies — not built yet.** `PROXIES` in `.agents/project.py` names the project's screen audit for this judge once it exists (UI_REVIEW_RUBRIC §6 describes the pattern); until then the judge scores this dimension on its reading alone. `verify.py proxies --judge ui-designer` runs it; a value out of its range caps this dimension at 2.

**How to use it.** Find the level the work sits nearest, quote the evidence — a file and line, a screenshot, a measured value — and give 1 or 3 when it sits between two. The person's own examples, under From the person, outrank the ones written here.

## 4 — what good looks like

- A navigation list — the chosen row at the same size, heavier, on a pill: more than colour.
- A disabled setting carries its reason in words ("Turn Wi-Fi on first"); the focus ring is an outline apart from selection; a wait says what it waits for, and success is said only once it happened.

## 2 — acceptable, with a clear gap

- Each state shown, but one only by colour or a faint grey the display may not hold, or a disabled control with no reason.

## 0 — what fails it

- A state the person cannot see: chosen and unchosen alike, focus invisible, an action with no answer.
