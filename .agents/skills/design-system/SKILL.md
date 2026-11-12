---
name: design-system
description: The project's design system, decided in DESIGN.md at the repo root — its principles, and every token (colour, type, space, radius, elevation, motion, layout) by semantic role with a value per theme — and carried into code by the token files (TOKEN_FILES in .agents/project.py). Screens take values from tokens by role, never as literals; themes are a second set of values for the same roles; components are reused before new ones are made; exceptions are registered with their reason. Owns the design check (DESIGN.md's contrast pairs against their floors, its ratios, its tokens present in code) and the token check (a colour literal in a UI file). Use when reading or changing DESIGN.md, adding or changing a token, a theme, a component or a style, when a screen needs a value the scale does not have, when moving a design file's styles into code, or when the design check fails.
---

# Design system

How a screen takes its values: from tokens, by role, decided in one place. That place is **`DESIGN.md`** at the repo
root (`DESIGN_FILE` in `.agents/project.py`) — the design brief, cited `DESIGN §n`. It holds the product's principles
(DESIGN §1), every token by role with its value in each theme (DESIGN §2–§7), the contrast pairs a screen paints
(DESIGN §2.2), the components (DESIGN §8), the accessibility floors (DESIGN §9) and the exceptions (DESIGN §10). The
token files in code (`TOKEN_FILES`) carry the same values to the platform. This skill holds the rules for using them and
the checks. DESIGN.md wins if this skill and it disagree — fix the skill.

## When to use

- Before any UI work — read DESIGN.md's principles and the tokens the change touches.
- Adding or changing a colour, type size, spacing step, radius, shadow, duration, easing or breakpoint.
- Adding a theme (dark mode, high contrast, a brand), or a component's states (hover, pressed, focus, disabled).
- A screen needs a value the scale does not have.
- Moving styles from a design file into code, or setting up DESIGN.md for a new project.
- The design check (`D1`–`D3`) or the token check (`T1`) fails in `verify.py run`.

## Rules

### Do

1. **Read DESIGN.md first** — the principles decide between two good options; the lower-numbered principle wins
   (DESIGN §1).
2. **Take every colour, size, space, radius, shadow and duration from a token** — a screen never holds a literal
   (DESIGN §1, Principle 5).
3. **Use semantic roles at the call site** — `color.text.secondary`, `space.lg`, not `grey-600` or `16px`; a theme then
   changes values without touching screens.
4. **Decide a token in DESIGN.md, then carry it to the token files, in the same change.** DESIGN.md is where the value
   and its reason live; the token files are the platform's copy, generated from it or kept in step by hand. The design
   check's D3 proves every token DESIGN.md names is in the token files.
5. **Make a theme a second column of values for the same roles** — never a second set of roles; every role used in a
   pair is checked in every theme (DESIGN §2.1, §2.2).
6. **Give a new colour role its kind in DESIGN §2.1, then every pair its kind calls for in §2.2, with its floor and its
   ratio per theme**, before any screen uses it; the design check lists a missing pair and recomputes each one
   ([`accessibility`](../accessibility/SKILL.md) Do 1–3).
7. **Give every interactive state its token** — rest, hover, pressed, focus, disabled, selected; a state is never an
   opacity trick on text.
8. **Register every exception** — an off-scale value carries `token-exception` in a comment on its line in code and a
   row in DESIGN §10 (value, where, why); the token check skips the line.
9. **Compute a nested radius** — inner = outer − the padding between them, so corners stay concentric (DESIGN §5).
10. **Reuse a component before making one; move a one-off into the shared components on its second caller**, both
    callers in the same change, and give it a row in DESIGN §8.
11. **Draft a token change as a specimen and take the person's yes before the token files change** — swatches, the
    type scale, a screen or two before and after; `verify.py approve <png> --kind mock`. A token is seen on every
    screen at once (`GATES` in `.agents/project.py`).

### Never

- **A literal colour, size or duration in a screen** — the token check finds colours; read for the rest.
- **A token named for its value** (`blue`, `sixteen`) at a call site — the name outlives the value.
- **A new token for one screen** — use the scale, or register an exception with its reason.
- **Opacity on text to make it secondary** — a token whose painted colour passes ([`accessibility`](../accessibility/SKILL.md)).
- **A value in the token files that DESIGN.md does not have**, or a ratio in DESIGN §2.2 written by hand without
  running the check.
- **Change a principle without the person** — the principles are theirs; propose the change and its reason.

## Procedure

`V` is `python3 .agents/skills/verify-change/scripts/verify.py`.

### Adding or changing a token

1. Read the scale it belongs to in DESIGN.md; a step that exists wins over a new one.
2. Draft a specimen in the scratchpad — the old and new values side by side on the screens that use the token — and
   take the person's yes: `V approve <png> --kind mock` (Do 11).
3. Change the row in DESIGN.md: the value per theme, the use.
4. For a colour, update every DESIGN §2.2 row that names it — run the design check and write the ratios it computes.
5. Carry the value to the token files.
6. `V run` — the design check, the token check, the project's build.

### Setting up DESIGN.md for a new project

1. Start from the template's demo `DESIGN.md`: keep its sections and its table shapes — the design check reads the
   `| Token | <Theme> | … |` tables, the colour table's `Kind` column, and the
   `| Foreground | Background | Floor | <Theme> | … |` table. Give every colour role its kind; run the check and it
   lists each pair the kinds call for that has no row.
2. Write the principles with the person: five or fewer, each a rule, what it means in practice, and why.
3. Replace the demo values with the product's — from the design file, or drafted and approved as a specimen.
4. Set `DESIGN_FILE` and `TOKEN_FILES` in `.agents/project.py`; run `V run`.

### Moving styles from a design file

1. List the design file's styles (colours, text styles, effects) and match each to a DESIGN.md token by role.
2. A style with no token is a question for the person: a new token, an existing one, or an exception.
3. Never paste the design file's raw values into a screen.

## Checks

Scripts — in [`scripts/`](scripts/), run from the repo root; `verify.py run` runs the design check when DESIGN.md, the
token files or the UI change, and the token check with it once `TOKEN_FILES` is set:

```sh
python3 .agents/skills/design-system/scripts/design_check.py      # D1–D4: DESIGN.md against its floors and the code
python3 .agents/skills/design-system/scripts/token_check.py       # T1: colour literals in UI files
```

- [ ] (script) **D1 contrast pair under its floor** — every DESIGN §2.2 pair, in every theme; no floor under its
  kind's (4.5 for text and on-fill, 3 for non-text) — 0 hits
- [ ] (script) **D2 ratio written wrong** — each ratio in DESIGN §2.2 within 0.05 of the computed one — 0 hits
- [ ] (script) **D3 token missing from the token files** — every token DESIGN.md names, and every colour value, is in
  `TOKEN_FILES` — 0 hits; skipped while `TOKEN_FILES` is empty
- [ ] (script) **D4 contrast pair missing** — every pair DESIGN §2.1's kinds call for has a row in §2.2: each `text`
  and `non-text` role on each `surface`, each `on-fill` role on each `fill` — 0 hits
- [ ] (script) **T1 colour literal outside the tokens** — `token_check.py` — 0 hits today (`BASELINE` in the script)
- [ ] Roles, not scale steps, at every call site (Do 3)
- [ ] Every state has its token (Do 7); every exception in DESIGN §10 (Do 8)
- [ ] The change follows DESIGN.md's principles (Do 1)
- [ ] A token change has the person's yes on its specimen (Do 11)

## Traps

- **The token check passes and a screen still has a literal** → it finds colours only; spacing, sizes and durations
  are read for → look at every number in a changed style.
- **D3 says a token is missing, but it is in the CSS** → its name there is spelled differently in a way the check
  cannot match (`--fg-2` for `color.text.secondary`) → name the code token after the role in DESIGN.md.
- **A dark theme looks muddy** → the theme swapped scale steps, not roles → define each role's dark value and add its
  pairs to DESIGN §2.2.
- **The design file and the code disagree** → two hand-kept copies with DESIGN.md skipped → DESIGN.md decides; fix the
  copy that is not it.

## Sources

| Topic | Where |
| --- | --- |
| Principles, tokens, pairs, components, exceptions | [DESIGN.md](../../../DESIGN.md) |
| Where the brief and the tokens live | `DESIGN_FILE`, `TOKEN_FILES` in `.agents/project.py` |
| Contrast in every theme | [`accessibility`](../accessibility/SKILL.md) |
| The gates a UI change passes | [`ui-designer`](../ui-designer/SKILL.md) |
| The design brief in the harness | [AGENT_HARNESS §23](../../../docs/AGENT_HARNESS.md#23-the-design-brief-designmd) |
