# ux-content-writer — Clear, one meaning

What scores of 0, 2 and 4 look like on this dimension, for the `ux-content-writer` judge. Each string has one meaning, the important words first, in the person's words. Its weight is in `.agents/evals/weights.json`; how it is scored is the judge's rubric, Quality (.agents/HARNESS.md §12).

**Measured proxies — built.** `ux_proxies.py` measures the share of strings with a generic button, "invalid", "e.g.", "click here" or "enable" (none). `verify.py proxies --judge ux-content-writer` runs them; a value out of its range caps this dimension at 2.

**How to use it.** Find the level the work sits nearest, quote the evidence — a file and line, a screenshot, a measured value — and give 1 or 3 when it sits between two. The person's own examples, under From the person, outrank the ones written here.

## 4 — what good looks like

- "Turn Wi-Fi on first" — one meaning, the action first. A name used for one thing only, across the product (UX_CONTENT §2, §4).

## 2 — acceptable, with a clear gap

- Understood on a second read; a word that could mean two things here.

## 0 — what fails it

- Ambiguous or misleading: "Error", "Invalid", a code the person cannot read.
