# ux-content-writer — Human, the product's voice

What scores of 0, 2 and 4 look like on this dimension, for the `ux-content-writer` judge. The product's voice: plain, calm, speaking to the person, never blaming. Its weight is in `.agents/evals/weights.json`; how it is scored is the judge's rubric, Quality (.agents/HARNESS.md §12).

**Measured proxies — built.** `ux_proxies.py` measures the share of strings with "please", "!", "oops", title case, "the user" or capitals (none). `verify.py proxies --judge ux-content-writer` runs them; a value out of its range caps this dimension at 2.

**How to use it.** Find the level the work sits nearest, quote the evidence — a file and line, a screenshot, a measured value — and give 1 or 3 when it sits between two. The person's own examples, under From the person, outrank the ones written here.

## 4 — what good looks like

- Sounds like the product in DESIGN.md's voice; addresses the person, never blames them (UX_CONTENT §1).

## 2 — acceptable, with a clear gap

- Correct but mechanical, or a tone that does not fit the moment.

## 0 — what fails it

- Blames the person ("You entered an invalid…"), shouts, or speaks as the system to itself.
