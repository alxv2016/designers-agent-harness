# doc-reviewer — Accurate to code and sources

What scores of 0, 2 and 4 look like on this dimension, for the `doc-reviewer` judge. Every symbol, value, path and § the doc names is true of the code and its sources. Its weight is in `.agents/evals/weights.json`; how it is scored is the judge's rubric, Quality (.agents/HARNESS.md §12).

**Measured proxies — built.** `doc_proxies.py` measures history words (none); the doc checks' anchors and links stay a floor. `verify.py proxies --judge doc-reviewer` runs them; a value out of its range caps this dimension at 2.

**How to use it.** Find the level the work sits nearest, quote the evidence — a file and line, a screenshot, a measured value — and give 1 or 3 when it sits between two. The person's own examples, under From the person, outrank the ones written here.

## 4 — what good looks like

- Every backticked symbol, token, value and path found in the code as written; every § resolves; measured values carry where they were measured.

## 2 — acceptable, with a clear gap

- True in substance, with one stale value or a renamed symbol.

## 0 — what fails it

- Describes behaviour the code no longer has, or values nobody measured stated as fact.
