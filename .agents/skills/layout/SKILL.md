---
name: layout
description: How a product's screens are laid out and how they adapt across window sizes, carried in the skill (references/layout.md) — content and the window deciding, never the device; mobile first on Bootstrap's six breakpoint tiers (sm 576, md 768, lg 992, xl 1200, xxl 1400) applied to the window's logical width, with a panel's logical width from its pixels and dpi; the scaffold's regions (system areas, navigation, top bar, body, bottom actions) and one scroll per pane; navigation by width (a bottom bar, a rail, a side list) with the same destinations at every tier; panes per tier and the canonical layouts (list and detail, supporting pane, feed); a twelve-column grid, gutters, the container's cap and margins that grow with the tier; spacing on a 4 or 8 base with proximity, padding inside and gap between; density by whole steps, never below the minimum target; content width and line length; what survives when the window changes size; round and small screens — watches (watchOS, Wear OS) and small or round panels — one glance per screen, one column scrolled by touch and the crown, bezel or encoder, margins as a percentage of the screen, the circle's safe area and lists that reach its centre, edges that follow the bezel — the principles for every platform, stated in the web's words and mapped to iOS, Android and embedded ESP-IDF devices with an LVGL display (flex and grid layouts modelled on CSS, pad_row and pad_column as gap, LV_SIZE_CONTENT, lv_pct, lv_dpx, rotation as a resize); the layout spec a draft records tier by tier, and the review of a layout change; plus layout_check.py for the patterns code can show, in web, native and C/C++ files. Values come from the project's own DESIGN.md. Portable — the folder works in any repo. Use when laying out a screen or a component, choosing breakpoints, navigation or panes, setting spacing, margins, a grid or density, making a screen adapt to phones, tablets, desktops, a watch or a round or small panel, when a layout scrolls sideways, breaks at a width or loses state on rotation, or when reviewing a layout change.
metadata:
  scope: portable
---

# Layout

How a product's screens are laid out and how they adapt. The principles and their reasons are kept in this skill at
[references/layout.md](references/layout.md) (cited `LAYOUT §n`); this page indexes them in one-line rules and holds
the steps: deciding a layout, building it, and the review. The breakpoints are Bootstrap's tiers; every other value —
the spacing scale, margins, gutters, pane widths, the container's cap, the measure, density levels — is the project's
own, in its `DESIGN.md`; that file wins over the reference, and the reference over this page.

**Platforms.** The rules below hold on every platform. Each is stated in the web's words, and the reference maps it to
**iOS**, **Android** and **Embedded (ESP-IDF, LVGL)** (LAYOUT §12) — LVGL's flex and grid layouts follow CSS, so the
same layout carries to a panel.

**Portable.** This folder is self-contained and links to nothing outside itself (it names the rest of a kit in
backticks): the reference and the layout check ([scripts/layout_check.py](scripts/layout_check.py)). Copy it into any
repo's `.agents/skills/` (or `.claude/skills/`) and it works there: the check reads `UI_PATHS` from
`.agents/project.py` when the repo has one, and scans every tracked UI file when it does not — web, native, and C or
C++ for firmware, outside vendored folders such as `node_modules/` and `managed_components/`. It reads the breakpoint
tiers from the project's `DESIGN.md` when it names them, and Bootstrap's otherwise. It needs git and Python 3.9+. In
the agent-harness kit, the `ui-designer` skill and agent apply it at their gates, the `design-system` skill owns the
spacing scale, the `accessibility` skill the minimum target and reflow, the `touch-and-gesture` skill safe areas and
the keyboard, and `verify.py run` runs the check.

## When to use

- Laying out a screen or a component, before drawing its draft.
- Choosing breakpoints, navigation, panes, a grid, margins, spacing or density.
- Making a screen adapt — a phone, a tablet, a desktop window, split screen, a foldable, an embedded panel in each
  rotation.
- Laying out for a watch, or a round or small square panel (LAYOUT §11).
- A layout scrolls sideways, breaks at one width, crowds or floats, or loses the person's place when the window
  changes.
- Reviewing a change to a layout.

## Rules

### Do

1. **Start from the smallest width and add as room appears** — mobile first; each tier adds to the one below
   (LAYOUT §1, §2).
2. **Read the window, never the device** — its logical width decides; no device type, user agent or model
   (LAYOUT §1, §12).
3. **Change the screen's structure only at Bootstrap's tiers** — `sm` 576, `md` 768, `lg` 992, `xl` 1200, `xxl` 1400,
   named as the brief's `breakpoint.*` tokens; a component that must change elsewhere uses its container's width
   (LAYOUT §2, §12).
4. **Write "below a tier" as 0.02 px under it on the web** — `max-width: 767.98px` (LAYOUT §2).
5. **Build every screen from the same regions, each in a fixed place, and scroll only the body** — one scroll per
   pane (LAYOUT §3).
6. **Put navigation at the bottom on `xs` and `sm`, at the side from `md`**, with the same destinations in the same
   order at every tier (LAYOUT §4).
7. **Add panes as the width allows, each at or above its minimum width**, and keep the pane in use when two become
   one (LAYOUT §5).
8. **Pick list and detail, a supporting pane or a feed before inventing a layout** (LAYOUT §5).
9. **Span whole columns, cap the content with the container, and grow margins with the tier** — each a token
   (LAYOUT §6).
10. **Take every gap from the spacing scale on its 4 or 8 base**; smaller inside a group than between groups; the
    container sets the gap, children carry no margins (LAYOUT §7).
11. **Change density by whole steps of the scale, never the hit area or the type** (LAYOUT §8).
12. **Give running text the measure's width and no more** — the measure is the `typography` skill's; a wider window
    adds panes or margin (LAYOUT §9).
13. **Keep scroll, selection, input and focus through every size change** (LAYOUT §10).
14. **Write the layout spec into the draft, tier by tier**, before the build (LAYOUT §13).
15. **Embedded (ESP-IDF, LVGL): find the panel's tier from its logical width** — pixels × 160 ÷ dpi — and lay out
    for that tier; a product for several boards picks it from the resolution at start (LAYOUT §2).
16. **Embedded (ESP-IDF, LVGL): lay out with flex and grid, gaps as `pad_row` and `pad_column`, sizes as
    `LV_SIZE_CONTENT` and `lv_pct`** — the web's layout in LVGL's words (LAYOUT §12).
17. **Embedded (ESP-IDF, LVGL): treat a rotation as a resize** — pick the tier again on
    `LV_EVENT_RESOLUTION_CHANGED`, keeping focus and scroll (LAYOUT §10).
18. **On a watch or a round or small panel, show one thing per screen in one column, scrolled vertically** — by touch
    and the crown, bezel or encoder alike; margins as a percentage of the screen; nothing in the curve or the corners;
    a round list's first and last items reach the centre (LAYOUT §11).
19. **Design the smallest watch or panel first; a larger one shows at least as much** (LAYOUT §11).

### Never

- **Choose a layout by device type** — a user agent, `userInterfaceIdiom`, an "is tablet" flag (LAYOUT §1).
- **Add a screen breakpoint that is not one of the brief's tiers** — a component's own change is a container query
  (LAYOUT §2).
- **Scale a phone layout up to a wide window**, or stretch a line of text across it (LAYOUT §1, §9).
- **Make anything wider than the window** — a fixed width at or above the smallest tier, a `100vw` element on a page
  that scrolls (LAYOUT §6).
- **Use a spacing, margin or gutter value off the brief's scale** — propose a step there first, or register an
  exception with its reason (LAYOUT §7).
- **Shrink a target below the brief's minimum to fit more in** — on a small panel, fewer items and paging (LAYOUT §8).
- **Animate a layout between tiers** — a size change lands at once (LAYOUT §10).
- **Lay out a round screen as if it were square** — text in the curve is clipped, and the framebuffer's corners are
  never seen (LAYOUT §11).
- **Claim a layout adapts from reading code** — it is resized across each tier on the target.
- **Embedded (ESP-IDF, LVGL): place objects at literal coordinates** — `lv_obj_set_pos` pins them to one panel and
  one rotation (LAYOUT §12).

## Procedure

### Deciding a screen's layout

1. **Read what exists** — DESIGN.md's layout and spacing tokens, the screens beside this one, the target's widths: the
   tiers the product ships to, or the panel's resolution and dpi.
2. **Name the content and its layout** — list and detail, a supporting pane, a feed, or a single column; and what the
   person does most on it (LAYOUT §5).
3. **Walk the tiers from `xs` up** — at each, the regions, the navigation, the panes, the grid, the margins; stop
   drawing a tier that only widens margins (LAYOUT §3–§6).
4. **Set the spacing by relationship** — inside a control, between controls, between groups — each a token
   (LAYOUT §7); and the density, if the surface is dense (LAYOUT §8).
5. **Decide what survives a size change** — which pane stays, where focus and scroll land (LAYOUT §10).
6. **Write the layout spec** into the draft's values file, tier by tier (LAYOUT §13); the draft is drawn at those
   widths and passes the `ui-designer` skill's gate 1.

### Building

1. **Build from the approved draft's spec, unchanged** — every value a token; a layout that must differ is a new draft.
2. **Write the tiers mobile first**, each from the brief's values (LAYOUT §2, §12).
3. **Run the layout check** (below) and the project's own checks.
4. **Resize across every tier boundary on the target** with a selection, a scroll position and a half-typed field;
   on a panel, rotate it. Hand the walk to the person for gate 3.

### Reviewing a layout change

1. **Run the layout check** on the changed UI files; a hit is a finding only on an added or changed line.
2. **Walk LAYOUT §14's order** — reflow and targets first, then window not device, breakpoints, regions and
   navigation, panes, grid and margins, spacing, content width, size changes, the draft.
3. **Read every number in a changed style** — a gap on the grid but off the scale, or a literal where a token
   belongs, is a finding the check cannot see.
4. **Hand the resize walk to the person** — what to do at each tier boundary on the target; never claim it passed
   from reading code.

## Checks

```sh
python3 .agents/skills/layout/scripts/layout_check.py            # every UI file, against the baseline
python3 .agents/skills/layout/scripts/layout_check.py <file> …   # the files a change touched
```

- [ ] (script) **G1** a layout chosen by device type — 0 hits
- [ ] (script) **G2** a screen breakpoint that is not one of the brief's tiers — 0 hits
- [ ] (script) **G3** a `100vw` width or Tailwind's `w-screen` — 0 hits
- [ ] (script) **G4** a spacing value off the base grid of 4 — 0 hits
- [ ] (script) **G5** a fixed width at or above the smallest tier outside a media or container query — 0 hits
- [ ] (script) **G6** Embedded: an object placed at literal coordinates — 0 hits
- [ ] The run read the UI files you expected — its last line counts the files it read, by kind (web, native,
  C/C++), and names where the tiers came from; "read no UI files" means nothing was checked
- [ ] The draft's layout spec covers each tier where the structure changes (Do 14)
- [ ] Navigation in its tier's form, the same destinations in the same order (Do 6)
- [ ] Panes at or above their minimum width; the pane in use survives a narrowing (Do 7)
- [ ] Every gap, margin and gutter a token; proximity groups (Do 9, Do 10)
- [ ] Running text held to the measure (Do 12)
- [ ] Resized across every tier boundary, or rotated on a panel, with state kept — handed to the person (Do 13)
- [ ] On a watch or a round or small panel: one purpose per screen, nothing in the curve or the corners, the list's
  ends reach the centre, the crown, bezel or encoder scrolls (Do 18)

G1 reads a user agent tested on a line that names a device, `userAgentData.mobile`, `userInterfaceIdiom`, an
`isTablet` name, `screen.width` and `UIScreen.main.bounds`; a width test named `isMobile` is not a device test and
passes. G2 reads `min-width` and `max-width` and range syntax (`width >= 768px`) in px, em and rem, in `@media`,
`matchMedia` and any query string such as a `useMediaQuery` hook's, and Tailwind's `min-[…]` and `max-[…]` variants;
a `@container` query is a component's and passes; a width 0.02 px under a tier counts as the tier; native code is not
read, so a width test in Swift or Kotlin against a number that is not a tier is the reviewer's. G3 passes a `100vw`
on a `position: fixed` rule. G4 reads CSS margin, padding, gap and inset in px and rem, Tailwind's arbitrary `p-[…]`,
`m-[…]` and `gap-[…]` and its half steps, SwiftUI `.padding(n)` and `spacing: n`, Compose `n.dp` in `padding(…)`,
`spacedBy(…)` and `Spacer`, Android XML `android:padding*` and `android:layout_margin*`, and LVGL's `pad_*` and
`margin_*` style setters; 0, 1 and 2 px pass as hairlines. G5 skips a value inside a media or container query or a
query string, and a rule that also sets a `max-width`; it keys on the smallest tier, so a narrower width that still
breaks reflow at 320 px is the reviewer's, and a table's `min-width` inside its own scroll box is a sanctioned
`layout-exception`. G6 reads C and C++ files and skips their comments: `lv_obj_set_pos` with two numbers that are not
both 0. A sanctioned hit carries `layout-exception` on its line with the reason. The check cannot see a gap off the
brief's scale but on the grid, a pane too narrow, navigation in the wrong form, or state lost on a resize — the draft,
the review and the walk find those.

## Traps

- **The page scrolls sideways on Windows but not on a Mac** → a `100vw` element is wider than the page by the
  scrollbar's width, and macOS hides scrollbars → `width: 100%` (G3).
- **A tablet in split view gets the tablet layout in a phone-sized window** → the layout tested the device, not the
  window → read the window's width (Do 2).
- **A media query on a token never matches** → `@media (min-width: var(--bp-md))`; custom properties do not work in
  media queries → the tier from the build or a Sass map (LAYOUT §12).
- **At exactly 768 px two rules apply, or none** → `max-width: 768px` overlaps `min-width: 768px` → `767.98px`
  (Do 4).
- **The list loses its place when the phone rotates** → state lived in a view the new tier removed → hoist it above
  the layout (Do 13).
- **Rows look uneven although each uses a token** → each child carries a margin, doubled between two and missing at
  the ends → the container's gap (Do 10).
- **Text runs edge to edge on a monitor** → the column grew with the window → the measure and the container's cap
  (Do 12).
- **Embedded: the screen breaks when the panel is rotated** → children placed with `lv_obj_set_pos` at the first
  orientation's coordinates → a flex or grid container (Do 16).
- **The first and last rows are cut off on a round watch** → the list was padded like a rectangle → pad its ends so
  they scroll to the centre, and shrink or inset rows near the edges (Do 18).
- **A larger watch shows the same few items, smaller margins wasted** → fixed margins in dp or points → margins as a
  percentage of the screen, and more content on the larger size (Do 18, Do 19).
- **Embedded: everything is tiny on a dense panel** → sizes written in pixels for a 160 dpi panel → the panel's
  tokens set for its density, or `lv_dpx` (Do 15).

## Sources

| Topic | Where |
| --- | --- |
| The principles, the spec, the review | [references/layout.md](references/layout.md) |
| Breakpoint tiers, max-width subtraction, containers, the twelve-column grid, gutters, spacers | Bootstrap 5.3 — Breakpoints, Containers, Grid, Gutters, Spacing (v5.3.9) |
| Spacing scales on a 4 or 8 base | IBM Carbon, Spacing; Atlassian Design System, Spacing; Shopify Polaris, Space; Bryn Jackson, "The 8-Point Grid" |
| List and detail, supporting pane, feed | Android Developers, "Canonical layouts" |
| Window, not device; state through size changes | Android Developers, "Use window size classes"; Apple Human Interface Guidelines, Layout |
| Bottom navigation | Apple Human Interface Guidelines, Tab bars |
| Watches and round screens | Apple Human Interface Guidelines — Designing for watchOS, Layout, Digital Crown; Android Developers, Wear OS — Screen sizes, Canonical adaptive layouts, Common layouts, Quality tiers |
| Reflow and target size | WCAG 2.2 — 1.4.10 Reflow, 2.5.8 Target Size (Minimum) |
| Embedded: flex, grid, styles, rotation | LVGL 9 docs — Flex, Grid, Style properties, Display (rotation, `LV_EVENT_RESOLUTION_CHANGED`), `lv_dpx` |
