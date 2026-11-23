# ux-designer — Feedback and status

What scores of 0, 2 and 4 look like on this dimension, for the `ux-designer` judge. Whether every action is answered and the system's status is visible. Its weight is in `.agents/evals/weights.json`; how it is scored is the judge's rubric, Quality (.agents/HARNESS.md §12).

**Measured proxies — none.** The judge scores this dimension on its reading alone; feedback within ~100 ms is the touch-and-gesture skill's floor.

**How to use it.** Find the level the work sits nearest, quote the evidence — a file and line, a screenshot, a measured value — and give 1 or 3 when it sits between two. The person's own examples, under From the person, outrank the ones written here.

## 4 — what good looks like

- Every press answered at once, on screen, by a sound or both; a wait shows what it waits for; success said only once it happened; status the person needs (battery, connection) on screen when it matters (HCI §2 H1).

## 2 — acceptable, with a clear gap

- Answered, but late or vague: a refresh with no sign it started, a spinner with no subject.

## 0 — what fails it

- Silent: a press with no answer, a failure nobody is told about.
