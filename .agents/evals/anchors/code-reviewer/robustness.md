# code-reviewer — Robustness: error paths, resources and limits of the platform

What scores of 0, 2 and 4 look like on this dimension, for the `code-reviewer` judge. Error paths and the platform's resources and limits: memory, the stack, a shared bus or connection, power states, timeouts, rate limits. Its weight is in `.agents/evals/weights.json`; how it is scored is the judge's rubric, Quality (.agents/HARNESS.md §12).

**Measured proxies — built.** `code_proxies.py` measures the sizes `SIZE_COMMAND` in `.agents/project.py` reports, when the project sets one: each part's share of its budget (at most 90 %) and its growth since the baseline (at most the part's own limit); peak memory is not measured. `verify.py proxies --judge code-reviewer` runs them; a value out of its range caps this dimension at 2.

**How to use it.** Find the level the work sits nearest, quote the evidence — a file and line, a screenshot, a measured value — and give 1 or 3 when it sits between two. The person's own examples, under From the person, outrank the ones written here.

## 4 — what good looks like

- Every call that can fail is checked and its failure shown; a sequence that shuts something down checks each step's result; no blocking wait on the UI's thread; memory bounded.

## 2 — acceptable, with a clear gap

- Failures handled on the main calls, one ignored; a resource cost noticed but not measured.

## 0 — what fails it

- A wait on a busy line retried on its own failure in a loop, so the UI freezes for seconds at a time; a power step sent without checking the state the driver tracks.
