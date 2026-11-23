# ui-designer — Fit to the medium: the display, its input and its limits

What scores of 0, 2 and 4 look like on this dimension, for the `ui-designer` judge. Fit to the medium the product runs on: the display's size, density and colour depth, what a refresh or a frame costs, and the input it has — touch, a pointer, keys or an encoder. Its weight is in `.agents/evals/weights.json`; how it is scored is the judge's rubric, Quality (.agents/HARNESS.md §12).

**Measured proxies — not built yet.** `PROXIES` in `.agents/project.py` names the project's screen audit for this judge once it exists (UI_REVIEW_RUBRIC §6 describes the pattern); until then the judge scores this dimension on its reading alone. `verify.py proxies --judge ui-designer` runs it; a value out of its range caps this dimension at 2.

**How to use it.** Find the level the work sits nearest, quote the evidence — a file and line, a screenshot, a measured value — and give 1 or 3 when it sits between two. The person's own examples, under From the person, outrank the ones written here.

## 4 — what good looks like

- Built for the medium: sizes on the display's own grid and whole pixels; motion only where the display can show it and the frame budget holds it; on a slow-refresh display (e-paper), a change painted with the refresh the project's policy names, text in solid ink; targets and controls sized for the input the device has.

## 2 — acceptable, with a clear gap

- Right on the target, but it costs more than it needs: a full redraw or refresh for a small change, a grey the display cannot hold, a control sized for a pointer on a touch screen.

## 0 — what fails it

- Built for another medium: animation a slow display cannot show, text on a dither, sizes off the display's grid, a hover-only control on a device with no pointer.
