# Touch

How touch input, gestures, scroll-linked motion and layout are built so they feel direct and never fight the
platform: how a gesture starts, claims its axis, shares with scrolling and decides on release; how the common gesture
patterns behave; how touch feedback, scroll effects and layout work on the web, iOS, Android and an embedded device's
panel; how an encoder and buttons stand beside touch; and how a gesture is specified, prototyped and walked on a
device. People read it to decide how a touch interaction should behave; coding agents read it, through the
`touch-and-gesture` skill, before they spec, build or review one.

**Where it lives.** In the `touch-and-gesture` skill, beside the steps and checks that apply it —
[its SKILL.md](../SKILL.md). The skill folder is self-contained: copy it into any repo's `.agents/skills/` and this
reference and the touch check come with it. Haptics, sound and status lights are its neighbour `FEEDBACK`'s
(`references/feedback.md`). The product's own values — its target size, its spring, its hold length, which gestures
it uses — live in its design brief (`DESIGN.md` in the agent-harness kit).

**What it builds on.** The floors for input are the `accessibility` skill's: a target size, a plain alternative to
every gesture, drag, long press and hover, acting on release, hover never the only path, both orientations, time
limits, reduced motion. How a move eases, settles and survives interruption — including keeping a dragged object under
the finger with no easing — is the `motion` skill's. This doc does not restate them; it says how each is built on
touch.

**Platforms.** Each principle is stated once, for every platform. How a platform builds it is labelled **Web**,
**iOS**, **Android** or **Embedded (ESP-IDF, LVGL)**, in a bold lead or a table column. Embedded means a device on
ESP-IDF that draws with LVGL and takes touch, a rotary encoder, buttons, or any mix of them. LVGL names here are LVGL
9's, checked against its 9.6 source; LVGL 8 spells some differently (`lv_btn_create`, `lv_obj_clear_flag`, the input
settings as fields of `lv_indev_drv_t`). Its input settings are LVGL's (`lv_conf.h`, or `CONFIG_LV_…` in Kconfig); the
values the product chooses for them live in its design brief, like every other value.

**Stability.** Cite this doc as `TOUCH §n`. Do not renumber; add new material under the next free number.

| § | Section | Look here for |
| --- | --- | --- |
| 1 | [Direct manipulation](#1-direct-manipulation) | What follows the drag, catching a moving object, how often the input is read, the platform tools |
| 2 | [Starting and claiming a gesture](#2-starting-and-claiming-a-gesture) | Movement tolerance, axis lock, sharing with scrolling, scroll chaining, the sheet hand-off |
| 3 | [Deciding on release](#3-deciding-on-release) | Distance or speed, the throw's speed and a rested finger, refusing a throw, resistance past a limit, which event acts, what cancels on touch |
| 4 | [Gesture patterns](#4-gesture-patterns) | Sheets, swipe actions, long press, hold, reorder, pull to refresh, pinch, screen and bezel edges, a scroll never an edge gesture, the open guard, decoration that takes no press |
| 5 | [Touch feedback](#5-touch-feedback) | The pressed state on touch, delays in scrolling lists, tap highlight, menus, selection; haptics point to `FEEDBACK` |
| 6 | [Scroll-linked motion](#6-scroll-linked-motion) | Triggered against driven, scroll events on a device, never taking over scrolling |
| 7 | [Mobile layout](#7-mobile-layout) | The visible area, safe areas, round and small panels, the keyboard, field keyboards, back, bottom navigation |
| 8 | [The gesture spec](#8-the-gesture-spec) | What to settle before building a gesture, and how to prototype it |
| 9 | [The device walk](#9-the-device-walk) | What only a real device shows, and how to check it |
| 10 | [Reviewing a gesture change](#10-reviewing-a-gesture-change) | What a review checks, and what it hands to the person |
| 11 | [Encoder and buttons](#11-encoder-and-buttons) | How a press and a long press line up with a tap, the events LVGL sends, back, lost presses; the focus model is `FOCUS`'s |

---

## 1. Direct manipulation

**Everything that reacts to a drag derives from the one drag position, and anything a gesture can touch can be caught
mid-animation.**

- **One position drives everything** — the scrim's opacity, the page behind, the handle, the sheet's corner radius;
  separate animations drift apart when the drag reverses.
- **Catching a moving object stops it under the finger with no jump** — the release animation is interruptible, so a
  second touch picks it up where it is (the `motion` skill, interruption).
- **The input is read at least as often as the screen draws** — what follows the finger moves no more often than the
  touch is read, so a slow read rate looks like a drag that lags and steps.
- **The touch's axes match the screen's** — a panel rotated without its touch rotated turns every drag sideways or
  backwards.
- **Platform tools** (Apple, "Designing Fluid Interfaces", WWDC 2018; MDN, Pointer events; LVGL, `lv_indev.h`):
  - **iOS**: a pan gesture recognizer's translation and velocity, interruptible animators or SwiftUI springs.
  - **Android**: `VelocityTracker`, Compose `draggable` and `AnchoredDraggableState`.
  - **Web**: pointer events with `setPointerCapture`, so the drag keeps its pointer when the finger leaves the element.
  - **Embedded (ESP-IDF, LVGL)**: a drag reads `lv_indev_get_point` or `lv_indev_get_vect` on `LV_EVENT_PRESSING`;
    `LV_OBJ_FLAG_PRESS_LOCK`, on by default on every child, keeps the press on the object when the finger leaves it. A
    press on a scroller mid-throw stops the throw where it is; an animation the product runs (`lv_anim_t`) is caught
    by deleting it on `LV_EVENT_PRESSED` and starting the drag from the object's current value.
- **Embedded (ESP-IDF, LVGL) — the read rate**: LVGL reads each input device on a timer at `LV_DEF_REFR_PERIOD`,
  the period that also refreshes the display and steps animations — its default and its cost are `MOTION §7.1`'s — so
  a drag moves at most once per period. Change one device's read period with
  `lv_timer_set_period(lv_indev_get_read_timer(indev), …)`, and keep the touch controller's own report rate at or
  above it. With the controller's interrupt line wired (`int_gpio_num` in `esp_lcd_touch_config_t`),
  `esp_lvgl_port` runs the device in `LV_INDEV_MODE_EVENT`, so the bus is read only while there is a touch (ESP-BSP,
  `esp_lvgl_port`).
- **Embedded (ESP-IDF, LVGL) — the axes**: set the controller's swap and mirror to the panel's rotation
  (`esp_lcd_touch_set_swap_xy`, `esp_lcd_touch_set_mirror_x`, `esp_lcd_touch_set_mirror_y`, or the same flags in
  `esp_lcd_touch_config_t`), and clamp a reported point to the panel — a controller can report a point a little past
  the last row or column (ESP-BSP, `esp_lcd_touch`).

## 2. Starting and claiming a gesture

**A press becomes a drag only past the platform's movement tolerance, then locks to one axis and claims only that
axis.**

- **Use the platform's tolerance** — one distance for every drag and scroll on the platform, so a custom drag and a
  scroll start at the same point; larger for touch than for a mouse.
- **Lock to one axis once the gesture starts**, measured from where it crossed the tolerance, so a vertical scroll
  that starts on a swipeable row scrolls the page and leaves the row alone.
- **Claim only the axes you use** — the other axis goes on to the scroller behind; only a handle, a slider thumb, a
  canvas or a map whose every gesture is the app's claims both.
- **A sheet with scrolling content hands off within the same finger** — while the list is not at its top, a downward
  drag scrolls it; once it reaches the top, the same drag moves the sheet. At a lower detent, an upward drag expands
  the sheet before its list scrolls. The leftover momentum of a fling that reaches the top never moves or closes the
  sheet (Apple HIG, Sheets; Material Design 3, Bottom sheets; Android, nested scrolling).
- **A custom pull to refresh or overscroll effect contains the platform's own**, so the page behind does not also
  refresh or bounce.

| Concern | Web | iOS | Android | Embedded (ESP-IDF, LVGL) |
| --- | --- | --- | --- | --- |
| Tolerance | Yours to set | The recognizers apply theirs | Touch slop (`ViewConfiguration.getScaledTouchSlop`) | The scroll limit: `LV_INDEV_DEF_SCROLL_LIMIT` (10 px by default), or `lv_indev_set_scroll_limit` per device; a custom drag starts at the same distance |
| Axis lock | Yours: compare the two moves at the tolerance | Pan recognizers per axis | Nested scrolling decides | LVGL picks the axis with the larger summed move once it passes the scroll limit, and keeps it for the rest of the press |
| Claiming an axis | `touch-action` names what the browser keeps: `pan-y` on a horizontal carousel, `manipulation` on a control that only taps (it also drops the double-tap zoom wait), `none` only on a handle, thumb, canvas or map (MDN, `touch-action`) | Recognizer failure requirements | Intercept only once the gesture is yours | `lv_obj_set_scroll_dir` limits a scroller to its axis. A drag that starts on an object passes up to the scroller behind through scroll chaining (`LV_OBJ_FLAG_SCROLL_CHAIN_HOR`, `_VER`, on by default on every child); removing one axis's flag claims that axis, as LVGL's slider does for its own; removing both stops every drag that starts there — the `touch-action: none` trap |
| Sheet hand-off | Yours: the list's scroll position decides | The sheet presentation does it | Nested scrolling does it | LVGL picks the scroller once per press: with the list at its top, a downward drag chains to the sheet; a drag that starts part-way scrolls only the list, to its elastic end, and its throw never moves the sheet. A hand-off within one press is the product's own code |
| Containing overscroll | `overscroll-behavior-y: contain` on that scroller | — | — | Nothing to contain: the elastic end stays on the scroller that took the press |

- **Embedded (ESP-IDF, LVGL) — swipes**: `LV_EVENT_GESTURE` fires during the press, only when no scroller took it,
  once the move passes `LV_INDEV_DEF_GESTURE_LIMIT` (50 px by default, `lv_indev_set_gesture_min_distance`) with each
  read's move above `LV_INDEV_DEF_GESTURE_MIN_VELOCITY` (3 px, `lv_indev_set_gesture_min_velocity`). It goes to the
  first object, from the pressed one up, without `LV_OBJ_FLAG_GESTURE_BUBBLE` — on by default on every child, so by
  default the screen gets it — and the object whose swipe it is removes that flag. It cannot be refused on release
  (§3).

## 3. Deciding on release

**On lift, commit when moved far enough or thrown fast enough in an allowed direction; otherwise go back.**

- **Distance or speed** — distance alone ignores a flick; a speed threshold holds only for the velocity measure it was
  tuned with (Material Design 3, Gestures; Compose `AnchoredDraggableState` takes both).
- **A pull back from the furthest point, or a finger resting before lift, refuses the throw**, and a refused gesture
  returns quickly; how it settles is the `motion` skill's.
- **The throw's speed is the finger's speed over a short window at the end of the drag** — never an average over the
  whole drag, which reads several times lower. A finger that rested before lifting placed the object rather than threw
  it: its speed is zero and distance alone decides. The window and the rest are values the project's design brief
  holds, tuned on the device and recorded there.

| Platform | The throw's speed comes from |
| --- | --- |
| Web | The recent `pointermove` events' positions and `timeStamp`s (with `getCoalescedEvents()` where the browser has it), kept for the brief's window |
| iOS | The platform's velocity: `UIPanGestureRecognizer`'s `velocity(in:)` |
| Android | The platform's velocity: `VelocityTracker`'s `computeCurrentVelocity` |
| Embedded (ESP-IDF, LVGL) | The times of the reads that reported a new position (`lv_tick_get()`), never per read — a touch controller can repeat its last point on the reads between its reports, which reads as a finger stopping; whether yours does is measured on the device |

- **Going, the object leaves from where the finger left it at the throw's speed; a settle from part way takes the time
  the distance left needs** (`MOTION §6`, `MOTION §3`).
- **Past a limit, the object follows with growing resistance and springs back** — never a dead stop (Apple HIG, scroll
  views).
- **What cancels on touch**: the system taking the touch — a call, the notification shade or Control Center — and on
  the web `pointercancel`; the object returns to rest and nothing commits (the `accessibility` skill's act-on-release
  floor; MDN, `pointercancel`).
- **One press has one outcome** — a tap acts on release; a long press acts instead of the tap, never as well.
- **A second finger is part of the gesture only when the gesture uses it** — pinch and rotate take it; a one-finger
  drag either ignores it or cancels, by the spec (§8).

**Embedded (ESP-IDF, LVGL)** (LVGL, `lv_event.h`, `lv_indev.c`, `lv_conf.h`):

- **Which event acts**: `LV_EVENT_PRESSED` fires on touch-down. On lift, `LV_EVENT_RELEASED` always fires;
  `LV_EVENT_CLICKED` fires only if the press did not scroll — and also after a long press; `LV_EVENT_SHORT_CLICKED`
  fires only when no long press was sent. A tap acts on `LV_EVENT_CLICKED`, or on `LV_EVENT_SHORT_CLICKED` when the
  object also has a long press. `LV_EVENT_PRESSED` only starts feedback or a drag, which then ends on
  `LV_EVENT_RELEASED` and `LV_EVENT_PRESS_LOST`.
- **A swipe that can be refused is a drag** — `LV_EVENT_GESTURE` commits during the press, once the move passes the
  gesture limit (§2), so a pull-back cannot refuse it; build it on `LV_EVENT_PRESSING` and decide on
  `LV_EVENT_RELEASED` by distance and the last reads' speed.
- **The throw**: LVGL measures a fling's speed in pixels per read and takes `LV_INDEV_DEF_SCROLL_THROW` (10 % by
  default, `lv_indev_set_scroll_throw`) off it on every animation step, so a change of `LV_DEF_REFR_PERIOD` changes
  how far a fling travels — re-derive the throw from the period, never tune it by eye at another.
- **Resistance past the end** is `LV_OBJ_FLAG_SCROLL_ELASTIC`, on by default: past the end the content follows more
  slowly — by `LV_INDEV_DEF_SCROLL_ELASTIC_FACTOR`, 4 by default, in LVGL 9.6 — and springs back.
- **What cancels**: when a scroll begins, LVGL takes `LV_STATE_PRESSED` off the pressed object and sends it no
  `LV_EVENT_CLICKED`. When the product takes the screen mid-press — an alert, a screen change, sleep —
  `lv_indev_reset` ends the press with `LV_EVENT_INDEV_RESET` and no click, and `lv_indev_wait_release` makes the rest
  of it do nothing; a custom drag treats `LV_EVENT_INDEV_RESET` and `LV_EVENT_PRESS_LOST` as a cancel and returns to
  rest.

## 4. Gesture patterns

**Prefer the platform's control for each pattern; each has a behaviour people already know, and each takes the
`accessibility` skill's plain alternative.**

| Pattern | Behaves | Platform control |
| --- | --- | --- |
| Sheet | Opens to its detents; drags closed from its top or handle; hands off with its list (§2); back closes it | iOS sheet presentation with detents; Material `ModalBottomSheet`; web `<dialog>` |
| Swipe actions on a row | Reveals actions along one axis; a full swipe may commit the first | iOS `swipeActions`; Android `SwipeToDismissBox` |
| Long press | The platform's timeout; tolerates small movement; the tap does the common thing at once, the hold reveals more | iOS context menus; Android long-click |
| Hold to confirm | Fills at a constant rate, drains fast on early release | — |
| Reorder | Starts from a handle or a hold, never from scrolling the list; scrolls near the edge; opens a gap where the item will land | iOS drag and drop in lists; Compose and RecyclerView item touch helpers |
| Pull to refresh | Only where content really refreshes, only from the top | iOS `refreshControl`; Material `PullToRefreshBox`; the browser's own on a document |
| Pinch and rotate | Centred on the fingers; settles to a sensible scale | iOS and Android scale gesture detectors |

- **Embedded (ESP-IDF, LVGL) — the controls**: pages side by side — `lv_tileview` (it scrolls one tile per fling
  with `LV_OBJ_FLAG_SCROLL_ONE`); a value set by dragging — `lv_slider`, `lv_arc`, `lv_roller`; a modal —
  `lv_msgbox`. A long press is `LV_EVENT_LONG_PRESSED` after `LV_INDEV_DEF_LONG_PRESS_TIME` (400 ms by default,
  `lv_indev_set_long_press_time`), never sent once the press has scrolled; a held stepper repeats on
  `LV_EVENT_LONG_PRESSED_REPEAT` every `LV_INDEV_DEF_LONG_PRESS_REP_TIME` (100 ms,
  `lv_indev_set_long_press_repeat_time`).
  LVGL has no sheet, swipe actions, reorder or pull to refresh — each is custom and has a spec (§8). Pinch and rotate
  need `LV_USE_GESTURE_RECOGNITION` and a controller that reports two points (`CONFIG_ESP_LCD_TOUCH_MAX_POINTS` above
  1).
- **Custom swipes start away from the system's edges** (the `accessibility` skill's floor) — Android's gesture
  exclusions (`setSystemGestureExclusionRects`) and iOS's deferred system edges
  (`preferredScreenEdgesDeferringSystemGestures`) stay small and rare, for full-screen games and drawing (Android,
  gesture navigation; Apple HIG, Gestures).
- **Embedded (ESP-IDF, LVGL) — the bezel's edges**: a device has no system edges unless the product defines them,
  and the product's own edge swipes take their place. The bezel hides the panel's outermost pixels, and a finger that
  lands at the edge is first reported a few pixels in, so an edge swipe starts from a band whose width is measured on
  the device and kept in DESIGN.md.
- **A scroll is never an edge gesture** — near an edge, a drag over content that scrolls stays a scroll unless it is
  fast: a slow drag goes back to scrolling, and only a fast flick is the swipe. Swipes and slow drags look alike for
  their first few millimetres, so the decision waits until they separate, a distance the design brief sets.
  **Embedded (ESP-IDF, LVGL)**: LVGL sends no `LV_EVENT_GESTURE` once a scroller has taken the press (§2); a product
  edge swipe that holds a direction in its band hands a slow drag back to the scroller, measuring speed between
  position reports (§3).
- **A surface that has just opened is dragged only by its handle for a moment** — a finger already moving as it
  arrives taps or scrolls the content instead of grabbing the surface; the handle, the way out, is never held back.
  The moment is a value the project's design brief holds, tuned on the device and recorded there, and outlasts the
  surface's entrance.
- **Decorative elements never take presses** — a caption, an icon, a divider or a handle's pill passes the press to
  what lies beneath it, so it never swallows a tap or a drag meant for the page.
  - **Web**: `pointer-events: none`.
  - **iOS**: `isUserInteractionEnabled = false`.
  - **Android**: not clickable and not focusable — `android:clickable="false"`, `android:focusable="false"`; in
    Compose, no `clickable` modifier.
  - **Embedded (ESP-IDF, LVGL)**: remove `LV_OBJ_FLAG_CLICKABLE` (`lv_obj_remove_flag`) — `lv_obj_create` makes
    every object clickable; LVGL's label, image, line and spinner are not.
- **Swipe directions mirror for right-to-left languages**, as navigation does.
- **The `accessibility` skill's keyboard and screen-reader floors, on touch platforms**: a reordered item moves with
  the arrow keys; each gesture's action is a named action — iOS `accessibilityCustomActions`, Android
  `AccessibilityAction`, visible controls on the web, and on a device a control the encoder and buttons reach (§11).

## 5. Touch feedback

**On touch, the pressed state is drawn at once and kept honest; acting on release is the `accessibility` skill's
floor.**

- **Rows inside a scrolling list wait a moment before showing pressed**, so a fast scroll never flashes them —
  Android's tap timeout, iOS's `delaysContentTouches`; on the web, a short delay before the pressed style on rows in a
  scroller.
- **Keep or replace the platform's touch feedback, never just remove it** — Android's ripple and state layers; on the
  web, remove the browser's tap highlight (`-webkit-tap-highlight-color`) only alongside your own pressed style
  (`:active`) (Material Design 3, States).
- **Hover never sticks after a tap** — a device with both touch and a mouse shows hover only to the mouse.
  **Web**: gate hover with `any-hover` and `any-pointer`; a laptop with a touch screen has both.
- **Menus open on a tap and dismiss on a tap outside**, not on press-down, so starting a scroll on a trigger opens
  nothing.
- **Control labels cannot be selected by a long press; content text always can** — turn selection off on the control,
  never on the page.
- **Haptics, sound and status lights are `FEEDBACK`'s** — which event gets which feel, when it fires, what to avoid,
  and how a press, a wait and an outcome are answered (`FEEDBACK §2`, `FEEDBACK §3`, `FEEDBACK §5`); this section
  keeps the pressed look.
- **A clear, reveal or stepper button inside a field acts without taking focus from it**, so the keyboard stays open.

**Embedded (ESP-IDF, LVGL)** (LVGL, `lv_indev_scroll.c`, `lv_theme_default.c`, `lv_style.h`):

- **The pressed state is a style on `LV_STATE_PRESSED`.** LVGL's default theme gives `lv_button` one, and
  `lv_obj_remove_style_all` removes it with the rest; a plain `lv_obj` made clickable never had one. Every tappable
  object draws one, from a DESIGN.md token.
- **The pressed delay in a scrolling list**: LVGL sets `LV_STATE_PRESSED` at touch-down and takes it off when a scroll
  begins, with no delay of its own. Give a row's pressed style a short transition delay (the `delay` of
  `lv_style_transition_dsc_init`), so a scroll that starts within it draws no flash; judge the delay on the device.
- **Hover**: a touch panel has none; `LV_EVENT_HOVER_OVER` comes only from a pointer such as a mouse.

## 6. Scroll-linked motion

**Scroll motion is either triggered by crossing a point, or driven by scroll position — and never takes scrolling
over.**

- **Triggered**: starts as an element arrives, runs on its own time, plays once; content is fully there if the script
  never runs. In product screens, keep it to content below the first view, and never make a person wait for content
  to appear.
- **Driven**: tied to scroll position — no duration, no easing, reverses with the scroll, stops when scrolling stops.
  On the web, scroll-driven animations behind a feature check (`@supports (animation-timeline: scroll())`), with the
  page complete without them (MDN, scroll-driven animations).
- **Never take over scrolling** — no rewritten distances, no one-flick-one-section, no home-made momentum; use the
  platform's scrolling and snapping (MDN, scroll snap). Taken-over scrolling also breaks the keyboard's scrolling keys.
- **Parallax and other decorative scroll motion follow the `motion` and `accessibility` skills** on reduced motion,
  and are skipped where they cost frames on phones and devices.
- **Embedded (ESP-IDF, LVGL) — driven effects**: `LV_EVENT_SCROLL` fires on every scroll step, through the drag and
  the throw, and its handler runs inside the frame. It sets a few style values (`translate`, `opa`) on the few objects
  in view and redraws only what changes — LVGL's circular-list example (`lv_example_scroll_translate.c`) is the
  pattern. What a frame can afford on the panel and its bus is the `motion` skill's.
- **Embedded (ESP-IDF, LVGL) — never taking over**: keep `LV_OBJ_FLAG_SCROLL_MOMENTUM` and
  `LV_OBJ_FLAG_SCROLL_ELASTIC`, on by default. Paging and snapping come from `lv_obj_set_scroll_snap_x`,
  `lv_obj_set_scroll_snap_y`, `LV_OBJ_FLAG_SCROLL_ONE` and `lv_tileview`, and the throw's feel from
  `lv_indev_set_scroll_throw` (§3) — never a hand-written momentum.

## 7. Mobile layout

**Lay out in the visible area, clear of the system's areas and the on-screen keyboard.**

On a device's panel the same rules hold with the device's own edges: the visible area is the panel's shape, the safe
areas are its corners and the band the bezel hides, and there is no on-screen keyboard, browser bar or system back
unless the product draws one.

| Concern | Rule | Web | iOS | Android | Embedded (ESP-IDF, LVGL) |
| --- | --- | --- | --- | --- | --- |
| The visible area | Full-height layouts follow what is visible, so a bottom action is never under the browser's bar | `dvh`/`svh` after a `100vh` fallback | Safe-area layout guides | Window insets | The panel's resolution; on a round panel, the circle inside it — the framebuffer's corners are never seen or touched |
| Safe areas | Paint to the edges; keep content clear of the notch, the corners and the home or gesture bar, in every orientation | `viewport-fit=cover` with `env(safe-area-inset-*)` | Safe-area guides | Edge-to-edge with insets | Clear of round or cut corners and the band the bezel hides, an inset kept in DESIGN.md and measured on the device |
| The keyboard | Never covers the focused field or the primary action; a fixed bottom action never covers the last field | The visual viewport; the viewport's `interactive-widget` | The keyboard layout guide | The IME inset | None unless the product draws `lv_keyboard`; then it never covers the `lv_textarea` it types into (`lv_keyboard_set_textarea`) |
| Keyboard on its own | A text field never takes focus unasked on touch, so the keyboard opens only on a tap; a dialog's first focus goes to the dialog or a button, never a text field | Autofocus a text field only with a fine pointer | Focus a field on a tap | Focus a field on a tap | Show the keyboard on a tap or a press on the field, never when encoder focus only passes over it |
| Field text | Large enough that the browser does not zoom on focus | 16 px on iOS Safari | — | — | — |
| Field keyboards | Each field asks for the right keyboard, return key and autofill | `type`, `inputmode`, `enterkeyhint`, `autocomplete` | `keyboardType`, `textContentType` | `inputType`, IME action, autofill hints | `lv_keyboard_set_mode` — `LV_KEYBOARD_MODE_NUMBER` for a number |
| Inner scrolling | An inner scroll area keeps its scroll; the page behind a modal does not scroll | `overscroll-behavior: contain`; a modal `<dialog>` | Modal presentation | Nested scrolling | A modal on `lv_layer_top()` over a clickable backdrop that covers the screen, so no press reaches the screen behind — `lv_msgbox_create(NULL)` builds one |

- **Back closes the topmost overlay first, one layer at a time** — Android back and predictive back; on the web, a
  modal `<dialog>` or a `popover` closes on Escape and on Android's back through the browser's close watchers; where
  an overlay uses history, it replaces its entry rather than stacking one per open, so back never traps (Android,
  predictive back; MDN, `<dialog>`, Popover API).
- **Embedded (ESP-IDF, LVGL) — back**: back is what the product defines — a key, a button, an edge swipe — one path
  on every screen, closing the topmost layer first; an encoder's or keypad's `LV_KEY_ESC` reaches the focused object as
  `LV_EVENT_CANCEL` (§11).
- **Bottom navigation**: which width takes a bottom bar, a rail or a side list is the `layout` skill's; on a bar, a
  few destinations, each icon with a label; switching is instant and keeps each tab's scroll
  and state; tapping the active tab returns to its top (Apple HIG, Tab bars; Material Design 3, Navigation bar).
  **Embedded (ESP-IDF, LVGL)**: pages side by side in an `lv_tileview` keep each page's scroll.

## 8. The gesture spec

**Before a gesture is built, a short spec settles how it behaves, and a prototype on the device settles how it feels.**

| Field | Settles |
| --- | --- |
| The gesture and its object | What the finger moves, and what it changes |
| Platform control | The platform's control for this pattern, or why a custom one |
| Axis and claim | Which axis it locks to; what it leaves to scrolling; how it hands off with a parent or child scroll |
| Start | The tolerance (the platform's); the edges it avoids |
| Release | The distance and the speed that commit; what refuses a throw; how it settles (the `motion` skill) |
| Limits | Resistance past the ends; snap points or detents |
| Interruption and cancel | Caught mid-animation; what cancels on touch; what a second finger does |
| Derived values | What else follows the drag position |
| Every input | The tap alternative and the screen-reader action (the `accessibility` skill); keyboard; mouse and pen; on a device, the encoder and buttons |
| Encoder and buttons | What a turn does in navigate and in edit mode, what a press and a long press do, how back works (§11) |
| Direction | Mirrored for right-to-left, or not, and why |
| Discoverability | How a person learns the gesture exists — the visible control is the first answer |
| Reduced motion | The drag still tracks; what the settle becomes |
| Haptics and lights | Which moments, if any, from the vocabulary in `FEEDBACK §2`, and their fallback |
| Input settings | **Embedded (ESP-IDF, LVGL)**: the read period, scroll limit, scroll throw, long-press time and gesture limit it relies on, each from DESIGN.md |

- **A video approves timing; only a prototype on the device approves feel** — a drag is judged under the finger, on
  the target's screen and refresh rate.
- **The spec sits beside the mock and the motion brief**, so the build has every value it needs.

## 9. The device walk

**Trackpads and emulators misreport touch; these are judged on real phones, with the person.**

**Web, iOS and Android**: walk on at least one iOS and one Android phone — the browsers people use there for web —
including a small screen and a lower-end device for frame rate.

**Embedded (ESP-IDF, LVGL)**: walk on the product's own hardware — its panel, touch controller, cover glass, bezel,
encoder and buttons — with the firmware's shipping configuration, since a debug build's optimisation and log level
change the frame rate.

| Walk | Passes when |
| --- | --- |
| Follow and release | The object stays under the finger every frame; hard and soft throws land differently; a refused throw returns quickly; on a device, a fast drag moves every frame without stepping |
| Claim and share | A vertical scroll on a swipeable row scrolls the page; a sideways carousel never scrolls the page |
| Sheets | A slow drag scrolls the list to its top and then moves the sheet; a fling that reaches the top leaves the sheet where it is; back closes it |
| Interruption | Pulling the notification shade or Control Center, or an incoming call, mid-drag leaves the object at rest; on a device, an alert or a screen change mid-drag does the same |
| Edges | Swiping in from each edge does what the system does, not what the app does; on a device, a swipe from each bezel edge starts where the spec says |
| Encoder and buttons | **Embedded (ESP-IDF, LVGL)**: each gesture's task is done by turn, press and long press alone; one detent moves one step; a press and a long press do what the spec says, the same on every screen; a quick press is never lost (§11) |
| Feedback | Fast scrolling flashes no row; after a tap nothing stays highlighted; long-pressing a button selects no text |
| Layout | The bottom action is visible before scrolling; safe areas clear in portrait and both landscapes; the last field and the action sit above the keyboard |
| Every input | Each gesture's task is done by taps alone, from the screen reader's actions (VoiceOver, TalkBack), and from a hardware keyboard |
| Text size | The largest text setting keeps every gesture's target and alternative usable |
| Reach | The primary actions are reachable one-handed |
| Reduced motion | The drag still tracks; the settle becomes a fade or a jump |

## 10. Reviewing a gesture change

**A review reads each gesture against its spec and §1–§7, ranks the `accessibility` skill's floors first, and hands
the feel to the person.**

| Asks | Against |
| --- | --- |
| Is there a spec, and a prototype the person approved? | §8 |
| Is it the platform's control, or is the custom one justified? | §4 |
| Does it claim only its axis, and hand off with scrolling correctly? | §2 |
| Does release decide by distance or speed, and do cancels commit nothing? | §3 |
| Are the system's edges left alone? | §4 |
| Is touch feedback kept, and pressed delayed in scrolling lists? | §5 |
| Is scrolling never taken over? | §6 |
| Is the layout clear of safe areas and the keyboard? | §7 |
| Does a press have one outcome — a tap on release, a long press instead of it? | §3 |
| Does every gesture's task work by the encoder and buttons, where the device has them? | §11 |
| **Embedded (ESP-IDF, LVGL)**: are the read period, scroll limit, throw and long-press time from DESIGN.md? | §1–§3 |

- **Report what needs a device** — the walks in §9 for each changed gesture and screen; never claim one passed from
  code.

---

## 11. Encoder and buttons

**An encoder and buttons are an equal input beside touch: each gesture's task is done by turning, pressing and
long-pressing, with the outcome a tap gives.**

The focus model these inputs drive is the `accessibility` skill's: what each input's job is, how edit mode is entered
and left, and how LVGL registers the encoder and buttons (`FOCUS §2`); keeping focus in view and the ring
(`FOCUS §6`, `FOCUS §7`); who takes an input when several could (`FOCUS §10`); the floors (`ACCESSIBILITY §5`). This
section says only how the press and the long press line up with a tap, and how LVGL decides them.

- **A press acts on the focused object, on release** — the same outcome a tap gives it, never a different one.
- **A long press does one documented thing, or nothing** — the long press's outcome on touch (§4), or the product's
  back; it never also does what the press does (§3).
- **A press shorter than one read still counts** — a press and its release that both land between two reads are
  latched by the driver until a read has reported them.

| Concern | Embedded (ESP-IDF, LVGL) |
| --- | --- |
| Press | On an object that is neither editable nor scrollable: `LV_EVENT_PRESSED` on press; on release `LV_EVENT_RELEASED`, `LV_EVENT_SHORT_CLICKED` (unless long-pressed) and `LV_EVENT_CLICKED` — the handlers a tap reaches, so §3's rule holds for both. On an editable widget or a scrollable container, the press serves edit mode instead (`FOCUS §2`) |
| Long press | After the long-press time (§4): on an editable or scrollable object it serves edit mode (`FOCUS §2`), and that object's own `LV_EVENT_LONG_PRESSED` is not sent; on any other object it sends `LV_EVENT_LONG_PRESSED` |
| Back | `LV_KEY_ESC`, from an encoder device or a keypad, reaches the focused object as `LV_EVENT_CANCEL` |
| Reads | LVGL reads a level at each read period (§1), not an event, which is why the driver latches a short press |

- **A long press on a slider or a scrollable list serves edit mode** (`FOCUS §2`), so a long-press action on one
  never fires from the encoder; give that action another path in the spec (§8).
- **Steps: the gesture spec's Encoder and buttons field (§8) and the walk (§9).**
