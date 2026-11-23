# ux-designer — Task flow, fewest steps

What scores of 0, 2 and 4 look like on this dimension, for the `ux-designer` judge. The task's path: the fewest steps, presses and screens from intent to done. Its weight is in `.agents/evals/weights.json`; how it is scored is the judge's rubric, Quality (.agents/HARNESS.md §12).

**Measured proxies — not built yet.** `PROXIES` in `.agents/project.py` names the project's screen audit for this judge once it exists (UI_REVIEW_RUBRIC §6 describes the pattern); until then the judge scores this dimension on its reading alone. `verify.py proxies --judge ux-designer` runs it; a value out of its range caps this dimension at 2.

**How to use it.** Find the level the work sits nearest, quote the evidence — a file and line, a screenshot, a measured value — and give 1 or 3 when it sits between two. The person's own examples, under From the person, outrank the ones written here.

## 4 — what good looks like

- The top task in the fewest steps the device allows — the empty state names the one step that starts it; a setting changed where it is read, no detour through a menu; defaults that make most steps unnecessary (HCI §10).

## 2 — acceptable, with a clear gap

- The task completes, with an extra step or screen it does not need, or a frequent action buried a level deep.

## 0 — what fails it

- The task cannot be completed, or loops back on itself; a dead end with no way out (HCI §2 H3).
