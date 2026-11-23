---
version: alpha
name: <Project>
description: <One line — what the product is and how it should feel.>
colors:
  light:
    bg:
      canvas: "#FFFFFF"
      surface: "#F4F5F7"
      overlay: "#FFFFFF"
    scrim: "#00000066"
    text:
      primary: "#1B1D21"
      secondary: "#585E69"
      on-primary: "#FFFFFF"
      disabled: "#A3A8B0"
    primary: "#2457D6"
    primary-pressed: "#1B45AD"
    border: "#7D838D"
    focus: "#2457D6"
  dark:
    bg:
      canvas: "#111317"
      surface: "#1B1E24"
      overlay: "#22262E"
    scrim: "#00000099"
    text:
      primary: "#F2F3F5"
      secondary: "#A9AFBA"
      on-primary: "#0B1020"
      disabled: "#5A606B"
    primary: "#7EA2FF"
    primary-pressed: "#A5BEFF"
    border: "#7A818E"
    focus: "#7EA2FF"
typography:
  title:
    fontFamily: "system-ui, sans-serif"
    fontSize: 22px
    lineHeight: 28px
    fontWeight: 600
  body:
    fontFamily: "system-ui, sans-serif"
    fontSize: 16px
    lineHeight: 24px
    fontWeight: 400
  label:
    fontFamily: "system-ui, sans-serif"
    fontSize: 14px
    lineHeight: 20px
    fontWeight: 500
  caption:
    fontFamily: "system-ui, sans-serif"
    fontSize: 13px
    lineHeight: 18px
    fontWeight: 400
spacing:
  xs: 4px
  sm: 8px
  md: 12px
  lg: 16px
  xl: 24px
size:
  target: 44px
breakpoint:
  sm: 576px
  md: 768px
  lg: 992px
  xl: 1200px
  xxl: 1400px
rounded:
  sm: 4px
  md: 8px
  lg: 16px
elevation:
  light:
    overlay: "0 8px 24px rgba(0, 0, 0, 0.24)"
  dark:
    overlay: "0 8px 24px rgba(0, 0, 0, 0.24)"
layer:
  raised: 1
  sticky: 10
  scrim: 20
  overlay: 30
  menu: 40
  toast: 50
  tooltip: 60
duration:
  fast: 120ms
  base: 200ms
easing:
  enter: "cubic-bezier(0.22, 1, 0.36, 1)"
  exit: "cubic-bezier(0.33, 1, 0.68, 1)"
motion:
  hover:
    duration: "{duration.fast}"
    timingFunction: "{easing.exit}"
  menu-enter:
    duration: "{duration.base}"
    timingFunction: "{easing.enter}"
  menu-exit:
    duration: "{duration.fast}"
    timingFunction: "{easing.exit}"
---

# `<Project>` — Design

> **Starter.** Copy this file to the repo root as `DESIGN.md` and replace every example with your product's
> principles and values. It is in [Google's DESIGN.md format](https://github.com/google-labs-code/design.md): keep the
> front matter's keys, the section names and their order, and the tables' shapes — the design check reads them. How
> each part is written: the `design-system` skill's references/brief.md.

The design brief for this product: the YAML front matter above holds every design token, with a value per theme; the
sections below say what each one is for, and the principles every screen follows. People read it to know how the
product looks and why; coding agents read it before any UI work and take every value from the tokens it names.

**Source of truth.** The front matter decides every token value; the prose decides how to apply them. The token files
in code carry the same values to the platform. Where code and this file disagree, find which side is intended, then
fix the other in the same change. The design check (`design_check.py`) proves the [contrast pairs](#contrast-pairs)
meet their floors, that every pair the colour kinds call for is there, that the ratios written are true, that every
theme has a value, and that every token named here exists in the token files.

**Stability.** Cite this file by section name — `DESIGN.md → Colors`. Keep Google's section names and order; add a
section of the product's own after Do's and Don'ts.

| Tag | Meaning |
| --- | --- |
| `[SPEC]` | From a standard — WCAG 2.2, a platform's design guidelines |
| `[DES]` | From the design file, frame or component named beside it |
| `[?]` | Unverified — tracked in [Open items](#open-items) |

| Section | Look here for |
| --- | --- |
| [Overview](#overview) | What every screen holds to, and why; the tie-breakers |
| [Colors](#colors) | Colour roles and their kinds; contrast pairs and their ratios |
| [Typography](#typography) | The type roles and where each goes |
| [Layout](#layout) | The spacing scale; tap target; breakpoints and how screens adapt |
| [Elevation & Depth](#elevation--depth) | Depth per theme, the stacking order |
| [Shapes](#shapes) | Corner radii and the nesting rule |
| [Motion](#motion) | Durations, easings, each move; reduced motion |
| [Voice & Content Strategy](#voice--content-strategy) | How the product speaks: voice, case, the words it uses |
| [Components](#components) | What each component is for, its states, when not to use it |
| [Do's and Don'ts](#dos-and-donts) | The principles as guardrails |
| [Accessibility](#accessibility) | The floors this product meets |
| [Exceptions](#exceptions) | Values allowed off the scale, and why |
| [Open items](#open-items) | What is not settled yet, and what would settle it |

---

## Overview

`<Two sentences: what the product is, and how it should look and feel.>` Five principles or fewer. When two options
both pass the rules, the lower-numbered principle decides; each principle's practice is in
[Do's and Don'ts](#dos-and-donts).

1. **`<A rule the product holds to>`** Why: `<the reason, and what breaks without it>`.
2. **Accessible by default.** Why: a screen that some people cannot use is not finished.
3. **Every colour, size, space, radius, duration and easing is a token from this file.** Why: one change here reaches
   every screen, and a theme changes values without touching screens.

---

## Colors

### Roles

Screens use roles, never raw values; a theme is a second set of values for the same roles — the front matter's
`colors.light` and `colors.dark`. A role's token is its path under its theme: `colors.light.bg.canvas` is
`color.bg.canvas`. Each role has a kind, which says what it may be painted on and which floor applies.

| Kind | Means | Paired in [Contrast pairs](#contrast-pairs) |
| --- | --- | --- |
| surface | A background a screen paints content on | As the background for every text and non-text role |
| text | Painted as words — or as an icon that carries meaning | On every surface, floor 4.5 |
| non-text | Borders, separators, the focus ring | On every surface, floor 3 |
| fill | A solid background for a control | As the background for every on-fill role |
| on-fill | Words and icons on a fill | On every fill, floor 4.5 |
| scrim, exempt | Never under text; disabled, decorative, or a logotype | Not paired |

| Token | Kind | Use |
| --- | --- | --- |
| `color.bg.canvas` | surface | The page behind everything |
| `color.bg.surface` | surface | Cards, grouped rows |
| `color.bg.overlay` | surface | Sheets, dialogs, menus — above the scrim; the lightest layer in dark |
| `color.scrim` | scrim | Behind a sheet or dialog; never under text |
| `color.text.primary` | text | Body text, titles |
| `color.text.secondary` | text | Supporting text, captions, placeholders |
| `color.text.on-primary` | on-fill | Text on `color.primary` and `color.primary-pressed` |
| `color.primary` | text, fill | The primary action, links, selection |
| `color.primary-pressed` | fill | The primary action while pressed or hovered |
| `color.text.disabled` | exempt | Disabled controls' text and icons — never anything enabled |
| `color.border` | non-text | Control borders and separators that carry meaning |
| `color.focus` | non-text | The focus ring |

### Contrast pairs

Every pair the kinds in [Roles](#roles) call for, with its floor and its ratio in each theme. Floors: 4.5 for text, 3
for non-text `[SPEC]` (WCAG 1.4.3, 1.4.11). Run the design check and write the ratios it computes.

| Foreground | Background | Floor | Light | Dark |
| --- | --- | --- | --- | --- |
| `color.text.primary` | `color.bg.canvas` | 4.5 | 16.88 | 16.75 |
| `color.text.primary` | `color.bg.surface` | 4.5 | 15.47 | 15.04 |
| `color.text.secondary` | `color.bg.canvas` | 4.5 | 6.52 | 8.44 |
| `color.text.secondary` | `color.bg.surface` | 4.5 | 5.98 | 7.58 |
| `color.primary` | `color.bg.canvas` | 4.5 | 6.16 | 7.53 |
| `color.primary` | `color.bg.surface` | 4.5 | 5.65 | 6.76 |
| `color.text.primary` | `color.bg.overlay` | 4.5 | 16.88 | 13.66 |
| `color.text.secondary` | `color.bg.overlay` | 4.5 | 6.52 | 6.88 |
| `color.primary` | `color.bg.overlay` | 4.5 | 6.16 | 6.14 |
| `color.border` | `color.bg.canvas` | 3 | 3.82 | 4.74 |
| `color.border` | `color.bg.surface` | 3 | 3.50 | 4.26 |
| `color.border` | `color.bg.overlay` | 3 | 3.82 | 3.87 |
| `color.focus` | `color.bg.canvas` | 3 | 6.16 | 7.53 |
| `color.focus` | `color.bg.surface` | 3 | 5.65 | 6.76 |
| `color.focus` | `color.bg.overlay` | 3 | 6.16 | 6.14 |
| `color.text.on-primary` | `color.primary` | 4.5 | 6.16 | 7.66 |
| `color.text.on-primary` | `color.primary-pressed` | 4.5 | 8.40 | 10.29 |

- **The focus ring is drawn outside the control with a gap**, so it is measured against the surface the control sits
  on, never against the control's own fill — `color.focus` equals `color.primary` here.
- **In dark, a higher layer is lighter**: `color.bg.canvas`, then `color.bg.surface`, then `color.bg.overlay`.
- **A selected state carries a shape** — a checkmark or a leading bar — never only a tint, and never a ring, which
  reads as focus.

---

## Typography

The front matter's `typography.<role>` is the token `text.<role>`.

| Token | Use |
| --- | --- |
| `text.title` | Section and sheet titles |
| `text.body` | Body text |
| `text.label` | Buttons, field labels, tabs |
| `text.caption` | Captions, timestamps |

- **A role's weight is the same in every state**, so a hover or a selection never changes a size.

---

## Layout

The front matter's `spacing.<step>` is the token `space.<step>`.

| Token | Use |
| --- | --- |
| `space.xs` | Icon to its label |
| `space.sm` | Inside a control; between related lines |
| `space.md` | Between controls in a group |
| `space.lg` | Screen edge below `breakpoint.sm`; inside a card |
| `space.xl` | Between groups |
| `size.target` | The smallest hit area of any control, drawn or padded |
| `breakpoint.sm` | From here: wider margins; still one column |
| `breakpoint.md` | From here: navigation at the side; two columns where content allows |
| `breakpoint.lg` | From here: two panes where the content has them |
| `breakpoint.xl` | From here: content held to the container's cap |
| `breakpoint.xxl` | From here: a third pane where the content has one; otherwise wider margins |

- **The tiers are Bootstrap's, written mobile first** — each applies from its width up; "below a tier" is 0.02 px
  under it on the web (`767.98px`).
- **Mocks are drawn at the sizes the product ships** — on a screen that resizes, each tier where the layout changes,
  plus 320 px wide for reflow; on a device's fixed panel, its one resolution in each rotation, and no breakpoint
  token.

---

## Elevation & Depth

| Token | Use |
| --- | --- |
| `elevation.overlay` | Sheets, dialogs, menus |
| `layer.raised` | Content lifted over the page |
| `layer.sticky` | Sticky headers and bars |
| `layer.scrim` | The scrim behind a sheet or dialog |
| `layer.overlay` | Sheets and dialogs |
| `layer.menu` | Menus and popovers — above a dialog, so one opened inside it shows |
| `layer.toast` | Toasts, above an open dialog |
| `layer.tooltip` | Tooltips, above everything |

- **A surface takes at most a step in surface colour and a shadow**; in dark, `color.bg.overlay` carries the layer
  where a black shadow cannot read.
- **Overlays render at the top level of the screen, in the `layer.*` order**, never inside a parent that clips them.

---

## Shapes

The front matter's `rounded.<step>` is the token `radius.<step>`.

| Token | Use |
| --- | --- |
| `radius.sm` | Tags, small chips |
| `radius.md` | Buttons, fields, list rows |
| `radius.lg` | Cards, sheets |

- **A nested corner is the outer radius minus the padding between them**, rounded down to a radius token; past a
  `space.xl` gap the inner surface takes its own component's radius.
 ---

## Motion

The front matter keeps the primitives — `duration`, `easing` — and, under `motion`, each move as one token naming its
duration and easing.

| Token | Use |
| --- | --- |
| `duration.fast` | Hover, press, a toggle's state |
| `duration.base` | Most moves: a menu, a popover, a toast |
| `easing.enter` | Something arriving |
| `easing.exit` | Something leaving |
| `motion.hover` | Hover and press |
| `motion.menu-enter` | A menu or popover opening |
| `motion.menu-exit` | A menu or popover closing |

- **Under reduced motion, a move becomes a fade or nothing**, while motion the person drives and a wait indicator keep
  moving.

---

## Voice & Content Strategy

`<How the product speaks, in a line.>` The rules for writing each element are the `ux-content` skill's.

- **Sentence case everywhere** — titles, buttons, labels; capitals only for names.
- **A button says what it does, as a verb** — never "OK" or "Submit".

| Say | Not | Why |
| --- | --- | --- |
| `<the product's word>` | `<the words it replaces>` | `<one name for one thing>` |

---

## Components

Reuse before making one; a one-off moves here on its second caller.

| Component | For | States | Not for |
| --- | --- | --- | --- |
| `Button` | An action: primary (one per view), secondary | Rest, hover and pressed (`color.primary-pressed`), focus, disabled (`color.text.disabled`) | Navigation to another screen — use a link |

---

## Do's and Don'ts

Each principle in [Overview](#overview), in practice.

- **Do `<what principle 1 means on a screen>`** (Principle 1).
- **Do take contrast pairs from [Contrast pairs](#contrast-pairs), make targets at least `size.target`, and draw the
  focus order in the mock** (Principle 2).
- **Don't use a value with no token** — decide it here first, or register it in [Exceptions](#exceptions) with its
  reason (Principle 3).

---

## Accessibility

This product meets WCAG 2.2 AA `[SPEC]`; the rules and how to check them are the `accessibility` skill's. On top of
AA:

- **Hit areas are `size.target`**, above AA's 24 px.

---

## Exceptions

A value off the scale is allowed only here, with where it is used and why.

| Value | Where | Reason |
| --- | --- | --- |
| `<value>` | `<file or component>` | `<why it is off the scale>` |

---

## Open items

What this file does not settle yet, each with what would settle it.

| Item | Status | Unblocked by |
| --- | --- | --- |
| `<what is not settled>` | Open | `<what would settle it>` |
