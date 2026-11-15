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

**Stability.** Cite this doc as `DESIGN_BRIEF §n`. Do not renumber; add new material under the next free number.

| § | Section | Look here for |
| --- | --- | --- |
| 1 | [The brief](#1-the-brief) | What DESIGN.md holds, its sections and the table shapes the check reads |
| 2 | [Principles](#2-principles) | How the product's tie-breakers are written |
| 3 | [Tokens and roles](#3-tokens-and-roles) | Naming by role, primitives, one owner per value |
| 4 | [Colour](#4-colour) | Kinds, pairs, states, solid surfaces, status hues, icons |
| 5 | [Themes](#5-themes) | Complete themes, dark ordering, re-chosen accents, the first frame |
| 6 | [Type](#6-type) | A scale by role, weights that hold across states, numbers, fonts |
| 7 | [Space, size and stability](#7-space-size-and-stability) | The spacing scale, targets, reserved boxes, states that keep size |
| 8 | [Radius](#8-radius) | A small scale by component size, concentric corners |
| 9 | [Surfaces and elevation](#9-surfaces-and-elevation) | At most a surface step and a shadow, borders against elevation, shadows, hairlines, image edges |
| 10 | [Layers](#10-layers) | A named stacking order |
| 11 | [Gradients and decoration](#11-gradients-and-decoration) | When a gradient, a fade or a glass material earns its place |
| 12 | [Motion tokens](#12-motion-tokens) | Durations, easings and the feedback ladder as tokens |
| 13 | [Components and states](#13-components-and-states) | Reuse, states, the four states of a data view |
| 14 | [Exceptions](#14-exceptions) | A value off the scale, registered with its reason |
| 15 | [Tokens in code](#15-tokens-in-code) | Carrying the brief to the web, iOS and Android |
| 16 | [The checks](#16-the-checks) | What the scripts prove, and what is left to read |

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
  space (OKLCH, a palette tool) keeps its source there and writes the resulting hex here.
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
  Android: tint from the theme).
- **A hover colour may be derived while drafting** (mixing the base with the surface), but the result is written as
  the role's value, so the check can measure it.

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

## 6. Type

**A small scale of text roles — size, line height, weight, use — that follows the person's text-size setting.**

- **Name text by role** — `text.title`, `text.body`, `text.label`, `text.caption` — with its size and line height.
- **Carry type in a unit that scales** — `rem` on the web, Dynamic Type text styles on iOS, `sp` on Android — so text
  reaches 200 % (WCAG 1.4.4).
- **A role's weight is the same in every state**: hover, pressed and selected never change it, since a heavier weight
  is a wider word and the layout moves.
- **Numbers that update use tabular figures** (web: `font-variant-numeric: tabular-nums`; SwiftUI:
  `monospacedDigit()`; Android: the `tnum` font feature), so a counter or a timer does not jitter.
- **A web font is loaded so it does not shift the layout**: only the weights used, the first view's fonts first, and a
  fallback with matched metrics (web.dev, "Best practices for fonts"; MDN, `size-adjust`).

## 7. Space, size and stability

**A spacing scale on a fixed base, a minimum target, and boxes that never move once the person is reading.**

- **One base, a few steps** — a 4 px or 8 px base; space between related things smaller than between groups.
- **A minimum hit area as a token** (`size.target`), at or above WCAG's 24 px; a small control grows its hit area
  without growing its drawing, and two hit areas never overlap.
- **Everything that arrives late has its box reserved** — media with a known aspect ratio, a deferred component with a
  placeholder of its size, a late banner laid over content rather than pushed into it (web.dev, "Cumulative Layout
  Shift").
- **A state change never changes a size** — a label that swaps to "Saving…" keeps its control's width; a selected
  row keeps its height.

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

## 12. Motion tokens

**Durations, easings and scales are tokens like any other, decided in the brief with the surfaces they move.**

- **A few durations, named by size of move** (fast, base, slow), and easings named by job (enter, exit, standard).
- **The feedback ladder is tokens too**: how soon a wait shows an indicator, how fast a spinner turns, and when a
  progress bar replaces it (Nielsen Norman Group, "Response Times: The 3 Important Limits").
- **How each surface enters and leaves** — menu, dialog, sheet, toast — is a table in the brief, so every build of it
  moves the same way.
- **Reduced motion is decided in the brief**: what a move becomes, and what keeps moving (the `accessibility` skill).

## 13. Components and states

**Reuse a component before making one; every component lists its states, and every data view its four.**

- **A component row says what it is for, its states, and what it is not for** — the last column stops the wrong reuse.
- **A one-off moves into the shared components on its second caller**, both callers in the same change.
- **Every state is drawn and has its tokens** — rest, hover, pressed, focus, disabled, selected, loading, error.
- **A view that shows data is designed in four states — loading, empty, error, full — each the size of full.** Empty
  comes in two kinds: first use, which teaches and offers the first action; no results, which says what was searched
  and how to clear it. An error says what happened and the way forward (Nielsen Norman Group, empty states and error
  messages).
- **Loading keeps the shape of what is coming** — a placeholder in the loaded geometry, an action's wait inside its
  control, a refresh that keeps the old content (Nielsen Norman Group, "Skeleton Screens 101").

## 14. Exceptions

**A value off the scale is allowed only with its row in the brief's exceptions: the value, where, and why.**

- **The code line carries `token-exception`** in a comment, so the token check skips it and a reader finds the row.
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
| Any | A token file in the W3C Design Tokens Community Group format, built to each platform by a tool such as Style Dictionary | `color.text.secondary` |

- **Name a code token after its role** — the design check matches any spelling of the same words, so
  `--color-text-secondary` matches `color.text.secondary`, and `--fg-2` does not.
- **A value in code that the brief does not have is drift** — fix the copy that is not the brief.
- **A screen reads tokens, never the primitive ramp or a literal.**

## 16. The checks

**The scripts prove the brief is consistent and present in code; reading proves the rest.**

| Check | Finds |
| --- | --- |
| D1 | A contrast pair under its floor, written with a floor under its kind's, or on a translucent background |
| D2 | A ratio written wrong, or a pair naming an unknown role |
| D3 | A token the brief names, or a colour value it gives, missing from the token files |
| D4 | A pair the kinds call for with no row |
| D5 | A colour with a value in one theme and none in another |
| D6 | A translucent surface or fill |
| T1 | A colour literal in a UI file outside the token files |

- **What no script reads**: a spacing, size, radius, shadow or duration literal in a screen; a depth cue stacked on
  another; a dark overlay whose edge disappears; a state that changes a size. A reviewer reads every number in a
  changed style.
