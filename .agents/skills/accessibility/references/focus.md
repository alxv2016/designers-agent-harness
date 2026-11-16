# Focus

Where focus is, when it shows, and what moves it — one model for every input a product has: a pointer, a finger, a
keyboard, a rotary encoder, a few buttons. The floors focus must meet are ACCESSIBILITY §5, in this skill's
[criteria.md](criteria.md); this reference is the model that meets them, decided once so every screen gets it. People
read it to design how a product is driven without a pointer; coding agents read it, through the `accessibility`
skill, before they build navigation, an overlay, a list or a control.

**Where it lives.** In the `accessibility` skill, beside the floors in [criteria.md](criteria.md) and the steps in
[its SKILL.md](../SKILL.md). The folder is self-contained and travels with this reference.

**Source of truth.** WCAG 2.2 (2.1.1, 2.1.2, 2.4.3, 2.4.7, 2.4.11, 2.4.13 at AAA, 3.2.1); the WAI-ARIA Authoring
Practices Guide — *Developing a Keyboard Interface* and the *Dialog (Modal) Pattern*; the HTML Standard — the
sequential focus navigation starting point and the `autofocus` attribute; CSS Selectors Level 4 — the
`:focus-visible` pseudo-class, whose heuristics each browser applies. A standard wins over this reference where they
differ; a project's design brief may go further, never below.

**Stability.** Cite this doc as `FOCUS §n`. Do not renumber; add new material under the next free number.

**Platforms.** Each rule is stated once for every platform. How to meet it on one platform is labelled **Web**,
**iOS**, **Android** or **Embedded (ESP-IDF, LVGL)**. Embedded guidance is for any ESP-IDF device with an LVGL
screen: a small panel, touch and/or a rotary encoder or buttons, no screen reader and no system settings.

| § | Section | Look here for |
| --- | --- | --- |
| 1 | [The focus model](#1-the-focus-model) | The focus position and the ring as two things; the words used here; the states a control can be in at once |
| 2 | [Inputs and what each does](#2-inputs-and-what-each-does) | The keyboard, the encoder, buttons and touch mapped to one another; one job per input; wrapping; the first press with no ring |
| 3 | [When the ring shows](#3-when-the-ring-shows) | Focus-visible: a tap shows no ring, a keyboard or encoder does; code that moves focus |
| 4 | [Where the next step starts](#4-where-the-next-step-starts) | The starting point after a tap, a scroll or an arrival; what a drag does to the ring |
| 5 | [Opening and closing screens and overlays](#5-opening-and-closing-screens-and-overlays) | No ring on arrival; focus into a modal; autofocus; focus placed for the next press; Escape and back one level; focus back to the opener, and when the opener is gone |
| 6 | [Keeping focus in view](#6-keeping-focus-in-view) | Scrolling to focus for inputs that cannot see; the margin and pinned bars; touch scrolls nothing |
| 7 | [The focus ring](#7-the-focus-ring) | Outline not border, room in containers and between siblings, focus against selection and edit mode, appearance |
| 8 | [What takes focus](#8-what-takes-focus) | Controls only; readings and headings; disabled and hidden; handing focus on before a control goes; state changes |
| 9 | [Messages and focus](#9-messages-and-focus) | A toast takes no focus; a message that needs an answer is a dialog |
| 10 | [Who takes an input](#10-who-takes-an-input) | The order of owners, from the top overlay to the page |
| 11 | [Building it once](#11-building-it-once) | One press handler, one overlay stack, one focus policy, one way to hide a focused control |
| 12 | [Traps](#12-traps) | Symptoms that mislead, their causes and fixes |

---

## 1. The focus model

**Each screen has one focus position, shared by every input, and one ring that shows it — the position and the ring
are separate, and hiding the ring keeps the position.** A finger moves the position; a keyboard, encoder or keys carry
on from it; the ring appears for the inputs that cannot see what they steer (§3).

- **Hiding the ring is not losing the place.** After a tap on the background the ring goes, and the next Tab or
  detent carries on from there rather than from the top of the screen (§4).
- **One position for every input.** If touch and the encoder each kept their own, turning the knob after a tap would
  move a ring from somewhere else entirely.
- **Focus alone never acts** — only an activation does (WCAG 3.2.1). A ring passing over a control changes nothing.

| Term | Means |
| --- | --- |
| Focus position | The control the next activation key acts on and the next step moves from, whether or not a ring shows |
| Ring | The focus indicator drawn on the focused control |
| Stop | A control the focus order reaches |
| Step | One move of focus: a Tab, an arrow, an encoder detent, a next or previous button |
| Starting point | Where the next step starts when no ring shows (§4) |
| Edit mode | A focused value control taking the step input to change its value instead of moving focus |
| Overlay | Anything over the screen that takes input while it is up: a dialog, a sheet, a menu, a dropdown's list |
| Reading | Text that shows a value or describes; never a stop (§8) |

- **Seven states, each its own**: focused, ringed, selected, pressed, editing, disabled and visible. Any of them can be
  true with any other — a control focused with no ring after a tap, a selected item not focused, a slider in edit
  mode still focused — so none is drawn as the look of another (§7).
- **Web:** the position is `document.activeElement`; the ring is the `:focus-visible` style.
- **Android:** after a touch the device is in touch mode, where views take no focus unless `focusableInTouchMode`
  and no focus highlight shows; a key or D-pad press leaves touch mode and shows focus.
- **iOS:** focus and its ring exist while a hardware keyboard drives the interface (Full Keyboard Access on iPhone,
  keyboard navigation on iPad); touch shows none.
- **Embedded (ESP-IDF, LVGL):** the position is the group's focused object (`lv_group_get_focused`); the ring is the
  style on its `LV_STATE_FOCUSED` and `LV_STATE_FOCUS_KEY`. Sending `LV_EVENT_DEFOCUSED` to it removes `FOCUSED`,
  `FOCUS_KEY` and `EDITED` and leaves the group's position where it was. `lv_group_focus_obj` on the object the group
  already focuses returns without sending anything, so give a hidden ring back by sending `LV_EVENT_FOCUSED`;
  `lv_group_focus_obj(NULL)` is refused.

## 2. Inputs and what each does

**Each input has one job, the same on every screen; the keyboard is the model the others map onto.**

| Job | Keyboard | Encoder or buttons (Embedded) | iOS and Android |
| --- | --- | --- | --- |
| Move focus one stop | Tab, Shift+Tab | One detent clockwise or anticlockwise; the next or previous button | Tab on a hardware keyboard; Android: the D-pad and arrow keys |
| Activate what is focused | Enter, Space | The select key — the encoder's press, or the enter button | Enter, Space; Android: the D-pad's centre |
| Close the top overlay, one level | Escape | A back or menu key | Android: Back; iOS: the VoiceOver escape gesture (a two-finger scrub) |
| Change a value inside one stop | Arrows inside a composite | Detents while the control is in edit mode | Arrows; Android: the D-pad |
| Act on what is under the pointer | A click | A tap | A tap |

- **One job per input, the same everywhere.** A key that selects on one screen and closes on another makes the person
  guess, and each new screen decides it again.
- **One physical press is one activation**, and a held key does what a press does, once — unless the hold is a
  documented repeat, adjustable as ACCESSIBILITY §14 asks.
- **The step input moves focus and the view follows (§6); it never scrolls content on its own.** A knob that scrolled
  would need a second mode to choose anything, and the ring would be left behind the content.
- **Embedded: the focus order wraps at both ends.** A one-axis knob turned past the last stop reaches the first;
  stopping at an end would mean turning all the way back. LVGL groups wrap by default (`lv_group_set_wrap`). **Web:**
  Tab does not wrap within a page — it moves on to the browser — except inside a modal, where it wraps (§5).
- **Embedded: an activation key never acts on something the person cannot see is focused.** With no ring showing, the
  first press shows the ring — on the focused control when it is in view, else on the starting point (§4) — and does
  nothing else; the next press acts. A press with no visible target is a press nobody aimed.
- **Embedded (ESP-IDF, LVGL):** `esp_lvgl_port` registers a rotary encoder (`lvgl_port_add_encoder`) and three
  navigation buttons (`lvgl_port_add_navigation_buttons`) as `LV_INDEV_TYPE_ENCODER`; a keypad is
  `LV_INDEV_TYPE_KEYPAD` (`LV_KEY_NEXT`, `LV_KEY_PREV`, `LV_KEY_ENTER`, `LV_KEY_ESC`). A back key that closes overlays
  is handled before LVGL sees it, so one press never both closes an overlay and clicks the focused control (§10).
- **Embedded (ESP-IDF, LVGL): how the encoder enters and leaves edit mode** — this section is the one place that
  says it. A short press on a plain control clicks it; on an editable one (a slider, arc, roller, dropdown) the release
  enters edit mode for the group (`lv_group_set_editing`, shown as `LV_STATE_EDITED`). A short press leaves edit mode
  only where the widget's own handler does so: the slider, arc and roller leave on the release, and the dropdown when
  an option is chosen. A long press — held past `lv_indev_set_long_press_time` — toggles edit mode for the group, in
  or out, when the group holds more than one object. So every editable control can be left by the encoder alone
  (WCAG 2.1.2), and a custom editable widget leaves edit mode on its own release the same way.

## 3. When the ring shows

**The ring shows when focus was moved by an input that cannot see what it steers — a keyboard, an encoder, keys — or
by code acting for one; a tap or a click moves focus with no ring.** WCAG 2.4.7 asks for a mode in which the focus
indicator is visible; a ring under every tap is noise under the finger, which can see what it touched.

- **A text field awaiting typing shows that it has focus however it was reached** — the caret and the field's focused
  look — because the person has to know where the typing goes.
- **Code that moves focus follows the input that caused it**: after a key or a detent, the ring shows; after a tap,
  it does not.
- **A ring once hidden stays hidden until the next step or activation key** — never brought back by a timer or a state
  change.
- **Web:** style the ring on `:focus-visible`, never on `:focus`. Browsers' heuristics show it after keyboard focus
  and in a text field, and not after a pointer click on a button.
- **Android:** touch mode gives this behaviour (§1). **iOS:** the keyboard's focus ring appears only while a hardware
  keyboard drives focus.
- **Embedded (ESP-IDF, LVGL):** LVGL adds `LV_STATE_FOCUS_KEY` beside `LV_STATE_FOCUSED` only when the input that
  focused the object is a keypad or encoder — its own focus-visible. Focus set by code (`lv_group_focus_obj`) takes the
  input LVGL finds for the group, a pointer when the device has one, so on a touch device code-set focus carries no
  `FOCUS_KEY`. Two ways to meet the rule:

| Approach | Does | Costs |
| --- | --- | --- |
| The ring on `LV_STATE_FOCUS_KEY` alone | A tap focuses with no ring and nothing else is needed | A ring given back by code — an overlay closing under a back key handled outside LVGL — can fail to draw: it gets `FOCUS_KEY` only when the input LVGL finds for the event is an encoder or keypad, and `lv_group_focus_obj` passes a pointer device when there is one |
| The ring on `LV_STATE_FOCUSED` and `LV_STATE_FOCUS_KEY`, taken off after a tap | Every way of focusing draws the same ring; the product removes it after a tap by sending `LV_EVENT_DEFOCUSED` to the tapped control | LVGL focuses a tapped control while it processes the press, so the ring can show for a frame when it is removed later than that — at the next touch read, or from a timer that runs after a redraw. Unverified per panel: settled by filming taps on the device |

## 4. Where the next step starts

**With no ring showing, the next step starts from where the person last was — the control or the point they tapped —
else from what is in view; never from a place the view has scrolled away from.** This is the HTML Standard's
sequential focus navigation starting point: a click on the page's content sets where the next Tab starts.

| Starting point | Next step forward | Next step back |
| --- | --- | --- |
| A tap on a control (it has the position, no ring) | The control after it | The control before it |
| A tap anywhere else — a background, a reading, a label | The first control after the tapped point | The last control before it |
| No tap: the screen arrived, or the person scrolled | The first control in view | The last control in view |
| None of these in view | The order's first control, brought into view | The order's last |
| A ring is showing | The next stop, as always | The previous stop |

- **"After" and "before" follow the focus order, judged by where controls sit on the screen** — after is below the
  point, or beside it later on the same line.
- **A control wholly in view comes first**; a partly visible one only when nothing is wholly in view, so the first step
  does not pull the view back a whole row.
- **A scroll or a drag is not a selection, and leaves no starting point** — where the finger went down says nothing
  about where the content is now; the next step starts from what is in view.
- **A drag drops the ring.** The press that starts it decides the ring as any press does (§3), and nothing during the
  drag brings it back.
- **A control pinned over scrolling content — a sticky bar's button — is no starting point**; it stays put while the
  content moves, so it says nothing about where the person is reading.
- **The starting point is spent by the next step**, and forgotten when the screen changes or an overlay opens or closes.
- **Web:** the browser keeps the starting point for clicks; a script that scrolls content leaves focus alone.
- **Embedded (ESP-IDF, LVGL):** LVGL steps from the group's focused object wherever it is, scrolled off the panel or
  not. The product reads each detent before LVGL does — a wrapper around the encoder's read callback — and, with no
  ring showing, focuses the starting point instead of stepping. Where "no ring showing" includes "the focused control
  is out of view", a quick turn can restart from the viewport: LVGL animates a scroll into view (`LV_ANIM_ON`), so a
  control the encoder has just focused is still out of view until the scroll lands. Test visibility only once no
  scroll is running.

## 5. Opening and closing screens and overlays

**A screen or a sheet opens with no ring and waits for the first step; a modal opened by a keyboard, encoder or key
moves focus into itself; closing an overlay hands focus back to what opened it.**

- **A screen or a sheet opens as a web page loads: nothing ringed.** The position may name its first control; the
  first step rings what is in view (§4).
- **A modal — a dialog, a menu, a dropdown's list — moves focus to its first control as it opens.** The ring shows
  when a keyboard, encoder or key opened it; opened by a tap, its control holds the position with no ring.
- **A modal that asks before something that cannot be undone opens on its least destructive control** — Cancel, not
  Delete — so a press made out of habit changes nothing (WAI-ARIA's dialog pattern).
- **Autofocus is for a screen whose one main job is that control** — a search screen's field, where the person
  arrives to type. Elsewhere, moving focus on arrival takes the person past everything above it.
- **Embedded: a device may place the ring where one press is clearly next** — only when that press changes nothing
  that cannot be undone, the ring is taken from no stop the person chose, and a tap still removes it. Focus alone
  still does nothing (WCAG 3.2.1).
- **Inside a modal, focus stays in it and wraps, and the screen under it is inert** — no step, tap or drag reaches it.
- **Escape, back or the menu key closes only the topmost overlay, one level per press.** A half-filled dialog is never
  thrown away with the sheet under it. Every overlay closes this way; none is a trap (WCAG 2.1.2).
- **Closing hands focus back to the opener, with the ring only if the opener had it.** Nested overlays return to the
  one beneath, not to the screen. Closing leaves the screen as it was: its position and its scroll.

| The opener, as the overlay closes | Focus goes to |
| --- | --- |
| Still there and in view | The opener |
| Deleted | The next control in the focus order — "another element that provides logical workflow" (WAI-ARIA) |
| Hidden or disabled | The next control that can take focus; none, and nothing is ringed |
| Scrolled out of view | The opener, brought into view (§6) |
| No other control | Nothing; the next step starts from what is in view (§4) |

- **Web:** `<dialog>` opened with `showModal()` makes the rest of the page inert and closes on Escape; a custom modal
  uses `inert` on the rest and records `document.activeElement` before it opens, to return to it.
- **Android:** Back closes the top dialog or sheet. **iOS:** `accessibilityViewIsModal` keeps VoiceOver inside; the
  escape gesture calls `accessibilityPerformEscape`.
- **Embedded (ESP-IDF, LVGL):** each overlay has its own group, bound to the input while it is up
  (`lv_indev_set_group`); a stack of open overlays records each one's opener, and closing binds the group beneath and
  refocuses its opener.

## 6. Keeping focus in view

**When an input that cannot see moves focus out of view, the view scrolls to bring it in, with a margin and clear of
anything pinned; focus moved by a touch scrolls nothing.**

- **Only the blind inputs need it.** A keyboard or an encoder can reach what is off screen; a finger can touch only
  what is already on it, and scrolling a half-visible tapped row drags the content out from under the finger.
- **Scroll to a margin, not to the edge**, so the control's neighbour shows where the walk goes next.
- **Nothing pinned covers a focused control** (WCAG 2.4.11): a sticky header, a footer, a toast, a floating button.
  The margin is measured from the edge of the area the pinned things leave clear.
- **Focus set by code scrolls only when it acts for a key or a detent.**
- **Web:** browsers scroll a focused element into view; `scroll-padding` on the scroller keeps it clear of a sticky
  header, `scroll-margin` on the element sets the margin, and `focus({ preventScroll: true })` keeps script focus from
  scrolling after a tap.
- **Embedded (ESP-IDF, LVGL):** many LVGL widgets turn on scroll-on-focus as they are made — `lv_button`, `lv_switch`,
  `lv_slider` and `lv_textarea` among them — and LVGL focuses a tapped control on the press, so a tapped, half-visible
  control scrolls under the finger. Clear `LV_OBJ_FLAG_SCROLL_ON_FOCUS` on controls, and scroll in the group's focus
  callback (`lv_group_set_focus_cb`, called before the object gets `LV_EVENT_FOCUSED`) only when `lv_indev_active()`
  is a keypad or an encoder. `lv_obj_scroll_to_view_recursive` scrolls to the edge; the margin is the product's own
  scroll.

## 7. The focus ring

**One ring, drawn as the focused control's own state, outside the control, never moving the layout, with room in every
container, and distinct from selection and from edit mode.** Its contrast is a floor: 3:1 against everything it
touches (ACCESSIBILITY §2).

- **An outline, not a border.** A border is part of the box, so the content shifts when focus arrives and reads as the
  text changing size; an outline takes no space. **Web:** `outline` with `outline-offset`. **Embedded (ESP-IDF,
  LVGL):** `outline_width` and `outline_pad`; LVGL counts `border_width` in a control's content space
  (`lv_obj_get_style_space_left` and its siblings) and never the outline.
- **Room in every clipping ancestor.** A container that clips — a scroller always does — needs padding at least the
  ring's extent (its width plus its offset). **Web:** `overflow` other than `visible` clips the outline. **Embedded
  (ESP-IDF, LVGL):** a parent clips its children to its own area unless it has `LV_OBJ_FLAG_OVERFLOW_VISIBLE`, and then
  to its extra draw size, which is 0 for a plain container.
- **Embedded (ESP-IDF, LVGL): siblings sit at least the ring's extent apart.** LVGL paints a ring with its object, so a
  neighbour drawn later covers the part that reaches it.
- **Focus is not selection** — "the selected state must be visually distinct from the focus indicator" (WAI-ARIA).
  Draw them with different properties — a ring for focus, a fill, an edge or a check for selection — so both can show
  at once.
- **Edit mode looks different again**, with the same geometry so nothing moves: a ring of another lightness, not
  another hue alone, so colour does not carry it alone (ACCESSIBILITY §2).
- **The ring is the focused control's state and nothing else draws it**, so it can never sit apart from the position.
  A control that draws its ring on a child forwards the state to it.
- **Embedded (ESP-IDF, LVGL): style the ring on both `LV_STATE_FOCUSED` and `LV_STATE_FOCUS_KEY`**, and edit mode on
  `LV_STATE_EDITED`. A style's state with the higher value wins — `FOCUS_KEY` outranks `FOCUSED`, `EDITED` outranks
  both — so a ring restyled on `FOCUSED` alone loses to the theme's ring on `FOCUS_KEY` under the encoder. The
  default theme draws its ring in the primary colour at `LV_OPA_50`, measured composited (ACCESSIBILITY §2).
- **Appearance above AA (WCAG 2.4.13, AAA), optional:** the ring's area at least that of a 2 CSS px perimeter of the
  control, and 3:1 between its focused and unfocused pixels. A project adopts it in its design brief.

## 8. What takes focus

**Only controls are stops — what can be pressed or set; text that shows a value, and headings, are not; disabled and
hidden controls are skipped.** A stop that does nothing is a step wasted, and Tab on a web page stops on controls,
never on text.

- **A reading carries its meaning in words**, read by eye and by scrolling; on platforms with a screen reader, the
  reader reaches text by its own navigation. Never make text focusable to make it readable.
- **Every control a finger can tap is a stop.** One a finger can reach and the keys cannot is half-built.
- **A composite widget is one stop, moved within by its own keys** — tabs, menus, listboxes, radio groups, grids and
  toolbars take one Tab stop with arrows inside, Home and End, and type-to-find in long lists (WAI-ARIA's keyboard
  patterns). **Embedded:** a one-axis knob has no second axis, so a list's rows are stops of their own; a value
  control — a slider, roller, dropdown — is one stop, changed in edit mode (§2).
- **A value never changes because focus passed over it** — editing takes a press, and the ring shows it (§7).
- **Disabled and hidden controls are skipped**, and hidden means out of the order (ACCESSIBILITY §5). **Web:** native
  `disabled` leaves the order; WAI-ARIA keeps a disabled item focusable with `aria-disabled` where it must stay
  discoverable inside a composite.
- **Hand focus on before hiding or deleting the focused control**, to where the next step is — the neighbouring row,
  the control the change leads to. The ring goes along only if the control had it.
- **A change of state never moves focus or changes screens** — a connection arriving, a reading updating. A ring that
  jumps under a resting hand is a press nobody aimed. The hand-over above is the one exception.
- **Embedded (ESP-IDF, LVGL):** hiding an object that holds `LV_STATE_FOCUSED` focuses the next one in its group,
  wrapping — possibly the screen's first control; deleting the focused object refocuses by the group's refocus policy
  (`lv_group_set_refocus_policy`, previous by default). Focus the right neighbour first, then hide or delete.

## 9. Messages and focus

**A message that asks nothing takes no focus; one that needs an answer is a dialog, and takes focus as a modal
does (§5).**

- **A toast is not in the focus order and traps nothing** — the person turning through a list never finds the encoder
  steering a line of news. It may close on a tap.
- **Timing stands in for focus** — how long a toast stays is ACCESSIBILITY §8; making it heard without focus is
  ACCESSIBILITY §10.
- **News the person must acknowledge is a one-button dialog**, never a toast.
- **Embedded (ESP-IDF, LVGL):** a toast is in no group and not on the overlay stack (§11); a tap on it is a tap on
  the background (§4).

## 10. Who takes an input

**When more than one thing could take an input, the first owner in a fixed order takes it, and nothing below it sees
it.** This is mostly the embedded case, where one encoder and one touch panel serve every layer; the web's equivalent
is named where there is one.

| Order | Owner | Takes | Web equivalent |
| --- | --- | --- | --- |
| 1 | The topmost overlay | Every step and activation, and every touch outside it | A modal dialog with the page inert |
| 2 | A control in edit mode | Every step, until it is left | A composite's arrow keys; a text field's keys |
| 3 | A contact something claimed — a sheet being dragged | That contact's every move, until the finger lifts | Pointer capture (`setPointerCapture`) |
| 4 | A screen's own handler for the step input | The steps it registered for, before focus navigation | A key handler on the page |
| 5 | Focus navigation | Every other step | Tab order |
| 6 | The screen | A contact no owner above took | The page |

- **A step never reaches what is behind an overlay, and edit mode never leaks a step to navigation.**
- **A drag is never a tap at its end.**
- **Keys that act across the product — power, lock, the menu key — decide before any of this**, so the same press
  means the same thing on every screen.
- **A screen's own handler (order 4) gives the steps back while a control edits and while an overlay is up**, and
  shows on screen what its steps move — otherwise the same input does two things the person cannot tell apart.

## 11. Building it once

**Focus is decided once, in the product's input model — one press handler, one overlay stack, one focus policy
applied to every group, one way to hide a focused control — never per screen.** Every per-screen copy is another
place to forget a rule.

- **One press handler sees the start of every contact**: a tap on a control moves the position with no ring; a tap
  anywhere else drops the ring and records the point (§3, §4). No background, label or surface has its own handler.
- **One overlay stack**: opening records the opener and what had the input; closing hands both back (§5). Nesting is
  then correct without any overlay knowing it nests.
- **One focus policy**, applied to every screen's and overlay's group as it is made: wrapping, scrolling for the blind
  inputs (§6), the starting point (§4).
- **One way to hide or delete a focused control**, which hands focus on first (§8).
- **A departure from the model is recorded, with its reason, in the project's design brief** — or it is a bug.
- **Web:** listeners on the document rather than on each element; one dialog manager. **Embedded (ESP-IDF, LVGL):** a
  wrapper around each input device's read callback, an overlay stack over LVGL groups, and the focus policy set with
  `lv_group_set_wrap` and `lv_group_set_focus_cb` on every group.

## 12. Traps

- **The ring can flash for a frame under a tap** — when it is styled on `LV_STATE_FOCUSED` and taken off later than
  the touch read that focused the control, after a redraw → take it off in that same read (§3). Unverified per panel:
  film taps on the device.
- **The first detent after scrolling can drag the screen back to where the ring was left** — when the step starts
  from the group's stored position, as LVGL's own step does → start from what is in view (§4).
- **The ring can vanish as the encoder reaches a row below the fold** — when a handler clears the ring on
  `LV_EVENT_SCROLL_BEGIN` without asking which input is active: a scroll made by code, the encoder's scroll into view
  among them, sends that event too → clear the ring on scroll only when a pointer is the active input (§4, §6).
- **A tapped row at the panel's edge can jump under the finger** — when the control keeps scroll-on-focus, since LVGL
  focuses it on the press → scroll only for the blind inputs (§6).
- **Hiding a control can send the ring to the top of the screen** — when the hidden control held `LV_STATE_FOCUSED`:
  LVGL focuses the group's next member, wrapping → hand focus on before hiding (§8).
- **A ring restyled for the encoder never appears** → the style is on `LV_STATE_FOCUSED` and the theme's
  `LV_STATE_FOCUS_KEY` outranks it → style both (§7).
- **Closing a dialog lands on the screen's first control** → the opener is not recorded → one overlay stack (§11).
