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

**Stability.** Cite this doc as `MOTION §n`. Do not renumber; add new material under the next free number.

| § | Section | Look here for |
| --- | --- | --- |
| 1 | [Whether to animate](#1-whether-to-animate) | Frequency, purpose, the budget, first paint, keyboard changes |
| 2 | [Easing](#2-easing) | Choosing a curve by the journey; curve before duration |
| 3 | [Duration](#3-duration) | Time by size and distance; exits shorter; floors; no delay on a response |
| 4 | [Space and origin](#4-space-and-origin) | Nothing from nothing, growing from the trigger, direction, object permanence, press and hover |
| 5 | [Choreography](#5-choreography) | One clock per object, one entrance per container, stagger, asymmetric timing, one personality |
| 6 | [Interruption and physics](#6-interruption-and-physics) | Retargeting from where it is, springs, direct manipulation |
| 7 | [Rendering and performance](#7-rendering-and-performance) | Cheap properties, the frame budget, measuring, content visible without motion |
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
- **Keyboard-driven changes land at once** — arrow navigation, a shortcut, focus moving: the focus or selection
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

## 7. Rendering and performance

**Animate only what the renderer can move cheaply, name what animates, and measure on the device people hold.**

| Platform | Cheap — moved without re-layout | Costly — re-lays out or repaints every frame |
| --- | --- | --- |
| Web | `transform` (translate, scale, rotate), `opacity`, `clip-path` | Width, height, top, left, margin, padding, font size; animated shadows and large blurs |
| iOS | A view's or layer's transform and opacity | Its frame or constraints, animated every frame |
| Android (Compose) | `graphicsLayer` — translation, scale, rotation, alpha | Size, padding and other modifiers that re-measure |
| Android (Views) | `translationX/Y`, `scaleX/Y`, `rotation`, `alpha` | `LayoutParams` changed every frame |

- **Name each property that animates** — "everything that changes" drags unrelated properties along (web: never
  `transition: all`).
- **Motion during busy work runs where it cannot be blocked** — the browser's compositor, iOS Core Animation's render
  server, Android's RenderThread.
- **When the look calls for a costly property, draw the same picture with a cheap one** — grow by scale, move by
  transform, cross-fade two shadows instead of animating one.
- **A moving element does not push its neighbours** unless their reflow is the meaning (a list reordering).
- **The frame budget is one frame at the screen's refresh rate** — about 16 ms at 60 Hz, 8 ms at 120 Hz — on a
  mid-range phone, not the development machine.
- **Values that change every frame bypass the UI framework's re-render** — an animated value, not a state update per
  frame.
- **Blur costs by radius times area** — keep animated blur small; promote an element to its own layer only to fix a
  dropped frame that was seen, on that element.
- **Work nobody can see stops** — loops, video and canvases pause off-screen and in the background.
- **Content is visible if the animation never runs** — the hidden state belongs to the animation's start, not to the
  element's resting style; reduced motion or a failed script must never hide content.
- **Measure the build people get, on the device class they hold** — a release build on a mid-range phone, recorded
  and scrubbed frame by frame (web.dev, "How to create high-performance CSS animations"; MDN, "CSS and JavaScript
  animation performance").

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
| Edges | Many items, a slow device, loading, right-to-left |

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

- **Change one variable at a time — curve before duration** — re-record, and compare side by side with the previous
  recording and a reference.
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
| Rendering | Cheap properties, named; nothing hidden if the animation never runs |
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
| Reduced motion | The system setting that asks for minimal movement |
| Vestibular | The balance sense that large or parallax motion can upset |
