---
name: touch-and-gesture
description: How touch input, gestures, scroll-linked motion and layout are specified, built, reviewed and checked so they feel direct and never fight the platform, carried in the skill (references/touch.md) — the principles for every platform, with guidance labelled for the web, iOS, Android and embedded ESP-IDF devices with an LVGL screen — what follows a drag, catching a moving object, how often the touch is read (the touch controller and LVGL's read period); the platform's movement tolerance, axis lock, claiming only one axis (touch-action, LVGL's scroll limit and scroll chaining), a sheet that hands off with its list; deciding on release by distance or speed, one outcome per press (LVGL's CLICKED, SHORT_CLICKED and long press), resistance past a limit, the throw, what cancels on touch; the platform's sheets, swipe actions, long press, hold to confirm, reorder, pull to refresh and pinch, screen and bezel edges; the throw's speed from the last moments and a rested finger that places rather than throws; a scroll never an edge gesture, a just-opened surface dragged only by its handle, decoration that takes no press; the pressed state on touch (LV_STATE_PRESSED), delays in scrolling lists, tap highlight, hover on hybrid devices; feedback beyond the screen, carried in references/feedback.md — haptics, sound and a device's status lights as one small vocabulary of event types, fired after the input is accepted and within about 100 ms, success only once it happened, the haptics to avoid, a press answered, a wait shown and an outcome said in words, status lights in a priority order, and pairing haptics with lights, with each platform's haptic API (iOS feedback generators, Android HapticFeedbackConstants, the Web Vibration API's limits, a device's own actuator and LED drivers); scroll-triggered against scroll-driven motion and never taking over scrolling; the visible area, safe areas, round and small panels, the on-screen keyboard, field keyboards, back closing the top layer, bottom navigation; a rotary encoder and buttons as an equal input (how a press and a long press line up with a tap; the focus model is the accessibility skill's); the gesture spec, the prototype on the device, the device walk and the review of a gesture change; plus touch_check.py for the patterns code can show, in web and C/C++ LVGL files. Builds on the accessibility skill's input floors and the motion skill's easing and interruption. Values come from the project's own DESIGN.md. Portable — the folder works in any repo. Use when designing, building or reviewing a drag, swipe, sheet, long press, reorder, pull to refresh or pinch, a pressed state, a haptic, a status light or what a press, a wait and an outcome feel like, a scroll-linked effect, a full-height or keyboard-heavy mobile screen, a device screen's touch, encoder or buttons, or when a gesture lags, jumps, fights scrolling or closes by accident.
metadata:
  scope: portable
---

# Touch and gesture

How touch, gestures, scroll-linked motion, layout and feedback are decided and checked. The principles and their
reasons are kept in this skill at [references/touch.md](references/touch.md) (cited `TOUCH §n`) and
[references/feedback.md](references/feedback.md) — haptics, sound, status lights, and answering a press, a wait and an
outcome (cited `FEEDBACK §n`); this page indexes them in one-line rules and holds the steps: the gesture spec, the
prototype, the build, the review and the device walk. The skill takes its values — the product's target size,
spring, hold length, which gestures it uses and, on a device, its read period, scroll limit, throw and long-press time
— from the project's own `DESIGN.md`; that file wins over the references, and the references over this page.

**Platforms.** The rules below hold on every platform. The reference labels how each is built — **Web**, **iOS**,
**Android**, **Embedded (ESP-IDF, LVGL)** — and an embedded device's encoder and buttons stand beside its touch as an
equal input (TOUCH §11).

**Portable.** This folder is self-contained and links to nothing outside itself (it names the rest of a kit in
backticks): the two references and the touch check ([scripts/touch_check.py](scripts/touch_check.py)). Copy it into any
repo's `.agents/skills/` (or `.claude/skills/`) and it works there: the check reads `UI_PATHS` from
`.agents/project.py` when the repo has one, and scans every tracked UI file — web, and C and C++ — when it does not.
It needs git and Python 3.9+.

**Builds on.** The `accessibility` skill owns the floors for input — target size, a plain alternative to every
gesture, drag, long press and hover, acting on release, both orientations, time limits, and on a device the encoder's
and keys' reach, focus order and visible focus — and the `motion` skill owns how a move eases, settles and survives
interruption, including keeping a dragged object under the finger. This skill says how each is built on touch, and
what a turn and a press do beside it, and does not restate them. In the agent-harness kit, the `ui-designer` skill
and agent apply it at their gates, and `verify.py run` runs the check.

## When to use

- Designing, building or reviewing a drag, a swipe, a sheet, a long press, hold to confirm, a reorder, pull to refresh
  or a pinch.
- A pressed state, touch feedback, a hover that must also work on touch.
- A haptic, a sound or a status light for an event; a press that starts work, a wait, a success or a failure.
- A scroll-linked effect — a reveal on scroll, a scroll-driven progress, parallax.
- A mobile screen that is full height, has fields and a keyboard, a bottom bar, or overlays that back should close.
- A device screen on LVGL — its touch panel, a round or small layout, a rotary encoder or buttons.
- A gesture lags the finger, jumps on release, fights the page's scrolling, or closes something by accident.

## Rules

### Do

1. **Derive everything that follows a drag from its one position, read as often as the screen draws, and let a moving
   object be caught** (TOUCH §1).
2. **Start a drag only past the platform's tolerance, lock it to one axis, and claim only that axis** — `touch-action`
   on the web, scroll chaining on one axis in LVGL (TOUCH §2).
3. **Hand a sheet off with its list within the same finger; never let a fling's momentum move or close it**
   (TOUCH §2).
4. **Decide on release by distance or speed; let a pull-back refuse the throw; resist past a limit** (TOUCH §3).
5. **Treat the system taking the touch as a cancel, and decide in the spec what a second finger does** (TOUCH §3).
6. **Prefer the platform's control for each gesture pattern; justify a custom one** (TOUCH §4).
7. **Keep custom swipes off the system's edges, and mirror them for right-to-left** (TOUCH §4).
8. **Delay pressed in a scrolling list, and keep or replace the platform's touch feedback** — on LVGL, a style on
   `LV_STATE_PRESSED` for every tappable object (TOUCH §5).
9. **Never let hover stick after a tap — on the web, gate it with `any-hover`/`any-pointer`; turn selection off on
   controls, never the page** (TOUCH §5).
10. **Keep haptics rare, caused by the person, never the only signal, and under the system's or the product's
    setting** (FEEDBACK §1, §4).
11. **Make scroll motion either triggered once or driven by position, and never take scrolling over** (TOUCH §6).
12. **Lay out in the visible area, clear of safe areas — on a device, its round or cut corners and the bezel's band —
    and the keyboard** (TOUCH §7).
13. **Ask each field for its keyboard, return key and autofill; never focus a text field unasked on touch**
    (TOUCH §7).
14. **Close the topmost overlay first on back, Escape or an outside tap — prefer `<dialog>` and popovers on the web;
    one back path on every screen of a device** (TOUCH §7).
15. **Write the gesture spec, and prototype the gesture on the device, before the build** (TOUCH §8).
16. **Hand the person the device walk; review a gesture change against its spec** (TOUCH §9, §10).
17. **Give a press one outcome: a tap acts on release, a long press acts instead of the tap, never as well** — on LVGL,
    `LV_EVENT_CLICKED`, or `LV_EVENT_SHORT_CLICKED` beside a long press (TOUCH §3).
18. **Make an encoder and buttons an equal input where the device has them: each gesture's task by turn, press and
    long press, a press giving a tap's outcome** (TOUCH §11; what each input does and the focus it moves are
    `FOCUS §2`, its floors `ACCESSIBILITY §5`).
19. **Take a device's input settings — read period, scroll limit, throw, long-press time, gesture limit — from
    DESIGN.md, and re-derive the throw when the read period changes** (TOUCH §1–§3).
20. **Take the throw's speed from a short window at the end of the drag, measured between position reports; a finger
    that rested before lifting places, never throws — the window and the rest from DESIGN.md** (TOUCH §3).
21. **Never let a scroll become an edge gesture; drag a just-opened surface only by its handle for a moment, its
    length from DESIGN.md; let decoration take no press** (TOUCH §4).
22. **Make feedback confirm what the screen shows, from one small vocabulary — one event type, one feel everywhere; an
    event with no chosen pattern stays silent** (FEEDBACK §1, §2).
23. **Fire feedback only after the input is accepted, within about 100 ms, and signal success only once it
    happened** (FEEDBACK §3).
24. **Answer a press at once, show a wait, say the outcome in words, and give the controls back on every way out**
    (FEEDBACK §5).
25. **On a device with status lights, keep a small cue vocabulary in a priority order — nothing animated forever,
    critical cues also on the display, and the floors of `ACCESSIBILITY §2` and `ACCESSIBILITY §8`** (FEEDBACK §6,
    §7).

### Never

- **Claim every axis on a surface that sits in something that scrolls** — `touch-action: none` on a carousel or a
  sheet, or LVGL scroll chaining off on both axes; only a handle, a slider thumb, a canvas or a map takes it
  (TOUCH §2).
- **Move or close a sheet on a fling's leftover momentum** (TOUCH §2).
- **Act on touch-down, or let a long press also fire the tap** — `LV_EVENT_PRESSED` is for feedback and a drag's
  start (TOUCH §3).
- **Remove the platform's touch feedback without a replacement** — on LVGL, `lv_obj_remove_style_all` on a button
  with no pressed style after it (TOUCH §5).
- **Rewrite scrolling — distances, momentum, one-flick-one-section** — on LVGL, removing scroll momentum or elastic
  (TOUCH §6).
- **On the web, put a full-height layout on the legacy viewport unit alone** (TOUCH §7).
- **Stack a history entry per overlay so back becomes a trap** (TOUCH §7).
- **Tell anything by vibration or a light alone, buzz while waiting, or signal success for a request** (FEEDBACK §1,
  §3, §4).
- **Claim a gesture feels right from a video, a simulator or code** — it is judged under the finger, on the device.

## Procedure

### Specifying a gesture

1. **Read before asking** — the project's DESIGN.md (its target size, spring and any gesture rules), what sibling
   surfaces do, and the platform's own control for this pattern (TOUCH §4).
2. **Prefer the platform's control** — its sheet, swipe actions, refresh — over a hand-built one; a custom gesture needs
   a reason in the spec.
3. **Fill the gesture spec** (TOUCH §8) — one question at a time to the person, each with a recommended answer.
4. **Write it beside the mock and the motion brief** as `<screen>_gesture<n>.md`.

### Prototyping and building

1. **Prototype on the device before the build** — in the scratchpad, a quick build or a prototyping tool, on the
   target's screen and refresh rate; on an embedded device, a build flashed to the product's own hardware, since a
   simulator on a desktop reads a mouse, not the touch controller. A video approves timing, not feel. In the kit,
   record the person's yes in their words: `verify.py decision "gesture prototype approved on device: <screen> —
   <their words>"`.
2. **Build from the spec's values**, each from DESIGN.md, with the plain alternative in the same change.
3. **Run the touch check** (below), and the accessibility and motion checks.

### Reviewing a gesture change

1. **Read each gesture against its spec and the review table** (TOUCH §10), the `accessibility` skill's floors first.
2. **Run the touch check on the changed UI files.**
3. **List the device walks the change needs** (TOUCH §9) and hand them to the person; never claim one passed.

## Checks

```sh
python3 .agents/skills/touch-and-gesture/scripts/touch_check.py            # every UI file, against the baseline
python3 .agents/skills/touch-and-gesture/scripts/touch_check.py <file> …   # the files a change touched
```

- [ ] (script) **T1** a surface that claims every axis — 0 hits, or a handle, thumb, canvas or map marked
- [ ] (script) **T2** a full-height layout on `100vh` alone — 0 hits
- [ ] (script) **T3** a text field focused unasked — 0 hits
- [ ] (script) **T4** selection off for the whole page — 0 hits
- [ ] (script) **T5** the tap highlight removed with no pressed style — 0 hits
- [ ] (script) **T6** an LVGL object whose only press handler is `LV_EVENT_PRESSED` — 0 hits
- [ ] (script) **T7** `LV_EVENT_CLICKED` on an object that also has a long press — 0 hits
- [ ] (script) **T8** LVGL scroll chaining off on both axes — 0 hits, or a handle, slider, canvas or map marked
- [ ] (script) **T9** LVGL scroll momentum or elastic removed — 0 hits
- [ ] (script) **T10** an LVGL button stripped of its styles with no pressed style — 0 hits
- [ ] A gesture spec for every gesture, and the person's recorded yes on its prototype on the device (Do 15)
- [ ] One axis claimed; the sheet hand-off right; release by distance or speed; one outcome per press (Do 2–4, 17)
- [ ] The `accessibility` skill's input floors met for every gesture
- [ ] On a device with an encoder or buttons, each gesture's task done by them (Do 18)
- [ ] The device walk handed to the person — never claimed from code (Do 16)
- [ ] The throw's speed from the last moments; edge swipes that never take a slow scroll; decoration that takes no
      press (Do 20, 21)
- [ ] Every haptic, sound or light from the vocabulary, after acceptance, success only once it happened; a press, a
      wait and an outcome answered (Do 22–24)
- [ ] On a device with status lights, the cue order, nothing animated forever, the accessibility floors (Do 25)

The check reads web files (CSS, Tailwind classes, markup, scripts) for T1–T5 and C and C++ files on LVGL 8 or 9 for
T6–T10; iOS and Android code is not read. It reports how many web and C/C++ files it read, and says plainly when it
read none. T2, T5, T6, T7 and T10 look across one file: T5 cannot see a highlight reset in another file, Tailwind's
base styles already remove it project-wide, and a handler or a pressed style in another file is not seen. T6–T8 and
T10 match an object by the text of its expression. A sanctioned hit carries `touch-exception` on its line with the
reason — a drag handle, a slider thumb, a canvas or a map that takes every gesture, with its plain alternative named;
a press that only gives feedback while LVGL's own widget acts.

## Traps

- **The page will not scroll over a carousel** → the carousel set `touch-action: none` → `pan-y`, so the browser keeps
  vertical scrolling (Do 2).
- **A sheet closes when the person flings its list back to the top** → the fling's momentum carried into the sheet →
  hand off only within the finger's own drag (Do 3).
- **The swipe fires when the person meant to scroll** → no tolerance or axis lock → the platform's tolerance, then lock
  (Do 2).
- **Rows flash while scrolling fast** → pressed shown on touch-down in a scrolling list → a short pressed delay (Do 8).
- **The bottom button is hidden under the browser's bar** → `100vh` alone → `dvh` or `svh` after the fallback (Do 12).
- **The keyboard covers the field being typed in** → the layout ignores the keyboard's inset → follow the visual
  viewport, the keyboard layout guide or the IME inset (Do 12).
- **Back leaves the page instead of closing the sheet**, or needs three presses → overlays not on the platform's close
  path, or one history entry each → `<dialog>`, a popover, or a replaced entry (Do 14).
- **A swipe from the edge goes back instead of revealing the drawer** → the custom swipe starts at the system's edge →
  start it away from the edge, or give the drawer a button (Do 7).
- **A drag on a device lags and steps** → LVGL reads the touch once per `LV_DEF_REFR_PERIOD` (its default is
  `MOTION §7.1`'s) → set the read period from the panel's frame rate, and the controller's report rate at or above it
  (Do 1).
- **A vertical drag that starts on a carousel scrolls nothing on a device** → scroll chaining off on both axes →
  turn off only the carousel's own axis (Do 2).
- **A long press on a row also opens it** → the row acts on `LV_EVENT_CLICKED`, which LVGL sends after a long press
  too → `LV_EVENT_SHORT_CLICKED` (Do 17).
- **Flings travel too far, or die at once, after a change of refresh period** → LVGL takes the scroll throw off on
  every animation step → re-derive the throw from the new period (Do 19).
- **A long-press action on a slider never fires from the encoder** → LVGL's long press on an editable object toggles
  edit mode → give the action another path (Do 18).
- **A quick click of a hardware button does nothing** → the press and release both fell between two reads → latch
  the press in the driver until a read reports it (Do 18).
- **A hard fling on a device lands like a slow drag** → the speed read per read, and the controller can repeat its
  last point between reports → measure between position reports over the brief's window (Do 20).
- **A tap on a sheet's content right after it opens drags or closes the sheet** → the finger, already moving, grabbed
  the surface → for a moment only the handle drags it (Do 21).
- **A tap on a caption does nothing** → a decorative object took the press → make it not clickable (Do 21).
- **People turn haptics off** → a feel on every step, while waiting, or for background updates → the vocabulary, after
  acceptance, the lightest feel for the most frequent event (Do 22, 23).

## Sources

| Topic | Where |
| --- | --- |
| The principles, the gesture spec, the device walk, the review | [references/touch.md](references/touch.md) |
| Haptics, sound, status lights; a press, a wait and an outcome | [references/feedback.md](references/feedback.md) |
| Haptic effects and their meaning on Android | Android Developers: haptics design principles, `HapticFeedbackConstants` |
| Haptics on the web | MDN, `Navigator.vibrate`; caniuse, Vibration API (no Safari or iOS Safari) |
| Response-time limits | Nielsen Norman Group, "Response Times: The 3 Important Limits" || Gestures, sheets, haptics, layout | Apple Human Interface Guidelines (Gestures, Sheets, Playing haptics, Layout) |
| Gestures, states, bottom sheets, navigation | Material Design 3; Android Developers (gestures, nested scrolling, edge-to-edge, predictive back, IME) |
| Fluid, interruptible gestures | Apple WWDC 2018, "Designing Fluid Interfaces" |
| Pointer events, `touch-action`, viewport units, `<dialog>`, popovers, scroll snap | MDN Web Docs |
| Input devices, events, scrolling, groups, the read period and defaults on a device | LVGL 9 documentation and source (`lv_indev.h`, `lv_event.h`, `lv_obj.h`, `lv_group.h`, `lv_conf_template.h`) |
| Touch controllers and their LVGL port on ESP-IDF | Espressif ESP-BSP: `esp_lcd_touch`, `esp_lvgl_port` (touch, knob, navigation buttons) |
