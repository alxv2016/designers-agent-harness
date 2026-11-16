# Motion

How motion in a product is decided, drafted, built, debugged and reviewed: whether something should move at all,
which curve and how long, where it comes from and goes, how several moves fit together, how it survives being
interrupted, what it costs to render, what it becomes under reduced motion, and the words to name it. People read it
to decide motion with reasons; coding agents read it, through the `motion` skill, before they draft a motion study,
build an animation or review one.

**Where it lives.** In the `motion` skill, beside the steps and checks that apply it — [its SKILL.md](../SKILL.md).
The skill folder is self-contained: copy it into any repo's `.agents/skills/` and this reference and the motion check
come with it. The product's own values — its durations, curves and the ceiling on how long a move may run — live in
its design brief (`DESIGN.md` in the agent-harness kit) and win over this reference. The accessibility floors on
motion (reduced motion, flashing, pausing) are the `accessibility` skill's.

**Platforms.** Every principle holds on every platform and is stated once. Guidance for one platform is labelled
**Web**, **iOS**, **Android** or **Embedded (ESP-IDF, LVGL)** — the last for a device with a display drawn by LVGL on
an Espressif chip, whose own rendering budget is §7.1.

**Stability.** Cite this doc as `MOTION §n`. Do not renumber; add new material under the next free number.

| § | Section | Look here for |
| --- | --- | --- |
| 1 | [Whether to animate](#1-whether-to-animate) | Frequency, purpose, the budget, first paint, keyboard changes |
| 2 | [Easing](#2-easing) | Choosing a curve by the journey; curve before duration |
| 3 | [Duration](#3-duration) | Time by size and distance; exits shorter; floors; no delay on a response |
| 4 | [Space and origin](#4-space-and-origin) | Nothing from nothing, growing from the trigger, direction, object permanence, press and hover |
| 5 | [Choreography](#5-choreography) | One clock per object, one entrance per container, stagger, asymmetric timing, one personality |
| 6 | [Interruption and physics](#6-interruption-and-physics) | Retargeting from where it is, springs, direct manipulation |
| 7 | [Rendering and performance](#7-rendering-and-performance) | Cheap properties, the frame budget, measuring, content visible without motion; on an embedded display, the area redrawn, the bus, layers and draw buffers (§7.1) |
| 8 | [Reduced motion](#8-reduced-motion) | Designing the reduced variant of each move |
| 9 | [The motion brief](#9-the-motion-brief) | The interview before a motion study, and the fields it fills |
| 10 | [Debugging motion](#10-debugging-motion) | The loop, and symptoms mapped to their usual causes |
| 11 | [Reviewing motion](#11-reviewing-motion) | What a review checks, what it leaves alone, the order of fixes |
| 12 | [Glossary](#12-glossary) | The words for motion, so a brief and a review mean the same thing |

---

## 1. Whether to animate

**Motion earns its place by explaining a change the person caused; the more often they meet it, the less it moves.**

- **Frequency decides first.** An interaction repeated many times a session — typing, moving through a list, a command
  palette, a menu opened by a shortcut — changes instantly; a transition's cost is paid on every use, long after its
  novelty is gone.
- **Every move finishes the sentence "this moves so that…"** with one of: feedback on an input, where something came
  from or went, a state that changed, softening an abrupt change, or explaining a relationship. "It looks nice" is not
  one of them (Material Design 3, Motion; Nielsen Norman Group, "The Role of Animation and Motion in UX").
- **Motion is a budget.** Each extra animation dilutes the rest; dense, data-heavy and task-critical screens stay still,
  and nothing decorative sits between the person and their goal.
- **Nothing at rest plays an entrance on first paint**, and a one-time introduction does not replay on return —
  animating what was already there implies a change that did not happen.
- **Keyboard-driven changes land at once** — arrow navigation, a shortcut, focus moving, a hardware button or a rotary
  encoder stepping through a list: the focus or selection
  indicator reaches its new place on the frame of the keypress, never trails behind it, so the person never sees
  focus in the wrong place.
- **"Don't animate" is a complete answer**, written down as a decision so it is not reopened by the next review.

## 2. Easing

**Pick the curve by the journey, then tune the duration to the curve.**

| Journey | Curve | Why |
| --- | --- | --- |
| Something arrives | Decelerate (fast start, long settle) | The first frames, the ones the person watches, move at once |
| Something leaves | An accelerate or a short decelerate, by the project's choice, kept short | By the time it leaves, attention has moved on; the platforms ship an accelerate for exits (Material Design 3, emphasized accelerate) |
| Something moves within the screen | Ease both ends | It starts and stops on screen, in view |
| Hover and press | A gentle ease, quick | A state change, not a journey |
| Time passing — a spinner, a progress bar, a hold filling | Linear | Constant speed is honest about time; on a move it reads mechanical |

- **Curve first, then duration** — a curve that front-loads its travel reaches its target sooner, so perceived speed
  depends on the curve; change one at a time.
- **An arrival, a hover or a press never starts slowly** — an ease-in there holds back the response the person is
  watching for. A move within the screen eases both ends, and an exit may accelerate.
- **Every curve is one of the brief's named curves**, never an ad-hoc value in a screen.
- **Web:** the CSS keywords `ease-out`, `ease-in` and `ease-in-out` are a decelerate, an accelerate and both ends; a
  named curve is a custom property holding a `cubic-bezier()`, used by name.
- **Embedded (ESP-IDF, LVGL):** a curve is a path callback set with `lv_anim_set_path_cb`. LVGL ships
  `lv_anim_path_ease_out` (decelerate, `cubic-bezier(0, 0, 0.58, 1)`), `lv_anim_path_ease_in` (accelerate),
  `lv_anim_path_ease_in_out`, `lv_anim_path_linear`, `lv_anim_path_overshoot`, `lv_anim_path_bounce` and
  `lv_anim_path_step` (holds, then jumps to the end value when the duration ends — a change with no motion). A
  named curve from the brief is one path callback per curve, built on `lv_cubic_bezier` with
  `LV_BEZIER_VAL_FLOAT`, or `lv_anim_set_bezier3_param` with `lv_anim_path_custom_bezier3` (LVGL source,
  `lv_anim.h`, `lv_math.h`).
- **Embedded (ESP-IDF, LVGL): set the path on every animation** — `lv_anim_init` leaves `lv_anim_path_linear`, so an
  `lv_anim_t` with no path travels at constant speed; `lv_screen_load_anim` never sets one, so its slides are linear
  too, and a slide that should decelerate is built as an `lv_anim_t` (LVGL source, `lv_anim.c`, `lv_display.c`).

## 3. Duration

**Time grows with the size of what moves and how far it travels; exits are shorter; feedback starts at once.**

- **Small feedback is fast, surfaces are medium, only full-screen changes are long** — a slow tooltip feels sluggish,
  a fast full-screen change cannot be followed (Material Design 3, Easing and duration).
- **An exit takes less time than its entrance**, and travels no farther than it must.
- **Too fast is a fault too** — a move shorter than the eye can track reads as a glitch; the brief's shortest duration
  is the floor.
- **Feedback starts within about a tenth of a second** — the first visible frame follows the input (Nielsen Norman
  Group, "Response Times: The 3 Important Limits").
- **No delay before a response to the person's action**; a delay belongs only to hover intent (a tooltip's first
  appearance) and to a stagger.
- **A change of varying size scales its duration with the change**, clamped between the brief's shortest and longest —
  one line expanding and ten lines expanding should not take the same time.
- **The brief sets a ceiling**; anything longer is an exception with its reason.
- **A duration is a named constant from the brief**, never a number written at the call.
- **Embedded (ESP-IDF, LVGL):** a duration is milliseconds given to `lv_anim_set_duration` (older code's
  `lv_anim_set_time`, mapped by LVGL's `api_map` headers), `lv_style_transition_dsc_init`, `lv_obj_fade_in` or
  `lv_screen_load_anim`, each from a constant generated from or copied out of the brief. `lv_anim_speed_clamped` turns
  a speed and the brief's shortest and longest durations into a duration that grows with the distance.
- **Embedded (ESP-IDF, LVGL): count frames, not only milliseconds** — LVGL steps animations once per refresh period
  (§7.1), and a move gets about its duration divided by the frame time the device reaches: 150 ms at 30 fps is four
  or five frames. Check the brief's shortest duration against the frame rate measured
  on the device — a move drawn in two or three frames is seen as two or three positions, not as motion.

## 4. Space and origin

**Things come from somewhere, go back the way they came, and stay one object while they move.**

- **Nothing grows from nothing** — an entrance starts near its full size with its opacity rising, never from zero
  scale, and travels a short distance unless it really comes from off-screen.
- **A surface opened by a control grows from that control**; a centred dialog grows from its centre.
- **Leave the way you came, and let direction mean navigation** — forward and back move in opposite directions, mirrored
  for right-to-left languages (Material Design 3, shared axis; Apple HIG, Right to left).
- **An item that opens into a larger view expands from where it sits** — at no frame is neither the item nor the view
  visible (Material Design 3, container transform; Apple, "Designing Fluid Interfaces", WWDC 2018).
- **Press feedback is felt more than seen** — a slight depression from the moment of press, gliding back on release;
  hover is smaller still, and only on things that respond to a click. A control that answers hover but not press feels
  dead.
- **Never move the element that holds the hover; move its content** — on the web, a hovered element that slides out
  from under the pointer loses hover, drops back and loops.
- **Hover motion runs only where a real hovering pointer exists**, and whatever hover reveals, keyboard focus reveals
  too (WCAG 1.4.13, 2.1.1).
- **Embedded (ESP-IDF, LVGL):** a touch panel has no hover, so press feedback is the only pointer feedback — LVGL's
  `LV_STATE_PRESSED` style, with a style transition. The point a scale or rotation works around is
  `transform_pivot_x`/`transform_pivot_y`; set it on the trigger's side. An entrance that grows is costly on a device
  (§7.1), so a short translate with opacity rising is the usual way to come from somewhere.

## 5. Choreography

**Several moves read as one composition: one clock per object, one entrance per container, a short ordered stagger.**

- **Parts that move as one thing share one duration and one curve** — a dialog and its scrim, a sheet and its
  backdrop; different clocks make one object read as two.
- **A surface arrives with its content in place** — a second wave of child entrances makes the person wait to read.
- **A stagger is short and ordered by importance**: the whole sequence fits the brief's ceiling, the lead element comes
  first, input is never blocked while it runs, and a menu used many times a session is never staggered.
- **A deliberate held action and its cancel run at different speeds** — a hold fills slowly and evenly, a release
  drains fast; one shared timing makes cancelling feel broken.
- **Small, similar content swapping in place crossfades** with at most a small directional hint, rather than a full
  slide (Material Design 3, fade through).
- **The product has one motion personality** — how fast, how much overshoot — decided once in the brief, not per
  screen.
- **Embedded (ESP-IDF, LVGL):** parts that move as one thing are driven by one `lv_anim_t` whose exec callback sets
  every part from the one value — a sheet's position and its scrim's opacity worked out together — so they cannot drift
  apart. A stagger is `lv_anim_set_delay` from the brief's stagger token, or an `lv_anim_timeline_t` with each
  animation added at its start time (`lv_anim_timeline_add`).

## 6. Interruption and physics

**Anything the person can retrigger or reverse continues from where it is; anything they drag follows the finger.**

- **Retarget, never restart** — a toggled drawer, a reordered list or a stacking toast animates from its current
  position to the new target; a timeline that restarts from its first frame is for loops and one-shots only (Apple,
  "Designing Fluid Interfaces", WWDC 2018; MDN, "Using CSS transitions").
- **A spring suits motion that ends a gesture or may be redirected** — it carries velocity into a new target. Describe
  it by perceived duration and bounce, with no bounce unless a gesture put force in (Apple, "Animate with springs",
  WWDC 2023; Material Design 3, motion physics).
- **During direct manipulation the object stays under the finger**, with no easing or smoothing; easing or a spring
  applies only after release, starting from the release velocity.
- **Motion the person drives is theirs** — it keeps tracking under reduced motion, and it sits outside the brief's
  duration ceiling.
- **A retarget takes the time the distance left needs** — the full duration scaled by the share of the travel still to
  go, never less than the brief's shortest duration.
- **Web:** a CSS transition retargets from the current value by itself; a keyframe animation restarts.
- **Embedded (ESP-IDF, LVGL): retarget by starting a new animation from the current value.** `lv_anim_start`
  replaces a running animation on the same variable and exec callback, so a new `lv_anim_t` whose start value is
  where the object is now (`lv_obj_get_y`, `lv_obj_get_style_translate_y`, or the running animation's
  `current_value` from `lv_anim_get`) continues without a jump; one whose start value is the original start is the
  restart. A style transition (`lv_style_transition_dsc_t`) starts from the property's current value, as a CSS
  transition does (LVGL source, `lv_anim.c`, `lv_obj_style.c`).

```c
/* Retarget a sheet: from where it is, in the time the distance left needs (MOTION §6). */
int32_t from = lv_obj_get_y(sheet);
lv_anim_t a;
lv_anim_init(&a);
lv_anim_set_var(&a, sheet);
lv_anim_set_exec_cb(&a, (lv_anim_exec_xcb_t)lv_obj_set_y);
lv_anim_set_values(&a, from, target);
lv_anim_set_duration(&a, scaled_ms(MOTION_ENTER_MS, LV_ABS(target - from), travel));
lv_anim_set_path_cb(&a, motion_path_decelerate);
lv_anim_start(&a); /* replaces the running animation on sheet + lv_obj_set_y */
```

- **Embedded (ESP-IDF, LVGL):** LVGL has no spring — a spring is a path callback that computes a damped oscillation
  from `act_time` and `duration`, with its perceived duration and bounce from the brief. During a drag the object
  follows the touch point on every `LV_EVENT_PRESSING` (`lv_indev_get_vect` gives the movement since the last input
  read); on `LV_EVENT_RELEASED` the settle starts from the speed of the last few reads.

## 7. Rendering and performance

**Animate only what the renderer can move cheaply, name what animates, and measure on the device people hold.**

| Platform | Cheap — moved without re-layout | Costly — re-lays out or repaints every frame |
| --- | --- | --- |
| Web | `transform` (translate, scale, rotate), `opacity`, `clip-path` | Width, height, top, left, margin, padding, font size; animated shadows and large blurs |
| iOS | A view's or layer's transform and opacity | Its frame or constraints, animated every frame |
| Android (Compose) | `graphicsLayer` — translation, scale, rotation, alpha | Size, padding and other modifiers that re-measure |
| Android (Views) | `translationX/Y`, `scaleX/Y`, `rotation`, `alpha` | `LayoutParams` changed every frame |
| Embedded (ESP-IDF, LVGL) | A small area: the position of a small object (`lv_obj_set_x`/`_y`, `translate_x`/`_y`), the `opa` or colour of a small part | A large area, whatever the property: a full-screen fade or slide; `transform_scale`, `transform_rotation` and `opa_layered` (a layer buffer); shadows, gradients and blurs redrawn each frame; width and height (lays out the children) — §7.1 |

- **Name each property that animates** — "everything that changes" drags unrelated properties along (web: never
  `transition: all`).
- **Motion during busy work runs where it cannot be blocked** — the browser's compositor, iOS Core Animation's render
  server, Android's RenderThread. **Embedded (ESP-IDF, LVGL):** there is no such place — LVGL draws on its own task
  (esp_lvgl_port's), so work done in that task, such as an event callback that decodes, writes flash or waits on the
  network, stops every animation; hand that work to another task, and take the port's lock (`lvgl_port_lock`) when
  another task touches LVGL.
- **When the look calls for a costly property, draw the same picture with a cheap one** — grow by scale, move by
  transform, cross-fade two shadows instead of animating one.
- **A moving element does not push its neighbours** unless their reflow is the meaning (a list reordering).
- **The frame budget is one frame at the screen's refresh rate** — about 16 ms at 60 Hz, 8 ms at 120 Hz — on a
  mid-range phone, not the development machine. **Embedded (ESP-IDF, LVGL):** the budget is LVGL's refresh period,
  and both the drawing and the transfer to the panel fit in it (§7.1).
- **Values that change every frame bypass the UI framework's re-render** — an animated value, not a state update per
  frame.
- **Blur costs by radius times area** — keep animated blur small. **Web:** promote an element to its own compositing
  layer (`will-change: transform`) only to fix a dropped frame that was seen, on that element.
- **Work nobody can see stops** — loops, video and canvases pause off-screen and in the background.
- **Content is visible if the animation never runs** — the hidden state belongs to the animation's start, not to the
  element's resting style; reduced motion or a failed script must never hide content.
- **Measure the build people get, on the device class they hold** — a release build on a mid-range phone, recorded
  and scrubbed frame by frame (web.dev, "How to create high-performance CSS animations"; MDN, "CSS and JavaScript
  animation performance"). **Embedded (ESP-IDF, LVGL):** the production board with the production `sdkconfig` —
  compiler optimisation, CPU, flash and PSRAM speed — and the radios (Wi-Fi, Bluetooth) running as they do in use.

### 7.1 The frame budget on an embedded display (ESP-IDF, LVGL)

**On a device, the cost of a frame is the area that changed: the CPU draws every changed pixel and sends it to the
panel, with no compositor to move a finished layer.**

- **Each frame, LVGL redraws only the areas marked invalid** — a moving object marks where it was and where it is,
  so a small thing moving is cheap, and anything that changes the whole screen — a fade, a slide, a full-screen
  gradient shifting — redraws and sends every pixel, every frame.
- **The refresh period caps the frame rate.** `LV_DEF_REFR_PERIOD` (33 ms by default, so at most 30 fps) is the
  display refresh, the input read and the animation step together; lowering it raises the ceiling, and input reads and
  animation steps then run as often, which costs CPU. Espressif's own tuning sets it to 10–15 ms with
  `CONFIG_FREERTOS_HZ=1000` (Espressif, "LCD & LVGL Performance", esp_lvgl_port; ESP-FAQ, LCD).
- **The bus caps a full-screen change.** Sending a frame takes width × height × bytes per pixel × 8 ÷ (bus clock ×
  data lines): a 320 × 240 RGB565 frame on a 40 MHz single-line SPI bus takes about 31 ms, so a full-screen move there
  cannot pass 30 fps however fast the drawing is; QSPI's four lines take a quarter of that (derived). A small area
  sends in a fraction of it.
- **Layers cost memory and time.** `opa_layered`, `blend_mode` and `bitmap_mask_src` draw the widget into a simple
  layer in chunks of `LV_DRAW_LAYER_SIMPLE_BUF_SIZE`; `transform_scale_x`/`_y`, `transform_rotation` and skew draw
  it into a transform layer the size of the transformed area, which cannot be chunked, then resample every pixel
  (LVGL, "Draw layers"). Plain `opa` needs no layer but mixes each part on its own, so overlapping children show
  through one another.
- **Draw buffers decide the speed.** Buffers in internal, DMA-capable RAM are the fastest; a buffer under about 10 %
  of the screen slows drawing badly, above about 25 % gains little, and two buffers let the next area draw while the
  last one sends. A buffer in PSRAM is slower, and SPI DMA cannot read PSRAM, so the driver copies through internal
  RAM (esp_lvgl_port's `buff_dma`, `buff_spiram`, `trans_size`; Espressif, "LCD & LVGL Performance";
  ESP-Techpedia, SPI/QSPI LCD summary).
- **A full-refresh or direct mode changes the sums** — `full_refresh` redraws the whole screen every frame, so a small
  move costs as much as a fade; know which mode the project's display port uses before judging a move cheap.
- **A pixel accelerator moves the line, not the rule** — on a chip with one (the ESP32-P4's PPA, `LV_USE_PPA`), fills,
  blends and transforms get cheaper, and the area changed still sets the cost.

| Move | Cost each frame | Instead |
| --- | --- | --- |
| A small object sliding or fading | Its old and new area | — the cheap case |
| A full-screen fade (`LV_SCREEN_LOAD_ANIM_FADE_*`, `lv_obj_fade_in` on the screen) | Both screens drawn, every pixel blended and sent | A cut, a slide, or a fade of only the area that changes |
| A full-screen slide | Every pixel drawn and sent | Keep it for navigation that needs direction; keep it short |
| A scale or rotation | A transform layer the widget's size, every pixel resampled | Scale only small things; enter by a short translate with opacity rising |
| An animated shadow, gradient or blur | Redrawn over its whole area | Animate the object, keep the decoration still |
| Width or height | The widget and its children laid out and redrawn | Move by position; reveal by moving the content inside a fixed-size parent that clips it |

## 8. Reduced motion

**Design the reduced variant of every move: travel goes, the change of state stays.**

- **Remove travel** — position, scale, rotation, parallax, zoom and page slides; **keep** a short fade or colour change
  that carries meaning; **drop** motion that is purely decorative.
- **Driven motion and wait indicators keep moving** — a drag still tracks, a spinner still turns.
- **An essential sequence steps between its key states** rather than vanishing.
- **Loops and autoplay do not start; a paused loop rests on a frame that shows what it is.**
- **The reduced variant is approved by watching it with the setting on**, beside the full one in the motion study.
- **Some floors hold under every setting, not only reduced motion** — anything that moves on its own for more than
  5 s can be paused, nothing flashes more than three times a second, and anything that dismisses itself respects the
  time-limit floor. They, and each platform's setting, are the `accessibility` skill's; the product's own reduced
  variant of each surface is in its brief.
- **Web, iOS, Android:** the reduced variant follows the system's setting — **Web:** the `prefers-reduced-motion`
  media query.
- **Embedded (ESP-IDF, LVGL): build the reduced variant in one helper** — the setting itself is the product's own and
  `ACCESSIBILITY §8` holds it. Every `lv_anim_t` and style transition starts through one helper that reads it and
  turns each move into its reduced variant: travel becomes a short fade, or a cut — `lv_anim_path_step`, or a
  duration of 0 for a change that lands at once — while drags and wait indicators keep moving. The variant is decided
  in that one place, not per screen.

## 9. The motion brief

**Before a motion study is drawn, an interview fills a short brief; no field is left blank.**

| Field | Settled by |
| --- | --- |
| The change | The two states and the trigger, read from the repo — never asked |
| Frequency | How often one person meets it in a session; constant repeat ends the brief at "no motion" |
| Purpose | One of the five in §1; none ends the brief at "no motion" |
| Properties | Which differ between the two states, and only those |
| Origin and direction | Where it comes from and goes; the reverse path |
| Interruption | What happens if retriggered or reversed mid-way |
| Feel | A reference the person names, or a choice between two — never a number asked for; the curve and duration proposed from the brief's tokens |
| Reduced motion | What the move becomes with the setting on |
| Edges | Many items, a slow device or the frame rate an embedded display reaches, loading, right-to-left |

- **One question at a time, each with a recommended answer**; an unanswered question takes the recommendation, marked
  *assumed*.
- **Recon before questions** — the tokens, what sibling surfaces do, how reduced motion is handled — read from the repo.
- **The brief sits beside the study** (`<screen>_motion<n>.md` beside the GIF or video) and is what the person approves
  with it.

## 10. Debugging motion

**Reproduce on the target, record, scrub it slowed down, name the symptom, change one thing, compare.**

| Symptom | Usual causes, most likely first |
| --- | --- |
| Feels slow | A slow-start curve; a duration too long for its size; a delay before the response |
| Feels lifeless or robotic | Linear on a move; symmetric enter and exit; no origin |
| Feels cheap | Growing from zero; several clocks on one object; overshoot without a gesture |
| Stutters, drops frames | A costly property animating; work on the main thread; a large blur; too many layers |
| Jumps or snaps | A timeline restarting instead of retargeting; a size animated without measuring; a layout shift |
| Exit does not play | The element removed before its exit ran |
| Fires wrongly or flickers on hover | The hovered element moving itself; a hover firing on touch |
| Embedded: smooth for small moves, stutters on full-screen ones | The bus cannot send a full frame in one refresh period; a full-refresh buffer mode; draw buffers in PSRAM (§7.1) |
| Embedded: every animation stalls at once | Work in the LVGL task — an event callback that decodes, writes flash or waits; a refresh period quantised up by a slow FreeRTOS tick |
| Embedded: a slanted tear across a moving edge | The transfer is not synchronised to the panel's own refresh (its tearing-effect signal) |
| Embedded: moves at constant speed and stops dead | The `lv_anim_t` has no path, so it runs `lv_anim_path_linear` (§2) |

- **Change one variable at a time — curve before duration** — re-record, and compare side by side with the previous
  recording and a reference.
- **Embedded (ESP-IDF, LVGL): measure on the device, and film the panel.** `LV_USE_SYSMON` with
  `LV_USE_PERF_MONITOR` shows the frame rate and CPU load on screen (`LV_USE_PERF_MONITOR_LOG_MODE` sends them to the
  log instead); `LV_USE_REFR_DEBUG` paints each redrawn area so a move's cost is visible; `LV_USE_LAYER_DEBUG` marks
  every layer. Log a frame's drawing and transfer time with `esp_timer_get_time()` around the flush. A screenshot and a
  desktop simulator show neither the frame rate nor tearing — film the panel with a phone's slow-motion camera
  (240 fps) and scrub that recording.
- **Confirm at full speed, then again with fresh eyes**; when nothing fits, ask again whether it should move at all.
- **Each cause found is a lesson for the repo**, not just a fix.

## 11. Reviewing motion

**A review checks each moving thing against §1–§8, ranks accessibility first, and prefers removing over adding.**

| Category | Asks |
| --- | --- |
| Purpose and frequency | Does it have a purpose from §1; is it on something met constantly? |
| Easing and duration | Right curve for the journey; time fits the size; exit shorter; no delay on a response |
| Space and origin | Grows from its trigger; leaves the way it came; one object throughout |
| Choreography | One clock per object; one entrance per container; stagger short and ordered |
| Interruption | Retargets from where it is; drags track the finger |
| Rendering | Cheap properties, named; nothing hidden if the animation never runs; on an embedded display, the area redrawn each frame kept small (§7.1) |
| Reduced motion and the floors | A designed reduced variant; driven motion and waits still move; loops can be paused, nothing flashes, self-dismissing things respect the time limit |
| Cohesion | The same surface moves the same way everywhere |

- **Leave alone what is right by design** — a centred dialog growing from its centre, linear on a loop, a long one-time
  introduction the person approved.
- **Fix in this order**: remove the move; reduce it; change the curve; fix the origin; make it interruptible; move it
  to cheap properties; make enter and exit asymmetric; polish.
- **Accessibility findings rank first**, whatever their size.
- **Missed opportunities are reported apart from faults** — a move that would explain a change, with its purpose from
  §1.

## 12. Glossary

| Term | Means |
| --- | --- |
| Easing | How speed changes across a move |
| Decelerate (ease-out) | Fast start, slow finish — for arrivals |
| Accelerate (ease-in) | Slow start, fast finish — only for very short exits |
| Standard (ease-in-out) | Slow at both ends — for moves within the screen |
| Linear | Constant speed — for loops and time passing |
| Duration | How long a timed move runs |
| Delay | Waiting before a move starts |
| Stagger | A group moving in sequence, a short step apart |
| Choreography | The order and overlap of several moves as one composition |
| Keyframe | A set value at a point on a move's timeline |
| Transition | A move from the current value to a new target; it can be retargeted |
| Interruptible | Can be redirected mid-way without restarting |
| Spring | Physics-modelled motion with no fixed length, settling by its parameters |
| Bounce (overshoot) | Passing the target before settling |
| Damping | How quickly a spring's oscillation dies out |
| Perceived duration | When a spring looks finished, despite tiny residual motion |
| Direct manipulation | An object tracking the finger or pointer one to one |
| Transform origin | The point scale and rotation work around |
| Origin-aware | Growing out of the control that caused it |
| Object permanence | One object visibly travelling between its states |
| Shared-element transition | An item morphing from its small to its large form |
| Shared axis | Enter and exit along one direction that encodes navigation |
| Crossfade | One state dissolving into another in place |
| Morph | One shape changing into another while staying on screen |
| Press feedback | A small, immediate depression on press |
| Hover intent | A short dwell before hover acts |
| Hover flicker | A loop caused by moving the hovered element itself |
| Asymmetric timing | Different speeds for a deliberate phase and its reversal |
| Cohesion | Sub-moves sharing one timing so a component reads as one |
| Compositing | Moving or fading a layer without redoing layout or paint |
| Jank | Visible stutter from dropped frames |
| Frame budget | The time one frame may take: drawing, plus on an embedded display, sending it to the panel |
| Refresh period | How often a renderer draws a frame; on LVGL it also steps animations (§7.1) |
| Partial refresh | Redrawing and sending only the areas of the screen that changed |
| Draw buffer | The memory a renderer draws pixels into before they are sent to the display |
| Path callback | LVGL's easing curve: a function that maps elapsed time to the animated value |
| Tearing | Parts of two frames on screen at once, seen as a slanted break across a moving edge |
| Reduced motion | The setting that asks for minimal movement — the system's, or on a device, the product's own |
| Vestibular | The balance sense that large or parallax motion can upset |
