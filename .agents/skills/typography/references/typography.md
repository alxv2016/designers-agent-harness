# Typography

How a product's type is applied: which text role goes where, how roles build a hierarchy, which families and how many,
line height, letter and paragraph spacing, line length and alignment, emphasis, numbers, editorial treatments, and
text that scales with the person's setting, on every screen from a desktop to a watch. People read it to set type with
reasons; coding agents read it, through the `typography` skill, before they draft a screen, build one or review one.

**Where it lives.** In the `typography` skill, beside the steps and checks that apply it — [its SKILL.md](../SKILL.md).
The skill folder is self-contained: copy it into any repo's `.agents/skills/` and this reference and the typography
check come with it. The product's type scale — every role's family, size, line height, weight and letter spacing —
lives in its design brief (`DESIGN.md` in the agent-harness kit) and wins over this reference; how those tokens are
written and carried into code is the `design-system` skill's, the floors on resizing, text spacing and contrast are
the `accessibility` skill's, and the words themselves, their case and their length are the `ux-content` skill's.

**Platforms.** Every principle holds on every platform and is stated once. Guidance for one platform is labelled
**Web**, **iOS**, **Android** or **Embedded (ESP-IDF, LVGL)** — the last for a device with a display drawn by LVGL on
an Espressif chip, whose fonts are compiled into the firmware at fixed sizes (§12).

**Stability.** Cite this doc as `TYPOGRAPHY §n`. Do not renumber; add new material under the next free number.

| Tag | Meaning |
| --- | --- |
| `[D]` | Derived — calculated from cited values, not measured |

| § | Section | Look here for |
| --- | --- | --- |
| 1 | [Principles](#1-principles) | Type serves reading; roles, not sizes; the brief's scale |
| 2 | [Roles](#2-roles) | Display, headline, title, body, label, caption — what each is for, and the platforms' names for them |
| 3 | [The scale](#3-the-scale) | How many sizes, the steps between them, what each role token holds |
| 4 | [Hierarchy](#4-hierarchy) | Size, weight, colour and space; one top level per screen; semantics that match |
| 5 | [Families and fonts](#5-families-and-fonts) | The system font first, one or two families, pairing, variable fonts, coverage, licences |
| 6 | [Line height and spacing](#6-line-height-and-spacing) | Line height by role, letter spacing, paragraph spacing |
| 7 | [Line length and alignment](#7-line-length-and-alignment) | The measure, start alignment, centring, justification, wrapping and truncation |
| 8 | [Emphasis and case](#8-emphasis-and-case) | Weight first, italic sparingly, underline for links, capitals with tracking |
| 9 | [Numbers](#9-numbers) | Tabular and proportional figures, alignment, units |
| 10 | [Editorial treatments](#10-editorial-treatments) | Display type, a hero number, an eyebrow, a pull quote, an initial |
| 11 | [Text that scales](#11-text-that-scales) | The person's text size, minimum sizes, hierarchy at every size |
| 12 | [Small screens and panels](#12-small-screens-and-panels) | A watch, a round screen, an LVGL panel's compiled fonts |
| 13 | [The same type on each platform](#13-the-same-type-on-each-platform) | Each idea in web, iOS, Android and LVGL terms |
| 14 | [The type spec](#14-the-type-spec) | What a draft records about its type |
| 15 | [Reviewing type](#15-reviewing-type) | What a review of type checks, in order |
| 16 | [The checks](#16-the-checks) | What the typography check finds, and what is left to read |

---

## 1. Principles

**Type exists to be read; a screen uses a few roles from the brief's scale, each for its job, and never a size of its
own.**

- **Readability before character** — a face, size or treatment that slows reading costs more than it adds; legibility
  at the smallest size and the longest line decides.
- **Choose by role, never by size** — a heading is the brief's title role, not "20 px bold"; the role carries size,
  line height, weight and spacing together, and changes everywhere at once when the brief changes.
- **The scale is the brief's** — every role's values are tokens in DESIGN.md; this reference says which role to use
  where and how to set it, never what its numbers are.
- **Few roles per screen** — three or four sizes make a clear hierarchy; every extra size weakens the others.
- **The person's text size wins** — every role follows the platform's text-size setting, and the layout makes room
  (§11).
- **Consistency is meaning** — the same kind of text takes the same role on every screen, so a role tells the person
  what kind of text they are reading.

## 2. Roles

**Six kinds of text cover most products; each has a job, and a product names the ones it uses.**

| Role | Use for | Never for | Apple text styles | Material roles |
| --- | --- | --- | --- | --- |
| Display | Short, critical text, the largest on the screen — a hero number, a one-line statement on a welcome or summary screen | A paragraph, anything inside a control, more than one per screen | Large Title (and visionOS's Extra Large Titles) | Display large, medium, small |
| Headline | The main heading of a screen that is mostly content, a large top bar that collapses as the page scrolls, and section headings in long reading | Controls, cards; a regular bar's title is the title role | Title 1, Title 2 | Headline large, medium, small |
| Title | The title of a bar, sheet, dialog or card; a list row's primary line; a group's heading | Running text | Title 3, Headline | Title large, medium, small |
| Body | Running text, descriptions, a list row's second line, a field's helper text | Labels inside controls | Body, Callout, Subheadline | Body large, medium, small |
| Label | Text inside a control — a button, a tab, a chip, a navigation item, a field's label | Sentences | Body or Subheadline in a control (the system sets it) | Label large, medium, small |
| Caption | Metadata — a timestamp, a count, a footnote, a legend | Anything the person must read to act or to stay safe | Footnote, Caption 1, Caption 2 | Body small, Label small |

Sources: Apple Human Interface Guidelines, Typography; Android Developers, "Material Design 3 in Compose" — the
platforms' names for their own roles. The brief maps its role tokens (for example `text.title`, `text.body`) to these.

- **Display is for short, critical text** — "the largest text on the screen" (Android Developers, "Material Design 3
  in Compose"); a display role that runs to a second paragraph is a headline.
- **Body is the reading role** — the size and line height chosen for "a comfortable reading experience over multiple
  lines" (Apple Human Interface Guidelines, Typography); every other role is measured against it.
- **A label is short and one line** — when a label needs a sentence, the sentence belongs in body text beside the
  control (the `ux-content` skill).
- **A product rarely needs every role and size** — "Your product will likely not need all 15 default styles"
  (Android Developers, "Material Design 3 in Compose"); the brief names only what screens use.

## 3. The scale

**A small scale with clear steps between roles; each role token holds every value it needs.**

- **Each role token holds its family, size, line height, weight and letter spacing** — set together, so no screen
  mixes a role's size with another role's line height.
- **Steps between roles are wide enough to see** — neighbouring roles differ by more than a pixel or two; a modular
  ratio (each step a fixed multiple of the last, often 1.2 to 1.333) keeps them in proportion (Tim Brown, "More
  Meaningful Typography", A List Apart).
- **Sizes and line heights land on the base grid** — on a 4 base, line heights are multiples of 4, so baselines line
  up with the spacing (the `layout` skill).
- **Sizes may change by window tier, roles never do** — a display or headline may be smaller on a narrow window than a
  wide one, as a token per tier in the brief; body text stays the reading size.
- **Embedded (ESP-IDF, LVGL): each role at each size is a compiled font** — the scale is the list of fonts in the
  firmware, and every extra size costs flash (the `design-system` skill).

## 4. Hierarchy

**One thing on the screen reads first, and the order of the rest is clear from size, weight, colour and space.**

- **One top level per screen** — one text in the screen's highest role, whether that is a display, a headline or a
  bar's title; two equal top levels make the person choose where to start.
- **Change one property at a time to rank** — size, then weight, then colour; a heading that is larger, bolder and a
  different colour has spent three signals on one step.
- **Weight and colour emphasise within a role** — "Adjust font weight, size, and color as needed to emphasize
  important information and help people visualize hierarchy" (Apple Human Interface Guidelines, Typography); colour is
  never the only signal (the `accessibility` skill).
- **Space belongs to its heading** — more space above a heading than below it, so the heading groups with what it
  introduces (the `layout` skill's proximity).
- **The visual levels match the semantic ones** — a heading styled as a title is marked as a heading at its level in
  code, and the levels never skip (the `accessibility` skill, WCAG 1.3.1).

## 5. Families and fonts

**The platform's system font first; at most two families; every font covers every character the product shows.**

- **Start from the system font** — it scales with the person's setting, matches the platform and costs no download:
  SF Pro and New York on Apple platforms, which "support dynamic optical sizes" (Apple Human Interface Guidelines,
  Typography), Roboto and the platform's families on Android, `system-ui` on the web.
- **A custom face earns its place** — a brand that needs it; on Apple platforms "make sure it implements the same
  behaviors" as the system font — Dynamic Type and Bold Text (Apple Human Interface Guidelines, Typography).
- **One or two families** — "Minimize the number of typefaces you use" (Apple Human Interface Guidelines,
  Typography); a second family contrasts with the first in structure (a serif for display over a sans for reading),
  never a near-match.
- **A family's weights before a second family** — weight and size give most of the contrast a screen needs.
- **Variable fonts when the product uses many weights** — one file for every weight and width; Android supports them
  from Android 8 (API 26), and on the web they help mainly where many styles are used (Android Developers, "Work with
  fonts"; web.dev, "Best practices for fonts").
- **Every string draws in the font** — every language the product ships, its punctuation and symbols; a missing glyph
  falls back to another face or a box. On an embedded panel the glyph ranges are compiled in (the `design-system`
  skill).
- **The licence allows the use** — embedding in an app, self-hosting and subsetting on the web each need the licence's
  permission (web.dev, "Best practices for fonts").
- **Web, iOS, Android: icons as SVG or the platform's symbols before an icon font** — an icon font that fails to load
  draws boxes or letters, and its glyphs can reach a screen reader as text; where one is used, each icon is hidden
  from assistive technology and its control carries the name.
- **Embedded (ESP-IDF, LVGL): icons compiled into a font are the norm** — LVGL's built-in symbols or glyphs added with
  the font converter, taking the label's text colour (the `design-system` skill).
- **Web: loading fonts without shifting the layout is the `design-system` skill's** — the weights used, a fallback
  with matched metrics, `font-display`.

## 6. Line height and spacing

**Reading text gets room between lines; large text gets less; capitals and small text get a little more letter
space.**

| Text | Line height | Letter spacing |
| --- | --- | --- |
| Body, several lines | About 1.3 to 1.5 × the size `[D]` | The font's default |
| Titles and headlines | About 1.2 to 1.3 × `[D]` | Default, or slightly tighter at the largest sizes |
| Display | About 1.1 to 1.2 × `[D]` | Slightly tighter |
| All capitals, small capitals | One line | 5 % to 12 % of the size added (Butterick, *Practical Typography*) |
| Caption and small label | About 1.3 × `[D]` | Default, or slightly looser |

The ranges are derived from the platforms' defaults — Apple's Body at 17/22 pt is 1.29, Material's body roles 1.33 to
1.5 and its display large 1.12 — and from Butterick's 120 % to 145 % for running text (Apple Human Interface
Guidelines, Typography; Android Developers, "Material Design 3 in Compose"; Butterick, *Practical Typography*).

- **Three or more lines never get tight leading** — "If you need to display three or more lines of text, avoid tight
  leading" (Apple Human Interface Guidelines, Typography).
- **Line height grows with the text** — a unitless ratio, or a `rem` value, on the web; a line height fixed in `px`
  clips enlarged text. Its value at the default size lands on the base grid (§3).
- **The person may space text further and nothing breaks** — WCAG 1.4.12's values are the `accessibility` skill's.
- **Paragraphs are separated by space or an indent, not both** — on screens, space between paragraphs (Butterick,
  *Practical Typography*).
- **Embedded (ESP-IDF, LVGL): line and letter spacing are style properties** — `text_line_space` and
  `text_letter_space` in pixels, from the role's tokens.

## 7. Line length and alignment

**Running text is held to a readable measure, aligned to its start edge, and wraps rather than truncates.**

- **The measure: about 45 to 75 characters a line for running text in an alphabetic script, never over 80** (Robert
  Bringhurst, *The Elements of Typographic Style*; WCAG 1.4.8 Visual Presentation, AAA). The brief names it as a
  token, in characters where the platform can (`ch` on the web, the width of the "0"); scripts with wider characters,
  such as Chinese, Japanese and Korean, take a shorter measure the brief names per script.
- **A wide window does not lengthen lines** — it gives the text more margin or a second pane (the `layout` skill).
- **Text aligns to its start edge** — left in a left-to-right language, right in a right-to-left one; never a fixed
  "left" that stays left in Arabic or Hebrew.
- **Centre only short text** — a title, one or two lines on an empty state, a dialog's message on a watch; centred
  running text loses the edge the eye returns to (Butterick, *Practical Typography*).
- **Justify only with hyphenation, and never in a narrow column** — "Always use hyphenation with justified text"
  (Butterick, *Practical Typography*); without it, justification opens rivers of space.
- **Wrap before truncating; truncate only where the full text is one step away** — a list row may end in an ellipsis
  when its detail shows the rest; a button, an error or a heading never truncates, and truncation stays rare as the
  text grows ("Keep text truncation to a minimum as font size increases", Apple Human Interface Guidelines,
  Typography).

## 8. Emphasis and case

**Emphasise by weight first, sparingly; underline means a link; capitals are for a few words with added spacing.**

- **Weight first** — one step heavier within the role; bold and italic "as little as possible, and not together"
  (Butterick, *Practical Typography*).
- **Italic for titles of works, terms and a light stress** — not for whole sentences, and only where the face has a
  true italic.
- **Underline only for links** (Butterick, *Practical Typography*); a link in running text is underlined or otherwise
  marked by more than colour (the `accessibility` skill).
- **Avoid the lightest weights for reading** — Apple advises against Ultralight, Thin and Light, preferring Regular,
  Medium, Semibold or Bold (Apple Human Interface Guidelines, Typography); a light weight is for display sizes only.
- **All capitals for less than a line, with letter spacing added** — an eyebrow, a short label; never a sentence
  (Butterick, *Practical Typography*). The capitals are set by style; why the words stay in sentence case is the
  `ux-content` skill's.
- **A role's weight holds in every state** — a hover or a selection never makes text heavier, which would widen it and
  move the layout (the `design-system` skill).

## 9. Numbers

**Figures that change or stack in columns share one width; figures in sentences read like words.**

- **Tabular figures where numbers change or align** — a timer, a counter, prices in a column, a table; proportional
  figures in running text. The spelling on each platform, and on a panel the choice of face, is the `design-system`
  skill's.
- **Columns of numbers align on the decimal point or the right edge**, with the same number of decimals.
- **A unit is smaller or lighter than its number in a hero figure**, never a different baseline; formatting —
  separators, units, dates — is the `ux-content` skill's.

## 10. Editorial treatments

**An editorial treatment is a single, deliberate break from the scale for one piece of content, used once on a
screen.**

- **Display type for one statement** — a welcome line, a summary, a result; short, and the only display text on the
  screen.
- **A hero number** — a large figure in the display role with its unit and label in smaller roles; tabular figures if
  it updates (§9). Wear OS keeps a numerals role for large figures that need no translation (Android Developers, Wear
  OS "Apply the design").
- **An eyebrow above a headline** — a short label in the label role, often in capitals with letter spacing (§8),
  naming the section or category.
- **A pull quote** — a short excerpt set larger, in a title or headline role, apart from the text; it repeats words
  already on the screen, so assistive technology reads it once — the copy is hidden from it, or the quote is not a
  repeat.
- **An initial (a drop cap)** — the first letter of long-form reading set large, sunk into the first lines; decoration
  that keeps the word whole for a screen reader and for search (Robert Bringhurst, *The Elements of Typographic
  Style*).
- **Large, editorial layouts may need a larger role than the scale's top** — visionOS adds Extra Large Title 1 and 2
  "for wide, editorial-style layouts" (Apple Human Interface Guidelines, Typography); a product adds such a role to the
  brief, never as a size on one screen.

## 11. Text that scales

**Every role follows the person's text size, keeps the hierarchy at every size, and never drops below the platform's
minimum.**

- **Carry type in the platform's scaling unit** — `rem` on the web, Dynamic Type text styles on iOS, `sp` on Android
  (the `design-system` skill); text reaches 200 % without loss (WCAG 1.4.4; the `accessibility` skill).
- **The hierarchy holds at every size** — "Maintain a consistent information hierarchy regardless of the current font
  size" (Apple Human Interface Guidelines, Typography); large roles may grow less than body text, but never fall below
  the role under them.
- **The layout makes room** — rows become columns, labels wrap, fixed heights grow (the `layout` skill); "Prioritize
  important content when responding to text-size changes" (Apple Human Interface Guidelines, Typography).
- **The platform's default and minimum sizes** (Apple Human Interface Guidelines, Typography):

| Platform | Default | Minimum |
| --- | --- | --- |
| iOS, iPadOS | 17 pt | 11 pt |
| macOS | 13 pt | 10 pt |
| watchOS | 16 pt | 12 pt |
| visionOS | 17 pt | 12 pt |
| tvOS | 29 pt | 23 pt |

On Android, Material's body roles run 14 to 16 sp and its smallest roles 11 to 12 sp, the working floor (Android
Developers, "Material Design 3 in Compose"). The web has no standard minimum: the brief names one, and body text sits
at 1 rem or larger.

- **Web: body text at 1 rem, the browser's default, or larger** — Butterick puts web body text at 15 to 25 px
  (*Practical Typography*); field text has a floor of its own (the `touch-and-gesture` skill).
- **macOS has no Dynamic Type** (Apple Human Interface Guidelines, Typography) — the product's own text-size setting,
  if it offers one, scales the roles.
- **Embedded (ESP-IDF, LVGL): the person's text size is a product setting, if the product has one** — a set of
  compiled fonts per size, or a run-time font engine (the `design-system` skill); with none, the scale is sized for the
  panel's density and viewing distance.

## 12. Small screens and panels

**On a watch or a small panel, type is fewer roles, larger and shorter; on an LVGL panel, every role is a font
compiled into the firmware.**

- **Fewer roles** — a title, body and a caption at most; a hero number where the screen is a glance.
- **Short text, one or two lines** — a glance reads a word or a figure, not a paragraph (the `layout` skill's small
  screens).
- **Curved text only for a short title or the time at an edge** of a round screen — Wear OS sets surface titles as arc
  text (Android Developers, Wear OS "Apply the design"); running text stays straight and inside the circle.
- **watchOS: 16 pt default, 12 pt minimum** (§11).
- **Embedded (ESP-IDF, LVGL): the role's font is a compiled font** — size, weight and bits per pixel fixed when the
  firmware is built (4 bpp for smooth edges on a colour panel), held in the brief's C header and applied through shared
  styles; a screen never names a font of its own (the `design-system` skill).
- **Embedded (ESP-IDF, LVGL): no italic or bold without a compiled font for it** — emphasis is a heavier compiled font
  or colour plus a second signal; LVGL synthesises neither.
- **Embedded (ESP-IDF, LVGL): set type for the viewing distance** — a panel read at arm's length or across a room needs
  larger roles than a phone at the same pixel density; the size floor at that distance is the `accessibility` skill's.

## 13. The same type on each platform

**Type is decided once, by role, and set with each platform's equivalent.**

| Concept | Web | iOS | Android | Embedded (ESP-IDF, LVGL) |
| --- | --- | --- | --- | --- |
| A role | A CSS class or custom properties from the brief's role token | A `Font.TextStyle`, or a custom font with `relativeTo:` | A `TextStyle` in `MaterialTheme.typography`, or a `TextAppearance` | A shared `lv_style_t` with the role's font, line and letter space |
| A size that scales | `rem` | Dynamic Type text styles; `UIFontMetrics` for a custom font | `sp` | A compiled font per size, or a run-time engine |
| Line height | Unitless `line-height`, or `rem` | The text style's leading; `lineSpacing` adds to it | `lineHeight` in `sp` or `em` | `text_line_space` |
| Letter spacing | `letter-spacing` in `em` | `tracking` | `letterSpacing` | `text_letter_space` |
| Weight | `font-weight` | `.fontWeight` | `FontWeight` | A separate compiled font |
| Start alignment | `text-align: start` | `.leading` alignment | `TextAlign.Start` | `LV_TEXT_ALIGN_AUTO`, which follows the text's direction |
| Hyphenation | `hyphens: auto` with `lang` set | `hyphenationFactor` on the paragraph style | `hyphens = Hyphens.Auto` | None — start-aligned, never justified |
| Measure | `max-width` in `ch` | `readableContentGuide`, a `maxWidth` frame | `widthIn(max =)` | The label's width |
| Wrap or truncate | `overflow-wrap`; `text-overflow: ellipsis`; `text-wrap: balance` for headings | `lineLimit`, `truncationMode` | `maxLines`, `TextOverflow` | The label's long mode — wrap, dots, scroll (`LV_LABEL_LONG_MODE_*` from LVGL 9.3) |

- **iOS: a size outside the text styles scales only through `relativeTo:`, `@ScaledMetric` or `UIFontMetrics`** —
  `.font(.system(size:))` with a literal and `UIFont.systemFont(ofSize:)` are fixed sizes that ignore Dynamic Type.
- **Android: text in `dp` or `px` ignores the person's font scale** — `sp` only.
- **Web: font sizes in `px` ignore the browser's font-size setting** — `rem`, with the root left at the browser's
  default.

## 14. The type spec

**A draft records each text's role, so the build has no type left to decide.**

The draft's values file (`<screen>_mock<n>.md` in the `ui-designer` skill) holds, for each piece of text:

| Field | Holds |
| --- | --- |
| Role | The brief's role token — display, headline, title, body, label or caption, as the brief names them |
| Emphasis | Any weight or colour change within the role, and why |
| Measure and alignment | The measure token for running text; start, or centred and why |
| Wrap or truncate | What happens to the longest string, and at the largest text size |
| Numbers | Tabular or proportional |
| Editorial | Any treatment from §10, and that it is the screen's one |

- **The draft is drawn with the longest string and at the largest text size** the product supports, as well as the
  default.
- **A size or weight that is not a role is a finding at the draft** — the `ui-designer` skill's gate 1; add a role to
  the brief, or use an existing one.

## 15. Reviewing type

**A type review reads the screen at the default and the largest text size, in a fixed order, accessibility first.**

1. **Scaling and floors** — every text in the platform's scaling unit; at 200 % or the largest size nothing is
   clipped, overlapped or lost; nothing under the platform's minimum; text spacing overrides break nothing (§11; the
   `accessibility` skill).
2. **Roles** — every text a role from the brief, used for its job (§2); no size or weight of its own.
3. **Hierarchy** — one top level; ranks clear by one property at a time; visual levels match the headings in code
   (§4).
4. **Families** — the system font or the brief's; at most two families; every glyph present (§5).
5. **Line height and spacing** — reading text not tight; capitals spaced (§6).
6. **Measure and alignment** — running text within the measure; start-aligned; justified only with hyphenation; wraps
   before it truncates (§7).
7. **Emphasis** — weight first; no bold italic; underline only on links; no light weights for reading (§8).
8. **Numbers** — tabular where they change or align (§9).
9. **Editorial** — at most one treatment, and it is the brief's (§10).
10. **The draft** — the built type matches the draft's spec (§14).

## 16. The checks

**The typography check finds what a line of code can show; reading the screen at its largest text size finds the
rest.**

| Check | Finds | § |
| --- | --- | --- |
| Y1 | Web: a font size in `px` — a CSS `font-size` or `font` shorthand, a font-size custom property, Tailwind's `text-[…px]`, a JS style's `fontSize` | §11, §13 |
| Y2 | Web: a line height in `px` — it does not grow with the text | §6 |
| Y3 | Android: text sized in `dp` or `px` — an XML `textSize`, `COMPLEX_UNIT_DIP` or `_PX`, `.dp.toSp()` | §11, §13 |
| Y4 | iOS: a fixed font size that ignores Dynamic Type — `.system(size:)` in a file with no `@ScaledMetric`, `.custom(…, size:)` without `relativeTo:`, `UIFont.systemFont(ofSize:)` or `UIFont(name:size:)` in a file with no `UIFontMetrics` | §11, §13 |
| Y5 | Web: justified text without hyphenation in the same rule or class list | §7 |
| Y6 | A light weight — 100 to 300, `lighter`, Thin, ExtraLight, UltraLight, Light, `sans-serif-light` — which is hard to read at text sizes | §8 |
| Y7 | Web: capitals set by style — `text-transform`, `textTransform`, the `uppercase` class — with no letter spacing in the same rule, style object or class list | §6, §8 |
| Y8 | Embedded: one of LVGL's built-in fonts set on one object with `lv_obj_set_style_text_font`, not the role's shared style | §12 |

- **What no script reads**: a role used for the wrong job, a hierarchy with two top levels, a measure too long, text
  that truncates where it should wrap, a missing glyph, a heading in code at the wrong level. The draft, the review
  and the screen at its largest text size find those.
