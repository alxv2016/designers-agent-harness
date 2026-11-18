# Design Brief

How a product's design brief is written and kept: one file, `DESIGN.md` at the repo root, that decides the principles
and every design token by role with a value per theme, and the rules for colour, themes, type, space, radius,
surfaces, layers, decoration, motion, components and exceptions that keep screens consistent. People read it to know
how to decide a value; coding agents read it, through the `design-system` skill, before they change a token or build
a screen.

**Where it lives.** In the `design-system` skill, beside the steps and checks that apply it — [its SKILL.md](../SKILL.md)
— with a starter brief to copy ([templates/DESIGN.md](templates/DESIGN.md)). The skill folder is self-contained: copy
it into any repo's `.agents/skills/` and this reference, the template, the design check and the token check come with
it. The product's own values and choices live in its `DESIGN.md`, cited `DESIGN §n`, and win over this reference.

**Platforms.** Each rule is written for every platform. Guidance that holds on one platform only carries its label —
**Web**, **iOS**, **Android**, **Embedded (ESP-IDF, LVGL)** for a device that draws its own screen with LVGL — in a
bold lead or a table row.

**Stability.** Cite this doc as `DESIGN_BRIEF §n`. Do not renumber; add new material under the next free number.

| Tag | Meaning |
| --- | --- |
| `[D]` | Derived — calculated from cited values, not measured |

| § | Section | Look here for |
| --- | --- | --- |
| 1 | [The brief](#1-the-brief) | What DESIGN.md holds, its sections and the table shapes the check reads |
| 2 | [Principles](#2-principles) | How the product's tie-breakers are written |
| 3 | [Tokens and roles](#3-tokens-and-roles) | Naming by role, primitives, one owner per value |
| 4 | [Colour](#4-colour) | Kinds, pairs, states, solid surfaces, status hues, icons; the panel a device draws on |
| 5 | [Themes](#5-themes) | Complete themes, dark ordering, re-chosen accents, the first frame |
| 6 | [Type](#6-type) | A scale by role, weights that hold across states, numbers, fonts |
| 7 | [Space, size and stability](#7-space-size-and-stability) | The spacing scale, targets, reserved boxes, states that keep size |
| 8 | [Radius](#8-radius) | A small scale by component size, concentric corners |
| 9 | [Surfaces and elevation](#9-surfaces-and-elevation) | At most a surface step and a shadow, borders against elevation, shadows, hairlines, image edges |
| 10 | [Layers](#10-layers) | A named stacking order |
| 11 | [Gradients and decoration](#11-gradients-and-decoration) | When a gradient, a fade or a glass material earns its place |
| 12 | [Motion tokens](#12-motion-tokens) | Durations, easings and the feedback ladder as tokens |
| 13 | [Components and states](#13-components-and-states) | Reuse, states, the four states of a data view; choosing a control by what it does; actions that cannot be undone |
| 14 | [Exceptions](#14-exceptions) | A value off the scale, registered with its reason |
| 15 | [Tokens in code](#15-tokens-in-code) | Carrying the brief to the web, iOS, Android and an embedded device (ESP-IDF, LVGL) |
| 16 | [The checks](#16-the-checks) | What the scripts prove, and what is left to read |
| 17 | [Layout tokens](#17-layout-tokens) | Breakpoint tiers, margins, gutters, the container's cap, pane widths, the measure, density levels |

---

## 1. The brief

**One file decides how the product looks: `DESIGN.md` at the repo root.** It sits beside `AGENTS.md` — that file is
how to work in the repo, this one is what the product should look and feel like.

| § | Holds |
| --- | --- |
| 1 | Principles — the tie-breakers, numbered |
| 2 | Colour — roles with a kind and a value per theme (2.1); every contrast pair with its floor and ratios (2.2) |
| 3–7 | Type, space and size, radius and elevation with the layer order and any decoration, motion, layout — each a token table |
| 8 | Components — what each is for, its states, what it is not for |
| 9 | Accessibility — the floors the product meets above WCAG 2.2 AA |
| 10 | Exceptions — values allowed off the scale, with the reason |
| 11 | Open items — what is not settled, and what would settle it |

- **Keep the table shapes; the design check reads them.** A token table's header starts `| Token |`; the colour table
  adds a `Kind` column and one column per theme (`| Token | Kind | Light | Dark | Use |`); the pairs table is
  `| Foreground | Background | Floor | <Theme> | … |`.
- **Write each colour as hex in the token tables** — the value the checks measure. A product that authors in another
  space (OKLCH, a palette tool) keeps its source there and writes the resulting hex here. The token files spell it
  the platform's way (§15).
- **The numbers in this table are the starter's**; a product's brief may number its sections otherwise, and the
  checks read the table shapes, never the numbers. Skills cite a section by what it holds.
- **Number every section and never renumber** — skills, rubrics and code comments cite `DESIGN §n`.
- **Start from the template** ([templates/DESIGN.md](templates/DESIGN.md)); it passes the design check as it stands.

## 2. Principles

**Five or fewer, numbered; when two options both pass the rules, the lower-numbered principle decides.**

- **Write each as a rule, what it means on a screen, and why** — "Accessible by default" with "contrast pairs come from
  §2.2" beside it, not a value word like "delightful".
- **The person owns the principles.** An agent proposes a change with its reason and never edits one alone.
- **A principle broken on purpose is a recorded decision**, never a silent exception.

## 3. Tokens and roles

**A screen names a role — what the value is for — and the brief gives the role its value in each theme.**

- **Name by role, not by value** — `color.text.secondary`, `space.lg`, `radius.md`; never `grey-600`, `sixteen` or
  `blue`. The name outlives the value, and a theme changes values without touching a screen.
- **A primitive ramp, if the product keeps one, lives only in the token files**, aliased by the roles; no ramp step is
  named at a call site (Material Design 3, colour roles; Apple HIG, semantic colours).
- **One owner per value.** The brief decides it; the token files carry it; a design file is a source for intent, never
  a second owner.
- **A new token answers a need the scale cannot meet on more than one screen.** One screen's odd value is an
  exception (§14), not a token.

## 4. Colour

**Every colour role has a kind, and every pair its kind calls for is written with its floor and checked in every
theme.**

| Kind | Painted | Floor | Paired |
| --- | --- | --- | --- |
| surface | As a background for content | — | Under every text and non-text role |
| text | As words, or an icon that carries meaning | 4.5 | On every surface |
| non-text | As borders, separators, the focus ring | 3 | On every surface |
| fill | As a control's solid background | — (3 when the fill is the control's only boundary: give it `non-text` too) | Under every on-fill role |
| on-fill | As words and icons on a fill | 4.5 | On every fill |
| scrim, exempt | Behind overlays; disabled, decorative, logotypes | none | Not paired |

- **Floors are WCAG 2.2's**: 4.5:1 for text, 3:1 for non-text (1.4.3, 1.4.11); a brief may raise one, never lower it.
- **Every interactive state is its own role value** — rest, hover, pressed, focus, disabled, selected — never an
  opacity trick on text, whose painted colour then depends on what is under it. Two states may share a value when they
  look the same (hover and pressed on a phone-first product), never a computed one.
- **A selected or on state carries a shape** — a checkmark, a leading bar, a filled switch — not only a tint, which
  is colour alone (WCAG 1.4.1); and never a ring, which reads as focus.
- **The focus ring is drawn outside its control with a gap**, so it is measured against the surface, never the
  control's fill — the only way a focus colour equal to the accent still shows on an accent button.
- **A surface or fill is solid.** A tint behind content (a selected row, a status banner) is its own solid role, not a
  translucent accent laid over the surface; a translucent tint goes grey on dark and has no fixed colour to check.
  Only a scrim or an exempt role is translucent (D6).
- **Status hues stay apart from the accent** — when success shares the accent's hue, "the primary action" and "it
  worked" look alike; words and icons still carry the meaning (WCAG 1.4.1).
- **Icons take the text role they sit with**, so they follow the theme (web: `currentColor`; iOS: template rendering;
  Android: tint from the theme; Embedded (ESP-IDF, LVGL): a symbol-font icon takes the label's `text_color`, an
  image icon `image_recolor` at full `image_recolor_opa`).
- **A hover colour may be derived while drafting** (mixing the base with the surface), but the result is written as
  the role's value, so the check can measure it.
- **When the product ships on one known panel, the brief names it and its values are chosen for it.** A browser or a
  phone shows the product on many screens; a device shows it on one, and the panel changes what a value looks like.

| Embedded (ESP-IDF, LVGL): the panel | What the brief decides |
| --- | --- |
| Colour depth | The depth the display is driven at (`LV_COLOR_DEPTH`; `LV_COLOR_FORMAT_DEFAULT` in LVGL releases after 9.5). At 16-bit RGB565, LVGL keeps the top 5 bits of red and blue and 6 of green, so each value moves by up to 7 levels per channel, a grey takes a green or magenta tint (`#767676` paints `#737573`), and near-black surface steps can merge `[D]`. Surface steps stay far enough apart to survive it; a pair near its floor is measured again on the painted value, which moves a ratio by about 0.1 `[D]` |
| AMOLED | A black pixel is unlit: it draws no current and shows true black, so the dark canvas is `#000000` and every raised surface a lighter step (§5). A static, bright element — a status bar, a logo, a clock face — ages its pixels unevenly (burn-in): the brief keeps static elements dim, moves or dims them over time, and names when the screen sleeps |
| LCD | The backlight lights every pixel, so black is a dark grey, saves no power, and a dark canvas gains nothing over a near-black one; viewing angle shifts contrast, so pairs keep margin above their floors |
| Brightness | A brightness setting scales every colour; the brief names the lowest level the product allows, and the darkest surface steps and the `non-text` pairs are checked on the device at that level, where an AMOLED panel crushes near-black steps together |

## 5. Themes

**A theme is a second column of values for the same roles — complete, checked, and chosen on the first frame.**

- **Every role has a value in every theme column** (D5), and every image, illustration and embedded widget has a
  version per theme. Half a dark mode — a white dropdown on dark — is worse than none (Apple HIG, Dark Mode).
- **In dark, lighter means higher**: the canvas is darkest and each raised layer is lighter, the topmost lightest; an
  inverted order makes overlays sink (Material Design 3, tonal elevation; Apple HIG, base and elevated backgrounds).
- **Dark accents are re-chosen per role, on the same hue, by moving lightness** — a mirrored light step turns text
  pastel and tints vanish; draining saturation changes the brand into a duller colour.
- **The product declares to the platform exactly the themes it has**, so native controls, scrollbars and autofill
  match (web: `color-scheme`; iOS: the interface style; Android: the DayNight theme).
- **The right theme is on the first frame, and switching themes is one change, not every colour animating at its own
  pace** — a flash of the wrong theme reads as broken (MDN, `prefers-color-scheme`).
- **Embedded (ESP-IDF, LVGL): there is no system appearance to follow or declare.** A theme is a product setting,
  stored on the device (in NVS) and read before the first screen is built; the display stays dark until that first
  frame is drawn. Switching restyles at run time: the shared `lv_style_t`s take the other theme's values and
  `lv_obj_report_style_change(NULL)` redraws every object that uses them, or the LVGL theme is initialised again
  (`lv_theme_default_init(…, dark, …)` restyles the display it is given). A single-theme device writes one column.
- **Embedded (ESP-IDF, LVGL): on an AMOLED panel, dark is often the product's only theme** — black pixels draw no
  current and do not heat the panel, so a light theme costs battery and age (§4, the panel table).

## 6. Type

**A small scale of text roles — size, line height, weight, use — that follows the person's text-size setting.** How
each role is applied on a screen — which role goes where, hierarchy, the measure, emphasis — is the `typography`
skill's.

- **Name text by role** — `text.title`, `text.body`, `text.label`, `text.caption` — with its size and line height.
- **Carry type in a unit that scales** — `rem` on the web, Dynamic Type text styles on iOS, `sp` on Android — so text
  reaches 200 % (WCAG 1.4.4).
- **A role's weight is the same in every state**: hover, pressed and selected never change it, since a heavier weight
  is a wider word and the layout moves.
- **Numbers that update use tabular figures** (web: `font-variant-numeric: tabular-nums`; SwiftUI:
  `monospacedDigit()`; Android: the `tnum` font feature; Embedded (ESP-IDF, LVGL): a compiled font carries the
  face's default digits, so choose a face whose default digits share one width, or give each digit a fixed box), so a
  counter or a timer does not jitter.
- **Web: a web font is loaded so it does not shift the layout**: only the weights used, the first view's fonts first,
  and a fallback with matched metrics (web.dev, "Best practices for fonts"; MDN, `size-adjust`).
- **Embedded (ESP-IDF, LVGL): the type scale is the list of fonts compiled into the firmware.** LVGL's built-in
  engine draws a font converted ahead of time (`lv_font_conv`) to C arrays at one size and one bit depth, kept in
  flash, so each role's size and weight is its own font (`text.title` → a 28 px semibold font) and every font costs
  flash. The brief lists each compiled font beside its role: face, size, weight, bits per pixel (4 for smooth edges
  on a colour panel, 1 for a monochrome one), and the glyph ranges it holds.
- **Embedded (ESP-IDF, LVGL): a compiled font holds only the glyphs it was given** — the ranges and symbols the
  converter took — and a missing glyph draws as a box (`LV_USE_FONT_PLACEHOLDER`) or nothing, unless the font's
  `fallback` font has it. Every string the product shows, in every language it ships, is drawn from the fonts'
  ranges; the brief names them.
- **Embedded (ESP-IDF, LVGL): the person's text size is a product setting, if the product has one** — a choice
  between compiled sets of fonts, or a run-time engine (`tiny_ttf`, FreeType) that renders any size at a cost in RAM
  and time. With no setting, the scale is sized for the panel's density and viewing distance.

## 7. Space, size and stability

**A spacing scale on a fixed base, a minimum target, and boxes that never move once the person is reading.**

- **One base, a few steps** — a 4 px or 8 px base. How the steps are applied — proximity, margins, gutters, gaps,
  density — is the `layout` skill's.
- **A minimum hit area as a token** (`size.target`), at or above WCAG's 24 px; a small control grows its hit area
  without growing its drawing, and two hit areas never overlap.
- **Everything that arrives late has its box reserved** — media with a known aspect ratio, a deferred component with a
  placeholder of its size, a late banner laid over content rather than pushed into it (web.dev, "Cumulative Layout
  Shift").
- **A state change never changes a size** — a label that swaps to "Saving…" keeps its control's width; a selected
  row keeps its height.
- **Embedded (ESP-IDF, LVGL): a pixel is the panel's own pixel**, at a density the brief knows — there is no CSS
  pixel, point or dp in between. The brief records the panel's resolution and density, and sets `size.target` and
  the type scale from physical size (millimetres at that density) and the viewing distance, then writes them in px.

## 8. Radius

**A small radius scale assigned by component size, and corners that nest.**

- **Radius by size of thing** — small for tags, medium for controls and rows, large for cards and sheets — not one
  generous radius on everything (Material Design 3, shape scale).
- **A nested corner is concentric: inner = outer − the gap between the edges**, rounded down to a radius token, 0
  under the smallest; a repeated outer radius pinches the gap at the corner.
- **Past a wide gap, the two surfaces stop reading as nested**, and the inner one takes its component's own radius;
  the brief names the space step where that starts (the starter uses `space.xl`).

## 9. Surfaces and elevation

**Each surface shows its depth with at most a step in surface colour and a shadow, from a short ladder of named
levels; a line that carries meaning stays a border.**

| Cue | For | Contrast |
| --- | --- | --- |
| Elevation (a shadow) | Cards, menus, sheets, dialogs over the canvas | None needed — it is depth, not information |
| A step in surface colour | Grouped content on the canvas; raised layers in dark | None needed |
| A border | A field's outline, a divider that separates meaning | 3:1 (WCAG 1.4.11) |
| A faint edge | A non-interactive raised surface in dark where a shadow cannot read; an image against a matching surface | None — a role of kind `exempt`; never the only boundary of something a person can press |

- **A surface takes at most a step in surface colour and a shadow**; an edge joins them only where the shadow cannot
  read (in dark). Edge plus shadow plus tint plus gradient reads as decoration (Material Design 3, elevation).
- **Anything a person can press keeps a boundary at 3:1** — a border, or a fill that passes on its surface — even when
  it is also raised (WCAG 1.4.11).
- **A raised container takes elevation; a control's outline and a meaningful divider take the border role** — a card
  with only a border has no depth, and a field with only a shadow has no visible boundary.
- **Elevation is a short ladder of named levels**, rising in offset and blur more than in darkness — a darker shadow
  looks dirty, a softer wider one looks farther.
- **A shadow is translucent**, so it composites over any background; an opaque grey is tuned to one surface only.
- **A convincing shadow often has two layers** — a tight contact shadow and a wide ambient one; a single large blur
  can read as a glow (Material Design, key and ambient light).
- **These shadow rules are written web-first; the intent carries to every platform** — a ladder of levels, one light
  direction, a visible edge in dark. Android draws elevation from one value per level and iOS sets a layer's shadow,
  so each level maps to the platform's own way of drawing it.
- **Embedded (ESP-IDF, LVGL): depth is a surface step and an edge before it is a shadow.** A shadow costs frame time
  (what it costs: `MOTION §7.1`), and on a black AMOLED canvas a dark shadow cannot read at all. The elevation ladder
  on a device is surface steps and a faint edge; a shadow level is allowed only where the panel was measured to hold
  its frame rate with it.
- **All shadows share one light direction**, the same offset sign on every level.
- **An interactive raised surface changes only its elevation on hover or press**, and only that property animates.
- **In dark, every raised surface's edge stays visible** — by a lighter surface, a faint light edge, or both — checked
  on every menu, popover, sheet and dialog, including where one overlaps a card.
- **Hairlines are the device's thinnest crisp line** on dense screens, from a border-width token.
- **Photos and screenshots get a faint neutral edge inside their bounds** — translucent black in light, translucent
  white in dark, never a tinted grey — so they hold their shape against a near-matching surface.

## 10. Layers

**Stacking order is a named scale, decided in the brief beside elevation; no ad-hoc large numbers in code.**

- **Name each layer by what sits there** — raised content, sticky headers, menus, the scrim, overlays (sheets and
  dialogs), toasts, tooltips — and fix their order once: does a toast sit above an open dialog?
- **Overlays render at the top level of the screen**, not inside a parent that clips them (MDN, stacking context).
- **Embedded (ESP-IDF, LVGL): there is no z-index; order is the object tree.** A child draws over its parent and
  over the siblings created before it; `lv_obj_move_to_index` reorders siblings. The screen's layers set the rest:
  the active screen, then `lv_layer_top()` for overlays that outlive a screen change (dialogs, toasts), then
  `lv_layer_sys()` above everything. The brief's named order says which parent or layer each one is created on.
- **A stress walk proves the order**: a dialog, a menu inside it, a tooltip inside that, and a toast, all open at
  once; nothing covers what it should not, and focus is never hidden (WCAG 2.4.11).

## 11. Gradients and decoration

**Decoration is rare, has a job, and is built from the palette's roles.**

- **At most one gradient per screen, with a job**; several decorative gradients are a common sign of a generated look.
- **A gradient to transparent uses eased stops, and a two-hue gradient interpolates in a perceptual colour space** —
  a straight ramp bands and greys its middle (MDN, `<color-interpolation-method>`).
- **Fade content with a mask on the content**, not an overlay painted in the background colour, which matches one
  surface only (MDN, `mask-image`).
- **Never fade over content that scrolls**; an overflow hint shows only while there is more to reach.
- **Text over a gradient, an image or a glass material is measured at its worst point** (WCAG 1.4.3).
- **Decorative layers never take input or focus**, and are hidden from assistive tech (WCAG 1.1.1).
- **A translucent glass material only where real content moves behind it** — blur over a flat colour costs
  rendering and says nothing (Apple HIG, materials). Its role is `exempt`, so the check does not pair it; the text on
  it is measured by hand at its worst point.
- **Embedded (ESP-IDF, LVGL): a gradient bands at 16-bit colour, and LVGL 9's software renderer does not dither it.**
  RGB565 has 32 levels of red and blue and 64 of green, so a wide gradient shows steps, worst in dark, slow ramps.
  Keep a gradient's lightness span short, or draw it as an image dithered when it is made; check it on the panel, as
  a computer screen at 24-bit hides the bands. A gradient takes at most `LV_GRADIENT_MAX_STOPS` stops (2 unless
  raised, each extra stop costing RAM), interpolates in RGB, and an angled, radial or conic one needs
  `LV_USE_DRAW_SW_COMPLEX_GRADIENTS`.
- **Embedded (ESP-IDF, LVGL): a gradient, a fade or a blur is allowed only where the panel was measured to hold its
  frame rate with it** — what each costs a frame is `MOTION §7.1`'s.

## 12. Motion tokens

**Durations, easings and scales are tokens like any other, decided in the brief with the surfaces they move.**

- **A few durations, named by size of move** (fast, base, slow), and easings named by job (enter, exit, standard).
- **The feedback ladder is tokens too**: how soon a wait shows an indicator, how fast a spinner turns, and when a
  progress bar replaces it (Nielsen Norman Group, "Response Times: The 3 Important Limits").
- **How each surface enters and leaves** — menu, dialog, sheet, toast — is a table in the brief, so every build of it
  moves the same way.
- **Reduced motion is decided in the brief**: what a move becomes, and what keeps moving (the `accessibility` skill).
- **Embedded (ESP-IDF, LVGL): an easing token is a path callback.** A duration is a millisecond constant; a named
  easing maps to `lv_anim_path_ease_out` and its siblings, or a `cubic-bezier()` value to
  `lv_anim_path_custom_bezier3` with `lv_anim_set_bezier3_param` (its points scaled by `LV_BEZIER_VAL_FLOAT`), so a
  device and a web build of the same token move alike.

## 13. Components and states

**Reuse a component before making one, and choose it by what it does; every component lists its states, and every data
view its four.**

- **A component row says what it is for, its states, and what it is not for** — the last column stops the wrong reuse.
- **A one-off moves into the shared components on its second caller**, both callers in the same change.
- **Every state is drawn and has its tokens** — rest, hover, pressed, focus, disabled, selected, loading, error.
- **A view that shows data is designed in four states — loading, empty, error, full — each the size of full.** Empty
  comes in two kinds: first use, which teaches and offers the first action; no results, which says what was searched
  and how to clear it. An error says what happened and the way forward (Nielsen Norman Group, empty states and error
  messages).
- **Loading keeps the shape of what is coming** — a placeholder in the loaded geometry, an action's wait inside its
  control, a refresh that keeps the old content (Nielsen Norman Group, "Skeleton Screens 101").
- **Choose the control for a setting or an action by what it does, before laying out the rows.** A control promises
  what happens when it is used: a list row reads as a place to go or a value to read, a field as text to edit, a
  button as "do this". A control that breaks its promise — a row that opens a prompt for typed text, a row that
  deletes — misleads before it is ever pressed.

| What the person does | Control |
| --- | --- |
| Types a value and keeps it | A field that shows what it holds — not a list row that opens a prompt |
| Turns one thing on or off, applied at once | A switch, the whole row its target |
| Picks one of two to four short options | A segmented control or a radio set |
| Picks one of more options than fit a row | A list or a picker — a dropdown, or a wheel where the options are a sequence |
| Sets a number in a range, watching it change | A slider, applied as it moves |
| Reads a value it cannot set | A reading: a label and its value, never drawn as a control |
| Starts an action | A button, named for the action |

- **When typed text is checked and where the problem is said is `ACCESSIBILITY §9`'s** (forms and errors); the
  brief's field component carries the error state that rule needs.
- **An action that cannot be undone is its own button in the brief's danger role, never a list row.** The danger
  role is a `fill` with its `on-fill` pair (§4), a status hue kept apart from the accent; it says the action cannot be
  taken back.
- **It still asks first.** The colour warns; the confirmation is what stops a stray press. Where its first focus
  lands is `FOCUS §5`'s, and the words on its buttons are `UX_CONTENT §5`'s.

| Platform | The confirmation |
| --- | --- |
| Web | A `<dialog>` opened with `showModal()`, its choices `<button>`s; `autofocus` sets the first focus (which button: `FOCUS §5`) |
| iOS | An alert, or an action sheet for a choice tied to what was tapped: `UIAlertController` with `UIAlertAction` styles `.destructive` and `.cancel`; in SwiftUI, `.alert` or `.confirmationDialog` with `Button(role: .destructive)` and `Button(role: .cancel)` |
| Android | A Material dialog — `MaterialAlertDialogBuilder`, or Compose's `AlertDialog` — the action as its confirm button, Cancel as its dismiss button |
| Embedded (ESP-IDF, LVGL) | A message box: `lv_msgbox_create(NULL)` draws it modal, over a backdrop on `lv_layer_top()`, with its choices from `lv_msgbox_add_footer_button`; with a keypad or an encoder, `lv_group_focus_obj` sets the first focus as it opens (which button: `FOCUS §5`) |

- **The components are a closed set.** A setting takes one of the brief's components; one that seems to need a new
  kind of control is a new component, decided in the brief before any code: the component it would replace, why that
  one fails, then its row by the first rule of this section.
- **Embedded (ESP-IDF, LVGL): a component is a set of shared styles and one function that builds the widget.** The
  styles (`lv_style_t`, initialised once from the tokens) carry the looks; the function creates the LVGL widget and
  adds them with `lv_obj_add_style(obj, &style, selector)`, one per state — `LV_STATE_PRESSED`, `LV_STATE_FOCUSED`,
  `LV_STATE_CHECKED` for selected, `LV_STATE_DISABLED` — so every instance takes each state from the same tokens,
  and a screen restyles none of them with its own `lv_obj_set_style_*` calls. The token header holds values and
  styles only; the builders sit in a widgets module above it, so a colour change never changes a widget tree. A
  touch-only device has no hover state (`LV_STATE_HOVERED` needs a pointer); a device driven by a knob or keys has
  focus.

## 14. Exceptions

**A value off the scale is allowed only with its row in the brief's exceptions: the value, where, and why.**

- **The code line carries `token-exception`** in a comment (`/* token-exception */`, `// token-exception` in C and
  C++), so the token check skips it and a reader finds the row.
- **A computed value is not an exception** — a nested radius from the rule in §8, a hover colour written as a role.
- **An exception that spreads to a second screen becomes a token.**

## 15. Tokens in code

**The token files carry the brief's values to the platform, named after the roles, generated from the brief or kept in
step by hand.**

| Platform | Where tokens usually live | A role named `color.text.secondary` becomes |
| --- | --- | --- |
| Web | CSS custom properties, one block per theme (`:root`, `[data-theme="dark"]`, `prefers-color-scheme`) | `--color-text-secondary` |
| iOS | An asset catalog colour set with Any and Dark appearances; a Swift extension for the rest | `colorTextSecondary` / `Color.textSecondary` |
| Android | Theme attributes and `values/` + `values-night/` resources; a Compose theme object | `color_text_secondary` / `textSecondary` |
| Embedded (ESP-IDF, LVGL) | A C or C++ header of `constexpr` values named by role (`static const` or `#define` in C), with the shared `lv_style_t`s built from them once at start and the compiled fonts declared (`LV_FONT_DECLARE`); one value set per theme | `kColorTextSecondary` = `0x6B7280`, painted as `lv_color_hex(kColorTextSecondary)` |
| Any | A token file in the W3C Design Tokens Community Group format, built to each platform by a tool such as Style Dictionary | `color.text.secondary` |

- **Name a code token after its role** — the design check matches any spelling of the same words, so
  `--color-text-secondary`, `colorTextSecondary` and `kColorTextSecondary` match `color.text.secondary`, and `--fg-2`
  does not.
- **Write each colour with the brief's exact digits in the platform's spelling** — `#6B7280` in CSS, `0x6B7280` in C
  and C++ (any case, an integer suffix allowed); the design check accepts both and no other number (D3).
- **A value in code that the brief does not have is drift** — fix the copy that is not the brief.
- **A screen reads tokens, never the primitive ramp or a literal.**
- **Embedded (ESP-IDF, LVGL): a theme is a second set of the same constants, chosen at run time** — a struct of role
  values per theme, or one array per role indexed by theme, so restyling (§5) swaps the set and rebuilds the styles
  from it. Both sets live in the token header, so the design check finds every theme's value.
- **Embedded (ESP-IDF, LVGL): a translucent role keeps the brief's eight digits in one constant** (`0x00000066` for
  `#00000066`, read as RRGGBBAA), split where it is painted into the colour (`lv_color_hex(c >> 8)`) and the opacity
  (`(lv_opa_t)(c & 0xFF)`), since LVGL takes the two apart.

## 16. The checks

**The scripts prove the brief is consistent and present in code; reading proves the rest.**

| Check | Finds |
| --- | --- |
| D1 | A contrast pair under its floor, written with a floor under its kind's, or on a translucent background |
| D2 | A ratio written wrong, or a pair naming an unknown role |
| D3 | A token the brief names, or a colour value it gives, missing from the token files — a colour matched in CSS or C spelling (§15) |
| D4 | A pair the kinds call for with no row |
| D5 | A colour with a value in one theme and none in another |
| D6 | A translucent surface or fill |
| T1 | A colour literal in a UI file outside the token files; in C and C++, only a number in a colour's place — LVGL's colour constructors and palette, a colour-named call, a label recolour — outside comments, and never an address or a register value |

- **Both scripts say how many files they read**, and a run that read none says so, so a pass is never an empty one.
- **What no script reads**: a spacing value on the base grid but off the scale (the `layout` skill's check finds one
  off the base grid), and a size, radius, shadow or duration literal in a screen; a depth cue stacked on
  another; a dark overlay whose edge disappears; a state that changes a size; on a device, a font that is not in the
  brief's compiled list, banding in a gradient, and a value that the panel's colour depth paints differently. A
  reviewer reads every number in a changed style, and the panel shows the rest.

## 17. Layout tokens

**The brief's layout section names the tiers a screen changes at and every width a layout uses, so no screen decides
one for itself.**

| Token | Holds |
| --- | --- |
| `breakpoint.sm` … `breakpoint.xxl` | Bootstrap's tiers, with the values the `layout` skill gives, each with what changes from it up |
| Margins by tier | The screen's edge, a spacing step per tier, smaller below `breakpoint.md` |
| `size.gutter` | The gap between grid columns and between panes |
| `size.content-max`, or a cap per tier | The widest the content runs, centred |
| `size.pane-min`, pane widths | A pane's minimum, and a fixed pane's width |
| The measure | The widest a line of running text runs, in characters where the platform can |
| Density levels | Each level as whole steps of the spacing scale; never a smaller target |
| Small screens | The width below which a screen is laid out as a small screen, a watch's or round panel's margins as a percentage of the screen, and the smallest size supported |

- **Name only what the product uses** — a product with no panes names no pane width; a device with one fixed panel
  names no breakpoint and records the panel's resolution and density instead (§7); the `layout` skill still places
  that panel in a tier by its logical width, to choose its structure.
- **Every value lands on the spacing scale's base**, and a tier is never a value between Bootstrap's — a component that
  must change at its own width uses its container's width, not a new tier.
- **The layout check reads the `breakpoint.*` rows**, so they keep the token table's shape (§1); how each token is
  used is the `layout` skill's.
