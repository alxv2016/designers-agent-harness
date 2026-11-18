# Layout

How a product's screens are laid out and how they adapt: the breakpoints a layout changes at, the regions every screen
is built from, which navigation and how many panes each width takes, the grid, margins and container that hold content,
how space is applied, density, how wide content may run, what happens when the window changes size, and how a watch or a
round or small panel is laid out. People read it to decide a layout with reasons; coding agents read it, through the
`layout` skill, before they draft a screen, build one or review one.

**Where it lives.** In the `layout` skill, beside the steps and checks that apply it — [its SKILL.md](../SKILL.md).
The skill folder is self-contained: copy it into any repo's `.agents/skills/` and this reference and the layout check
come with it. The product's own values — its spacing scale, margins, gutters, pane widths, content width and density
levels — live in its design brief (`DESIGN.md` in the agent-harness kit) and win over this reference; the scale itself
is decided by the `design-system` skill, the minimum target size by the `accessibility` skill, and safe areas and the
on-screen keyboard by the `touch-and-gesture` skill.

**Platforms.** Every principle holds on every platform and is stated once, in its web form, then mapped. Guidance for
one platform is labelled **Web**, **iOS**, **Android** or **Embedded (ESP-IDF, LVGL)** — the last for a device with a
display drawn by LVGL on an Espressif chip. LVGL's layouts are modelled on the web's — its flex and grid layouts follow
CSS Flexbox and Grid, and its padding and gaps are style properties — so a layout decided for the web carries to a
panel with the same words (§12).

**Stability.** Cite this doc as `LAYOUT §n`. Do not renumber; add new material under the next free number.

| Tag | Meaning |
| --- | --- |
| `[D]` | Derived — calculated from cited values, not measured |

| § | Section | Look here for |
| --- | --- | --- |
| 1 | [Principles](#1-principles) | Content and the window decide; one structure that adapts; every value a token |
| 2 | [Breakpoints](#2-breakpoints) | Bootstrap's six tiers, mobile first, the units on each platform, a panel's logical width |
| 3 | [The scaffold](#3-the-scaffold) | The regions every screen is built from, and what scrolls |
| 4 | [Navigation by width](#4-navigation-by-width) | A bottom bar, a rail or a side list, by tier; the same destinations at every width |
| 5 | [Panes and canonical layouts](#5-panes-and-canonical-layouts) | How many panes per tier; list and detail, a supporting pane, a feed |
| 6 | [Grids, containers and margins](#6-grids-containers-and-margins) | Columns and gutters, the container's cap, margins that grow with the tier |
| 7 | [Spacing](#7-spacing) | The base grid, proximity, padding inside and gap between |
| 8 | [Density](#8-density) | Tighter or looser by whole steps, never below the minimum target |
| 9 | [Content width](#9-content-width) | Room for the measure, forms, media that keep their shape, sideways scrolling |
| 10 | [When the window changes](#10-when-the-window-changes) | Rotation, split screen, resizing, folding; state that survives |
| 11 | [Round and small screens](#11-round-and-small-screens) | Watches and small panels: one glance per screen, the circle's safe area, percentage margins, vertical scrolling, edges that follow the bezel |
| 12 | [The same layout on each platform](#12-the-same-layout-on-each-platform) | The web's layout words mapped to iOS, Android and LVGL |
| 13 | [The layout spec](#13-the-layout-spec) | What a draft records about its layout, tier by tier |
| 14 | [Reviewing layout](#14-reviewing-layout) | What a review of a layout change checks, in order |
| 15 | [The checks](#15-the-checks) | What the layout check finds, and what is left to read |

---

## 1. Principles

**Content and the window decide the layout; one structure adapts across every width, and every value is a token.**

- **Start at the smallest width and add as room appears** — mobile first: the one-column layout is the base, and each
  breakpoint adds columns, panes or navigation on top of it (Bootstrap 5.3, Breakpoints).
- **The window decides, never the device** — a tablet in split screen is a phone-width window, a phone held sideways
  is a short one, a desktop window can be any size. A layout reads the width it is given, never a device type, a user
  agent or a model name.
- **One structure that adapts, never a phone layout scaled up** — as the window widens, the layout reflows (columns
  join), reveals (a pane, labels on navigation), repositions (navigation moves from the bottom to the side) or divides
  (one view becomes list and detail); it never stretches a phone screen across a monitor.
- **Content sets the breakpoint a component changes at** — a card row wraps when its cards reach their minimum width,
  whatever tier that falls in; the tiers in §2 decide the screen's structure, a component's own container decides the
  component (§12, container queries).
- **Every space, width and margin is one of the brief's tokens** — a spacing step, a gutter, a pane width, the content
  width; a value off the scale is an exception registered with its reason (the `design-system` skill).
- **What the person was doing survives a change of size** — the scroll position, the selection, a half-typed field
  and focus stay where they were (§10).

## 2. Breakpoints

**The product's breakpoints are Bootstrap's six tiers, applied mobile first to the window's logical width.**

| Tier | Infix | From | Typical structure |
| --- | --- | --- | --- |
| Extra small | — (`xs`) | 0 | One column, navigation at the bottom, the primary action within thumb reach |
| Small | `sm` | 576 | One column, wider margins; a small phone held sideways, a narrow split-screen window |
| Medium | `md` | 768 | Navigation moves to the side; two columns where content allows; most phones held sideways |
| Large | `lg` | 992 | Two panes — list and detail, or content and a supporting pane |
| Extra large | `xl` | 1200 | Two panes with room; content held to the container's cap |
| Extra extra large | `xxl` | 1400 | A third pane where the content has one; otherwise wider margins, never longer lines |

Source: Bootstrap 5.3, Breakpoints (v5.3.9) — the widths are Bootstrap's; the structure column is this reference's.

- **Each tier starts at its width and holds until the next** — a rule for `md` applies from 768 upward. Write layout
  rules as "from this tier up" (`min-width`), so each tier only adds to the one below.
- **Web: a "below this tier" rule subtracts 0.02 px** — `max-width: 767.98px`, never `767px` or `768px`, so a window
  with a fractional width, which a high-density display can give, falls in exactly one tier (Bootstrap 5.3,
  Breakpoints). Native code compares numbers: `width < 768`.
- **The tiers are the brief's tokens** — `breakpoint.sm` to `breakpoint.xxl`, named once in DESIGN.md's layout section
  and read by code from there; a width that is not a tier is a component's own container query, never a screen
  breakpoint (§12).
- **The width is logical, never physical pixels** — CSS pixels on the web, points on iOS, dp on Android; on an
  embedded panel, the panel's pixels scaled to a 160 dpi reference, below.
- **Height is checked, not tiered** — the tiers are widths. A short window — a phone held sideways, a laptop with a
  docked keyboard — keeps the top bar and any fixed bottom bar from taking most of the height; the draft shows it at
  the smallest height the product supports (§13).
- **Embedded (ESP-IDF, LVGL): a panel's logical width is its width in pixels × 160 ÷ its dpi** — the same reference
  LVGL's `lv_dpx()` scales by. A 320 px panel at about 143 dpi is about 358 logical, `xs`; an 800 px panel at about
  217 dpi is about 590, `sm`; a 1024 px panel at about 170 dpi is about 964, `md` `[D]`. A panel read from farther
  away than a phone, such as one on a wall, scales by the viewing distance as the brief's type does (the
  `design-system` skill). Most panels are `xs` or `sm`, and a rotation can move a panel across a tier (§10).
- **Embedded (ESP-IDF, LVGL): a product built for one panel has one tier**, and its layout is that tier's; a product
  built for several boards picks its tier from the display's resolution at start, never from the board's name.

## 3. The scaffold

**Every screen is built from the same few regions, each in a fixed place, and only the body scrolls.**

| Region | Holds | Rule |
| --- | --- | --- |
| System areas | The status bar, the notch, the home or gesture bar; on a panel, round or cut corners and the band the bezel hides | Painted under, never covered with content — the `touch-and-gesture` skill's safe areas |
| Navigation | The product's top destinations | One place per tier (§4); the same destinations in the same order at every width |
| Top bar | The screen's title, back, and its few actions | Stays at the top; may shrink as the body scrolls, never moves sideways |
| Body | The content, in one to three panes (§5) | The only region that scrolls, each pane on its own |
| Bottom actions | A screen's primary action, a toolbar | Above the system area and the keyboard; never on top of the body's last item |

- **A region keeps its place at every width it appears in** — the person learns where back, the title and the
  primary action are once; a region that changes place at a tier moves the whole of it, never one control.
- **One scroll per pane** — the page and an inner panel scrolling the same way fight the finger and the wheel; a
  region that holds a list scrolls the list, and the screen around it stays still.
- **The body's last item clears whatever is fixed over it** — padding at its end the height of the bottom bar and the
  system area, so the last row can scroll into view.
- **Embedded (ESP-IDF, LVGL): the regions are objects on the screen in a column flex** — the top bar and bottom
  actions `LV_SIZE_CONTENT` high, the body `flex_grow` 1 and scrollable on one axis; navigation is a region only when
  the panel has room for it (§4).

## 4. Navigation by width

**The product's top destinations sit at the bottom on a narrow window and move to the side as it widens; they are the
same destinations, in the same order, at every width.**

| Tier | Navigation | Why |
| --- | --- | --- |
| `xs`, `sm` | A bottom bar of three to five destinations, each an icon with a label | The thumb reaches the bottom of a phone held in one hand (Apple Human Interface Guidelines, Tab bars) |
| `md` | A rail at the leading edge — icons with labels, stacked | Two hands hold the sides of a tablet; the bottom of a wide screen is far from both |
| `lg` and up | The rail, or a side list with full labels and sections when there are more destinations | The width can spare a column, and labels read faster than icons |

- **More than five destinations at `xs`** — the five most used in the bar and the rest behind a "More" destination or
  a menu in the top bar; never a scrolling bar.
- **The current destination is shown by more than colour** — a filled icon or an indicator, never a heavier label,
  which widens the text and moves the layout (the `accessibility` and `typography` skills).
- **How a bar behaves — switching, each destination's scroll and state, the active tab returning to its top — is
  the `touch-and-gesture` skill's**; this section decides only which form navigation takes and where.
- **Focus order follows the navigation's visual order** at every tier — a rail reads top to bottom, a bar leading to
  trailing.
- **The primary action stays with its content**, not with the navigation — when navigation moves to the side, a
  screen's primary action stays in its screen.
- **Embedded (ESP-IDF, LVGL): a small panel shows one destination at a time** — a home screen of destinations, or
  pages side by side in an `lv_tileview`, with back on one path the product defines (the `touch-and-gesture` skill);
  a bottom bar only when the panel's height leaves the body room for its content, and a rail when the panel is wide
  (`md` or more). The encoder or keys step through the destinations in their visual order.

## 5. Panes and canonical layouts

**The body holds one pane on a narrow window and adds panes as the width allows, each pane at or above its minimum
width; three layouts cover most screens.**

| Tier | Panes |
| --- | --- |
| `xs`, `sm` | One |
| `md` | One, or two when each holds its minimum width (`size.pane-min` or the brief's name for it) |
| `lg`, `xl` | Two |
| `xxl` | Two, or three when the content has a third — a supporting pane beside list and detail |

| Layout | Use for | Narrow (one pane) | Wide (two or more) |
| --- | --- | --- | --- |
| List and detail | Items the person picks from and reads one at a time — messages, files, settings | The list; picking an item opens its detail on top, and back returns to the list | List and detail side by side; the list marks the item shown |
| Supporting pane | Content with a companion that only makes sense beside it — a document and its comments, a video and what is next | The supporting content below the main, or in a sheet | The main pane takes the larger share, a ratio the brief names; the supporting pane the rest |
| Feed | Many items of the same kind, browsed — cards, photos, products | One column | A grid whose column count follows the items' minimum width; headers and dividers span every column |

Source: the three layouts are the ones Android Developers name in "Canonical layouts"; the tiers are §2's.

- **A pane is fixed or fluid, and the brief says which** — a list pane holds a fixed width token, a detail or main pane
  takes the rest; two fluid panes share by a named ratio.
- **The gap between panes is a spacing token**, the same at every tier; a divider in it is optional, never both a wide
  gap and a heavy line.
- **When two panes become one, the pane the person is acting in stays** — reading a detail, the narrower window shows
  the detail, and back leads to the list; with nothing picked, the wide layout shows a placeholder in the detail pane
  that says what to pick, never an empty box.
- **A pane may be resized by dragging its edge only with a plain alternative** — a button or a setting that sets the
  same widths (the `accessibility` skill).
- **Embedded (ESP-IDF, LVGL): two panes are two objects in a row flex** — the list a fixed width token, the detail
  `flex_grow` 1; on one-pane panels, list and detail are two screens and back returns to the list with its scroll and
  focus where they were.

## 6. Grids, containers and margins

**Columns align content without dictating it; a container caps the content's width; margins grow with the tier.**

- **A twelve-column grid with a fixed gutter is the common default from `md` up** — twelve divides into halves, thirds,
  quarters and sixths, and a narrow window uses fewer columns, or none; Bootstrap's gutter is 1.5 rem (24 px) (Bootstrap
  5.3, Grid; Gutters). The product's column count and gutter are the brief's tokens; a product with no grid lays out
  with panes and gaps alone.
- **A component spans whole columns at each tier** — six of twelve at `md`, four at `lg`; it never sets its own width
  in pixels against the grid.
- **The container caps the width of the content, centred, from a tier up** — Bootstrap's `.container` caps at 540,
  720, 960, 1140 and 1320 px from `sm` to `xxl` (Bootstrap 5.3, Containers). The product names its own caps, or one
  `size.content-max`, as tokens; a full-bleed region — a map, a hero image, a table — runs edge to edge outside it.
- **Margins grow with the tier, from the brief's spacing scale** — a smaller step at `xs`, a larger one from `md`;
  fluid between two steps (`clamp()` on the web) when the brief says so.
- **Nothing is wider than the window** — no fixed width at or above the smallest tier's, no `100vw` element on a page
  that scrolls (it adds the scrollbar's width and scrolls sideways); the page reflows at 320 CSS px wide (the
  `accessibility` skill, WCAG 1.4.10).
- **Embedded (ESP-IDF, LVGL): the grid is an LVGL grid layout** — `lv_obj_set_grid_dsc_array` with `LV_GRID_FR(1)`
  columns, the gutter as the container's `pad_column`, each child placed by `lv_obj_set_grid_cell`; the screen's
  margin is the screen's padding, from the brief's spacing token, inside the panel's safe area (§12).

## 7. Spacing

**Every gap is a step on one scale built on a 4 or 8 base; space shows what belongs together.**

- **One base, a few steps** — an 8-point base with a 4-point half step for small elements is the common standard:
  Bootstrap's spacers are 4, 8, 16, 24 and 48 px at a 16 px root (Bootstrap 5.3, Spacing), and IBM Carbon, Atlassian
  and Shopify Polaris build their scales on 4 or 8 (IBM Carbon, Spacing; Atlassian Design System, Spacing; Shopify
  Polaris, Space; Bryn Jackson, "The 8-Point Grid"). The product's scale is the brief's (the `design-system` skill).
- **Sizes land on the base too** — a control's height, an icon's box, a line height: on a 4 base, multiples of 4, so
  edges and baselines line up across components.
- **Proximity groups** — the space inside a group is smaller than the space between groups, by at least one step, so
  related things read as one (the Gestalt law of proximity).
- **Padding is inside a box, gap is between boxes** — the container sets the gap between its children (`gap` on the
  web, `pad_row` and `pad_column` on LVGL, `spacing:` in SwiftUI, `Arrangement.spacedBy` in Compose); children do not
  each carry a margin that doubles at one edge and goes missing at the other.
- **The same relationship gets the same space everywhere** — a label to its field, a heading to its body, a card to
  the next card: one token each, named for the relationship in the brief.
- **An optical adjustment off the scale is an exception** — an icon nudged to look centred, registered with its reason;
  never a habit.

## 8. Density

**Density tightens or loosens a surface by whole steps of the spacing scale, never below the minimum target and never
by shrinking text.**

- **Density changes padding and row height**, by one or two steps of the scale; type sizes, icon sizes and the
  hit area stay.
- **The hit area never drops below the brief's minimum target** (`size.target`, at or above WCAG 2.5.8's 24 × 24 CSS px)
  — a denser row keeps its target, and the spacing around each small target stays clear (WCAG 2.5.8); the
  `accessibility` skill holds the floor.
- **Density follows the kind of surface** — dense where the person scans many items with a pointer: data tables, long
  lists, toolbars and inspectors on a wide window; the default on touch, on forms, on anything read once.
- **Offer density as the person's setting when people disagree on it**, applied across the whole product.
- **Embedded (ESP-IDF, LVGL): a small panel is no reason to shrink targets** — fewer items per screen, and paging or
  scrolling for the rest; density on a panel is chosen for the finger, the encoder and the viewing distance, in panel
  pixels from the brief's tokens.

## 9. Content width

**Content gets the width it reads best at; a wider window adds panes or margin, never longer lines.**

- **Running text is held to the measure the `typography` skill sets** — a token in the brief; the layout gives text
  that width and no more.
- **A wide window gives text more margin or a second pane** — the container cap (§6) and the measure keep the line;
  a form keeps its fields at the width of what they hold, never stretched across the screen.
- **Media keep their aspect ratio** — an image or video fills its column's width at its own ratio, with its box
  reserved before it loads (the `design-system` skill, layout stability).
- **Tables and code may scroll sideways in their own box**, never the page (WCAG 1.4.10).
- **Embedded (ESP-IDF, LVGL): a label is given its column's width** — how it wraps on the panel is the
  `accessibility` skill's reflow, and the room each string needs the `ux-content` skill's.

## 10. When the window changes

**The layout follows the window as it changes, and the person's place survives.**

- **What changes a window's size** — rotation, split screen and slide-over, resizing a desktop window, folding or
  unfolding a phone, moving to an external display, the browser's zoom.
- **The layout recomputes from the new width**, through the same tiers (§2); nothing is decided once at launch.
- **The person's text size is a layout input too** — at the largest text size (200 %, Dynamic Type's accessibility
  sizes, Android's font scale) a row that no longer fits becomes a column, a label wraps rather than clips, and a
  fixed-height box grows (`ViewThatFits`, `FlowRow`, a wrapping flex); the `accessibility` skill holds the floor.
- **Scroll, selection, input and focus stay** — the item that was in view stays in view, the selected item stays
  selected, a half-typed field keeps its text, focus stays on the same element; state lives above the layout that
  shows it, never in a view a tier removes.
- **Two panes becoming one keep the pane in use** (§5); one becoming two shows the detail of the item that was open.
- **A size change lands at once** — a layout the product animates itself does not animate between tiers (the `motion`
  skill: no layout property animates); a platform container's own transition, such as a split view's, stays, and
  follows reduced motion.
- **Embedded (ESP-IDF, LVGL): rotation is the panel's resize** — `lv_display_set_rotation` swaps the width and height,
  LVGL sends `LV_EVENT_RESOLUTION_CHANGED` to the display's handlers (`lv_display_add_event_cb`), and flex and grid
  containers re-lay their children themselves; a layout that picked its structure by tier picks again in that event,
  keeping the focused object and each list's scroll.

## 11. Round and small screens

**A watch or a small panel shows one thing at a glance: one column inside the screen's safe shape, margins that scale
with the screen, and vertical scrolling driven by touch and the crown, bezel or encoder alike.**

These screens fall inside `xs`, where §2's tiers do not divide them; the screen's shape and size do. This section
governs, over §3 to §5, on a watch, on any round screen, and on a panel narrower than the size the brief names for a
small screen; it holds on a round screen, a rounded square such as Apple Watch, and an embedded panel of either shape.

### 11.1 Every small screen

- **One glance, one purpose per screen** — the one piece of information the person came for and one or two actions;
  people look for seconds, "concise app interactions that can last for less than a minute each" (Apple Human
  Interface Guidelines, Designing for watchOS). The hierarchy is shallow: a few levels, never a deep tree.
- **One column, scrolling vertically** — vertical scrolling is the default layout, and vertical pages beat horizontal
  ones; a screen that does not scroll is kept for a single task such as a media player, a picker or a workout
  (Apple Human Interface Guidelines, Digital Crown; Android Developers, Wear OS "Common layouts").
- **The crown, bezel or encoder scrolls what touch scrolls, and touch can do all it does** — with visible movement for
  every step, and haptic detents where the platform gives them (Apple Human Interface Guidelines, Digital Crown); on
  a panel, the encoder steps focus through the column in its visual order (the `accessibility` skill's focus model).
- **Design the smallest screen first; a larger one shows at least as much, never less** — Wear OS starts at its
  smallest round screen, 192 dp, and splits small from large at 225 dp (Android Developers, Wear OS "Screen sizes",
  "Quality tiers"). The brief names its own smallest watch or panel and any split, as a token.
- **Margins are a percentage of the screen, not a fixed size** — they scale with the circle, so content is never
  clipped on a larger or smaller watch (Android Developers, Wear OS "Screen sizes"). The brief names the percentages.
- **Fewer, larger targets, never smaller ones** — the brief's minimum target holds on the smallest screen; a screen
  with too many controls splits into two (§8).
- **Text is short and wraps; curved text only for a short title at an edge** — the type sizes are the brief's, and
  the `ux-content` skill holds the room each string needs.

### 11.2 Round screens

- **On a round screen, the curve takes width at the top and bottom** — a row at height *y* from the centre has
  2√(r² − y²) of width; the largest square inside the circle is the diameter ÷ √2, about 70.7 % of it, an inset of
  about 14.6 % on each side `[D]`. Centre rows may run wider than that square; top and bottom rows must run narrower.
- **A screen that does not scroll is three bands** — top and bottom bands inset from the curve, the middle band the
  full width for the main content (Android Developers, Wear OS "Canonical adaptive layouts").
- **A scrolling list on a round screen reaches the centre at both ends** — the first item, a header, and the last item
  carry enough padding to scroll to the middle of the screen, where the circle is widest; rows near the top and bottom
  edges shrink or move inward as they scroll, so none is cut by the curve (Wear OS `TransformingLazyColumn`; LVGL,
  below).
- **Edges follow the bezel** — a curved scroll indicator, the time at the top, a button that hugs the bottom edge use
  the screen's curve rather than fighting it, and grow with the screen (Android Developers, Wear OS "Canonical
  adaptive layouts").

### 11.3 Rounded-square screens

- **On a rounded-square screen, backgrounds run to the edge and text stays inside the margins** — the bezel frames the
  screen; text buttons span the full width, and a row holds at most three icon buttons or two text buttons (Apple
  Human Interface Guidelines, Layout). No text sits in a rounded corner.

### 11.4 Embedded (ESP-IDF, LVGL)

- **Embedded (ESP-IDF, LVGL): lay out inside the circle, never the framebuffer's square** — the panel's visible
  shape is the `touch-and-gesture` skill's safe area; a scrolling column is a flex column with
  `LV_SCROLL_SNAP_CENTER`, and each row is moved or scaled in the column's `LV_EVENT_SCROLL` by its distance from the
  centre, as LVGL's round-display scroll example does; margins are set from the panel's width as a percentage
  (`lv_pct`) or from the brief's tokens for its one panel.

## 12. The same layout on each platform

**A layout is decided once, in the web's words, and built with each platform's equivalent.**

| Concept | Web | iOS | Android | Embedded (ESP-IDF, LVGL) |
| --- | --- | --- | --- | --- |
| The window's width | The viewport, in CSS px | The window's width in points | The window's width in dp (Jetpack WindowManager, `WindowMetricsCalculator`) | The display's resolution, as a logical width (§2) |
| A tier, from here up | `@media (min-width: 768px)` from the brief's tier; Bootstrap's `media-breakpoint-up(md)` | `width >= 768` in the view that owns the layout; `horizontalSizeClass` decides the system's own containers | `widthDp >= 768`; Views: a `layout-w768dp` resource folder | `logical_width >= 768`, at start and on a resolution change |
| A component's own breakpoint | `@container (min-width: …)` on its container | `ViewThatFits`; the container's size from `onGeometryChange` | `BoxWithConstraints` | The parent's content width, read in `LV_EVENT_SIZE_CHANGED` |
| A row or column | `display: flex; flex-direction: row` | `HStack`, `VStack` | `Row`, `Column` | `lv_obj_set_flex_flow(obj, LV_FLEX_FLOW_ROW)` |
| Wrapping | `flex-wrap: wrap` | A custom `Layout`, `LazyVGrid` | `FlowRow` | `LV_FLEX_FLOW_ROW_WRAP`; `LV_OBJ_FLAG_FLEX_IN_NEW_TRACK` starts a new line |
| Take the space left | `flex-grow: 1` | `.frame(maxWidth: .infinity)`, `Spacer()` | `Modifier.weight(1f)` | `lv_obj_set_flex_grow(child, 1)` |
| Align along and across | `justify-content`, `align-items`, `align-content` | The stack's `alignment`, `Spacer` | `Arrangement`, `Alignment` | `lv_obj_set_flex_align(obj, main, cross, track)` |
| Gap between children | `gap`, `row-gap`, `column-gap` | `spacing:` | `Arrangement.spacedBy` | `pad_row`, `pad_column` style properties |
| Padding | `padding` | `.padding()` | `Modifier.padding` | `pad_left`, `pad_right`, `pad_top`, `pad_bottom`, `pad_all` |
| A grid | `display: grid; grid-template-columns: 1fr 2fr` | `Grid`, `LazyVGrid` with `GridItem` | `LazyVerticalGrid` | `lv_obj_set_grid_dsc_array` with `LV_GRID_FR(1)`, `LV_GRID_FR(2)`, `LV_GRID_TEMPLATE_LAST` |
| A cell spanning columns | `grid-column: 1 / span 2` | `.gridCellColumns(2)` in a `Grid`; a section header in a `LazyVGrid` | `GridItemSpan(maxLineSpan)` for a full row | `lv_obj_set_grid_cell(child, LV_GRID_ALIGN_STRETCH, 0, 2, …)` |
| Sized by content | `width: fit-content`, `auto` | The view's ideal size | `wrapContentWidth()` | `LV_SIZE_CONTENT` |
| A share of the parent | `width: 50%` | `containerRelativeFrame` (iOS 17; a share of the nearest container) | `fillMaxWidth(0.5f)` | `lv_pct(50)` |
| Cap the width | `max-width` | `.frame(maxWidth:)` | `widthIn(max =)` | `max_width` style property |
| Navigation by width | A bottom bar below `md`, a rail or side list from it (§4) | `TabView`, with `.sidebarAdaptable` for a sidebar on a wide window | `NavigationSuiteScaffold`, its type chosen from the tier: `NavigationBar`, `NavigationRail`, a drawer | A home screen or `lv_tileview` pages; a rail object on a wide panel |
| List and detail | Two grid columns from a tier up | `NavigationSplitView` | `ListDetailPaneScaffold` | Two objects in a row flex, or two screens (§5) |
| A logical unit | CSS px, `rem` | Points | dp | `lv_dpx(n)` |

- **Web: a breakpoint token cannot be a CSS custom property inside `@media`** — `@media (min-width: var(--bp-md))`
  never matches. The tiers reach media queries through the preprocessor or build (a Sass map, PostCSS custom media)
  or through `matchMedia` in script, each from the brief's values.
- **A platform container splits at its own size unless the product tells it** — Android's pane and navigation
  scaffolds default to their own window classes; pass the tier's decision in (a `PaneScaffoldDirective` with the
  tier's pane count, the navigation suite's type from the tier). iOS's `NavigationSplitView` and `TabView` follow
  the size class, which the product accepts for those system containers and does not fight; its own layouts follow
  the tiers.
- **iOS: the iPad tab bar sits at the top** — the thumb-reach reason for a bottom bar (§4) is the iPhone's.
- **iOS: choose a layout by width, never by `userInterfaceIdiom`** — an iPad app in split view is a phone-width
  window.
- **Android: never branch on "is this a tablet"** — a resource flag set by screen size, the device's smallest width or
  its model; read the window.
- **Embedded (ESP-IDF, LVGL): place with flex and grid, not coordinates** — on a parent with no layout, `lv_obj_set_pos`
  with numbers pins an object to one panel and one rotation (a flex or grid parent overrides it); `lv_obj_align` to a
  parent edge or a flex or grid cell moves with the layout. Spacing values are the brief's tokens from its C header,
  applied through shared `lv_style_t` styles (the `design-system` skill).

## 13. The layout spec

**A draft records its layout tier by tier, so the build has nothing left to decide.**

The draft's values file (`<screen>_mock<n>.md` in the `ui-designer` skill) holds, for each tier the draft shows:

| Field | Holds |
| --- | --- |
| Tiers drawn | Each tier where the layout changes, at a width inside it, plus 320 CSS px for reflow and the shortest height; on a panel, its resolution in each rotation it supports |
| Shape | Rectangle, round or rounded square; on a round screen, the inset used at the top, middle and bottom (§11) |
| Regions | Which of §3's regions appear, and where |
| Navigation | Bar, rail or side list (§4), and the destinations in order |
| Panes | How many, which are fixed and which fluid, their width tokens or ratio, the gap token (§5) |
| Grid and container | Columns, gutter, the container's cap or full bleed (§6) |
| Margins | The edge token at this tier |
| Spacing | The token for each relationship — inside a control, between controls, between groups (§7) |
| Density | The density level, and each target's hit area (§8) |
| Content width | The measure for running text (§9) |
| On a size change | What stays and what moves when the window crosses into the next tier (§10) |

- **Draw at least the narrowest tier and the widest the product supports**, and every tier in between where the
  structure changes; a tier that only widens margins needs no drawing of its own.
- **The focus order is written per tier when it changes** — navigation moving from the bottom to the side moves it in
  the order.

## 14. Reviewing layout

**A layout review walks the screen at each tier, in a fixed order, accessibility first.**

1. **Reflow and targets** — at 320 CSS px nothing scrolls sideways or is cut off; every target holds the minimum hit
   area at every density (the `accessibility` skill).
2. **Window, not device** — no layout chosen by device type, user agent or model (§1, §12).
3. **Breakpoints** — each screen breakpoint is one of the brief's tiers, written mobile first (§2).
4. **Regions and navigation** — the regions in their places; navigation in the tier's form, the same destinations in
   the same order (§3, §4).
5. **Panes** — the count fits the tier and each pane its minimum width; the pane in use survives a narrowing (§5).
6. **Grid, container, margins** — whole columns, the container's cap, margins from the scale (§6).
7. **Spacing** — every gap a token; proximity groups; padding inside and gap between (§7).
8. **Content width** — running text held to the measure; media at their ratio (§9).
9. **Size changes** — resized across each tier boundary with a selection, a scroll position and a half-typed field: all
   survive (§10).
10. **Round and small screens** — one purpose per screen; nothing in the curve or the corners; the first and last
    items reach the centre; the crown, bezel or encoder scrolls what touch does (§11).
11. **The draft** — the built layout matches the draft's spec tier by tier (§13); a difference is a new draft.

## 15. The checks

**The layout check finds what a line of code can show; the walk across tiers finds the rest.**

| Check | Finds | § |
| --- | --- | --- |
| G1 | A layout chosen by device type — a user agent test, `userInterfaceIdiom`, an `isTablet` flag | §1, §12 |
| G2 | A screen breakpoint that is not one of the brief's tiers — in a media query, `matchMedia` or a Tailwind `min-[…]` or `max-[…]` variant | §2 |
| G3 | A width of `100vw`, or Tailwind's `w-screen`, which scrolls sideways when the page has a scrollbar | §6 |
| G4 | A spacing value off the base grid — a margin, padding, gap or inset that is not a multiple of 4; SwiftUI, Compose and LVGL padding and gaps too | §7 |
| G5 | A fixed `width` or `min-width` at or above the smallest tier (576 px, 36 rem) outside a media or container query, in a rule with no `max-width` | §6 |
| G6 | Embedded: an object placed at literal coordinates with `lv_obj_set_pos` | §12 |

- **The tiers come from the brief** — the check reads `breakpoint.*` rows from DESIGN.md's token tables when the repo
  has one, and Bootstrap's 576, 768, 992, 1200 and 1400 otherwise; a `max-width` 0.02 px below a tier counts as that
  tier.
- **What no script reads**: a spacing value on the grid but off the brief's scale, or written as a literal where a
  token belongs (the reviewer reads every number in a changed style); a pane under its minimum width; navigation in
  the wrong form for its tier; focus or state lost on a resize; a line of text over the measure. The draft, the
  review and the walk across tiers find those.
