# doc-reviewer — Answer first, findable

What scores of 0, 2 and 4 look like on this dimension, for the `doc-reviewer` judge. The reader finds the answer first: each section opens with its rule, the contents table leads there. Its weight is in `.agents/evals/weights.json`; how it is scored is the judge's rubric, Quality (.agents/HARNESS.md §12).

**Measured proxies — built.** `doc_proxies.py` measures the share of sections whose first line is the answer, not a preamble (at least 0.9). `verify.py proxies --judge doc-reviewer` runs them; a value out of its range caps this dimension at 2.

**How to use it.** Find the level the work sits nearest, quote the evidence — a file and line, a screenshot, a measured value — and give 1 or 3 when it sits between two. The person's own examples, under From the person, outrank the ones written here.

## 4 — what good looks like

- Every section's first sentence is its answer in bold or plain; the contents table names what each holds; a reader with one question lands on it in one jump (DOCUMENTATION_GUIDELINES §3.6).

## 2 — acceptable, with a clear gap

- Findable, but some sections open with background and reach the rule in the third sentence.

## 0 — what fails it

- A narrative to read end to end; the rule buried mid-paragraph; no contents table.
