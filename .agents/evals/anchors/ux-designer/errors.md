# ux-designer — Error prevention and recovery

What scores of 0, 2 and 4 look like on this dimension, for the `ux-designer` judge. Preventing errors, and recovering from those that happen. Its weight is in `.agents/evals/weights.json`; how it is scored is the judge's rubric, Quality (.agents/HARNESS.md §12).

**Measured proxies — none.** The judge scores this dimension on its reading alone.

**How to use it.** Find the level the work sits nearest, quote the evidence — a file and line, a screenshot, a measured value — and give 1 or 3 when it sits between two. The person's own examples, under From the person, outrank the ones written here.

## 4 — what good looks like

- Impossible choices are disabled with their reason; what cannot be undone asks first; an error says what happened and what to do ("Wrong password. Check it and try again."), keeps what was typed and returns the person to where they were (HCI §2 H5, H9).

## 2 — acceptable, with a clear gap

- Errors are caught, but recovery costs work: input cleared, the flow restarted, the cause unnamed.

## 0 — what fails it

- An error loses the person's data or leaves them stuck; a destructive action with no confirm and no undo.
