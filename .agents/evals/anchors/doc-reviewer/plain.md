# doc-reviewer — Plain language

What scores of 0, 2 and 4 look like on this dimension, for the `doc-reviewer` judge. Plain language: short sentences, the reader's words, terms defined once. Its weight is in `.agents/evals/weights.json`; how it is scored is the judge's rubric, Quality (.agents/HARNESS.md §12).

**Measured proxies — built.** `doc_proxies.py` measures the mean sentence length (at most 25 words) and the longest (at most 50). `verify.py proxies --judge doc-reviewer` runs them; a value out of its range caps this dimension at 2.

**How to use it.** Find the level the work sits nearest, quote the evidence — a file and line, a screenshot, a measured value — and give 1 or 3 when it sits between two. The person's own examples, under From the person, outrank the ones written here.

## 4 — what good looks like

- Short active sentences in the words the reader uses; each term defined where it first appears; no jargon a designer would stop at.

## 2 — acceptable, with a clear gap

- Correct, with long sentences or an undefined term or two.

## 0 — what fails it

- Dense with undefined terms, passive and long; history in place of the current state.
