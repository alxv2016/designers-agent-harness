# ux-content-writer — Says what happened and what to do

What scores of 0, 2 and 4 look like on this dimension, for the `ux-content-writer` judge. An error, empty state or status says what happened and what to do next. Its weight is in `.agents/evals/weights.json`; how it is scored is the judge's rubric, Quality (.agents/HARNESS.md §12).

**Measured proxies — built.** `ux_proxies.py` measures the share of strings titled "Error" (none). `verify.py proxies --judge ux-content-writer` runs them; a value out of its range caps this dimension at 2.

**How to use it.** Find the level the work sits nearest, quote the evidence — a file and line, a screenshot, a measured value — and give 1 or 3 when it sits between two. The person's own examples, under From the person, outrank the ones written here.

## 4 — what good looks like

- "Wrong password. Check it and try again." — what happened, then the one next action; "No follow-ups yet" with "Hold AI or press Record." (UX_CONTENT §5.7, §5.8).

## 2 — acceptable, with a clear gap

- Says what happened, not what to do; or the action without the reason.

## 0 — what fails it

- "Something went wrong" — nothing the person can act on.
