# `<Project>` — Design

> **Starter.** Copy this file to the repo root as `DESIGN.md` and replace every example with your product's
> principles and values. Keep the section numbers and the table shapes — the design check reads them. How each part
> is written: the `design-system` skill's references/brief.md.

The design brief for this product: the principles every screen follows and every design token by role, with its value
in each theme. People read it to know how the product looks and why; coding agents read it before any UI work and take
every value from the tokens it names.

**Source of truth.** This file decides the principles and the token values. The token files in code carry the same
values to the platform. Where code and this file disagree, find which side is intended, then fix the other in the same
change. The design check (`design_check.py`) proves the contrast pairs in §2.2 meet their floors, that every pair the
colour kinds call for is there, that the ratios written are true, that every theme has a value, and that every token
named here exists in the token files.

**Stability.** Cite this file as `DESIGN §n`. Do not renumber; add new material under the next free number.

| Tag | Meaning |
| --- | --- |
| `[SPEC]` | From a standard — WCAG 2.2, a platform's design guidelines |
| `[DES]` | From the design file, frame or component named beside it |
| `[?]` | Unverified — tracked in §11 |

| § | Section | Look here for |
| --- | --- | --- |
| 1 | [Principles](#1-principles) | What every screen holds to, and why; the tie-breakers |
| 2 | [Colour](#2-colour) | Colour roles with a value per theme; contrast pairs and their ratios |
| 3 | [Type](#3-type) | The type scale: size, line height, weight, use |
| 4 | [Space and size](#4-space-and-size) | The spacing scale; tap target; content width |
| 5 | [Radius and elevation](#5-radius-and-elevation) | Corner radii, nesting rule, depth, the stacking order |
| 6 | [Motion](#6-motion) | Durations, easings; the motion rules and reduced motion |
| 7 | [Layout](#7-layout) | Breakpoints and how screens adapt |
| 8 | [Components](#8-components) | What each component is for, its states, when not to use it |
| 9 | [Accessibility](#9-accessibility) | The floors this product meets |
| 10 | [Exceptions](#10-exceptions) | Values allowed off the scale, and why |
| 11 | [Open items](#11-open-items) | What is not settled yet, and what would settle it |

---

## 1. Principles

Five or fewer. When two options both pass the rules, the lower-numbered principle decides.

1. **`<A rule the product holds to>`**
   - In practice: `<what it means on a screen>`.
   - Why: `<the reason, and what breaks without it>`.
2. **Accessible by default.**
   - In practice: contrast pairs come from §2.2; targets are at least `size.target`; focus order is part of the mock.
   - Why: a screen that some people cannot use is not finished.
3. **Every colour, size, space, radius, duration and easing is a token from this file.**
   - In practice: a value with no token is decided here first, or registered in §10 with its reason.
   - Why: one change here reaches every screen, and a theme changes values without touching screens.

---

## 2. Colour

### 2.1 Roles

Screens use roles, never raw values; a theme is a second column of values for the same roles. Each role has a kind,
which says what it may be painted on and which floor applies.

| Kind | Means | Paired in §2.2 |
| --- | --- | --- |
| surface | A background a screen paints content on | As the background for every text and non-text role |
| text | Painted as words — or as an icon that carries meaning | On every surface, floor 4.5 |
| non-text | Borders, separators, the focus ring | On every surface, floor 3 |
| fill | A solid background for a control | As the background for every on-fill role |
| on-fill | Words and icons on a fill | On every fill, floor 4.5 |
| scrim, exempt | Never under text; disabled, decorative, or a logotype | Not paired |

| Token | Kind | Light | Dark | Use |
| --- | --- | --- | --- | --- |
| `color.bg.canvas` | surface | `#FFFFFF` | `#111317` | The page behind everything |
| `color.bg.surface` | surface | `#F4F5F7` | `#1B1E24` | Cards, grouped rows |
| `color.bg.overlay` | surface | `#FFFFFF` | `#22262E` | Sheets, dialogs, menus — above the scrim; the lightest layer in dark |
| `color.scrim` | scrim | `#00000066` | `#00000099` | Behind a sheet or dialog; never under text |
| `color.text.primary` | text | `#1B1D21` | `#F2F3F5` | Body text, titles |
| `color.text.secondary` | text | `#585E69` | `#A9AFBA` | Supporting text, captions, placeholders |
| `color.text.on-accent` | on-fill | `#FFFFFF` | `#0B1020` | Text on `color.accent` and `color.accent.pressed` |
| `color.accent` | text, fill | `#2457D6` | `#7EA2FF` | The primary action, links, selection |
| `color.accent.pressed` | fill | `#1B45AD` | `#A5BEFF` | The primary action while pressed or hovered |
| `color.text.disabled` | exempt | `#A3A8B0` | `#5A606B` | Disabled controls' text and icons — never anything enabled |
| `color.border` | non-text | `#7D838D` | `#7A818E` | Control borders and separators that carry meaning |
| `color.focus` | non-text | `#2457D6` | `#7EA2FF` | The focus ring |

### 2.2 Contrast pairs

Every pair the kinds in §2.1 call for, with its floor and its ratio in each theme. Floors: 4.5 for text, 3 for
non-text `[SPEC]` (WCAG 1.4.3, 1.4.11). Run the design check and write the ratios it computes.

| Foreground | Background | Floor | Light | Dark |
| --- | --- | --- | --- | --- |
| `color.text.primary` | `color.bg.canvas` | 4.5 | 16.88 | 16.75 |
| `color.text.primary` | `color.bg.surface` | 4.5 | 15.47 | 15.04 |
| `color.text.secondary` | `color.bg.canvas` | 4.5 | 6.52 | 8.44 |
| `color.text.secondary` | `color.bg.surface` | 4.5 | 5.98 | 7.58 |
| `color.accent` | `color.bg.canvas` | 4.5 | 6.16 | 7.53 |
| `color.accent` | `color.bg.surface` | 4.5 | 5.65 | 6.76 |
| `color.text.primary` | `color.bg.overlay` | 4.5 | 16.88 | 13.66 |
| `color.text.secondary` | `color.bg.overlay` | 4.5 | 6.52 | 6.88 |
| `color.accent` | `color.bg.overlay` | 4.5 | 6.16 | 6.14 |
| `color.border` | `color.bg.canvas` | 3 | 3.82 | 4.74 |
| `color.border` | `color.bg.surface` | 3 | 3.50 | 4.26 |
| `color.border` | `color.bg.overlay` | 3 | 3.82 | 3.87 |
| `color.focus` | `color.bg.canvas` | 3 | 6.16 | 7.53 |
| `color.focus` | `color.bg.surface` | 3 | 5.65 | 6.76 |
| `color.focus` | `color.bg.overlay` | 3 | 6.16 | 6.14 |
| `color.text.on-accent` | `color.accent` | 4.5 | 6.16 | 7.66 |
| `color.text.on-accent` | `color.accent.pressed` | 4.5 | 8.40 | 10.29 |

- **The focus ring is drawn outside the control with a gap**, so it is measured against the surface the control sits
  on, never against the control's own fill — `color.focus` equals `color.accent` here.
- **In dark, a higher layer is lighter**: `color.bg.canvas`, then `color.bg.surface`, then `color.bg.overlay`.
- **A selected state carries a shape** — a checkmark or a leading bar — never only a tint, and never a ring, which
  reads as focus.

---

## 3. Type

| Token | Size | Line height | Weight | Use |
| --- | --- | --- | --- | --- |
| `text.title` | 22 px | 28 px | 600 | Section and sheet titles |
| `text.body` | 16 px | 24 px | 400 | Body text |
| `text.label` | 14 px | 20 px | 500 | Buttons, field labels, tabs |
| `text.caption` | 13 px | 18 px | 400 | Captions, timestamps |

- **A role's weight is the same in every state**, so a hover or a selection never changes a size.

---

## 4. Space and size

| Token | Value | Use |
| --- | --- | --- |
| `space.xs` | 4 px | Icon to its label |
| `space.sm` | 8 px | Inside a control; between related lines |
| `space.md` | 12 px | Between controls in a group |
| `space.lg` | 16 px | Screen edge below `breakpoint.sm`; inside a card |
| `space.xl` | 24 px | Between groups |
| `size.target` | 44 px | The smallest hit area of any control, drawn or padded |

---

## 5. Radius and elevation

| Token | Value | Use |
| --- | --- | --- |
| `radius.sm` | 4 px | Tags, small chips |
| `radius.md` | 8 px | Buttons, fields, list rows |
| `radius.lg` | 16 px | Cards, sheets |
| `elevation.overlay` | `0 8px 24px rgba(0, 0, 0, 0.24)` | Sheets, dialogs, menus |
| `layer.raised` | 1 | Content lifted over the page |
| `layer.sticky` | 10 | Sticky headers and bars |
| `layer.scrim` | 20 | The scrim behind a sheet or dialog |
| `layer.overlay` | 30 | Sheets and dialogs |
| `layer.menu` | 40 | Menus and popovers — above a dialog, so one opened inside it shows |
| `layer.toast` | 50 | Toasts, above an open dialog |
| `layer.tooltip` | 60 | Tooltips, above everything |

- **A nested corner is the outer radius minus the padding between them**, rounded down to a radius token; past a
  `space.xl` gap the inner surface takes its own component's radius.
- **A surface takes at most a step in surface colour and a shadow**; in dark, `color.bg.overlay` carries the layer
  where a black shadow cannot read.
- **Overlays render at the top level of the screen, in the `layer.*` order**, never inside a parent that clips them.

---

## 6. Motion

| Token | Value | Use |
| --- | --- | --- |
| `duration.fast` | 120 ms | Hover, press, a toggle's state |
| `duration.base` | 200 ms | Most moves: a menu, a popover, a toast |
| `easing.enter` | `cubic-bezier(0.22, 1, 0.36, 1)` | Something arriving |
| `easing.exit` | `cubic-bezier(0.33, 1, 0.68, 1)` | Something leaving |

- **Under reduced motion, a move becomes a fade or nothing**, while motion the person drives and a wait indicator keep
  moving.

---

## 7. Layout

| Token | Value | Use |
| --- | --- | --- |
| `breakpoint.sm` | 576 px | From here: wider margins; still one column |
| `breakpoint.md` | 768 px | From here: navigation at the side; two columns where content allows |
| `breakpoint.lg` | 992 px | From here: two panes where the content has them |
| `breakpoint.xl` | 1200 px | From here: content held to the container's cap |
| `breakpoint.xxl` | 1400 px | From here: a third pane where the content has one; otherwise wider margins |

- **The tiers are Bootstrap's, written mobile first** — each applies from its width up; "below a tier" is 0.02 px
  under it on the web (`767.98px`).
- **Mocks are drawn at the sizes the product ships** — on a screen that resizes, each tier where the layout changes,
  plus 320 px wide for reflow; on a device's fixed panel, its one resolution in each rotation, and no breakpoint
  token.

---

## 8. Components

Reuse before making one; a one-off moves here on its second caller.

| Component | For | States | Not for |
| --- | --- | --- | --- |
| `Button` | An action: primary (one per view), secondary | Rest, hover and pressed (`color.accent.pressed`), focus, disabled (`color.text.disabled`) | Navigation to another screen — use a link |

---

## 9. Accessibility

This product meets WCAG 2.2 AA `[SPEC]`; the rules and how to check them are the `accessibility` skill's. On top of
AA:

- **Hit areas are `size.target`**, above AA's 24 px.

---

## 10. Exceptions

| Value | Where | Reason |
| --- | --- | --- |
| `<value>` | `<file or component>` | `<why it is off the scale>` |

---

## 11. Open items

| Item | Status | Unblocked by |
| --- | --- | --- |
| `<what is not settled>` | Open | `<what would settle it>` |
