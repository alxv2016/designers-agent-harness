# doc-reviewer — Concise, one home per rule

What scores of 0, 2 and 4 look like on this dimension, for the `doc-reviewer` judge. Each rule said once, in its one home, in as few words as hold it. Its weight is in `.agents/evals/weights.json`; how it is scored is the judge's rubric, Quality (.agents/HARNESS.md §12).

**Measured proxies — built.** `doc_proxies.py` measures sentences of 12 words or more found word for word in another doc (none). `verify.py proxies --judge doc-reviewer` runs them; a value out of its range caps this dimension at 2.

**How to use it.** Find the level the work sits nearest, quote the evidence — a file and line, a screenshot, a measured value — and give 1 or 3 when it sits between two. The person's own examples, under From the person, outrank the ones written here.

## 4 — what good looks like

- One home per rule; elsewhere a one-line pointer `DOC §n`; tables where the content is a table; no filler words, no history.

## 2 — acceptable, with a clear gap

- Clear, but a rule restated in a second doc, or paragraphs where a table would do.

## 0 — what fails it

- The same rule in three places, slightly different; long sentences that hedge.
