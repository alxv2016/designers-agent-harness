# Feedback

What a product makes felt, heard or lit, beyond the screen, when the person acts and when something happens: one small
vocabulary of events, when each fires, what never to do, how a press, a wait and an outcome are answered, status
lights on a device, and how the channels pair. People read it to choose the feedback for an event; coding agents read
it, through the `touch-and-gesture` skill, before they add a haptic, a sound or a light, or answer a press that starts
work.

**Where it lives.** In the `touch-and-gesture` skill, beside the touch reference (`references/touch.md`, cited
`TOUCH §n`) and [its SKILL.md](../SKILL.md). The skill folder is self-contained: copy it into any repo's
`.agents/skills/` and this reference comes with it. The product's own values — which events it gives a feel or a
light, its patterns, its colours, its timings and brightness — live in its design brief (`DESIGN.md` in the
agent-harness kit).

**Sources of truth.** Apple Human Interface Guidelines, Playing haptics; Android Developers, haptics design principles
and `HapticFeedbackConstants`; the W3C Vibration API (MDN, `Navigator.vibrate`); Nielsen Norman Group, "Response
Times: The 3 Important Limits". The design brief wins for the product's values, this reference for which event gets
which feedback and why.

**What it builds on.** The floors are the `accessibility` skill's: colour never the only signal (`ACCESSIBILITY
§2`), flashing and motion (`ACCESSIBILITY §8`) and status messages announced in words (`ACCESSIBILITY §10`). The
wait indicator's timings and a data view's states are the design brief's (`DESIGN_BRIEF §12`, `DESIGN_BRIEF §13`).
This doc does not restate them. The pressed look on a control is `TOUCH §5`'s.

**Platforms.** Each principle is stated once, for every platform. How a platform builds it is labelled **Web**,
**iOS**, **Android** or **Embedded (ESP-IDF, LVGL)**, in a bold lead or a table column. Status lights are an embedded
concern: most web and phone products have none.

**Stability.** Cite this doc as `FEEDBACK §n`. Do not renumber; add new material under the next free number.

| § | Section | Look here for |
| --- | --- | --- |
| 1 | [Principles](#1-principles) | Supplement the screen; one event, one feel; each channel alone; the person's settings |
| 2 | [The vocabulary](#2-the-vocabulary) | The event types, their feel, and each platform's matching effect |
| 3 | [When feedback fires](#3-when-feedback-fires) | After the input is accepted, within about 100 ms; success only once it happened |
| 4 | [Haptics to avoid](#4-haptics-to-avoid) | Strong steps, repeats while waiting, background updates, patterns nobody tells apart |
| 5 | [Pending, done and failed](#5-pending-done-and-failed) | Answering a press, showing a wait, saying the outcome, giving the controls back |
| 6 | [Status lights](#6-status-lights) | A device's lights: the vocabulary, the priority order, timing, brightness |
| 7 | [Pairing haptics and lights](#7-pairing-haptics-and-lights) | One accepted event, both channels; what is never paired |
| 8 | [Platform tools](#8-platform-tools) | Each platform's haptic API, its limits, and the device's own drivers |

---

## 1. Principles

**Feedback confirms what the screen already shows; it never carries information of its own.**

- **Supplement the screen, never replace it** — everything a haptic, a sound or a light says is also on the screen in
  words or a visible state; an error, a warning or a notice is never told by vibration or a light alone. Why: the
  person may not be holding or looking at the device, may have haptics or lights off, or may not tell colours apart.
- **Each channel stands without the other** — with haptics off the screen and the light still say it; with the light
  out of sight the screen and the haptic do.
- **One event type, one feel, everywhere in the product** — feedback belongs to the kind of interaction, not to the
  screen or the feature, so a person learns it once (Android, haptics design principles: be consistent).
- **Feedback is subtle** — noticeable in the hand or on a desk, never startling, and tuned on the device rather than
  from a datasheet or a simulator.
- **Strength follows importance and frequency** — the more often an event happens, the lighter its feel; a rare,
  important outcome may be stronger (Android, haptics design principles).
- **The person's settings apply to everything** — the system's haptics and sound settings, and on a device the
  product's own switches and strength; only the person's own controls change them.
- **The accessibility floors hold** — flashing and motion limits (`ACCESSIBILITY §8`); a status change announced in
  words (`ACCESSIBILITY §10`).

## 2. The vocabulary

**A small set of event types, each with one feel; never one pattern per feature. An event with no chosen pattern stays
silent.**

| Event | Feel | iOS | Android | Embedded (ESP-IDF, LVGL) |
| --- | --- | --- | --- | --- |
| A step or detent — a picker value, a slider step, a knob's detent | Very light, short tick | `UISelectionFeedbackGenerator` | `SEGMENT_TICK`, `SEGMENT_FREQUENT_TICK`, `CLOCK_TICK` | The actuator's lightest effect, one per step, a fast run collapsed |
| A press accepted | Light, short click | `UIImpactFeedbackGenerator` (`.light`) | `VIRTUAL_KEY`, `KEYBOARD_TAP` | A short click |
| A switch turned | Light, short click | `UIImpactFeedbackGenerator` | `TOGGLE_ON`, `TOGGLE_OFF` | A short click |
| A long press acting | Distinct from the tap | `UIImpactFeedbackGenerator` (`.medium`) | `LONG_PRESS` | A firmer click |
| A threshold crossed in a drag — a pull to refresh armed, a swipe ready to commit | Light, once each way | `UIImpactFeedbackGenerator` | `GESTURE_THRESHOLD_ACTIVATE`, `GESTURE_THRESHOLD_DEACTIVATE` | A short click |
| Open or close a surface | Soft, or the feel of the press that caused it | — | — | The click of the press that caused it |
| Success | Slightly more expressive | `UINotificationFeedbackGenerator` (`.success`) | `CONFIRM` | A short two-part pattern |
| Error or failure | Distinct, restrained | `UINotificationFeedbackGenerator` (`.error`) | `REJECT` | A short restrained pattern, unlike success |
| Attention needed | Distinct, never alarming | `UINotificationFeedbackGenerator` (`.warning`) | — | A short pattern, repeated at most once |
| A destructive action confirmed | Neutral — the press's own click, never celebratory | The press's | The press's | The press's |

- **A new event takes an existing type's feel** before it gets a pattern of its own; a new pattern is tuned on the
  device and recorded in the design brief first.
- **Web**: there is no portable haptic channel (§8), so the vocabulary is carried by the screen and, where the product
  has it, sound.
- **Prefer the platform's named effects** — they stay consistent with the system and fall back on hardware that
  cannot play a richer effect (Android, haptics design principles; Apple HIG, Playing haptics).

## 3. When feedback fires

**Feedback follows the input once the system has accepted it, within about 100 ms; an outcome is signalled only once
it has happened.**

- **After acceptance, never before** — a press the product then ignores, a key a lock drops, a control that is
  disabled gives no feel; a feel for an input that did nothing teaches the person it did something.
- **Within about 100 ms** — past about a tenth of a second a response stops reading as caused by the input (Nielsen
  Norman Group, "Response Times: The 3 Important Limits"). A haptic on a press fires with the press's look (`TOUCH §5`),
  not after the work it starts.
- **Success only after it succeeded** — never when it is merely requested, sent or queued; a request that later fails
  never had a success feel.
- **The same accepted event drives every channel**, so the haptic, the sound, the light and the screen stay together
  (§7).

## 4. Haptics to avoid

**A haptic that fires too often, too strongly or without meaning teaches the person to turn haptics off.**

- **A strong vibration on every step** — a frequent event gets the lightest feel, or none (§1).
- **Repeating haptics while waiting** — a wait is shown, not buzzed (§5).
- **Haptics for background updates** — data refreshing, a sync finishing, a state the person did not cause.
- **Patterns a person cannot tell apart, or cannot act on** — two patterns that feel the same are one pattern.
- **A haptic before the input is accepted** (§3).
- **A success feel for a request, or for something rejected** (§3).
- **Long, buzzy vibrations for touch feedback** — given the choice between a buzzy effect and none, choose none
  (Android, haptics design principles: clear haptics over buzzy ones).

## 5. Pending, done and failed

**A press is answered at once, a wait says it is waiting, and the outcome says what happened in words — the person
never wonders whether the product heard them.**

| Moment | Rule | Why |
| --- | --- | --- |
| The press | Its pressed look and any feel within about 100 ms (§3) | Later, it no longer reads as caused by the press |
| A wait | A working mark, shown only once the wait is long enough not to flicker, and kept long enough once shown not to blink off as the answer lands — both values are the brief's feedback ladder (`DESIGN_BRIEF §12`) | It says the product is busy, without a flicker that reads as a glitch |
| A label that changes while waiting | Keeps its width, laid out for its longest form | A control that grows or shrinks moves its neighbours under the finger |
| Every way out of a wait | The control that started it is usable again — done, failed, cancelled or the screen left | A trigger left disabled after a failure is a dead control |
| A switch that drives slow hardware or a network | Flips at once; flips back, with a message saying why, if the action fails | The common case feels instant, and the rare refusal is still told |
| An action that cannot be undone | Shows pending, and waits for the answer before showing the outcome | A success shown before it happened cannot be taken back |
| A view of data | Each of its states drawn, as `DESIGN_BRIEF §13` lists them | A blank view says nothing |

- **The outcome is said in words** — the result on the screen, announced as a status message
  (`ACCESSIBILITY §10`), with the feel and the light that confirm it (§2, §6).
- **A wait never blocks the ways out** — back, cancel, the home control and the product's edge gestures still work
  while it waits.

## 6. Status lights

**Embedded (ESP-IDF, LVGL).** A device's status lights — a single LED or an addressable chain — say a class of event,
never details and never navigation. Most web and phone products have none.

| Concern | Rule |
| --- | --- |
| Floors | No cue relies on colour alone, and none flashes past the flash limit, as `ACCESSIBILITY §2` and `ACCESSIBILITY §8` require |
| Vocabulary | A small set of cues — accepted input, success, error, attention, information, working, connection, critical, idle — each told apart in peripheral vision by pattern, position or pulse count as well as colour; never one animation per feature |
| Priority | Cue classes are ordered: critical, error, attention, notification, success, a transient interaction cue, background and ambient. A higher class interrupts a lower one; when it ends, the lower one resumes only if it still applies |
| Stale cues | A lower cue raised under a higher one is dropped, never queued; the same cue again restarts its time rather than playing twice; repeated notifications coalesce |
| Persistent states | Disconnected, low battery and the like get a quiet, steady indication, never continuous flashing |
| Timing | Short pulses for interaction feedback, slower patterns for attention and notifications, so the two read apart |
| Background work | Never animated forever: progress is low in intensity and stops at once on completion, failure or cancellation |
| Brightness | Capped by the design brief and by the power the supply can give; the person's level scales below the cap; never glaring in a dark room |
| Critical and error | Also on the display, in words; a cue that needs action says how it is acknowledged or dismissed |
| The display | The lights never compete with the screen for attention |

- **Tune durations, pauses, colours and brightness on the device** — the vocabulary is the rule; the numbers live in
  the design brief and in the code that plays them.
- **One owner arbitrates the lights** — every screen and service asks for a cue by class; none drives the LEDs
  directly, or the priority order cannot hold.

## 7. Pairing haptics and lights

**When a device has both, they reinforce one event and never compete.**

- **Trigger both from the same accepted event**, so their timing stays together (§3).
- **Most cues carry no haptic, and most haptics no cue** — a detent or a press is felt and not lit; ambient and
  background states are lit and not felt.
- **Pair a restrained error haptic with an error cue** only when the error matters to the person.
- **Pair a light success haptic with a success cue** only for a meaningful completed action.
- **Pair attention with a soft haptic only when it warrants interrupting.**
- **Each channel stands alone** (§1): with haptics off the cue still says it; with the lights out of sight the screen
  and the haptic do.

## 8. Platform tools

**Use the platform's named effects; play a custom one only where the platform has none, and through one place in the
code.**

- **iOS**: `UIImpactFeedbackGenerator`, `UISelectionFeedbackGenerator` and `UINotificationFeedbackGenerator`
  (`.success`, `.warning`, `.error`); SwiftUI's `sensoryFeedback`; Core Haptics (`CHHapticEngine`) for custom
  patterns. Call `prepare()` before an expected event to cut its latency. The system's haptics setting applies (Apple
  HIG, Playing haptics).
- **Android**: `View.performHapticFeedback` with an action constant from `HapticFeedbackConstants` — `CONFIRM` and
  `REJECT` from API 30, `SEGMENT_TICK`, `SEGMENT_FREQUENT_TICK`, `TOGGLE_ON`, `TOGGLE_OFF`,
  `GESTURE_THRESHOLD_ACTIVATE` and `DRAG_START` from API 34; `VibrationEffect` primitives for a custom effect. Avoid
  one-shot `Vibrator.vibrate(long)` buzzes for touch feedback. Only privileged apps can ignore the person's
  touch-feedback setting from API 33 (Android Developers, `HapticFeedbackConstants`; haptics design principles).
- **Web**: `navigator.vibrate` needs a prior user gesture and is not supported in Safari or Safari on iOS, so no web
  feedback depends on it — the screen carries every event, and a vibration where it exists only adds to it (MDN,
  `Navigator.vibrate`; caniuse, Vibration API).
- **Embedded (ESP-IDF, LVGL)**:
  - **Haptics** come from the product's own actuator and its driver — an ERM or LRA motor behind a haptic driver chip
    — called from the accepted event (§3), never from a draw or a scroll-step callback. One module owns the actuator,
    plays the vocabulary (§2) by event, holds the person's switch and strength, and collapses a burst of requests to
    what the actuator can play.
  - **A knob's detent tick is the one frequent haptic that earns its place**, because it is the knob's feel — one per
    detent, a fast spin collapsed.
  - **Lights** come from the product's LED driver — an addressable chain through Espressif's `led_strip` component, or
    plain GPIO or LEDC for a single LED — behind the one owner that arbitrates them (§6).
  - **Settings**: the product holds the on and off, and the strength, that a phone's system setting holds.
