---
name: accessibility
description: The accessibility floors every screen meets, from WCAG 2.2 AA, carried in the skill (references/criteria.md) with how to meet and test each on the web, iOS, Android and embedded ESP-IDF devices with an LVGL screen — text contrast 4.5:1 and 3:1 for large text and non-text measured against the colour actually painted, with contrast.py; colour never the only signal; text that resizes and reflows, or a large-text mode where nothing scales it; names, roles and labels; keyboard, encoder and key access, focus order, visible focus, modals and hidden content (LVGL groups and focus states); target size, converted to panel pixels from the pixel density; a plain alternative to every gesture and drag, actions on release, hover never the only path; tooltips that can be dismissed and hovered; time limits, autoplay, flashing and reduced motion, as the platform's setting or the product's own; forms, errors and status messages; closed functionality under EN 301 549 (no screen reader: visible words, sound and haptics, speech where needed) and physical controls; status lights that never rely on colour or flash; the focus model every input shares, carried in references/focus.md — the focus position apart from the ring, a tap shows no ring while a keyboard or encoder does, where the next step starts, screens and modals opening and closing and focus back to the opener, keeping focus in view, the ring's craft, what takes focus, who takes an input, the input mapping, building it once; the walks the person does on the target; and a11y_check.py for the patterns code can show, in web, native and C/C++ LVGL files. Portable — the folder works in any repo. Use when designing or reviewing a screen, picking a colour pair, putting text or an icon over a fill or an image, making a control, a form, a gesture, a tooltip or an animation, wiring an encoder or buttons to a screen, or asked "is this accessible?" or "does this pass contrast?".
metadata:
  scope: portable
---

# Accessibility

The floors every screen meets, and how to check each one. The floors and their reasons are WCAG 2.2 at level AA, with
the platforms' own guidelines where they ask for more and EN 301 549 where a product has no accessibility API, kept in
this skill at
[references/criteria.md](references/criteria.md) (cited `ACCESSIBILITY §n`), with the focus model that meets the
focus floors at [references/focus.md](references/focus.md) (cited `FOCUS §n`); this page indexes them — each rule is
one line citing the § that holds it — and holds the steps: the Procedure and the Checks. A reference wins if this page
and it disagree — fix this page.

**Platforms.** Each rule is stated once for every platform; how to meet it on one is labelled in the references —
**Web**, **iOS**, **Android**, **Embedded (ESP-IDF, LVGL)** — and a rule here names a platform only where its case
differs. A project that sets a floor above AA writes it in its design brief (`DESIGN.md` in
the agent-harness kit), and that floor wins over both.

**Portable.** This folder is self-contained and links to nothing outside itself (it names the rest of a kit in
backticks): the criteria, the focus model, the contrast script and the accessibility check ([scripts/](scripts/)).
Copy it into any repo's `.agents/skills/` (or `.claude/skills/`) and it works there: `a11y_check.py` reads
`UI_PATHS` from `.agents/project.py` when the repo has one, and scans every tracked UI file — web, native, and C or
C++ for an LVGL screen — when it does not, and says so when it read none; `contrast.py` needs nothing. They need git
and Python 3.9+. In the agent-harness kit, the `ui-designer` skill applies these floors at its three gates,
`design-system` keeps the product's colour pairs, and `verify.py run` runs both scripts' self-tests and, once
`UI_PATHS` is set, the accessibility check on the UI files.

## When to use

- Picking a text, icon or border colour against a background; text over a fill, a gradient or an image.
- Making a control: a button, a link, an input, a toggle, a custom component; a form and its errors.
- Adding a gesture, a drag, a long press, a hover state or a tooltip.
- Ordering focus; hiding or disabling something; opening a dialog, a sheet or a menu; showing a toast.
- Adding an animation, a transition, autoplay, a loop, a timeout or anything that flashes.
- Wiring an encoder, buttons or a keypad to a screen; deciding what a device with no screen reader shows, sounds and
  offers in its own settings; sizing text and targets on a small panel.
- Reviewing a screen or a mock, or asked "is this accessible?" or "does this pass contrast?".

## Rules

### Do

1. **Give text 4.5:1 against what is painted under it, and large text 3:1** — large is 24 px regular or 18.66 px bold
   and up (WCAG 1.4.3; ACCESSIBILITY §2).
2. **Give non-text 3:1** — icons that carry meaning, control borders, focus indicators, chart marks, a toggle's state
   (WCAG 1.4.11; ACCESSIBILITY §2).
3. **Measure against the colour actually painted**, in every state and every theme — a translucent fill composited
   over what is behind it, the worst part of an image under the text (ACCESSIBILITY §2).
4. **Make every action reachable with a keyboard alone — or the device's encoder or keys alone**, with no trap; on
   LVGL, every control in a group bound to the input (WCAG 2.1.1, 2.1.2; ACCESSIBILITY §5).
5. **Keep focus in reading order, always visible, never hidden by a sticky header or a toast** — the view order is the
   visual order (web: no positive tabindex; LVGL: the order added to the group, the ring on both `LV_STATE_FOCUSED`
   and `LV_STATE_FOCUS_KEY`) (WCAG 2.4.3, 2.4.7, 2.4.11; ACCESSIBILITY §5; FOCUS §7).
6. **Give every control a name a screen reader says, containing its visible label** — an icon-only button named for
   its action; inputs keep a visible label, not only a placeholder; with no screen reader, the visible label is the
   name (WCAG 4.1.2, 2.5.3, 3.3.2; ACCESSIBILITY §4, §9, §14).
7. **Make targets at least 24 × 24 px, and aim for the platform's 44 pt or 48 dp unless the design brief sets its
   own size**, with no two overlapping; on a panel, n × ppi ÷ 160 pixels (WCAG 2.5.8; 2.5.5 at AAA;
   ACCESSIBILITY §1, §6).
8. **Never use colour as the only signal** — an error has an icon or words, a link in text has an underline, a chart
   has labels or patterns (WCAG 1.4.1; ACCESSIBILITY §2).
9. **Let text resize to 200 % and reflow at 320 px wide**, and never block pinch zoom; where nothing can scale the
   text, offer a large-text mode with a capital H at 0.7° at the viewing distance (WCAG 1.4.4, 1.4.10, 1.4.12;
   EN 301 549 5.1.4; ACCESSIBILITY §3).
10. **Follow the person's reduced-motion setting — the platform's, or the product's own where there is none: remove
    travel, keep the change of state** — a move becomes a fade or nothing, while motion the person drives and a wait
    indicator keep moving; above AA, adopted by default (WCAG 2.3.3 at AAA; ACCESSIBILITY §1, §8).
11. **Give images that carry meaning a text alternative; hide decorative ones** (WCAG 1.1.1; ACCESSIBILITY §4).
12. **Mark structure in the code, not only in the look** — headings, lists, landmarks, table headers, the screen's
    title and language (WCAG 1.3.1, 2.4.2, 3.1.1; ACCESSIBILITY §4).
13. **Give every gesture and every drag a plain alternative** — a tap or click for one pointer, a named action for a
    screen reader, and on a device with an encoder or keys, a control they reach (WCAG 2.5.1, 2.5.7;
    ACCESSIBILITY §6).
14. **Fire an action on release, over the control** — sliding off cancels, and a cancelled gesture commits nothing;
    on LVGL, act on `LV_EVENT_CLICKED` and clear `LV_OBJ_FLAG_PRESS_LOCK` where sliding off must cancel (WCAG 2.5.2;
    ACCESSIBILITY §6).
15. **Show on keyboard focus and on touch whatever hover shows**, gating hover by what the input can do (WCAG 2.1.1;
    ACCESSIBILITY §6).
16. **Make what appears on hover or focus dismissible with Escape, hoverable, and lasting** until the person leaves it
    (WCAG 1.4.13; ACCESSIBILITY §7).
17. **Take hidden things out of the focus order and the accessibility tree**; a modal takes focus in, closes on
    Escape and back, and returns focus to its opener (WCAG 2.4.3; ACCESSIBILITY §5; FOCUS §5).
18. **Make a composite widget one stop, moved within by its own keys** — web and keyboards: one Tab stop with arrows
    inside; LVGL with an encoder: one group stop, changed in edit mode — and keep single-key shortcuts off while
    typing (WCAG 2.1.1, 2.1.4; ACCESSIBILITY §5; FOCUS §8).
19. **Announce a change that appears without moving focus** — a toast, "Saved", a result count — through a live
    region or the platform's announcement; with no screen reader, shown near focus with a sound or haptic (WCAG 4.1.3;
    ACCESSIBILITY §10).
20. **Let every time limit pause, extend or switch off**, and pause any toast while hovered, focused or pressed; on a
    device, in its own settings (WCAG 2.2.1; ACCESSIBILITY §8).
21. **Name each field's purpose for autofill, name each error in words under its field, and let paste and password
    managers work** (WCAG 1.3.5, 3.3.1, 3.3.3, 3.3.8; ACCESSIBILITY §9).
22. **Work in both orientations, and give any device-motion action an on-screen control** (WCAG 1.3.4, 2.5.4;
    ACCESSIBILITY §6).
23. **Caption video, describe it, and let sound be stopped; word instructions and links so they stand alone; keep
    navigation, names and help the same on every screen** (WCAG 1.2.1–1.2.5, 1.3.3, 1.4.2, 1.4.5, 2.4.4, 2.4.5, 3.1.2,
    3.2.3, 3.2.4, 3.2.6; ACCESSIBILITY §13).
24. **Where there is no screen reader, carry on screen and in sound what a reader would say** — a word on every
    control, state drawn by more than colour, a sound or haptic for each action and error, a spoken mode where the
    product's brief decides it needs one, and accessibility settings reached without the ability they make up for
    (EN 301 549 5.1, 5.2; ACCESSIBILITY §14).
25. **Make physical controls work without sight, grasping, force or two at once** — every knob action also by touch or
    a press, keys told apart by touch, a toggle's state felt or heard, key repeat adjustable or off (EN 301 549
    5.5–5.9, 8.4.2; ACCESSIBILITY §14).
26. **Keep the focus position apart from the ring** — a tap or click moves focus with no ring, a keyboard, encoder or
    key shows it, and hiding the ring keeps the place (WCAG 2.4.7; FOCUS §1, §3).
27. **Start the next step from where the person last was** — the control or point tapped, else what is in view; a
    scroll or a drag leaves no starting point, and a drag drops the ring (FOCUS §4).
28. **Open screens and sheets with no ring; move focus into a modal a key opened; close only the topmost overlay per
    press of Escape or back; hand focus back to the opener, or on when it is gone** (WCAG 2.1.2, 2.4.3, 3.2.1;
    FOCUS §5).
29. **Scroll to focus only for the inputs that cannot see** — with a margin and clear of pinned bars; focus a touch
    moved scrolls nothing (WCAG 2.4.11; FOCUS §6).
30. **Draw the ring as an outline with room around it, apart from selection and from edit mode** (WCAG 2.4.7;
    2.4.13 at AAA; FOCUS §7).
31. **Make only controls stops, hand focus on before a focused control hides or goes, and never move focus on a change
    of state; a message that asks nothing takes no focus** (WCAG 2.4.3, 3.2.1; FOCUS §8, §9).
32. **Give each input one job on every screen, decided once in one input model** — owners in a fixed order; on a
    device, the order wraps and a first press with no ring only shows it (FOCUS §2, §10, §11).
33. **Check typed text when it is committed, never on every keystroke** — the error itself is Do 21's
    (ACCESSIBILITY §9).
34. **Give a status light more than colour, put what it says on the screen too, and blink it at most 3 times a
    second** (WCAG 1.4.1, 2.3.1; ACCESSIBILITY §2, §8).

### Never

- **Call an element exempt from contrast unless it is disabled, decorative or a logotype** — a placeholder, a hint, a
  caption and a timestamp all carry meaning (WCAG 1.4.3, 1.4.11; ACCESSIBILITY §2).
- **Dim text with opacity to make it secondary** — use a colour whose painted value passes (ACCESSIBILITY §2).
- **Remove the focus outline without a replacement at 3:1** — a CSS `outline: none`, or an LVGL outline or border set
  to 0 on a focus state (WCAG 2.4.7; ACCESSIBILITY §5).
- **Make an enabled control look disabled**, or a disabled one look enabled; a disabled control's reason is on screen
  (ACCESSIBILITY §9).
- **Let content move, loop or autoplay for more than 5 s with no way to pause it** — a loading indicator shown while
  nothing else can be done is essential and exempt (WCAG 2.2.2; ACCESSIBILITY §8).
- **Flash anything more than 3 times a second** (WCAG 2.3.1; ACCESSIBILITY §8).
- **Put anything a person needs only behind a hover, a long press, a swipe or a tooltip** (WCAG 2.1.1, 2.5.1, 1.4.13;
  ACCESSIBILITY §6, §7).
- **Use a styled container where a platform control exists** — it is not focused, keyed or announced (WCAG 4.1.2;
  ACCESSIBILITY §4).
- **Claim a walk passed from reading code** — the walks are the person's, on the target (ACCESSIBILITY §11).

## Procedure

### Checking a colour pair

```sh
python3 .agents/skills/accessibility/scripts/contrast.py "<fg>" "<bg>"            # text: floor 4.5
python3 .agents/skills/accessibility/scripts/contrast.py --min 3 "<fg>" "<bg>"    # large text, icons, borders, focus
```

1. Take the colours the screen paints — the value in the theme in use (light and dark both), in each state, and
   composited (`#rrggbbaa` over its background) when translucent.
2. Run the pair; a FAIL is a finding, and the fix is a colour whose painted value passes, never a smaller floor.
3. Write each pair down where the project keeps them. In the agent-harness kit: the mock's values file at
   `ui-designer`'s first gate, and a pair the product keeps painting as a row in DESIGN.md's contrast pairs, which the
   design check recomputes on every change.

### Deciding a screen's accessibility, before it is built

For each screen or component, settle and write down, beside the mock:

1. **Contrast** — every text and non-text pair, in each state and theme (Do 1–3).
2. **Focus order** — the list of stops in reading order; where focus goes when a modal opens and closes, and when the
   focused thing goes away; which inputs show the ring and where the first step starts (Do 5, Do 17, Do 26–31).
3. **Names** — each control's accessible name, each image's alternative, what is decorative (Do 6, Do 11).
4. **Targets** — each target's size with its hit area, and the gaps between them (Do 7).
5. **Alternatives** — for each gesture, drag, long press and hover: the tap, the visible control and the
   screen-reader action that does the same (Do 13, Do 15).
6. **Motion** — what reduced motion does to each move, and which moves are driven or show a wait (Do 10).
7. **Announcements and time** — what is announced, and what pauses or never times out (Do 19, Do 20).
8. **With no screen reader** — the word on each control, the sound or haptic for each action and error, whether the
   product needs a spoken mode, and which settings it offers in place of the system's: large text, reduced motion,
   time limits (Do 24, Do 25).

### Checking the code

```sh
python3 .agents/skills/accessibility/scripts/a11y_check.py            # every UI file, against the baseline
python3 .agents/skills/accessibility/scripts/a11y_check.py <file> …   # the files a change touched
```

It finds what a pattern shows: the focus outline removed, pinch zoom blocked, a positive tabindex, an image with no
alternative, a page with no language, media that autoplays with no controls, a `<div>` or `<span>` with a click
handler and no role, an Android image with no description, and animation with no reduced-motion handling (A1–A9);
in C and C++ for an LVGL screen, an outline or border zeroed on a focus state with no other focus style (A10), text
dimmed with `text_opa` (A11), and an encoder or keypad input with no group bound to it (A12). A sanctioned hit
carries `a11y-exception` on its line with the reason. It prints how many UI files it read, and says so plainly when
it read none — a pass over no files checked nothing.

Its limits: the outline checks are per file and the reduced-motion and group checks per tree, so one rule anywhere
clears them; a role without a tab stop and key handling passes; the markup checks read web markup and Android XML, so
Swift and Kotlin views get little from it; the LVGL checks read direct style calls with literal values, so a style
built in one place and added for a focus state elsewhere passes, and an action bound to `LV_EVENT_PRESSED` is left to
the walks, since the same event rightly carries press feedback. A pass says nothing about focus order, names that
make sense, contrast over images, gestures or motion — the walks find those. Run the platform's own auditor too; LVGL
has none (ACCESSIBILITY §12).

### Walking a screen

The walks are in ACCESSIBILITY §11: keyboard, screen reader, zoom and reflow, reduced motion, and touch; on an
embedded device, the encoder and keys, light and angle, hands, and without looking where it speaks. An agent lists the
walks a change needs and hands them to the person for the target; it never claims one passed from code.

## Checks

- [ ] (script) Every text pair 4.5:1, large text and non-text 3:1 — `contrast.py`, against the painted colour, in each
  state and theme
- [ ] (script) No pattern that breaks a floor in the UI files — `a11y_check.py`
- [ ] Focus order follows reading order; focus visible at 3:1 and never hidden; modals return focus (Do 5, Do 17)
- [ ] Every control has a name containing its label; inputs keep a visible label (Do 6)
- [ ] Targets at least 24 × 24 px, aiming for the platform's size, none overlapping (Do 7)
- [ ] No meaning carried by colour alone (Do 8)
- [ ] Text resizes to 200 % and reflows at 320 px; zoom never blocked (Do 9)
- [ ] Images that carry meaning have an alternative; decoration hidden; structure, title and language in code
  (Do 11, Do 12)
- [ ] Every gesture, drag, long press and hover has a plain alternative; actions fire on release (Do 13–15)
- [ ] Hover and focus content dismissible, hoverable, lasting (Do 16)
- [ ] Reduced motion handled; driven motion and waits keep moving; nothing flashes; nothing loops without a pause
  (Do 10, Never)
- [ ] Composite widgets one stop — a Tab stop, or a group stop changed in edit mode; single-key shortcuts off while
  typing (Do 18)
- [ ] Status changes announced; time limits pause (Do 19, Do 20)
- [ ] Fields name their purpose; errors in words under their field; paste works; both orientations (Do 21, Do 22)
- [ ] Media captioned and described; instructions and links stand alone; navigation, names and help consistent (Do 23)
- [ ] With no screen reader: a word on every control, sound or haptic per action and error, the product's own large
  text, reduced-motion and time settings, a spoken mode where the brief needs one (Do 24)
- [ ] Physical controls: every knob action also by touch or press, keys told apart by touch, no two-at-once, repeat
  adjustable (Do 25)
- [ ] A tap shows no ring, a key or detent does; hiding the ring keeps the place; the next step starts from the last
  tap or from what is in view (Do 26, Do 27)
- [ ] Screens open with no ring; modals take focus in, close one level per press and hand focus back (Do 28)
- [ ] Focus scrolled into view for the blind inputs only, clear of pinned bars; the ring an outline with room, apart
  from selection and edit mode (Do 29, Do 30)
- [ ] Only controls are stops; focus handed on before a control goes; no focus moved by a state change; a toast
  takes no focus (Do 31)
- [ ] Each input one job everywhere, in one input model (Do 32)
- [ ] Typed text checked when committed, never on every keystroke (Do 33)
- [ ] Status lights: more than colour, said on the screen too, at most 3 blinks a second (Do 34)
- [ ] The walks handed to the person for the target — never claimed from code

## Traps

- **Passes in the mock, fails on the screen** → the mock measured the colour, the screen paints it at 60 % opacity over
  a photo → measure the composited colour (Do 3).
- **Passes in light, fails in dark** → the pair was checked in one theme → check every theme the product ships.
- **A grey hint text fails at 3.9:1** → secondary text is not exempt → take the next colour step down.
- **A custom control is skipped by Tab** → a styled `div` with no role or tab stop → use the platform's control.
- **A sheet closes by dragging only** → people who cannot drag are stuck in it → a visible close button, Escape and
  back (Do 13).
- **A row's actions appear on hover, and a phone never shows them** → hover gated by width, not input → show them on
  touch and on focus (Do 15).
- **A drawer is hidden with opacity 0 and Tab still walks into it** → invisible is not hidden → `inert` or the
  platform's hidden state (Do 17).
- **Reduced motion turns every animation off, and a dragged sheet stops following the finger** → a blanket reset →
  remove travel only, keep driven motion (Do 10).
- **A toast says "Saved" and the screen reader says nothing** → the live region was added with the message → it exists
  before the message arrives (Do 19).
- **The ring shows for a tap but not for the encoder, or a restyled ring never appears** → focus styled on
  `LV_STATE_FOCUSED` alone, and the theme's `LV_STATE_FOCUS_KEY` style outranks it → style both states (Do 5).
- **The encoder walks onto a control nobody can see** → an object at opacity 0, off the panel or on another screen
  stays in the group; LVGL skips only hidden and disabled ones → remove it from the group, or one group per screen
  (Do 17).
- **Sliding a finger off a button and lifting still presses it** → `LV_OBJ_FLAG_PRESS_LOCK`, set on every child object
  by default → clear it where sliding off must cancel, or make the action undoable (Do 14).
- **The contrast pair passes in the token file and fails on the glass** → an RGB565 panel truncates each channel, or
  the panel washes out in daylight → recheck the truncated values, and walk it in light (Do 3).

## Sources

| Topic | Where |
| --- | --- |
| The floors, with how to meet and test each per platform | [references/criteria.md](references/criteria.md) |
| WCAG 2.2, the success criteria cited here | The W3C's WCAG 2.2 Recommendation and its Understanding documents |
| Keyboard patterns for menus, dialogs, tabs, listboxes | The W3C's WAI-ARIA Authoring Practices Guide |
| The focus model, for every input | [references/focus.md](references/focus.md); the WAI-ARIA Authoring Practices Guide (*Developing a Keyboard Interface*, *Dialog (Modal) Pattern*); the HTML Standard (sequential focus navigation starting point, `autofocus`); CSS Selectors Level 4 (`:focus-visible`) |
| Target sizes, reduced motion and assistive tech on the platforms | Apple Human Interface Guidelines (Accessibility); Material Design and Android Developers (Accessibility); MDN (`prefers-reduced-motion`, ARIA live regions) |
| Closed functionality, operable parts and mechanical controls | ETSI EN 301 549 V3.2.1, clauses 5, 8 and 11 |
| Groups, input devices, focus states and style precedence on LVGL | LVGL's documentation (Input devices: Groups, Encoder, Keypad; Styles: States) and headers (`lv_group.h`, `lv_indev.h`, `lv_obj_style.h`, `lv_event.h`); Espressif's `esp_lvgl_port` README (encoder and navigation buttons) |
| The contrast formula | WCAG 2.2's definitions of contrast ratio and relative luminance — `contrast.py` |
