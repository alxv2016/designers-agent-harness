---
name: design-system
description: The project's design system, decided in DESIGN.md at the repo root — its principles, and every token (colour, type, space, radius, elevation, layers, motion, layout) by semantic role with a value per theme — and carried into code by the token files. Carries how a brief is written (references/brief.md — roles, colour kinds and pairs, complete themes and dark ordering, type that holds across states, layout stability, radius, surfaces and elevation, layers, decoration, motion tokens, components and their states, exceptions, tokens on the web, iOS, Android and an embedded ESP-IDF device with an LVGL screen — a C/C++ header of constexpr values by role with shared lv_style_t styles built from them, fonts compiled per size with their glyph ranges, a theme as a product setting restyled at run time, colour depth and RGB565 banding, AMOLED against LCD, depth without shadows) and a starter DESIGN.md that passes the checks. Screens take values from tokens by role, never as literals; themes are a second set of values for the same roles; components are reused before new ones are made; exceptions are registered with their reason. Owns the design check (DESIGN.md's contrast pairs against their floors, its ratios, every pair its kinds call for, a value in every theme, solid surfaces, its tokens present in code, in CSS or C spelling) and the token check (a colour literal in a UI file — web, native, and C/C++ with LVGL, where only a number in a colour's place counts). Portable — the folder works in any repo. Use when reading or changing DESIGN.md, adding or changing a token, a theme, a component or a style, when a screen needs a value the scale does not have, when setting up DESIGN.md for a new project, when moving a design file's styles into code or a device's token header, or when the design check fails.
metadata:
  scope: portable
---

# Design system

How a screen takes its values: from tokens, by role, decided in one place. That place is the project's own
**`DESIGN.md`** at the repo root — its design brief, which the person writes or updates for their product. It holds the
product's principles, every token by role with its value in each theme, the contrast pairs, the components, the
floors above AA and the exceptions; this page names each by what it holds (in the starter's numbering: §1, §2–§7,
§2.2, §8, §9, §10 — a brief numbered otherwise is cited by its own numbers). The values in any example DESIGN.md are
not this skill's; it reads whatever brief the project has. How a brief is written, and why, is kept in this skill at
[references/brief.md](references/brief.md) (cited `DESIGN_BRIEF §n`); this page indexes it in one-line rules and holds
the steps and the checks. The product's DESIGN.md wins over the reference, and the reference over this page — fix
this page.

**Portable.** This folder is self-contained and links to nothing outside itself (it names the rest of a kit in
backticks): the reference, a starter brief ([references/templates/DESIGN.md](references/templates/DESIGN.md)), and
the design and token checks ([scripts/](scripts/)). Copy it into any repo's `.agents/skills/` (or `.claude/skills/`)
and it works there: the scripts read `DESIGN_FILE`, `TOKEN_FILES` and `UI_PATHS` from `.agents/project.py` when the
repo has one, and fall back to `DESIGN.md`, no token files and every tracked UI file when it does not
([scripts/_config.py](scripts/_config.py)). The contrast formula is the `accessibility` skill's when it sits beside
this one, and the same WCAG formula otherwise. They need git and Python 3.9+. In the agent-harness kit, `verify.py
run` runs both checks, and the `ui-designer` skill and agent apply these rules at their gates.

## When to use

- Before any UI work — read DESIGN.md's principles and the tokens the change touches.
- Adding or changing a colour, type size, spacing step, radius, shadow, layer, duration, easing or breakpoint.
- Adding a theme (dark mode, high contrast, a brand), or a component's states (hover, pressed, focus, disabled).
- A screen needs a value the scale does not have.
- Setting up DESIGN.md for a new project, or moving styles from a design file into code.
- Carrying tokens to a device: the C/C++ token header, the LVGL styles, the compiled fonts, the panel's colour depth.
- The design check (`D1`–`D6`) or the token check (`T1`) fails.

## Rules

### Do

1. **Read DESIGN.md first** — the principles decide between two good options; where the brief ranks them, the higher-ranked wins
   (DESIGN_BRIEF §2).
2. **Take every colour, size, space, radius, shadow, layer and duration from a token** — a screen never holds a
   literal (DESIGN_BRIEF §3).
3. **Use semantic roles at the call site** — `color.text.secondary`, `space.lg`, not `grey-600` or `16px`; a primitive
   ramp lives only in the token files (DESIGN_BRIEF §3).
4. **Decide a token in DESIGN.md, then carry it to the token files, in the same change** (DESIGN_BRIEF §3, §15).
5. **Make a theme a second column of values for the same roles, complete in every cell**, with dark accents re-chosen
   by lightness on the same hue (DESIGN_BRIEF §5).
6. **Give a new colour role its kind in DESIGN.md's colour roles, then every pair its kind calls for in its contrast
   pairs, with its floor and its ratio per theme**, before any screen uses it (DESIGN_BRIEF §4).
7. **Give every interactive state its token** — rest, hover, pressed, focus, disabled, selected; never an opacity
   trick on text, and never a state that changes a size (DESIGN_BRIEF §4, §7).
8. **Register every exception** — `token-exception` on its code line and a row in DESIGN.md's exceptions (DESIGN_BRIEF §14).
9. **Compute a nested radius** — inner = outer − the gap between them, so corners stay concentric (DESIGN_BRIEF §8).
10. **Reuse a component before making one; move a one-off into the shared components on its second caller**, and give
    it a row in DESIGN.md's components (DESIGN_BRIEF §13).
11. **Draft a token change as a specimen and take the person's yes before the brief or the token files change** — the
    old and new values side by side on the screens that use them. A token is seen on every screen at once.
12. **Paint surfaces and fills solid**; only a scrim or an exempt role is translucent (DESIGN_BRIEF §4).
13. **Give a surface at most a step in surface colour and a shadow**, an edge only where the shadow cannot read, and
    anything a person can press a boundary at 3:1 (DESIGN_BRIEF §9).
14. **Keep dark surfaces ordered lighter as they rise, with every raised edge visible** (DESIGN_BRIEF §5, §9).
15. **Stack layers by the brief's named order**, overlays at the top level of the screen (DESIGN_BRIEF §10).
16. **Reserve the box for anything that arrives late, and design every data view in its four states** — loading,
    empty, error, full, each the size of full (DESIGN_BRIEF §7, §13).
17. **Show the right theme on the first frame and declare it to the platform** (DESIGN_BRIEF §5).
18. **Name the panel a product ships on when it has one, choose its values for it, and judge them on it** — the
    colour depth, the panel type, the lowest brightness; a gradient or a near-black step seen only on a computer
    screen is not checked (DESIGN_BRIEF §4, §11).
19. **Make every type role a font the product can draw** — on a device, a compiled font at that size and weight,
    holding every glyph the product's strings use (DESIGN_BRIEF §6).
20. **Choose each control by what it does, from the brief's components** — a typed value is a field, a few choices a
    switch, segmented control or radio set, many a list or picker, an action a button; an action that cannot be
    undone is its own button in the danger role, never a list row, and asks first (DESIGN_BRIEF §13); the
    confirmation's first focus is `FOCUS §5`'s and its words `UX_CONTENT §5`'s.

### Never

- **A literal colour, size, layer or duration in a screen** — the token check finds colours; read for the rest
  (DESIGN_BRIEF §16).
- **A token named for its value** (`blue`, `sixteen`) at a call site — the name outlives the value (DESIGN_BRIEF §3).
- **A new token for one screen** — use the scale, or register an exception (DESIGN_BRIEF §3, §14).
- **Opacity on text to make it secondary** — a role whose painted colour passes (DESIGN_BRIEF §4).
- **A value in the token files that DESIGN.md does not have**, or a contrast ratio in DESIGN.md written by hand without
  running the check (DESIGN_BRIEF §15).
- **Stacked depth cues, a second decorative gradient on a screen, or a fade over content that scrolls**
  (DESIGN_BRIEF §9, §11).
- **Change a principle without the person** — the principles are theirs; propose the change and its reason.

## Procedure

`V` is `python3 .agents/skills/verify-change/scripts/verify.py` in the agent-harness kit.

### Adding or changing a token

1. Read the scale it belongs to in DESIGN.md; a step that exists wins over a new one.
2. Draft a specimen in the scratchpad — the old and new values side by side on the screens that use the token — and
   take the person's yes (`V approve <file> --kind mock` in the kit) (Do 11).
3. Change the row in DESIGN.md: the value per theme, the use.
4. For a colour, update every contrast-pair row that names it — run the design check and write the ratios it computes.
5. Carry the value to the token files, named after the role (DESIGN_BRIEF §15).
6. Run the checks — the design check, the token check, the project's build (`V run` in the kit).

### Setting up DESIGN.md for a new project

1. Copy the starter: `cp .agents/skills/design-system/references/templates/DESIGN.md DESIGN.md` — it passes the
   design check as it stands; keep its section numbers and table shapes (DESIGN_BRIEF §1).
2. Write the principles with the person: five or fewer, each a rule, what it means in practice, and why.
3. Replace the example values with the product's — from the design file, or drafted and approved as a specimen. Give
   every colour role its kind; the check lists each pair the kinds call for that has no row.
4. In the kit, set `DESIGN_FILE` and `TOKEN_FILES` in `.agents/project.py` — the CSS, the native token files, or a
   device's token header (an exact file, a folder ending `/`, or a glob); then run the checks.

### Moving styles from a design file

1. List the design file's styles (colours, text styles, effects) and match each to a DESIGN.md token by role.
2. A style with no token is a question for the person: a new token, an existing one, or an exception.
3. Never paste the design file's raw values into a screen.

## Checks

Run from the repo root:

```sh
python3 .agents/skills/design-system/scripts/design_check.py              # D1–D6: DESIGN.md against its floors and the code
python3 .agents/skills/design-system/scripts/design_check.py --file F     # another brief, such as the starter
python3 .agents/skills/design-system/scripts/token_check.py               # T1: colour literals in UI files
python3 .agents/skills/design-system/scripts/design_check.py --test       # each check's own cases
python3 .agents/skills/design-system/scripts/token_check.py --test
```

Each run prints how many files it read; a run that read none says so and proves nothing.

- [ ] (script) **D1 contrast pair under its floor** — every contrast pair, in every theme; no floor under its
  kind's; none on a translucent background — 0 hits
- [ ] (script) **D2 ratio written wrong** — each ratio within 0.05 of the computed one — 0 hits
- [ ] (script) **D3 token missing from the token files** — every token DESIGN.md names, and every colour value with
  its exact digits (`#6B7280` in CSS, `0x6B7280` in C and C++), is in the token files — 0 hits; skipped while there
  are none
- [ ] (script) **D4 contrast pair missing** — every pair the colour kinds call for has a row in the contrast pairs — 0 hits
- [ ] (script) **D5 theme value missing** — every colour has a value in every theme column — 0 hits
- [ ] (script) **D6 translucent surface or fill** — 0 hits
- [ ] (script) **T1 colour literal outside the tokens** — `token_check.py`; in C and C++, a number in a colour's
  place (`lv_color_hex(0x…)`, `lv_color_make(…)`, `LV_COLOR_MAKE(…)`, `lv_palette_*`, a colour-named call) — 0 hits
  (`BASELINE` in the script)
- [ ] Roles, not scale steps, at every call site (Do 3); every number in a changed style is a token (Do 2)
- [ ] Every state has its token and keeps its size (Do 7); every exception in DESIGN.md's exceptions (Do 8)
- [ ] No stacked depth cues; pressable things keep a 3:1 boundary; dark overlays' edges visible (Do 13, Do 14)
- [ ] The change follows DESIGN.md's principles (Do 1)
- [ ] A token change has the person's yes on its specimen (Do 11)
- [ ] On a device: the change seen on the panel — gradients, near-black steps, the lowest brightness (Do 18); every
  type role a compiled font with the glyphs its strings use (Do 19)
- [ ] Each control fits what it does; an irreversible action is a danger-role button, never a list row, that asks
  first (Do 20)

## Traps

- **The token check passes and a screen still has a literal** → it finds colours only; spacing, sizes, layers and
  durations are read for → look at every number in a changed style.
- **D3 says a token is missing, but it is in the CSS** → its name there is spelled differently in a way the check
  cannot match (`--fg-2` for `color.text.secondary`) → name the code token after the role.
- **A dark theme looks muddy** → the theme swapped scale steps, not roles, or mirrored the accent → define each role's
  dark value and add its pairs to the contrast pairs (Do 5).
- **A menu disappears into the dark canvas** → its only depth cue was a black shadow → a lighter surface or a faint
  edge (Do 14).
- **A selected tint goes grey in dark** → it was a translucent accent over the surface → a solid role with its own
  pairs (Do 12).
- **The design file and the code disagree** → two hand-kept copies with DESIGN.md skipped → DESIGN.md decides; fix the
  copy that is not it.
- **D3 says a colour is missing, but the C header has it** → it is written with other digits — an alpha byte in
  front (`0xFF6B7280`) or a value rounded for the panel → write the brief's exact digits, `0x6B7280`
  (DESIGN_BRIEF §15).
- **A gradient is smooth in the mock and stepped on the device** → the panel runs at RGB565 and LVGL does not dither
  → a shorter lightness span or a dithered image, judged on the panel (Do 18).
- **A label shows boxes or gaps on the device** → its glyphs are not in the compiled font's ranges → add them to the
  font and name the ranges in DESIGN.md (Do 19).
- **The theme switch leaves some widgets in the old colours** → they hold local styles set once, or the shared
  styles changed without a redraw → restyle through the shared styles and call `lv_obj_report_style_change`
  (DESIGN_BRIEF §5).

## Sources

| Topic | Where |
| --- | --- |
| How a brief is written, and why | [references/brief.md](references/brief.md) |
| A starter brief that passes the checks | [references/templates/DESIGN.md](references/templates/DESIGN.md) |
| The settings the scripts read | [scripts/_config.py](scripts/_config.py) |
| Colour roles, tonal elevation, shape scale | Material Design 3 (Color, Elevation, Shape) |
| Semantic colours, dark mode, materials | Apple Human Interface Guidelines (Color, Dark Mode, Materials) |
| Contrast floors | WCAG 2.2 (1.4.3, 1.4.11) |
| Styles, themes, fonts and colour formats on a device | LVGL 9 documentation (Styles, Themes, Fonts, Colors) and its `Kconfig` (`LV_COLOR_DEPTH`, `LV_GRADIENT_MAX_STOPS`, `LV_USE_DRAW_SW_COMPLEX_GRADIENTS`) |
| Token files across platforms | The W3C Design Tokens Community Group format |
