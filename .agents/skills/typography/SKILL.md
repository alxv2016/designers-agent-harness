---
name: typography
description: How a product's type is applied, carried in the skill (references/typography.md) — the type scale itself is the project's own, in its DESIGN.md tokens, and the skill says which role goes where and how to set it — six roles (display, headline, title, body, label, caption) with what each is for and never for, mapped to Apple's text styles and Material's roles; a small scale with visible steps, each role token holding family, size, line height, weight and letter spacing; hierarchy from one property at a time with one top level per screen and headings that match in code; the system font first, one or two families, pairing, variable fonts, glyph coverage and licences, icons as images; line height by role, letter spacing for capitals, paragraph spacing; the measure of 45 to 75 characters, start alignment, centring only short text, justification only with hyphenation, wrapping before truncating; emphasis by weight first, italic sparingly, underline for links, no light weights for reading, capitals with tracking; tabular figures; editorial treatments — display type, a hero number, an eyebrow, a pull quote, an initial; text that follows the person's text size with the hierarchy intact and the platforms' minimum sizes; watches, round screens and LVGL panels' compiled fonts — the principles for every platform with guidance labelled for the web, iOS, Android and embedded ESP-IDF devices with an LVGL display; the type spec a draft records and the review of type; plus typography_check.py for the patterns code can show, in web, native and C/C++ files. Portable — the folder works in any repo. Use when choosing a text role, setting a heading, body text, a label or a caption, building a hierarchy, picking or pairing fonts, setting line height, letter spacing, line length or alignment, emphasising text, setting numbers, designing an editorial treatment, making text scale, or reviewing a screen's type.
metadata:
  scope: portable
---

# Typography

How a product's type is applied. The principles and their reasons are kept in this skill at
[references/typography.md](references/typography.md) (cited `TYPOGRAPHY §n`); this page indexes them in one-line rules
and holds the steps: choosing type for a screen, building it, and the review. The type scale — every role's family,
size, line height, weight and letter spacing — is the project's own, in its `DESIGN.md`; that file wins over the
reference, and the reference over this page.

**Platforms.** The rules below hold on every platform. Guidance for one platform is labelled **Web**, **iOS**,
**Android** or **Embedded (ESP-IDF, LVGL)** here and in the reference, which maps each idea across all four
(TYPOGRAPHY §13).

**Portable.** This folder is self-contained and links to nothing outside itself (it names the rest of a kit in
backticks): the reference and the typography check
([scripts/typography_check.py](scripts/typography_check.py)). Copy it into any repo's `.agents/skills/` (or
`.claude/skills/`) and it works there: the check reads `UI_PATHS` from `.agents/project.py` when the repo has one, and
scans every tracked UI file when it does not — web, native, and C or C++ for firmware, outside vendored folders such
as `node_modules/` and `managed_components/`. It needs git and Python 3.9+. It reads the project's `DESIGN.md` for the
scale and never assumes one; with no brief, it asks the person for the roles a change needs and proposes adding them
to one. In the agent-harness kit, the `ui-designer` skill and agent apply it at their gates, the `design-system`
skill owns how type tokens are written and loaded, the `accessibility` skill the floors on resizing and text spacing,
the `ux-content` skill the words and their case, the `layout` skill the space around text, and `verify.py run` runs
the check.

## When to use

- Choosing the role for a piece of text — a heading, body text, a label, a caption, a number.
- Building a screen's hierarchy, or a screen that reads as flat or noisy.
- Picking, pairing or loading fonts; adding a role to the brief.
- Setting line height, letter spacing, paragraph spacing, line length or alignment.
- Emphasising text, setting numbers, or designing an editorial treatment.
- Making text follow the person's text size, or fixing text that clips, truncates or overlaps when it grows.
- Reviewing a screen's type.

## Rules

### Do

1. **Choose every text by role, from the brief's scale** — display, headline, title, body, label, caption, as the
   brief names them; never a size or weight of its own (TYPOGRAPHY §1, §2).
2. **Use each role for its job** — display for short, critical text; body for reading; label inside controls; caption
   for metadata, never for what the person must read to act (TYPOGRAPHY §2).
3. **Keep a screen to three or four sizes and one top level** (TYPOGRAPHY §1, §4).
4. **Rank with one property at a time** — size, then weight, then colour; never colour alone (TYPOGRAPHY §4).
5. **Mark headings in code at the level they look** (TYPOGRAPHY §4).
6. **Start from the system font; use at most two families; cover every glyph the product shows** (TYPOGRAPHY §5).
7. **Give reading text room between lines, large text less, capitals added letter spacing** — line height as a ratio
   that grows with the text (TYPOGRAPHY §6).
8. **Hold running text to the brief's measure, about 45 to 75 characters** (TYPOGRAPHY §7).
9. **Align text to its start edge; centre only short text; justify only with hyphenation** (TYPOGRAPHY §7).
10. **Wrap before truncating; truncate only where the full text is one step away** (TYPOGRAPHY §7).
11. **Emphasise by weight first; italic sparingly; underline only links; capitals for a few words, by style**
    (TYPOGRAPHY §8).
12. **Set changing or aligned numbers in tabular figures** (TYPOGRAPHY §9).
13. **Use at most one editorial treatment on a screen, from the brief** (TYPOGRAPHY §10).
14. **Let every role follow the person's text size, with the hierarchy intact and nothing under the platform's
    minimum** (TYPOGRAPHY §11).
15. **On a watch or a small panel, use fewer, larger roles and short text** (TYPOGRAPHY §12).
16. **Write the type spec into the draft** — each text's role, emphasis, measure, wrap, numbers (TYPOGRAPHY §14).
17. **Embedded (ESP-IDF, LVGL): take each role's compiled font from the brief's header, through shared styles**
    (TYPOGRAPHY §12).

### Never

- **Set a font size, line height or weight that is not a role in the brief** — add the role there first.
- **Size text in a unit that ignores the person's setting** — `px` on the web, `dp` on Android, a fixed size on iOS
  (TYPOGRAPHY §11, §13).
- **Use the lightest weights for reading text** — Thin, ExtraLight, Light (TYPOGRAPHY §8).
- **Set capitals without letter spacing** (TYPOGRAPHY §6, §8).
- **Justify text without hyphenation, or centre running text** (TYPOGRAPHY §7).
- **Truncate a button, an error or a heading** (TYPOGRAPHY §7).
- **Web, iOS, Android: use an icon font where SVG or the platform's symbols serve** (TYPOGRAPHY §5).
- **Claim type reads well from code** — it is read on the target, at the default and the largest text size.

## Procedure

### Choosing type for a screen

1. **Read the brief's type roles** and the screens beside this one; note which roles they use for what.
2. **Give each text its role** by its job (TYPOGRAPHY §2); the top level first, then the rest in order.
3. **Check the hierarchy** — one top level, three or four sizes, each step one property (TYPOGRAPHY §4).
4. **Set the measure, alignment, wrapping and numbers** (TYPOGRAPHY §7, §9).
5. **Decide what happens at the largest text size** — what wraps, what moves (TYPOGRAPHY §11).
6. **Write the type spec** into the draft's values file (TYPOGRAPHY §14); draw the draft with the longest strings and
   at the largest text size too, and pass the `ui-designer` skill's gate 1.

### Building

1. **Build from the draft's spec, unchanged** — each text its role token; a new size is a new role in the brief.
2. **Run the typography check** (below) and the project's own checks.
3. **Read the screen on the target at the default and the largest text size**; hand that walk to the person for gate
   3.

### Reviewing type

1. **Run the typography check** on the changed UI files; a hit is a finding only on an added or changed line.
2. **Walk TYPOGRAPHY §15's order** — scaling and floors first, then roles, hierarchy, families, line height and
   spacing, measure and alignment, emphasis, numbers, editorial, the draft.
3. **Hand the reading to the person** — the screen at its largest text size on the target; never claim it from code.

## Checks

```sh
python3 .agents/skills/typography/scripts/typography_check.py            # every UI file, against the baseline
python3 .agents/skills/typography/scripts/typography_check.py <file> …   # the files a change touched
```

- [ ] (script) **Y1** Web: a font size in `px` — 0 hits
- [ ] (script) **Y2** Web: a line height in `px` — 0 hits
- [ ] (script) **Y3** Android: text sized in `dp` or `px` — 0 hits
- [ ] (script) **Y4** iOS: a fixed font size that ignores Dynamic Type — 0 hits
- [ ] (script) **Y5** Web: justified text without hyphenation — 0 hits
- [ ] (script) **Y6** a light weight — 0 hits, or a `typography-exception` for display text
- [ ] (script) **Y7** Web: capitals by style with no letter spacing — 0 hits
- [ ] (script) **Y8** Embedded: one of LVGL's built-in fonts named in a style setter — 0 hits
- [ ] The run read the UI files you expected — its last line counts the files it read, by kind (web, native,
  C/C++); "read no UI files" means nothing was checked
- [ ] Every text a role from the brief, used for its job (Do 1, Do 2)
- [ ] One top level; three or four sizes; headings in code at their level (Do 3, Do 5)
- [ ] Running text within the measure, start-aligned, wrapping before truncating (Do 8–10)
- [ ] The screen read at the largest text size on the target — handed to the person (Do 14)

Y1 reads CSS `font-size` and the `font` shorthand in px, a custom property named for font or text size in px
(`--text-body: 14px`), Tailwind's `text-[…px]` and a JS style object's `fontSize` as a number or a px string; a root
`font-size` in px counts, since it overrides the browser's setting; a chart's tick labels or a React Native style take
a `typography-exception`. Y2 reads CSS `line-height` and Tailwind's `leading-[…px]`; a line height that centres one
line in a fixed-height control takes a `typography-exception`. Y3 reads Android XML `android:textSize` in dp or px,
`COMPLEX_UNIT_DIP` and `COMPLEX_UNIT_PX`, and `.dp.toSp()`. Y4 reads SwiftUI `.system(size:)` — passed in a file with
`@ScaledMetric` — and `.custom(…, size:)` without `relativeTo:` on its line, and UIKit `UIFont.systemFont(ofSize:)`
and `UIFont(name:size:)` in a file that never names `UIFontMetrics`. Y5 and Y7 look in the same CSS rule, JS style
object or class list for hyphenation and letter spacing (`hyphens`, `hyphens-auto`; `letter-spacing`,
`letterSpacing`, `tracking-`); Y7 reads the `uppercase` class only inside a quoted class value, so copy that says
"uppercase" passes, and a `hyphens: auto` inherited from a parent is not seen. Y6 reads CSS weights 100 to 300 and
`lighter`, Tailwind's `font-thin`, `font-extralight` and `font-light`, SwiftUI's `.ultraLight`, `.thin` and `.light`
weights, Compose's `FontWeight.Thin`, `ExtraLight` and `Light`, Flutter's `FontWeight.w100` to `w300`, and Android's
`sans-serif-light` and `-thin`. Tailwind variants (`md:`, `dark:`) are read. Y8 reads C and C++ files and skips their
comments: `lv_obj_set_style_text_font` on one object given `&lv_font_montserrat_…`, `_unscii_`, `_dejavu_`,
`_simsun_` or `_source_han_sans_`; a shared style built with `lv_style_set_text_font`, as Do 17 asks, passes. A
sanctioned hit carries `typography-exception` on its line with the reason. The check cannot see a role used for the
wrong job, two top levels, a long measure, a missing glyph or text that truncates where it should wrap — the draft,
the review and the screen at its largest text size find those.

## Traps

- **Text grows but its box does not, and the last line is cut** → a fixed line height or a fixed-height container →
  a unitless line height and a box that grows (Do 7, Do 14).
- **The browser's larger text setting changes nothing** → font sizes in `px` → `rem` (Y1).
- **A custom font ignores Dynamic Type** → `.custom(_, size:)` without `relativeTo:` → relate it to a text style (Y4).
- **A counter jitters as it changes** → proportional figures → tabular figures (Do 12).
- **Every heading looks equally important** → each step changed size, weight and colour at once → one property per
  step (Do 4).
- **Embedded: a heading is not bold on the panel** → no bold font compiled for that role → compile it, or rank by size
  and colour (Do 17).

## Sources

| Topic | Where |
| --- | --- |
| The principles, the spec, the review | [references/typography.md](references/typography.md) |
| Text styles, Dynamic Type, minimum sizes, weights, leading, system fonts | Apple Human Interface Guidelines, Typography |
| Type roles and their defaults; fonts and variable fonts on Android | Android Developers — "Material Design 3 in Compose", "Work with fonts" |
| Web fonts: loading, formats, subsetting, licences | web.dev, "Best practices for fonts" |
| Line spacing, line length, emphasis, capitals, justification, paragraph spacing | Matthew Butterick, *Practical Typography*; Robert Bringhurst, *The Elements of Typographic Style* |
| A modular scale | Tim Brown, "More Meaningful Typography", A List Apart |
| Resizing and text spacing | WCAG 2.2 — 1.4.4 Resize Text, 1.4.12 Text Spacing, 1.4.8 Visual Presentation |
| Watches and arc text | Apple Human Interface Guidelines, Designing for watchOS; Android Developers, Wear OS "Apply the design" |
| Embedded: fonts, styles, text properties | LVGL 9 docs — Fonts, Style properties (`text_font`, `text_line_space`, `text_letter_space`, `text_align`), Label |
