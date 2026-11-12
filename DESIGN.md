# `<Project>` — Design

> **DEMO.** Every value here is an example, so the template has something real to check against. Replace them with
> your product's principles and tokens — keep the table shapes, which the design check reads.

The design brief for this product: the principles every screen follows and every design token by role, with its value
in each theme. People read it to know how the product looks and why; coding agents read it before any UI work — the
`ui-designer` and `design-system` skills load it first — and take every value from the tokens it names. It sits at the
root beside `AGENTS.md`: `AGENTS.md` is how to work here, `DESIGN.md` is what the product should look and feel like.

**Source of truth.** This file decides the principles and the token values. The token files in code (`TOKEN_FILES` in
`.agents/project.py`) carry the same values to the platform, generated from here or kept in step by hand; the design
file is a source for intent, cited `[DES]`. Where code and this file disagree, find which side is intended, then fix
the other in the same change. The design check (`design_check.py`, run by `verify.py run`) proves the contrast pairs in
§2.2 meet their floors, that every pair the colour kinds in §2.1 call for is there, that the ratios written there are
true, and that every token named here exists in the token files.

**Related.** [AGENTS.md](AGENTS.md) — the rules for every change. The skills that apply this file:
[`ui-designer`](.agents/skills/ui-designer/SKILL.md), [`design-system`](.agents/skills/design-system/SKILL.md),
[`accessibility`](.agents/skills/accessibility/SKILL.md).

**Stability.** Cite this file as `DESIGN §n`. Do not renumber; add new material under the next free number.

| Tag | Meaning |
| --- | --- |
| `[SPEC]` | From a standard — WCAG 2.2, a platform's design guidelines |
| `[DES]` | From the design file, frame or component named beside it |
| `[?]` | Unverified — tracked in §11 |

| § | Section | Look here for |
| --- | --- | --- |
| 1 | [Principles](#1-principles) | What every screen holds to, and why; the tie-breakers |
| 2 | [Colour](#2-colour) | Colour roles with light and dark values; contrast pairs and their ratios |
| 3 | [Type](#3-type) | The type scale: size, line height, weight, use |
| 4 | [Space and size](#4-space-and-size) | The spacing scale; tap target; content width |
| 5 | [Radius and elevation](#5-radius-and-elevation) | Corner radii, nesting rule, shadows |
| 6 | [Motion](#6-motion) | Durations, easings, reduced motion |
| 7 | [Layout](#7-layout) | Breakpoints and how screens adapt |
| 8 | [Components](#8-components) | What each component is for, its states, when not to use it |
| 9 | [Accessibility](#9-accessibility) | The floors this product meets |
| 10 | [Exceptions](#10-exceptions) | Values allowed off the scale, and why |
| 11 | [Open items](#11-open-items) | What is not settled yet, and what would settle it |

---

## 1. Principles

Five rules every screen follows. When two pull against each other, the lower number wins — between options that both
meet the §9 floors. The floors are never weighed against a principle.

1. **Clarity first — one primary action per screen.** A person knows what the screen is for and what to do next
   within a glance.
   - In practice: one `Button` in the primary or the danger variant per view — the danger variant is the primary when
     the main action destroys something; other actions are secondary or text buttons.
   - Why: two loud buttons make the person choose before they understand.
2. **Accessible by default.** Every screen meets §9 from its first mock, not in a later pass.
   - In practice: contrast pairs come from §2.2; targets are at least `size.target`; focus order is part of the mock.
   - Why: fixing access after the build means redrawing it.
3. **Content leads, chrome recedes.** Surfaces, borders and shadows exist to group content, never to decorate.
   - In practice: `color.bg.surface` groups; `color.border` separates only when space alone does not.
   - Why: every extra line competes with the content for attention.
4. **Calm motion.** Motion explains a change — where something came from, where it went — and never decorates.
   - In practice: `duration.base` for most moves, nothing over `duration.slow`; under reduced motion, a fade or
     nothing.
   - Why: motion that does not explain is noise, and for some people it is nausea.
5. **Consistent by system.** Every colour, size, space, radius and duration is a token from this file.
   - In practice: a value that is not here is an exception in §10, with its reason.
   - Why: a one-off value is a decision nobody can find again.

---

## 2. Colour

### 2.1 Roles

Screens use roles, never raw values; a theme is a second set of values for the same roles (design-system Do 3, Do 5).
Each role has a kind, which says what it may be painted on and which floor applies; the design check reads it (§2.2).

| Kind | Means | Paired in §2.2 |
| --- | --- | --- |
| surface | A background a screen paints content on | As the background for every text and non-text role |
| text | Painted as words — or as an icon that carries meaning | On every surface, floor 4.5 |
| non-text | Borders, separators, the focus ring | On every surface, floor 3 |
| fill | A solid background for a control | As the background for every on-fill role |
| on-fill | Words and icons on a fill | On every fill, floor 4.5 |
| scrim, exempt | Never under text; disabled or decorative | Not paired |

| Token | Kind | Light | Dark | Use |
| --- | --- | --- | --- | --- |
| `color.bg.canvas` | surface | `#FFFFFF` | `#111317` | The page behind everything |
| `color.bg.surface` | surface | `#F4F5F7` | `#1B1E24` | Cards, grouped rows |
| `color.bg.overlay` | surface | `#FFFFFF` | `#22262E` | Sheets, dialogs, menus, toasts — above the scrim |
| `color.bg.selected` | surface | `#E3EBFC` | `#23304F` | A selected `ListRow` or option |
| `color.scrim` | scrim | `#00000066` | `#00000099` | Behind a `Sheet` or `Dialog`; never under text |
| `color.text.primary` | text | `#1B1D21` | `#F2F3F5` | Body text, titles |
| `color.text.secondary` | text | `#585E69` | `#A9AFBA` | Supporting text, captions, placeholders |
| `color.text.on-accent` | on-fill | `#FFFFFF` | `#0B1020` | Text on `color.accent`, `color.accent.pressed` and `color.danger` fills |
| `color.accent` | text, fill | `#2457D6` | `#7EA2FF` | The primary action, links, selection |
| `color.accent.pressed` | fill | `#1B45AD` | `#A5BEFF` | The primary action while pressed or hovered |
| `color.text.disabled` | exempt | `#A3A8B0` | `#5A606B` | Disabled controls' text and icons — exempt from contrast, never used for anything enabled |
| `color.border` | non-text | `#7D838D` | `#7A818E` | Control borders and separators that carry meaning |
| `color.focus` | non-text | `#2457D6` | `#7EA2FF` | The focus ring |
| `color.danger` | text, fill | `#B42318` | `#FF8A80` | Destructive actions, errors |
| `color.success` | text | `#177433` | `#5FD38A` | Confirmations |

### 2.2 Contrast pairs

Every pair the kinds in §2.1 call for — each text and non-text role on each surface, each on-fill role on each fill —
with its floor and its ratio in each theme. The design check fails when a pair is missing, under its floor, or written
with a ratio that differs from the computed one. Floors: 4.5 for text, 3 for non-text `[SPEC]` (WCAG 1.4.3, 1.4.11).

| Foreground | Background | Floor | Light | Dark |
| --- | --- | --- | --- | --- |
| `color.text.primary` | `color.bg.canvas` | 4.5 | 16.88 | 16.75 |
| `color.text.primary` | `color.bg.surface` | 4.5 | 15.47 | 15.04 |
| `color.text.primary` | `color.bg.overlay` | 4.5 | 16.88 | 13.66 |
| `color.text.primary` | `color.bg.selected` | 4.5 | 14.11 | 11.77 |
| `color.text.secondary` | `color.bg.canvas` | 4.5 | 6.52 | 8.44 |
| `color.text.secondary` | `color.bg.surface` | 4.5 | 5.98 | 7.58 |
| `color.text.secondary` | `color.bg.overlay` | 4.5 | 6.52 | 6.88 |
| `color.text.secondary` | `color.bg.selected` | 4.5 | 5.45 | 5.93 |
| `color.accent` | `color.bg.canvas` | 4.5 | 6.16 | 7.53 |
| `color.accent` | `color.bg.surface` | 4.5 | 5.65 | 6.76 |
| `color.accent` | `color.bg.overlay` | 4.5 | 6.16 | 6.14 |
| `color.accent` | `color.bg.selected` | 4.5 | 5.15 | 5.29 |
| `color.danger` | `color.bg.canvas` | 4.5 | 6.57 | 8.15 |
| `color.danger` | `color.bg.surface` | 4.5 | 6.03 | 7.31 |
| `color.danger` | `color.bg.overlay` | 4.5 | 6.57 | 6.64 |
| `color.danger` | `color.bg.selected` | 4.5 | 5.50 | 5.72 |
| `color.success` | `color.bg.canvas` | 4.5 | 5.86 | 9.89 |
| `color.success` | `color.bg.surface` | 4.5 | 5.37 | 8.88 |
| `color.success` | `color.bg.overlay` | 4.5 | 5.86 | 8.07 |
| `color.success` | `color.bg.selected` | 4.5 | 4.90 | 6.95 |
| `color.border` | `color.bg.canvas` | 3 | 3.82 | 4.74 |
| `color.border` | `color.bg.surface` | 3 | 3.50 | 4.26 |
| `color.border` | `color.bg.overlay` | 3 | 3.82 | 3.87 |
| `color.border` | `color.bg.selected` | 3 | 3.19 | 3.33 |
| `color.focus` | `color.bg.canvas` | 3 | 6.16 | 7.53 |
| `color.focus` | `color.bg.surface` | 3 | 5.65 | 6.76 |
| `color.focus` | `color.bg.overlay` | 3 | 6.16 | 6.14 |
| `color.focus` | `color.bg.selected` | 3 | 5.15 | 5.29 |
| `color.text.on-accent` | `color.accent` | 4.5 | 6.16 | 7.66 |
| `color.text.on-accent` | `color.accent.pressed` | 4.5 | 8.40 | 10.29 |
| `color.text.on-accent` | `color.danger` | 4.5 | 6.57 | 8.29 |

- **A new pair a screen paints gets a row here before the screen is built** — the mock's values file names it.
- **Text never sits on `color.border`, `color.focus` or a translucent fill** unless its pair is in this table.
- **The focus ring is 2 px of `color.focus`, offset 2 px outside the control**, so it is measured against the surface
  the control sits on — never against the control's own fill (`color.focus` on `color.accent` is 1:1).
- **A floor is 4.5 for any text or on-fill role** — the 3 floor is for non-text roles only (§3: no role but
  `text.display` is large text).
- **A new role gets its kind, then its pairs, before any screen uses it** — the check lists the pairs it needs.

---

## 3. Type

One family, `font.sans` — the platform's system sans-serif — in five roles.

| Token | Size | Line height | Weight | Use |
| --- | --- | --- | --- | --- |
| `font.sans` | — | — | — | `system-ui, -apple-system, "Segoe UI", Roboto, sans-serif` |
| `text.display` | 32 px | 40 px | 600 | One per screen, at most: the screen's name on a landing view |
| `text.title` | 22 px | 28 px | 600 | Section and sheet titles |
| `text.body` | 17 px | 24 px | 400 | Everything people read |
| `text.label` | 15 px | 20 px | 500 | Buttons, field labels, tabs |
| `text.caption` | 13 px | 18 px | 400 | Timestamps, helper text — never the only place a fact appears |

- **Only `text.display` counts as large text for contrast** — WCAG's large is 24 px regular or 18.66 px bold (700)
  `[SPEC]`, and `text.title` at 22 px and 600 is neither; every other role needs 4.5:1.
- **Wrap, never truncate, body text.** Truncate only a label with its full text one tap away.

---

## 4. Space and size

A 4 px base. Space between related things is smaller than space between groups.

| Token | Value | Use |
| --- | --- | --- |
| `space.xs` | 4 px | Icon to its label |
| `space.sm` | 8 px | Inside a control; between related lines |
| `space.md` | 12 px | Between controls in a group |
| `space.lg` | 16 px | Screen edge on compact; inside a card |
| `space.xl` | 24 px | Between groups; screen edge on medium and up |
| `space.2xl` | 32 px | Between sections |
| `space.3xl` | 48 px | Above a screen's first section on expanded |
| `size.target` | 44 px | The smallest hit area of any control, drawn or padded |
| `size.content-max` | 720 px | The widest a column of text runs |

- **Sizes are written in px at 100 % text size; code carries type and space in a unit that scales with the person's
  text-size setting** — `rem` on the web, Dynamic Type on iOS, `sp` on Android — so §9's 200 % holds.

---

## 5. Radius and elevation

| Token | Value | Use |
| --- | --- | --- |
| `radius.sm` | 4 px | Tags, small chips |
| `radius.md` | 8 px | Buttons, fields, list rows |
| `radius.lg` | 16 px | Cards, sheets |
| `radius.full` | 9999 px | Pills, avatars |
| `elevation.raised` | `0 1px 2px rgba(0, 0, 0, 0.12)` | A card over the canvas |
| `elevation.overlay` | `0 8px 24px rgba(0, 0, 0, 0.24)` | Sheets, dialogs, menus |

- **A nested corner is the outer radius minus the padding between them**, never the same radius twice (design-system
  Do 9). Round down to the nearest radius token, and use 0 when the result is under `radius.sm`; a computed radius is
  not an exception.
- **Dark mode adds no shadow to `elevation.raised`**: a raised surface is `color.bg.surface` instead.
- **Dark mode keeps `elevation.overlay` and shows the layer with `color.bg.overlay`** — a black shadow does not read on
  `#111317`, so the lighter surface carries the elevation.

---

## 6. Motion

| Token | Value | Use |
| --- | --- | --- |
| `duration.fast` | 120 ms | Hover, press, a toggle's state |
| `duration.base` | 200 ms | Most moves: a sheet, a list reordering, a page within a flow |
| `duration.slow` | 320 ms | The longest move: a full-screen change |
| `easing.standard` | `cubic-bezier(0.2, 0, 0, 1)` | Moves that start and end on screen |
| `easing.enter` | `cubic-bezier(0, 0, 0, 1)` | Something arriving |
| `easing.exit` | `cubic-bezier(0.3, 0, 1, 1)` | Something leaving — exits are faster than entrances |

- **Under reduced motion, a move becomes a `duration.fast` fade or nothing** (Principle 4) — above AA, from WCAG
  2.3.3 at AAA `[SPEC]`.
- **Nothing flashes more than 3 times a second** `[SPEC]` (WCAG 2.3.1).
- **Nothing loops or autoplays for more than 5 s without a pause control** `[SPEC]` (WCAG 2.2.2).

---

## 7. Layout

| Token | Value | Use |
| --- | --- | --- |
| `breakpoint.medium` | 600 px | From here: two columns where content allows; `space.xl` edges |
| `breakpoint.expanded` | 1024 px | From here: a side navigation; content capped at `size.content-max` |

- **Compact is below `breakpoint.medium`: everything is one column**, navigation at the bottom, the primary action
  within thumb reach.
- **Columns divide the layout; `size.content-max` caps a column of text** — on expanded, a two-column layout may run
  wider than 720 px, but no paragraph does.
- **Mocks are drawn at 390 px and 1280 px wide** — one compact and one expanded — plus any size a change is about; the
  build is checked at 320 px wide too, where nothing scrolls sideways `[SPEC]` (WCAG 1.4.10).

---

## 8. Components

Reuse before making one; a one-off moves here on its second caller (design-system Do 10).

| Component | For | States | Not for |
| --- | --- | --- | --- |
| `Button` | An action: primary (one per view), secondary, text, danger | Rest, hover, pressed, focus, disabled, loading | Navigation to another screen — use a link or a `ListRow` |
| `TextField` | Text a person types, with a visible label above | Rest, focus, filled, error with its message, disabled | A choice from a few options — use a segmented control |
| `ListRow` | One item in a list: a title, optional supporting text, a trailing value or chevron | Rest, pressed, focus, selected | A paragraph of content |
| `Sheet` | A focused task over the current screen that keeps its context | Opening, open, closing | Anything a person must finish before going on — use a `Dialog` |
| `Dialog` | A decision the person must make now; a destructive action's confirmation | Open, with one primary (danger when it destroys) and one cancel | News — use a `Toast` |
| `Toast` | News that asks nothing, on `color.bg.overlay`, announced as a status message; it stays 6 s, longer while hovered or focused, and has a close | Showing, paused, leaving | Errors that need an action — show them in place; the only place a fact appears |

---

## 9. Accessibility

This product meets WCAG 2.2 AA `[SPEC]`; the rules and how to check them are the
[`accessibility`](.agents/skills/accessibility/SKILL.md) skill's. On top of AA:

- **Hit areas are `size.target`, 44 px**, above AA's 24 px — the product is used one-handed on a phone.
- **Every pair in §2.2 passes in both themes**, checked by the design check on every change to this file.
- **No time limit hides content**: a `Toast` pauses while hovered or focused and can be closed `[SPEC]` (WCAG 2.2.1).
- **Text sizes follow the platform's text-size setting** up to 200 % without loss.

---

## 10. Exceptions

| Value | Where | Reason |
| --- | --- | --- |
| `#000000` | The logo artwork, light theme | The brand's mark keeps its own colours; it carries no text and is never a control |
| `#FFFFFF` | The logo artwork, dark theme | The mark's reversed version — black would be 1.13:1 on `color.bg.canvas` |

---

## 11. Open items

| Item | Status | Unblocked by |
| --- | --- | --- |
| `color.border` in dark passes at 3.33:1 on `color.bg.selected` and 4.26:1 on `color.bg.surface`; whether it reads comfortably on an OLED phone at low brightness `[?]` — a preference, not a compliance question | Open | The person's look on a phone at 20 % brightness |
