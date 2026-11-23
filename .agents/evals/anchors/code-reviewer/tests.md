# code-reviewer — Test quality, a test that fails without the fix

What scores of 0, 2 and 4 look like on this dimension, for the `code-reviewer` judge. Whether the tests would catch the bug: a test that fails without the fix. Its weight is in `.agents/evals/weights.json`; how it is scored is the judge's rubric, Quality (.agents/HARNESS.md §12).

**Measured proxies — built.** `code_proxies.py` measures changed sources no test touches — includes, imports or a `host-sources:` line (none); whether a test fails on the old code is not measured. `verify.py proxies --judge code-reviewer` runs them; a value out of its range caps this dimension at 2.

**How to use it.** Find the level the work sits nearest, quote the evidence — a file and line, a screenshot, a measured value — and give 1 or 3 when it sits between two. The person's own examples, under From the person, outrank the ones written here.

## 4 — what good looks like

- A host test for the new logic that fails on the old code and passes on the new; it tests behaviour, not the implementation; the edge cases from correctness each have a case.

## 2 — acceptable, with a clear gap

- Tests added, but they pass on the old code too, or cover only the happy path.

## 0 — what fails it

- New behaviour with no test where the project tests that kind of thing.
