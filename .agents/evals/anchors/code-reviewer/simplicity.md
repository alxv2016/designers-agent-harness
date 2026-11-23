# code-reviewer — Simplicity, smallest change

What scores of 0, 2 and 4 look like on this dimension, for the `code-reviewer` judge. The smallest change that does it: no extra layers, flags or copies. Its weight is in `.agents/evals/weights.json`; how it is scored is the judge's rubric, Quality (.agents/HARNESS.md §12).

**Measured proxies — built.** `code_proxies.py` measures the longest changed function, in the languages `CODE_LANGS` names, (at most 60 lines) and its deepest nesting (at most 4). `verify.py proxies --judge code-reviewer` runs them; a value out of its range caps this dimension at 2.

**How to use it.** Find the level the work sits nearest, quote the evidence — a file and line, a screenshot, a measured value — and give 1 or 3 when it sits between two. The person's own examples, under From the person, outrank the ones written here.

## 4 — what good looks like

- The diff touches only what the task needs; it reuses what exists; each function does one thing and reads in one pass.

## 2 — acceptable, with a clear gap

- Works, with an extra abstraction or a duplicated block that a shared helper already covers.

## 0 — what fails it

- A rewrite where an edit would do; dead code, speculative options, deep nesting.
