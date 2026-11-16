---
name: motion
description: How motion in a product is decided, drafted, built, debugged and reviewed, carried in the skill (references/motion.md) — whether to animate at all (frequency, purpose, budget, keyboard changes land at once), choosing a curve by the journey and a duration by size and distance, nothing growing from nothing, growing from the trigger and leaving the way it came, one clock per object and short ordered staggers, retargeting from where it is, springs and direct manipulation, cheap properties and the frame budget, the reduced variant of every move, the motion brief interview before a motion study, the debugging loop from symptom to cause, the review of a motion change, and a glossary — the principles for every platform, with guidance labelled for the web, iOS, Android and embedded ESP-IDF devices with an LVGL display (path callbacks and duration tokens, the area redrawn each frame, the refresh period, the bus, layers and draw buffers, retargeting an lv_anim, reduced motion as a product setting, measuring on the panel); plus motion_check.py for the patterns code can show, in web, native and C/C++ files. Values come from the project's own DESIGN.md. Portable — the folder works in any repo. Use when deciding whether or how something should move, drafting a motion study, building or fixing a transition, an animation, a hover or press state, a stagger, a spring or a drag hand-off, when motion feels slow, cheap, janky or jumps, when reviewing a motion change, or asked "what's it called when…".
metadata:
  scope: portable
---

# Motion

How a product's motion is decided and checked. The principles and their reasons are kept in this skill at
[references/motion.md](references/motion.md) (cited `MOTION §n`); this page indexes them in one-line rules and holds
the steps: the motion brief, the study, the build, the debugging loop and the review. The values — the product's
durations, curves, scales, its ceiling on how long a move may run, and what each surface does when it enters and
leaves — are the project's own, in its `DESIGN.md`; that file wins over the reference, and the reference over this
page.

**Platforms.** The rules below hold on every platform. Guidance for one platform is labelled **Web**, **iOS**,
**Android** or **Embedded (ESP-IDF, LVGL)** here and in the reference; an embedded display's frame budget is MOTION
§7.1.

**Portable.** This folder is self-contained and links to nothing outside itself (it names the rest of a kit in
backticks): the reference and the motion check ([scripts/motion_check.py](scripts/motion_check.py)). Copy it into any
repo's `.agents/skills/` (or `.claude/skills/`) and it works there: the check reads `UI_PATHS` from
`.agents/project.py` when the repo has one, and scans every tracked UI file when it does not — web, native, and C or
C++ for firmware, outside vendored folders such as `node_modules/` and `managed_components/`. It needs git and Python
3.9+. It reads the project's `DESIGN.md` for values and never assumes them; with no brief, it asks the person for the
few values a change needs and proposes adding them to one. In the agent-harness kit, the `ui-designer` skill and agent
apply it at their gates, the `accessibility` skill holds the floors on motion, and `verify.py run` runs the check.

## When to use

- Deciding whether something should move, or how — before drawing a motion study.
- Building or changing a transition, an animation, a hover or press state, a stagger, a spring, a drag's release.
- Motion feels slow, lifeless, cheap or janky, jumps, skips its exit or misfires on hover.
- Reviewing a change that moves anything.
- Naming an effect — "what's it called when…" (MOTION §12).

## Rules

### Do

1. **Decide whether it moves before how** — frequency first; anything met many times a session changes instantly
   (MOTION §1).
2. **Give every move a purpose** — feedback, origin, a changed state, softening, or explaining; otherwise no motion
   (MOTION §1).
3. **Land keyboard-driven changes at once** — focus and selection never trail the key (MOTION §1).
4. **Pick the curve by the journey, then the duration by size and distance** — from the project's named curves and
   durations, never an ad-hoc value (MOTION §2, §3).
5. **Make exits shorter than entrances, and start feedback within a tenth of a second**, with no delay before a
   response (MOTION §3).
6. **Grow from near full size and from the trigger; leave the way you came** — direction encodes navigation, mirrored
   right to left (MOTION §4).
7. **Keep one object one object** — an item opening into a view expands from where it sits (MOTION §4).
8. **Give a press a felt response, a hover a smaller one, and move a hovered element's content, never the element**
   (MOTION §4).
9. **Move one object on one clock, enter one container once, and keep a stagger short, ordered and never blocking**
   (MOTION §5).
10. **Retarget from where it is; let drags track the finger and spring from the release velocity** (MOTION §6).
11. **Animate only cheap properties, named one by one, and keep content visible if the animation never runs**
    (MOTION §7).
12. **Measure on the device people hold, in the build they get** — a mid-range phone in a release build; on an
    embedded device, the production board and `sdkconfig` — before calling motion smooth (MOTION §7).
13. **Design the reduced variant of every move** — travel goes, the change of state stays, driven motion and waits
    keep moving (MOTION §8; the `accessibility` skill holds the floors).
14. **Fill the motion brief before drawing the study**, one question at a time, each with a recommended answer
    (MOTION §9).
15. **Debug by recording, scrubbing slowed down and changing one thing at a time, curve before duration**
    (MOTION §10).
16. **Embedded (ESP-IDF, LVGL): keep the area that changes each frame small** — a small thing moving is cheap, a
    full-screen fade, scale or rotation is not; know the refresh period, the bus and the buffer mode (MOTION §7.1).
17. **Embedded (ESP-IDF, LVGL): give every `lv_anim_t` the brief's path and duration, and retarget it from its
    current value** — `lv_anim_start` replaces the running one (MOTION §2, §3, §6).
18. **Embedded (ESP-IDF, LVGL): build every move's reduced variant in the one helper that starts animations** — a
    short fade or a cut in place of travel; the setting it reads is the `accessibility` skill's (MOTION §8).
19. **Embedded (ESP-IDF, LVGL): judge motion on the panel** — the performance monitor, the redrawn areas, a
    slow-motion recording of the screen; never a screenshot or the simulator (MOTION §10).

### Never

- **Animate on first paint something that was already there**, or replay a one-time introduction (MOTION §1).
- **Start an arrival, a hover or a press with a slow-starting curve** — an exit may accelerate (MOTION §2).
- **Grow an entrance from zero scale** (MOTION §4).
- **Animate every property, or a layout property** — width, height, top, left, margin, padding (MOTION §7).
- **Restart a retriggerable move from its first frame** (MOTION §6).
- **Use a duration, curve or scale the project's DESIGN.md does not name** — propose it there first.
- **Claim motion feels right from code or a still** — feel, speed and smoothness are seen on the target, in motion.
- **Embedded (ESP-IDF, LVGL): leave something that travels on the linear path** — `lv_anim_init`'s default and every
  `lv_screen_load_anim` slide (MOTION §2).
- **Embedded (ESP-IDF, LVGL): fade the whole screen** — both screens drawn and every pixel blended and sent, each
  frame (MOTION §7.1).
- **Embedded (ESP-IDF, LVGL): do slow work in the LVGL task** — it stops every animation (MOTION §7).

## Procedure

### Deciding motion — the brief

1. **Read before asking** — the two states and the trigger, the project's DESIGN.md motion tokens and its rules for how
   each surface enters and leaves, what sibling surfaces do, how reduced motion is handled (MOTION §9).
2. **Ask frequency and purpose first** — either can end the brief at "no motion", which is a complete answer: record
   it as a decision.
3. **Settle the rest one question at a time, each with your recommendation** — properties, origin and direction,
   interruption, feel (a reference or a choice between two, never a number), reduced motion, edges. An unanswered
   question takes the recommendation, marked *assumed*.
4. **Write the brief** beside the study as `<screen>_motion<n>.md`; no field blank.

### Drafting the study

1. **Draw the move at real speed** in the project's tokens — a GIF or a video, the full and the reduced variant side by
   side, plus a slowed copy for reading the curve.
2. **Show it with its brief and take the person's yes** — in the kit, `verify.py approve <file> --kind motion`. A still
   cannot approve timing.
3. **For a gesture, prototype it on the device** — a video approves timing, not how a drag feels under the finger.

### Building and fixing

1. **Build from the approved study's values**, each a token from DESIGN.md; a change of timing is a new study.
2. **Run the motion check** (below) and the project's own checks.
3. **When it feels wrong, run the debugging loop** (MOTION §10): reproduce on the target, record, scrub, name the
   symptom, change one variable, compare. Record each cause found as a lesson.

### Reviewing a motion change

1. **Walk every moving thing through the review categories** (MOTION §11): purpose and frequency, easing and duration,
   space and origin, choreography, interruption, rendering, reduced motion, cohesion.
2. **Leave alone what is right by design**; **rank accessibility first**; prefer removing over adding.
3. **Report missed opportunities apart from faults**, each with its purpose.
4. **Hand the feel to the person** — what to watch on the target, at full speed and with reduced motion on.

## Checks

```sh
python3 .agents/skills/motion/scripts/motion_check.py            # every UI file, against the baseline
python3 .agents/skills/motion/scripts/motion_check.py <file> …   # the files a change touched
```

- [ ] (script) **M1** every property animates — 0 hits
- [ ] (script) **M2** an entrance from zero scale — 0 hits
- [ ] (script) **M3** an ease-in curve where it may start an arrival, a hover or a press — 0 hits
- [ ] (script) **M4** a layout property animated — a transition list, a keyframe, `transition-[…]` — 0 hits
- [ ] (script) **M5** a hovered element that moves itself — 0 hits
- [ ] (script) **M6** smooth scrolling with no reduced-motion check — 0 hits
- [ ] (script) **M7** Embedded: a duration written as a number — `lv_anim_set_duration(&a, 300)`, a style
  transition's, `lv_obj_fade_in`'s or `lv_screen_load_anim`'s time — 0 hits
- [ ] (script) **M8** Embedded: something that travels on the linear path — an `lv_anim_t` moving x, y or translate
  with no path or `lv_anim_path_linear`, an `lv_screen_load_anim` slide — 0 hits
- [ ] (script) **M9** Embedded: a full-screen opacity fade — a FADE screen load, `lv_obj_fade_in/out` on the screen or
  the top layer — 0 hits
- [ ] The run read the UI files you expected — its last line counts the files it read, by kind (web, native,
  C/C++); a named file it "cannot be read" or that is "not a UI file" is not counted; "read no UI files" means
  nothing was checked
- [ ] Every move has a frequency and a purpose in its brief (Do 1, Do 2)
- [ ] Curves and durations are the project's tokens, exits shorter (Do 4, Do 5)
- [ ] Origin, direction and one object throughout (Do 6, Do 7)
- [ ] Retargets, never restarts; drags track the finger (Do 10)
- [ ] A reduced variant designed and watched with the setting on (Do 13)
- [ ] The feel handed to the person for the target — never claimed from code
- [ ] Embedded: the area redrawn each frame seen small (`LV_USE_REFR_DEBUG`) and the frame rate measured on the panel
  (Do 16, Do 19)
- [ ] Embedded: every move's reduced variant built in the one helper and watched with the setting on (Do 18)

M2 and M3 skip an exit — a CSS rule whose selector names leaving (exit, leave, out, dismiss; never a state such as
closed, which also governs the arrival), elsewhere a line that does; M5 reads only a rule whose last selector is the
hovered element; M6 is per file and ignores a query in a comment; the web checks read CSS, Tailwind classes and JS
objects, the native ones SwiftUI and Compose names. M7–M9 read C and C++ files (`.c`, `.cc`, `.cpp`, `.cxx`, `.h`,
`.hh`, `.hpp`, `.hxx`) and skip their comments, never a `/*` inside a string, and the web and native rules do not run
there; M7 passes a duration of 0 and any argument that names something; M8 reads one `lv_anim_t` from
`lv_anim_init` to `lv_anim_start` in one file, sees a path set by `lv_anim_set_path_cb` (`name`, `ns::Name`,
`&name`) or `a.path_cb =`, knows only LVGL's own x, y and translate setters (bare, `&`-taken or cast) — a
project-defined exec callback such as `anim_x_cb` is not followed — and skips a loop; M9 cannot see a hand-written
opacity animation on a full-screen object. A sanctioned hit carries `motion-exception` on its line with
the reason. The check cannot see a curve that feels wrong, a missing origin, a restart instead of a retarget or a
dropped frame — the study, the recording and the target find those.

## Traps

- **The drawer jumps when tapped twice quickly** → a keyframe timeline restarts on each toggle → a transition that
  retargets from the current position (Do 10).
- **The menu feels slow though its duration is short** → an ease-in curve holds back the first frames → a decelerate
  curve (Do 4).
- **A card flickers on hover** → the card itself translates out from under the pointer → move its content (Do 8).
- **Content is missing with reduced motion on** → the resting style hides it and only the animation reveals it → put
  the hidden state in the animation's start (Do 11).
- **It is smooth on the laptop and stutters on the phone** → measured on a fast machine in a debug build → a release
  build on a mid-range phone (Do 12).
- **The list takes a second to appear** → a long stagger across every item → a short step, the lead first, the rest
  together (Do 9).
- **Embedded: a panel moves at constant speed and stops dead** → the `lv_anim_t` has no path set, so it runs
  `lv_anim_path_linear` → the brief's decelerate path (Do 17).
- **Embedded: a retriggered move jumps back before it runs** → the new `lv_anim_t` starts from the original start
  value → start from the current value; `lv_anim_start` replaces the running one (Do 17).
- **Embedded: small moves are smooth and screen changes stutter** → a full-screen change redraws and sends every pixel,
  more than the bus carries in one refresh period → a cut or a shorter slide, buffers in internal DMA RAM (Do 16).
- **Embedded: every animation freezes for a moment** → slow work in the LVGL task → move it to another task (MOTION §7).

## Sources

| Topic | Where |
| --- | --- |
| The principles, the brief, debugging, review, glossary | [references/motion.md](references/motion.md) |
| Purpose, easing, duration, transitions, springs | Material Design 3 (Motion); Apple Human Interface Guidelines (Motion) |
| Fluid, interruptible motion and springs | Apple WWDC 2018, "Designing Fluid Interfaces"; WWDC 2023, "Animate with springs" |
| Response times | Nielsen Norman Group, "Response Times: The 3 Important Limits" |
| Rendering cost | MDN, "CSS and JavaScript animation performance"; web.dev, "How to create high-performance CSS animations" |
| Embedded: animations, paths, style transitions, layers | LVGL 9 source and docs — `lv_anim.h`, `lv_anim.c`, `lv_style.h`, `lv_obj_style.c`, `lv_display.c`, "Draw layers", `lv_conf.h` (`LV_DEF_REFR_PERIOD`, `LV_USE_PERF_MONITOR`, `LV_USE_REFR_DEBUG`); renamed functions in its `api_map` headers |
| Embedded: the frame budget on an ESP chip | Espressif, "LCD & LVGL Performance" (esp_lvgl_port); ESP-FAQ, LCD; ESP-Techpedia, "SPI/QSPI Interface Screen Related Issues Summary" |
