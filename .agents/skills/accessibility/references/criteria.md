# Accessibility

The accessibility floors any product with an interface meets, and how to meet and test each one on the web, iOS and
Android. The floor is WCAG 2.2 at level AA, cited `WCAG <n.n.n>`; where a platform's own guidelines ask for more
(Apple's Human Interface Guidelines, Material Design), the more is named beside it. People read it to know what a
screen owes the people using it; coding agents read it, through the `accessibility` skill, before they draw, build or
review a screen.

**Where it lives.** In the `accessibility` skill, beside the steps and checks that apply it —
[its SKILL.md](../SKILL.md). The skill folder is self-contained: copy it into any repo's `.agents/skills/` and this
reference, the contrast script and the accessibility check come with it. A project that sets a floor above AA writes
it in its own design brief (`DESIGN.md` in the agent-harness kit), and that floor wins over this one.

**Stability.** Cite this doc as `ACCESSIBILITY §n`. Do not renumber; add new material under the next free number.

| § | Section | Look here for |
| --- | --- | --- |
| 1 | [Scope](#1-scope) | The level, the platforms, what a project may add, the AAA criteria worth adopting |
| 2 | [Contrast and colour](#2-contrast-and-colour) | Text, non-text, the colour actually painted, states, themes, the only exemptions |
| 3 | [Text size and reflow](#3-text-size-and-reflow) | Resizing, reflow, text spacing, zoom |
| 4 | [Structure, names and labels](#4-structure-names-and-labels) | Semantics, names, roles, states, alternatives, titles, language |
| 5 | [Keyboard and focus](#5-keyboard-and-focus) | Reaching everything, focus order and visibility, modals, hidden content, composite widgets, shortcuts |
| 6 | [Pointer, touch and gesture](#6-pointer-touch-and-gesture) | Target size, alternatives to gestures and drags, acting on release, hover, orientation, device motion |
| 7 | [Content on hover or focus](#7-content-on-hover-or-focus) | Tooltips and popovers that can be dismissed, hovered and kept |
| 8 | [Time, motion and flashing](#8-time-motion-and-flashing) | Time limits, auto-moving content, flashing, reduced motion on each platform |
| 9 | [Forms and errors](#9-forms-and-errors) | Labels, input purpose, errors, authentication, redundant entry |
| 10 | [Status messages](#10-status-messages) | Changes announced without moving focus |
| 11 | [The walks](#11-the-walks) | The by-hand checks on the target, and what needs a real device |
| 12 | [Automated tools](#12-automated-tools) | What each platform's auditors catch, and what they cannot |
| 13 | [Media, consistency and links](#13-media-consistency-and-links) | Captions and audio description, sensory instructions, audio control, link purpose, consistent navigation and help |

---

## 1. Scope

**Every screen meets WCAG 2.2 level AA, on every platform the product ships, in every theme.** AA is the level laws
and procurement rules cite (the EU's EN 301 549, the US Section 508, the European Accessibility Act), and the level the
platforms' own guidelines assume.

- **WCAG is written for the web and applies to native apps too.** The W3C's guidance on applying WCAG to mobile and
  non-web software maps each criterion to native screens; this doc gives the web, iOS and Android way side by side.
- **A platform that asks for more sets the size to aim for on that platform** — Apple asks 44 × 44 pt targets and
  Material 48 × 48 dp where WCAG asks 24 × 24 CSS px (§6). A project's design brief decides whether it adopts each
  platform's size; its auditors (Android's Accessibility Scanner at 48 dp) flag what falls under it.
- **A project's design brief may set a floor above AA, never below it.** The brief writes each higher floor once with
  its reason; this doc stays the AA floor every project shares.
- **Two AAA criteria are worth adopting by default**: animation from interactions can be turned off (WCAG 2.3.3, §8),
  because every platform ships a reduced-motion setting that people rely on; and targets of 44 px (WCAG 2.5.5, §6),
  because the platforms ask for it anyway. A project adopts them in its design brief.
- **§2–§10 hold the criteria a design decides; §13 lists the rest of AA** — media, consistency and links — so the
  set is complete.
- **Conformance is per screen and per state.** A screen passes only when its hover, focus, pressed, selected, error,
  empty, loading and disabled states pass too, in light and dark.

## 2. Contrast and colour

**Text needs 4.5:1 against what is painted under it; large text and anything else that carries meaning need 3:1.**
Measure the colours the screen paints, not the tokens' names.

| Criterion | The floor | How to meet it | How to test |
| --- | --- | --- | --- |
| WCAG 1.4.3 Contrast (Minimum) | Text 4.5:1; large text — 24 px regular, or 18.66 px (14 pt) bold, and up — 3:1 | Pick a colour pair that passes in each theme; a pair the product keeps painting goes in the design brief | `contrast.py <fg> <bg>`; the brief's pairs on every change |
| WCAG 1.4.11 Non-text Contrast | 3:1 for the parts of a control needed to see it is there and what state it is in (a field's border, a toggle's track, a checkbox's box), focus indicators, icons that carry meaning, chart marks | A border or fill on every control whose edge is otherwise invisible; a selected state shown by more than a 1.1:1 tint | `contrast.py --min 3 <fg> <bg>`, against each colour the part sits next to |
| WCAG 1.4.1 Use of Colour | Colour is never the only way to tell something | An error has an icon and words; a link in running text is underlined; a chart's series have labels or patterns; a required field says so | Look at the screen in greyscale: everything still reads |

- **Measure against the colour actually painted.** A translucent fill composites over what is behind it; text over an
  image is measured against the image's lightest (or darkest) region under the text, or sits on a scrim that makes the
  worst case pass. `contrast.py` composites `#rrggbbaa` over its background for you.
- **Measure every state.** Hover, pressed, selected, focused and error colours are separate pairs; a hover that dims a
  button can drop it under its floor.
- **Measure every theme.** A pair that passes in light can fail in dark, and a high-contrast mode must not lower any
  ratio.
- **Only disabled and decorative things are exempt** (WCAG 1.4.3, 1.4.11), and logotypes. A placeholder, a hint, a
  caption, a timestamp and a secondary label all carry meaning and meet 4.5:1.
- **Never make text secondary with opacity.** The painted colour then depends on what is behind it; use a colour whose
  painted value passes.
- **An icon that carries meaning on its own meets 3:1 at least; a project may hold it to the text floor** — a brief that
  paints icons with its text colours keeps them at 4.5:1.
- **A focus indicator meets 3:1 against what it touches** — the surface it sits on, and the control's own fill
  wherever the ring touches it; a ring drawn with a gap shows the surface in between (WCAG 1.4.11; 2.4.13 at AAA asks
  for a 2 px outline's area as well).

## 3. Text size and reflow

**Text resizes to 200 % and the layout reflows at 320 CSS px wide without losing anything or scrolling sideways.**

| Criterion | The floor | How to meet it | How to test |
| --- | --- | --- | --- |
| WCAG 1.4.4 Resize Text | Text scales to 200 % with nothing cut off or overlapping | Web: sizes in `rem` or `em`, containers that grow; iOS: Dynamic Type text styles; Android: text in `sp`, Compose `TextUnit.sp` | Browser zoom 200 %; iOS's largest accessibility text size; Android font scale 200 % |
| WCAG 1.4.10 Reflow | At 320 CSS px wide (400 % zoom on a 1280 px screen), one direction of scrolling for reading | One column at narrow widths; long words wrap; tables and maps may scroll on both axes, nothing else | Narrow the window to 320 px; zoom to 400 % |
| WCAG 1.4.12 Text Spacing | Line height 1.5, paragraph spacing 2×, letter spacing 0.12 em and word spacing 0.16 em break nothing | No fixed heights on text containers; no clipping | Apply the four spacings with a bookmarklet or a test stylesheet |

- **Never block pinch zoom** — no `maximum-scale=1` or `user-scalable=no` in a web viewport (WCAG 1.4.4).
- **Field text on the mobile web is 16 px or more**, or iOS Safari zooms the page when the field takes focus.
- **Text in an image neither resizes nor reflows** — images of text are in §13 (WCAG 1.4.5).
- **Truncation keeps the whole text reachable** — a truncated label has its full text in its accessible name and a way
  to see it (wrapping at large sizes, a detail view).

## 4. Structure, names and labels

**What the look says, the code says too: every element has the role, name and state a screen reader announces.**

| Criterion | The floor | How to meet it |
| --- | --- | --- |
| WCAG 1.1.1 Non-text Content | An image that carries meaning has a text alternative saying what it means; a decorative one is hidden | Web: `alt`, `alt=""` for decoration, `aria-hidden` on decorative icons; iOS: `accessibilityLabel`, `accessibilityHidden`; Android: `contentDescription`, `null` for decoration |
| WCAG 1.3.1 Info and Relationships | Headings, lists, tables, groups and landmarks are marked in code | Web: the elements themselves (`h1`–`h6`, `ul`, `th`, `nav`, `main`, `fieldset`); iOS: the header trait; Android: `heading()` semantics |
| WCAG 1.3.2 Meaningful Sequence | The reading order is the visual order | The view order is the visual order; never reorder visually with CSS `order`, absolute positioning or a reversed stack |
| WCAG 2.4.2 Page Titled | Each screen or page has a title naming it | Web: `<title>` changing with the route; native: the navigation title |
| WCAG 2.4.6 Headings and Labels | Headings and labels say what follows them | Words, not decoration |
| WCAG 2.5.3 Label in Name | A control's accessible name contains its visible label, best at its start | Voice control users say what they see: "Send" is in the name of the Send button |
| WCAG 3.1.1 Language of Page | The language is declared | Web: `<html lang>`; native: the app's localisation |
| WCAG 4.1.2 Name, Role, Value | Every control exposes its name, role and state, and changes to them | The platform's own controls; a custom one sets each by hand |

- **Use the platform's controls.** A styled container with a tap handler is not focusable, not keyed and not announced;
  a button is a button, navigation is a link.
- **Name an icon-only control for its action, not its picture** — "Close", not "X"; "Search", not "magnifying glass".
- **Hide what is decorative from assistive tech** — an icon beside a text label, a divider, a background shape.
- **State is announced** — selected, expanded, checked, disabled, busy — from the control's semantics, never from
  colour alone.

## 5. Keyboard and focus

**Everything a pointer can do, a keyboard can do, in the visual order, with focus always visible and never trapped.**

| Criterion | The floor | How to meet it |
| --- | --- | --- |
| WCAG 2.1.1 Keyboard | Every action works from a keyboard | Platform controls; a custom one takes focus and handles Enter and Space (and arrows where its pattern says) |
| WCAG 2.1.2 No Keyboard Trap | Focus can always leave, with Tab or a documented key | A modal keeps focus inside on purpose and closes with Escape |
| WCAG 2.1.4 Character Key Shortcuts | A single-key shortcut can be turned off or remapped, or works only while its control has focus | Shortcuts take a modifier; single-key ones never fire while typing in a field |
| WCAG 2.4.1 Bypass Blocks | Repeated navigation can be skipped | Web: a skip link as the first stop, landmarks; native: headings to jump by |
| WCAG 2.4.3 Focus Order | Focus moves in an order that keeps meaning | The view order is the reading order; no positive `tabindex` |
| WCAG 2.4.7 Focus Visible | The focused element shows it | Web: `:focus-visible` styles, never `outline: none` without a replacement; native: the system focus ring |
| WCAG 2.4.11 Focus Not Obscured (Minimum) | The focused element is never wholly hidden by something the page put on top | Sticky headers, footers, toasts and cookie bars leave it visible; web: `scroll-padding` |
| WCAG 3.2.1 On Focus | Taking focus changes nothing on its own | No navigation, submit or popup on focus |

- **Hidden means out of the focus order and the accessibility tree**, not just invisible. A closed drawer, an
  off-screen menu and everything behind an open modal are inert. Web: `inert`, `hidden` or `display: none`, never
  opacity 0 or an off-screen offset alone; iOS: `accessibilityViewIsModal`, hidden elements; Android:
  `importantForAccessibility="noHideDescendants"`, Compose `Modifier.semantics { hideFromAccessibility() }`
  (`clearAndSetSemantics {}` on versions without it).
- **A modal takes focus in, keeps it, closes on Escape, and hands focus back to what opened it.** It also closes on
  Android's back and iOS VoiceOver's escape gesture (a two-finger scrub). WAI-ARIA's dialog pattern sets the steps;
  web's `<dialog>` with `showModal()` does most of them.
- **When the focused thing goes away, focus moves to its neighbour** — a deleted row hands focus to the next row, not
  to the top of the page.
- **A composite widget is one Tab stop with arrows inside** — tabs, menus, listboxes, radio groups, grids and
  toolbars, with Home and End, and type-to-find in long lists (the WAI-ARIA Authoring Practices' keyboard patterns).
- **Nothing fires while an input method is composing** — with a Japanese, Chinese or Korean keyboard, Enter confirms
  the word; it does not send.

## 6. Pointer, touch and gesture

**Every target is big enough to hit, every gesture and drag has a plain alternative, and nothing fires until the
finger lifts.**

| Criterion | The floor | How to meet it |
| --- | --- | --- |
| WCAG 2.5.8 Target Size (Minimum) | 24 × 24 CSS px, or a smaller target spaced so a 24 px circle centred on it touches no other target and no other small target's circle | Apple 44 × 44 pt and Material 48 × 48 dp are the platforms' sizes; a small icon grows its hit area without growing the layout (web: padding or a pseudo-element; iOS: a larger `contentShape` or hit-test inset; Android: Compose `minimumInteractiveComponentSize`, a touch delegate) |
| WCAG 2.5.1 Pointer Gestures | A gesture that needs a path (swipe, draw) or several fingers (pinch, two-finger tap) also works with one pointer, without a path | A swipe-to-delete row also has a delete in its menu; a pinch-zoomed map has + and − buttons; a carousel has next and previous |
| WCAG 2.5.7 Dragging Movements | Anything done by dragging can also be done with single taps or clicks | A sheet that drags closed has a close button; a reorderable list has move up and down; a slider takes a tap on its track and the arrow keys |
| WCAG 2.5.2 Pointer Cancellation | An action fires on release, over the control; sliding off before lifting cancels it | Platform buttons do this; web acts on `click`, never on `pointerdown` or `touchstart`; a drag released over a control does not also press it |
| WCAG 2.5.4 Motion Actuation | Anything triggered by moving the device (shake, tilt) also has a control on screen, and the motion can be turned off | Shake-to-undo has an Undo button and a setting |
| WCAG 1.3.4 Orientation | Every screen works in portrait and landscape, unless one orientation is essential | No orientation lock; a sticky header short enough for a landscape phone |

- **No two targets overlap**, and the spacing that makes a small target pass is not used by another target.
- **A screen reader takes over single-finger gestures.** With VoiceOver or TalkBack on, a custom swipe never reaches
  the app; every gesture's action is also a named action the reader offers (iOS: custom accessibility actions;
  Android: accessibility custom actions; web: visible buttons).
- **A long press is never the only way to an action** — whatever it reveals is also in a visible menu or button.
- **Hover adds; it never holds the only path.** Whatever appears on hover also appears on keyboard focus, and is
  always shown on a touch screen. Gate hover by what the input can do (web: `@media (hover: hover) and (pointer:
  fine)`), never by device name, user agent or screen width — tablets have pointers and laptops have touch screens.
- **A cancelled gesture commits nothing** — a system interruption (a call, the notification shade), a second finger
  or Escape returns the dragged thing to rest (web: handle `pointercancel`).
- **Screen edges belong to the system.** Custom swipes start away from the edges that the platform uses for back and
  home.

## 7. Content on hover or focus

**Anything that appears on hover or focus can be dismissed without moving, can itself be hovered, and stays until
the person leaves it** (WCAG 1.4.13).

| Requirement | Means | How to test |
| --- | --- | --- |
| Dismissible | Escape (or another key) closes it without moving the pointer or the focus | Hover the trigger, press Escape: it closes, the pointer has not moved |
| Hoverable | The pointer can move onto the new content without it closing | Move from the trigger onto the tooltip: it stays |
| Persistent | It stays until the trigger loses hover or focus, the person dismisses it, or its information is no longer true | Wait: it does not time out |

- **Nothing interactive or unique lives only in a tooltip.** A tooltip repeats or explains; a link or button inside
  hover content is reachable by keyboard and by touch too.
- **The platform's native tooltips are exempt** (the browser's `title` popup) — and are unreachable on touch, so they
  never hold anything a person needs.

## 8. Time, motion and flashing

**Nothing times out without warning, nothing moves on its own without a way to stop it, nothing flashes, and motion
follows the person's reduced-motion setting.**

| Criterion | The floor | How to meet it |
| --- | --- | --- |
| WCAG 2.2.1 Timing Adjustable | A time limit can be turned off, adjusted or extended, unless it is real-time or essential | A session warns and offers more time. A toast that disappears carries nothing found only in it — the result shows in place too — stays long enough to read, and pauses while hovered, focused or pressed so it can be finished |
| WCAG 2.2.2 Pause, Stop, Hide | Content that moves, blinks, scrolls or auto-updates on its own for more than 5 s, beside other content, can be paused, stopped or hidden | A carousel has pause; a looping background video has a pause control; a ticker stops |
| WCAG 2.3.1 Three Flashes or Below Threshold | Nothing flashes more than 3 times in any second | No strobing; a spinner's cycle stays far under 3 a second |
| WCAG 2.3.3 Animation from Interactions (AAA) | Motion a person's action sets off can be turned off, unless it is essential | Follow the platform's reduced-motion setting (below) |

- **On Android, check that a wait indicator still moves with Remove animations on** — an indicator driven by the
  animator duration scale stops with it; one that must keep moving is drawn so it does not depend on that scale.
- **A loading indicator shown while nothing else can be done is essential** under WCAG 2.2.2 and needs no pause — it
  ends when the wait ends, in the content, an error or a timeout.
- **Read each platform's setting.** Web: the `prefers-reduced-motion` media query, with smooth scrolling and autoplay
  only under `no-preference`. iOS: Reduce Motion (`UIAccessibility.isReduceMotionEnabled`, SwiftUI
  `accessibilityReduceMotion`), and the related settings Prefer Cross-Fade Transitions, Auto-Play Video Previews and
  Auto-Play Animated Images. Android: Remove animations, which sets the animator duration scale to 0
  (`Settings.Global.ANIMATOR_DURATION_SCALE`) so every system-timed animation jumps to its end — a fade the design
  keeps under reduced motion is handled on purpose.
- **Under reduced motion, remove travel and keep the change of state.** Movement across the screen, scaling, zooming,
  spinning, parallax and sliding page transitions go; a short fade, a colour change, or an instant change stays.
  Turning every animation off at once hides what changed.
- **Motion the person drives keeps moving** — a dragged sheet still follows the finger and a scroll still scrolls;
  only the motion the product adds after the release becomes a fade or a jump.
- **A wait indicator keeps moving** — a still spinner reads as frozen.
- **When motion carries the explanation, step between its states** rather than deleting them — the information
  stays, the travel goes.
- **Treat "not yet known" as reduced.** Web: no flash of the moving version before the query is read.
- **Under reduced motion, loops and autoplay do not start**, and a paused loop rests on a frame that shows what it is.
- **The reduced variant is judged by watching it with the setting on**, never by reading the code — a leftover
  transform still moves.

## 9. Forms and errors

**Every field has a visible label, asks for the right input, says what went wrong in words, and lets password
managers and paste do their work.**

| Criterion | The floor | How to meet it |
| --- | --- | --- |
| WCAG 3.3.2 Labels or Instructions | Every field has a visible label; a placeholder is not a label | A label above or beside the field, tied to it in code (web: `<label for>`; native: the field's accessibility label) |
| WCAG 1.3.5 Identify Input Purpose | Fields about the person say what they are, so autofill and assistive tech can fill them | Web: `autocomplete` (`email`, `name`, `one-time-code`); iOS: `textContentType`; Android: autofill hints |
| WCAG 3.3.1 Error Identification | An error is named in text and tied to its field | The message under the field, linked to it (web: `aria-describedby`; native: the field's error semantics) |
| WCAG 3.3.3 Error Suggestion | The message says how to fix it, when that is known | "Enter a date like 31/12/2026", not "Invalid input" |
| WCAG 3.3.4 Error Prevention (Legal, Financial, Data) | A legal, financial or data-deleting submission can be reviewed, corrected or undone | A review step, a confirmation, or an undo |
| WCAG 3.3.7 Redundant Entry | Information already entered in a process is not asked for again | Prefill it, or offer it to pick |
| WCAG 3.3.8 Accessible Authentication (Minimum) | Signing in never depends on remembering, transcribing or solving something, unless a helper is allowed | Paste and password managers work in every password and code field; a passkey or an emailed link is offered |
| WCAG 3.2.2 On Input | Changing a field's value changes nothing large on its own | No navigation on selecting an option; a submit button |

- **After a failed submit, focus goes to the first field in error**, or to an error summary that links to each field.
- **Tapping a field's label focuses or toggles it**, and a checkbox or switch row is one target with no dead gap.
- **A disabled control's reason is on screen** beside it, or the control stays enabled and explains on press.
- **An enabled control never looks disabled, and a disabled one never looks enabled** — the look is the only state a
  sighted person reads, and the semantics carry the same state to assistive tech (WCAG 4.1.2).
- **Each field asks for the right keyboard** — web: `type` and `inputmode`; iOS: `keyboardType`; Android: `inputType`.

## 10. Status messages

**A change that appears without moving focus — a toast, "Saved", a result count, a loading state — is announced by
the screen reader** (WCAG 4.1.3).

| Platform | How |
| --- | --- |
| Web | A live region that exists before the message arrives: `role="status"` (polite) for news, `role="alert"` (assertive) only for urgent errors |
| iOS | `UIAccessibility.post(notification: .announcement, …)`, or SwiftUI `AccessibilityNotification.Announcement` |
| Android | A live region on the view (`accessibilityLiveRegion`, Compose `liveRegion` semantics) |

- **An announcement never moves focus**; the person stays where they are.
- **One message per change** — a live region that rewrites itself on every keystroke floods the reader.

## 11. The walks

**An agent checks what code can show; the person walks the screen on the target for what only use can show.** A walk
is never claimed as passed from reading code.

| Walk | Steps | Passes when |
| --- | --- | --- |
| Keyboard | Tab through every stop, then Shift+Tab back; open and close each menu, dialog and sheet | Order follows reading order; focus always visible and never hidden; every action reachable; Escape closes what opened and focus returns to its opener; no trap |
| Screen reader | VoiceOver (macOS, iOS), TalkBack (Android) or NVDA (Windows): move through the screen, do each task, including each gesture's task from the actions menu | Every control says its name, role and state; decoration is silent; status changes are spoken; each gesture's task is done without the gesture |
| Zoom and reflow | Text at 200 % (the platform's largest text size on mobile); the window at 320 px wide | Nothing lost, cut off or overlapping; no sideways scrolling |
| Reduced motion | The platform's setting on; every transition, loop and autoplay | Every change of state still seen; nothing travels; drags still track; spinners still spin |
| Touch | On a phone: every target, every gesture, the alternatives to each | Targets hit first time one-handed; every drag and gesture also done with taps |

**What needs a real device.** Gesture feel, a screen reader's gestures and actions menu, announcements, the
reduced-motion and auto-play settings of iOS and Android (browser emulation covers only the web media query), the
on-screen keyboard over fields, and safe areas in each orientation. Emulators and trackpads misreport touch.

## 12. Automated tools

**Automated checks find only part of the failures — mostly missing names, roles, contrast and structure.** Run them
on every change; they never replace the walks (§11).

| Platform | Tools | Catches | Misses |
| --- | --- | --- | --- |
| Web | axe-core (in Playwright, Cypress, Storybook or the browser extension), Lighthouse | Missing names and alternatives, contrast on plain backgrounds, invalid ARIA, missing labels and language | Focus order, whether a name is useful, text over images, motion, gestures |
| iOS | Xcode's Accessibility Inspector audit; `performAccessibilityAudit()` in XCUITest | Missing labels, small targets, contrast, clipped Dynamic Type | Reading order, gesture alternatives, announcements |
| Android | Accessibility Scanner; Espresso and Compose accessibility checks | Small targets, missing labels, low contrast | Focus order, custom gestures, live regions |
| Any | `contrast.py` and the accessibility check in this skill | A colour pair under its floor; markup and style patterns that break a floor (the skill's Checks) | Everything a person has to see or do |

## 13. Media, consistency and links

**The rest of AA: media has captions and descriptions, instructions never rest on shape or place alone, and the same
thing looks, sits and is named the same on every screen.**

| Criterion | The floor | How to meet it |
| --- | --- | --- |
| WCAG 1.2.1–1.2.5 Time-based Media | Prerecorded audio has a transcript; video has captions and audio description (or a full text alternative); live video has captions | Captions as a text track (web: `<track kind="captions">`; native: the player's caption support), not burnt into the picture |
| WCAG 1.3.3 Sensory Characteristics | An instruction never rests only on shape, size, position, colour or sound | "Tap Save", not "tap the round button on the right" |
| WCAG 1.4.2 Audio Control | Sound that plays on its own for more than 3 s can be paused or turned down apart from the system volume | No autoplaying sound; a mute control beside any that plays |
| WCAG 1.4.5 Images of Text | Text is text, not a picture of it, unless the look is essential | Live text over an image; logotypes are exempt |
| WCAG 2.4.4 Link Purpose (In Context) | A link says where it goes, alone or with its sentence, list item or row | "Read the pricing", not "click here"; a row of "More" links each named for its item |
| WCAG 2.4.5 Multiple Ways | A page in a set can be reached more than one way, unless it is a step in a process | Navigation and search, or navigation and a site map |
| WCAG 3.1.2 Language of Parts | A passage in another language is marked | Web: `lang` on the element; native: the string's language attribute |
| WCAG 3.2.3 Consistent Navigation | Navigation repeated across screens keeps its order | Shared navigation components |
| WCAG 3.2.4 Consistent Identification | The same function has the same name and icon everywhere | One label per action across the product |
| WCAG 3.2.6 Consistent Help | Help offered on several screens (contact, chat, a help link) sits in the same place on each | A fixed slot for help in the shared layout |
