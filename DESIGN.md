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
| 5 | [Radius and elevation](#5-radius-and-elevation) | Corner radii, nesting rule, elevation per theme, border widths, the layer order |
| 6 | [Motion](#6-motion) | Durations, easings, scales; how each surface enters and leaves; the motion rules and reduced motion |
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
   - In practice: `color.bg.surface` groups; `color.border.subtle` separates rows space already separates; `color.border`
     separates only when space alone does not.
   - Why: every extra line competes with the content for attention.
4. **Calm motion.** Motion explains a change — where something came from, where it went — and never decorates.
   - In practice: `duration.base` for most moves, nothing the product starts over `duration.slow`; under reduced
     motion, a fade or nothing — except a wait and motion the person drives (§6).
   - Why: motion that does not explain is noise, and for some people it is nausea.
5. **Consistent by system.** Every colour, size, space, radius, border width, layer, duration, easing and scale is a
   token from this file.
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
| scrim, exempt | Never under text; disabled, decorative, or a logotype — a logotype that carries meaning has a text alternative naming it (WCAG 1.1.1); a divider or edge that is never a control's only boundary nor a state's only mark | Not paired |

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
| `color.border.subtle` | exempt | `#E1E3E8` | `#2E333C` | A divider between rows already separated by space and identified by their content; never the only mark of a state or a boundary |
| `color.edge` | exempt | `#0000001A` | `#FFFFFF1F` | The inside edge of an image, and of a raised surface in dark where a shadow cannot read; never a control's only boundary nor a state's only mark |
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
- **The focus ring is `border.width.focus` of `color.focus`, offset `space.focus-offset` outside the control**, so it
  is measured against the surface
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
| `space.lg` | 16 px | Screen edge below `breakpoint.sm`; inside a card |
| `space.xl` | 24 px | Between groups; screen edge from `breakpoint.sm` up |
| `space.2xl` | 32 px | Between sections |
| `space.3xl` | 48 px | Above a screen's first section from `breakpoint.lg` up |
| `space.focus-offset` | 2 px | The gap between a control and its focus ring |
| `size.target` | 44 px | The smallest hit area of any control, drawn or padded, on every platform |
| `size.target.material` | 48 px | Optional on Android: Material Design's recommended hit area (48 dp), where a layout has room; never below `size.target` |
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

Elevation, with a value per theme:

| Token | Light | Dark | Use |
| --- | --- | --- | --- |
| `elevation.raised` | `0 1px 2px rgba(0, 0, 0, 0.12)` | `none` | A card over the canvas — in dark, `color.bg.surface` carries it |
| `elevation.overlay` | `0 8px 24px rgba(0, 0, 0, 0.24)` | `0 8px 24px rgba(0, 0, 0, 0.24)` | Sheets, dialogs, menus — in dark, with `color.bg.overlay` |

Border widths, and the stacking order — ordinals, not pixels: a screen names the layer, and only the order matters:

| Token | Value | Use |
| --- | --- | --- |
| `border.width.hairline` | 1 px | Dividers and edges: the device's thinnest crisp line — one physical pixel on dense screens where the platform allows |
| `border.width.default` | 1 px | Control borders |
| `border.width.focus` | 2 px | The focus ring |
| `layer.raised` | 1 | Content lifted over the page |
| `layer.sticky` | 10 | Headers and bars that stay while content scrolls under them |
| `layer.scrim` | 20 | `color.scrim`, behind a `Sheet` or `Dialog` |
| `layer.overlay` | 30 | `Sheet`, `Dialog` — a later overlay stacks above an earlier one, in the order they opened, each with its own `color.scrim` directly under it |
| `layer.menu` | 40 | Menus and popovers — above a `Dialog`, so one opened inside it shows |
| `layer.toast` | 50 | `Toast` — readable while a `Dialog` is open |
| `layer.tooltip` | 60 | Tooltips, above everything |

- **A nested corner is the outer radius minus the padding between them**, never the same radius twice (design-system
  Do 9). Round down to the nearest radius token, and use 0 when the result is under `radius.sm`; a computed radius is
  not an exception.
- **In dark, every overlay takes a `border.width.hairline` inside edge of `color.edge`** — `color.bg.overlay` is
  1.10:1 on `color.bg.surface` and 1:1 on another overlay, and a black shadow does not read, so without it a menu over
  a card, or a `Toast` over a `Dialog`, melts into what is under it.
- **A surface takes at most a step in surface colour and a shadow**; `color.edge` joins them only where the shadow
  cannot read.
- **Photos and screenshots take a `color.edge` inside edge**, so a pale image holds its shape on a matching surface.
- **Overlays render at the top level of the screen, in the `layer.*` order** — a screen names the layer, never a
  number, and nothing renders inside a parent that clips it.
- **A menu opened inside a `Dialog` belongs to the dialog's focus scope**: Escape closes the menu first and returns
  focus to its trigger, then the dialog `[SPEC]` (WAI-ARIA Authoring Practices, dialog and menu button patterns).
- **No `Toast` or sticky bar covers the focused control** — a toast moves clear of it, and a scroll keeps the focused
  control clear of a sticky bar `[SPEC]` (WCAG 2.4.11).
- **A `Dialog` opened over a `Sheet` stacks above it with its own `color.scrim` between them** (`layer.overlay`'s
  opening order), so the sheet dims like the rest of the screen.
- **The stress walk proves the order**: a `Dialog`, a menu inside it, a tooltip and a `Toast` open at once, by touch,
  keyboard and screen reader — nothing hidden that should show, focus never covered.

---

## 6. Motion

| Token | Value | Use |
| --- | --- | --- |
| `duration.fast` | 120 ms | Hover, press, a toggle's state; the exit of anything that enters at `duration.base` or `duration.fast` |
| `duration.base` | 200 ms | Most moves: a menu, a popover, a toast, a list reordering, each item of a list entering; the exit of anything that enters at `duration.slow` |
| `duration.slow` | 300 ms | The longest move: a sheet, a dialog, a full-screen change |
| `duration.stagger` | 40 ms | The delay between items of a list entering together |
| `duration.spin` | 1000 ms | One full turn of a `Spinner` |
| `delay.indicator` | 1000 ms | How long a wait runs before a `Spinner` shows |
| `easing.enter` | `cubic-bezier(0.22, 1, 0.36, 1)` | Something arriving: fast at once, a long settle |
| `easing.exit` | `cubic-bezier(0.33, 1, 0.68, 1)` | Something leaving: it moves the moment it is dismissed, quieter than its entrance |
| `easing.standard` | `cubic-bezier(0.65, 0, 0.35, 1)` | A move that starts and ends on screen: a list reordering, a highlight sliding between tabs |
| `easing.hover` | `cubic-bezier(0.25, 0.1, 0.25, 1)` | Hover and press: a colour change, `scale.press` |
| `easing.sheet` | `cubic-bezier(0.32, 0.72, 0, 1)` | A sheet or drawer opening, and any move a gesture hands off |
| `easing.linear` | `linear` | Motion that shows time passing — a spinner, a progress bar, a hold-to-confirm fill — and the fade that replaces a move under reduced motion |
| `scale.enter` | 0.96 | Where a menu, popover or dialog starts, with opacity 0 |
| `scale.press` | 0.97 | A control while pressed |

The curves: the `cubic-bezier` fits of Robert Penner's ease-out quint (`easing.enter`), ease-out cubic
(`easing.exit`) and ease-in-out cubic (`easing.standard`) equations as published on easings.net; CSS `ease`
(`easing.hover`) from CSS Easing Functions Level 1; the sheet curve from the open-source Vaul drawer.

| Surface | Enters | Leaves |
| --- | --- | --- |
| Menu, popover | `duration.base`, `easing.enter`, from `scale.enter` at the trigger's side | `duration.fast`, `easing.exit`, to the trigger's side |
| `Dialog` | `duration.slow`, `easing.enter`, from `scale.enter` at its centre | `duration.base`, `easing.exit` |
| `Sheet` | `duration.slow`, `easing.sheet`, from its screen edge | `duration.base`, `easing.exit`, to the same edge |
| `Toast` | `duration.base`, `easing.enter`, from its screen edge | `duration.fast`, `easing.exit`, to the same edge |

Menus and popovers have no row in §8 yet; they take these values when they are added there. A loading indicator —
`Button`'s loading state included — is the `Spinner` in §8.

- **How often a thing is seen decides first whether it moves.** An action a person repeats many times an hour —
  typing, moving through a list, a command palette, a menu opened by a keyboard shortcut — does not animate; motion on
  it makes the product feel slow. A menu opened with Enter or Space on its trigger is a click from the keyboard and
  moves as it does from a pointer; one opened by a shortcut appears and leaves without moving.
- **A `Dialog` or `Sheet` moves however it is opened**, from the keyboard too, since it still needs to show where it
  came from.
- **Entering and leaving both ease out** — the move starts the instant it is triggered; an ease-in curve holds back
  the first frames, the ones people watch.
- **An exit takes the next shorter duration than its entrance, at the shortest `duration.fast`** — by the time
  something leaves, the person has already moved on.
- **An exit leaves the way it came** — a different way out reads as a different object.
- **Nothing grows from nothing** — a menu, popover or dialog starts at `scale.enter` with opacity 0, and one opened
  from a control grows from that control's side, because a thing that appears from a point has no believable origin.
- **A move triggered again mid-flight continues from where it is**, never restarts from its first frame — a restart
  makes the surface jump under the person's eye.
- **No move the product starts runs longer than `duration.slow`**; anything longer is an exception in §10. The
  ceiling applies to each move — in a staggered list, to each item's move, so five items at `duration.base` finish
  within 360 ms.
- **Motion the person drives sits outside the ceiling** — a drag, a scroll or a hold filling up lasts as long as they
  drive it.
- **A wait indicator sits outside the ceiling** — a spinner or progress bar lasts as long as the wait.
- **A wait shows no `Spinner` under `delay.indicator`, a `Spinner` from it, and a progress bar when it is expected to
  pass 10 s** — under a second the person's flow holds without a signal, and past ten they need to know how long
  (Jakob Nielsen, "Response Times: The 3 Important Limits", Nielsen Norman Group: 0.1 s, 1 s, 10 s). Only the
  `Spinner` waits: the control the person pressed shows its pressed state at once. The progress bar is not designed
  yet (§11).
- **A `Spinner` turns once per `duration.spin` on `easing.linear`** — chosen to read as busy rather than agitated
  (§11), and one turn a second is far under 3 flashes a second (WCAG 2.3.1).
- **Only position, scale, rotation, opacity and colour animate**, never size or layout, which drop frames.
- **A list enters with `duration.stagger` between its first five items; the rest enter with the fifth**, and only the
  items enter, not their container too — the order shows how to read it, and a longer cascade becomes a wait.
- **Hover never scales: it changes colour, through a role token such as `color.accent.pressed`** — a hover is a state,
  not a move, and growing the thing under the pointer shifts it while the person aims.
- **Opacity on hover is for non-text only, and the dimmed result still meets its floor against what is painted behind
  it** — 3:1 for a border or other non-text `[SPEC]` (WCAG 1.4.11), 4.5:1 for an icon that carries meaning, which
  §2.1 paints as text; dimmed text would paint a colour no §2.2 pair covers.
- **Under reduced motion, a move becomes a `duration.fast` fade on `easing.linear`, or nothing** (Principle 4) —
  above AA, from WCAG 2.3.3 at AAA `[SPEC]`.
- **Under reduced motion, a list's stagger is dropped** — every item fades in at once.
- **Reduced motion never stops what the person drives** — a dragged sheet still follows the finger, because stopping
  it would break the drag; only the motion the product adds after the release becomes a fade.
- **Reduced motion never stops what shows a wait** — a spinner or progress bar keeps moving, because a still one reads
  as frozen.
- **Nothing flashes more than 3 times a second** `[SPEC]` (WCAG 2.3.1).
- **Nothing loops or autoplays for more than 5 s without a pause control** `[SPEC]` (WCAG 2.2.2) — except a loading
  indicator while nothing else can be done, which WCAG counts as essential `[SPEC]`; it ends when the wait ends, in
  the content, an error or a timeout.

---

## 7. Layout

| Token | Value | Use |
| --- | --- | --- |
| `breakpoint.sm` | 576 px | From here: `space.xl` edges; still one column |
| `breakpoint.md` | 768 px | From here: a navigation rail at the side; two columns where content allows |
| `breakpoint.lg` | 992 px | From here: list and detail side by side; content capped at `size.content-max` |
| `breakpoint.xl` | 1200 px | From here: a side list with full labels in place of the rail |
| `breakpoint.xxl` | 1400 px | From here: wider margins only |

- **The tiers are Bootstrap's, mobile first** — each applies from its width up; "below a tier" is 0.02 px under it
  (`767.98px`) `[SPEC]` (Bootstrap 5.3, Breakpoints).
- **Below `breakpoint.md`, everything is one column**, navigation at the bottom, the primary action within thumb
  reach.
- **Columns divide the layout; `size.content-max` caps a column of text** — from `breakpoint.lg`, a two-pane layout
  may run wider than 720 px, but no paragraph does.
- **Mocks are drawn at 390 px and 1280 px wide** — one below `breakpoint.md` and one from `breakpoint.xl` — plus 768
  px when a change touches navigation or panes, and any size a change is about; the
  build is checked at 320 px wide too, where nothing scrolls sideways `[SPEC]` (WCAG 1.4.10).

---

## 8. Components

Reuse before making one; a one-off moves here on its second caller (design-system Do 10).

| Component | For | States | Not for |
| --- | --- | --- | --- |
| `Button` | An action: primary (one per view), secondary, text, danger | Rest, hover, pressed, focus, disabled, loading | Navigation to another screen — use a link or a `ListRow` |
| `TextField` | Text a person types, with a visible label above | Rest, focus, filled, error with its message, disabled | A choice from a few options — use a segmented control |
| `ListRow` | One item in a list: a title, optional supporting text, a trailing value or chevron | Rest, pressed, focus, selected — `color.bg.selected` with a checkmark in `color.accent` when the row is a choice, or a `space.xs` leading bar of `color.accent` at `radius.full` when it opens something; never a ring, which reads as focus; announced as selected (checked, for a choice), the mark itself hidden from screen readers | A paragraph of content |
| `Sheet` | A focused task over the current screen that keeps its context | Opening, open, closing | Anything a person must finish before going on — use a `Dialog` |
| `Dialog` | A decision the person must make now; a destructive action's confirmation; the confirmation behind a hold-to-confirm, opened by a tap, a key or a screen reader's action | Open, with one primary (danger when it destroys) and one cancel | News — use a `Toast` |
| `Spinner` | A wait with no known length: shown from `delay.indicator`, turning once per `duration.spin`, named "Loading", with a status announcement when it shows and when the wait ends; `Button`'s loading state at the label's size, the `Button` marked busy from the press; its size, stroke and colours are open in §11 | Turning, until the wait ends in the content, an error or a timeout | A wait expected over 10 s — a progress bar with how much is done |
| `Toast` | News that asks nothing, on `color.bg.overlay`, announced as a status message; it stays 6 s, paused while hovered, focused or pressed and resuming with the time left, and has a close; one that appears while a modal `Dialog` is open is announced at once and starts its 6 s when the modal closes | Showing, paused, leaving | Errors that need an action — show them in place; the only place a fact appears |

---

## 9. Accessibility

This product meets WCAG 2.2 AA `[SPEC]`; the rules and how to check them are the
[`accessibility`](.agents/skills/accessibility/SKILL.md) skill's. On top of AA:

- **Hit areas are `size.target` (§4) on every platform, Android included**, above AA's 24 px — the product is used
  one-handed on a phone; `size.target.material` is optional on Android, and Android's Accessibility Scanner flags a
  hit area under 48 dp.
- **Every pair in §2.2 passes in both themes**, checked by the design check on every change to this file.
- **No time limit hides content**: a `Toast` pauses and can be closed (§8) `[SPEC]` (WCAG 2.2.1).
- **Hold-to-confirm is a touch pattern for phones; every one also confirms through a `Dialog`**, which a tap,
  a key or a screen reader's action on the same control opens, so no one has to hold. A release before the
  fill completes — a tap included — never confirms: the fill drains and the `Dialog` opens `[SPEC]` (WCAG 2.1.1,
  2.5.2).
- **Text sizes follow the platform's text-size setting** up to 200 % without loss.
- **Motion follows the platform's reduced-motion setting** (§6) — WCAG 2.3.3 is AAA `[SPEC]`; every platform ships
  the setting and people rely on it.

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
| Whether `color.edge` at 12 % white reads on an OLED phone at low brightness `[?]` | Open | The person's look at a menu over a card in dark on a phone at 20 % brightness |
| Whether `duration.spin` at 1000 ms reads as busy rather than agitated on a phone `[?]` | Open | The person's look at the `Spinner` on the target |
| The `Spinner`'s size, stroke and colours, the `ListRow` checkmark's size, the progress bar, and how long a hold-to-confirm takes to fill — values the specimen drew but this file does not yet decide | Open | Each one's mock at the first gate when it is built, with its tokens decided here first |
