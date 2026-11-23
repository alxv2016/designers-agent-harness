# code-reviewer — Fit with the codebase

What scores of 0, 2 and 4 look like on this dimension, for the `code-reviewer` judge. Fit with the codebase: its layering, naming, components, comments and conventions. Its weight is in `.agents/evals/weights.json`; how it is scored is the judge's rubric, Quality (.agents/HARNESS.md §12).

**Measured proxies — built.** `code_proxies.py` measures new warnings in the project's own sources (none); a layering check the project runs (such as an ESP-IDF app's E1–E5) stays a floor. `verify.py proxies --judge code-reviewer` runs them; a value out of its range caps this dimension at 2.

**How to use it.** Find the level the work sits nearest, quote the evidence — a file and line, a screenshot, a measured value — and give 1 or 3 when it sits between two. The person's own examples, under From the person, outrank the ones written here.

## 4 — what good looks like

- Imports in the allowed directions (APP_ARCHITECTURE §2); names and file layout like their neighbours; comments cite `DOC §n` for decisions; the change reads as if the codebase's author wrote it.

## 2 — acceptable, with a clear gap

- Correct and layered, with a convention missed: a bare `§`, a new naming style, a helper in the wrong component.

## 0 — what fails it

- A feature imported by `app_shell`, a driver reaching into the UI, a style of its own.
