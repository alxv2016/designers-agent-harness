# code-reviewer — Correctness beyond the tests, edge cases

What scores of 0, 2 and 4 look like on this dimension, for the `code-reviewer` judge. Does it do what it claims for every input, beyond what the tests exercise: empty, missing, slow, failed, concurrent. Its weight is in `.agents/evals/weights.json`; how it is scored is the judge's rubric, Quality (.agents/HARNESS.md §12).

**Measured proxies — none.** The judge scores this dimension on its reading alone; whether a test fails on the old code is read, not measured (`code_proxies.py` measures the `tests` dimension's coverage only).

**How to use it.** Find the level the work sits nearest, quote the evidence — a file and line, a screenshot, a measured value — and give 1 or 3 when it sits between two. The person's own examples, under From the person, outrank the ones written here.

## 4 — what good looks like

- Every edge case named in the change is handled and shown handled: an empty list, a missing sensor, a timeout, a value at its limit, the order of async events.

## 2 — acceptable, with a clear gap

- The main path right; one edge unhandled or unclear — a gesture's speed taken over the whole drag rather than from its last samples.

## 0 — what fails it

- Wrong on the main path, or claims a fix it does not make.
