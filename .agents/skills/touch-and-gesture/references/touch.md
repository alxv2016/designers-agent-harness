# Touch

How touch input, gestures, scroll-linked motion and mobile layout are built so they feel direct and never fight the
platform: how a gesture starts, claims its axis, shares with scrolling and decides on release; how the common gesture
patterns behave; how touch feedback, scroll effects and mobile layout work on the web, iOS and Android; and how a
gesture is specified, prototyped and walked on a device. People read it to decide how a touch interaction should
behave; coding agents read it, through the `touch-and-gesture` skill, before they spec, build or review one.

**Where it lives.** In the `touch-and-gesture` skill, beside the steps and checks that apply it —
[its SKILL.md](../SKILL.md). The skill folder is self-contained: copy it into any repo's `.agents/skills/` and this
reference and the touch check come with it. The product's own values — its target size, its spring, its hold length,
which gestures it uses — live in its design brief (`DESIGN.md` in the agent-harness kit).

**What it builds on.** The floors for input are the `accessibility` skill's: a target size, a plain alternative to
every gesture, drag, long press and hover, acting on release, hover never the only path, both orientations, time
limits, reduced motion. How a move eases, settles and survives interruption — including keeping a dragged object under
the finger with no easing — is the `motion` skill's. This doc does not restate them; it says how each is built on
touch.

**Stability.** Cite this doc as `TOUCH §n`. Do not renumber; add new material under the next free number.

| § | Section | Look here for |
| --- | --- | --- |
| 1 | [Direct manipulation](#1-direct-manipulation) | What follows the drag, catching a moving object, the platform tools |
| 2 | [Starting and claiming a gesture](#2-starting-and-claiming-a-gesture) | Movement tolerance, axis lock, sharing with scrolling, the sheet hand-off |
| 3 | [Deciding on release](#3-deciding-on-release) | Distance or speed, refusing a throw, resistance past a limit, what cancels on touch |
| 4 | [Gesture patterns](#4-gesture-patterns) | Sheets, swipe actions, long press, hold, reorder, pull to refresh, pinch, screen edges |
| 5 | [Touch feedback](#5-touch-feedback) | The pressed state on touch, delays in scrolling lists, tap highlight, menus, selection, haptics |
| 6 | [Scroll-linked motion](#6-scroll-linked-motion) | Triggered against driven, never taking over scrolling |
| 7 | [Mobile layout](#7-mobile-layout) | The visible area, safe areas, the keyboard, field keyboards, back, bottom navigation |
| 8 | [The gesture spec](#8-the-gesture-spec) | What to settle before building a gesture, and how to prototype it |
| 9 | [The device walk](#9-the-device-walk) | What only a real device shows, and how to check it |
| 10 | [Reviewing a gesture change](#10-reviewing-a-gesture-change) | What a review checks, and what it hands to the person |

---

## 1. Direct manipulation

**Everything that reacts to a drag derives from the one drag position, and anything a gesture can touch can be caught
mid-animation.**

- **One position drives everything** — the scrim's opacity, the page behind, the handle, the sheet's corner radius;
  separate animations drift apart when the drag reverses.
- **Catching a moving object stops it under the finger with no jump** — the release animation is interruptible, so a
  second touch picks it up where it is (the `motion` skill, interruption).
- **Platform tools**: iOS — a pan gesture recognizer's translation and velocity, interruptible animators or SwiftUI
  springs; Android — `VelocityTracker`, Compose `draggable` and `AnchoredDraggableState`; web — pointer events with
  `setPointerCapture`, so the drag keeps its pointer when the finger leaves the element (Apple, "Designing Fluid
  Interfaces", WWDC 2018; MDN, Pointer events).

## 2. Starting and claiming a gesture

**A press becomes a drag only past the platform's movement tolerance, then locks to one axis and claims only that
axis.**

- **Use the platform's tolerance** — Android's touch slop (`ViewConfiguration.getScaledTouchSlop`); iOS recognizers
  apply theirs; on the web it is yours to set, larger for touch than for a mouse.
- **Lock to one axis once the gesture starts**, measured from where it crossed the tolerance, so a vertical scroll
  that starts on a swipeable row scrolls the page and leaves the row alone.
- **Claim only the axes you use** — web: `touch-action` names what the browser keeps (`pan-y` on a horizontal
  carousel, `manipulation` on a control that only taps, which also drops the double-tap zoom wait; `none` only on a
  handle, a slider thumb, a canvas or a map whose every gesture is the app's); iOS: recognizer failure requirements;
  Android: nested scrolling, intercepting only once the gesture is yours (MDN, `touch-action`).
- **A sheet with scrolling content hands off within the same finger** — while the list is not at its top, a downward
  drag scrolls it; once it reaches the top, the same drag moves the sheet. At a lower detent, an upward drag expands
  the sheet before its list scrolls. The leftover momentum of a fling that reaches the top never moves or closes the
  sheet (Apple HIG, Sheets; Material Design 3, Bottom sheets; Android,
  nested scrolling).
- **A custom pull to refresh or overscroll effect contains the browser's own** — `overscroll-behavior-y: contain` on
  that scroller, so the page behind does not also refresh or bounce.

## 3. Deciding on release

**On lift, commit when moved far enough or thrown fast enough in an allowed direction; otherwise go back.**

- **Distance or speed** — distance alone ignores a flick; a speed threshold holds only for the velocity measure it was
  tuned with (Material Design 3, Gestures; Compose `AnchoredDraggableState` takes both).
- **A pull back from the furthest point, or a finger resting before lift, refuses the throw**, and a refused gesture
  returns quickly; how it settles is the `motion` skill's.
- **Past a limit, the object follows with growing resistance and springs back** — never a dead stop (Apple HIG, scroll
  views).
- **What cancels on touch**: the system taking the touch — a call, the notification shade or Control Center — and on
  the web `pointercancel`; the object returns to rest and nothing commits (the `accessibility` skill's act-on-release
  floor; MDN, `pointercancel`).
- **A second finger is part of the gesture only when the gesture uses it** — pinch and rotate take it; a one-finger
  drag either ignores it or cancels, by the spec (§8).

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

- **Custom swipes start away from the system's edges** (the `accessibility` skill's floor) — Android's gesture
  exclusions (`setSystemGestureExclusionRects`) and iOS's deferred system edges
  (`preferredScreenEdgesDeferringSystemGestures`) stay small and rare, for full-screen games and drawing (Android,
  gesture navigation; Apple HIG, Gestures).
- **Swipe directions mirror for right-to-left languages**, as navigation does.
- **The `accessibility` skill's keyboard and screen-reader floors, on touch platforms**: a reordered item moves with
  the arrow keys; each gesture's action is a named action — iOS `accessibilityCustomActions`, Android
  `AccessibilityAction`, visible controls on the web.

## 5. Touch feedback

**On touch, the pressed state is drawn at once and kept honest; acting on release is the `accessibility` skill's
floor.**

- **Rows inside a scrolling list wait a moment before showing pressed**, so a fast scroll never flashes them —
  Android's tap timeout, iOS's `delaysContentTouches`; on the web, a short delay before the pressed style on rows in a
  scroller.
- **Keep or replace the platform's touch feedback, never just remove it** — Android's ripple and state layers; on the
  web, remove the browser's tap highlight (`-webkit-tap-highlight-color`) only alongside your own pressed style
  (`:active`) (Material Design 3, States).
- **Gate hover with `any-hover` and `any-pointer` on hybrid devices** — a laptop with a touch screen has both; after a
  tap, nothing stays highlighted.
- **Menus open on a tap and dismiss on a tap outside**, not on press-down, so starting a scroll on a trigger opens
  nothing.
- **Control labels cannot be selected by a long press; content text always can** — turn selection off on the control,
  never on the page.
- **Haptics are rare, short, caused by the person, never the only signal, and follow the system setting** (Apple HIG,
  Playing haptics; Android haptics design principles).
- **A clear, reveal or stepper button inside a field acts without taking focus from it**, so the keyboard stays open.

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
  and are skipped where they cost frames on phones.

## 7. Mobile layout

**Lay out in the visible area, clear of the system's areas and the on-screen keyboard.**

| Concern | Rule | Web | iOS | Android |
| --- | --- | --- | --- | --- |
| The visible area | Full-height layouts follow what is visible, so a bottom action is never under the browser's bar | `dvh`/`svh` after a `100vh` fallback | Safe-area layout guides | Window insets |
| Safe areas | Paint to the edges; keep content clear of the notch, the corners and the home or gesture bar, in every orientation | `viewport-fit=cover` with `env(safe-area-inset-*)` | Safe-area guides | Edge-to-edge with insets |
| The keyboard | Never covers the focused field or the primary action; a fixed bottom action never covers the last field | The visual viewport; the viewport's `interactive-widget` | The keyboard layout guide | The IME inset |
| Keyboard on its own | A text field never takes focus unasked on touch, so the keyboard opens only on a tap; a dialog's first focus goes to the dialog or a button, never a text field | Autofocus a text field only with a fine pointer | Focus a field on a tap | Focus a field on a tap |
| Field text | Large enough that the browser does not zoom on focus | 16 px on iOS Safari | — | — |
| Field keyboards | Each field asks for the right keyboard, return key and autofill | `type`, `inputmode`, `enterkeyhint`, `autocomplete` | `keyboardType`, `textContentType` | `inputType`, IME action, autofill hints |
| Inner scrolling | An inner scroll area keeps its scroll; the page behind a modal does not scroll | `overscroll-behavior: contain`; a modal `<dialog>` | Modal presentation | Nested scrolling |

- **Back closes the topmost overlay first, one layer at a time** — Android back and predictive back; on the web, a
  modal `<dialog>` or a `popover` closes on Escape and on Android's back through the browser's close watchers; where
  an overlay uses history, it replaces its entry rather than stacking one per open, so back never traps (Android,
  predictive back; MDN, `<dialog>`, Popover API).
- **Bottom navigation**: a few destinations, each icon with a label; switching is instant and keeps each tab's scroll
  and state; tapping the active tab returns to its top (Apple HIG, Tab bars; Material Design 3, Navigation bar).

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
| Every input | The tap alternative and the screen-reader action (the `accessibility` skill); keyboard; mouse and pen |
| Direction | Mirrored for right-to-left, or not, and why |
| Discoverability | How a person learns the gesture exists — the visible control is the first answer |
| Reduced motion | The drag still tracks; what the settle becomes |
| Haptics | Which moments, if any, and their fallback |

- **A video approves timing; only a prototype on the device approves feel** — a drag is judged under the finger, on
  the target's screen and refresh rate.
- **The spec sits beside the mock and the motion brief**, so the build has every value it needs.

## 9. The device walk

**Trackpads and emulators misreport touch; these are judged on real phones, with the person.**

Walk on at least one iOS and one Android phone — the browsers people use there for web — including a small screen and a
lower-end device for frame rate.

| Walk | Passes when |
| --- | --- |
| Follow and release | The object stays under the finger every frame; hard and soft throws land differently; a refused throw returns quickly |
| Claim and share | A vertical scroll on a swipeable row scrolls the page; a sideways carousel never scrolls the page |
| Sheets | A slow drag scrolls the list to its top and then moves the sheet; a fling that reaches the top leaves the sheet where it is; back closes it |
| Interruption | Pulling the notification shade or Control Center, or an incoming call, mid-drag leaves the object at rest |
| Edges | Swiping in from each edge does what the system does, not what the app does |
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

- **Report what needs a device** — the walks in §9 for each changed gesture and screen; never claim one passed from
  code.
