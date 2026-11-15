---
name: accessibility
description: The accessibility floors every screen meets, from WCAG 2.2 AA, carried in the skill (references/criteria.md) with how to meet and test each on the web, iOS and Android — text contrast 4.5:1 and 3:1 for large text and non-text measured against the colour actually painted, with contrast.py; colour never the only signal; text that resizes and reflows; names, roles and labels; keyboard access, focus order, visible focus, modals and hidden content; target size; a plain alternative to every gesture and drag, actions on release, hover never the only path; tooltips that can be dismissed and hovered; time limits, autoplay, flashing and reduced motion on each platform; forms, errors and status messages; the walks the person does on the target; and a11y_check.py for the patterns code can show. Portable — the folder works in any repo. Use when designing or reviewing a screen, picking a colour pair, putting text or an icon over a fill or an image, making a control, a form, a gesture, a tooltip or an animation, or asked "is this accessible?" or "does this pass contrast?".
---

# Accessibility

The floors every screen meets, and how to check each one. The floors and their reasons are WCAG 2.2 at level AA, with
the platforms' own guidelines where they ask for more, kept in this skill at
[references/criteria.md](references/criteria.md) (cited `ACCESSIBILITY §n`); this page indexes them — each rule is one
line citing the § that holds it — and holds the steps: the Procedure and the Checks. The reference wins if this page
and it disagree — fix this page. A project that sets a floor above AA writes it in its design brief (`DESIGN.md` in
the agent-harness kit), and that floor wins over both.

**Portable.** This folder is self-contained and links to nothing outside itself (it names the rest of a kit in
backticks): the criteria, the contrast script and the accessibility check ([scripts/](scripts/)). Copy it into any
repo's `.agents/skills/` (or `.claude/skills/`) and it works there: `a11y_check.py` reads `UI_PATHS` from
`.agents/project.py` when the repo has one, and scans every tracked UI file when it does not; `contrast.py` needs
nothing. They need git and Python 3.9+. In the agent-harness kit, the `ui-designer` skill applies these floors at its
three gates, `design-system` keeps the product's colour pairs, and `verify.py run` runs both scripts' self-tests and, once
`UI_PATHS` is set, the accessibility check on the UI files.

## When to use

- Picking a text, icon or border colour against a background; text over a fill, a gradient or an image.
- Making a control: a button, a link, an input, a toggle, a custom component; a form and its errors.
- Adding a gesture, a drag, a long press, a hover state or a tooltip.
- Ordering focus; hiding or disabling something; opening a dialog, a sheet or a menu; showing a toast.
- Adding an animation, a transition, autoplay, a loop, a timeout or anything that flashes.
- Reviewing a screen or a mock, or asked "is this accessible?" or "does this pass contrast?".

## Rules

### Do

1. **Give text 4.5:1 against what is painted under it, and large text 3:1** — large is 24 px regular or 18.66 px bold
   and up (WCAG 1.4.3; ACCESSIBILITY §2).
2. **Give non-text 3:1** — icons that carry meaning, control borders, focus indicators, chart marks, a toggle's state
   (WCAG 1.4.11; ACCESSIBILITY §2).
3. **Measure against the colour actually painted**, in every state and every theme — a translucent fill composited
   over what is behind it, the worst part of an image under the text (ACCESSIBILITY §2).
4. **Make every action reachable with a keyboard alone**, with no trap (WCAG 2.1.1, 2.1.2; ACCESSIBILITY §5).
5. **Keep focus in reading order, always visible, never hidden by a sticky header or a toast** — the view order is the
   visual order, no positive tabindex (WCAG 2.4.3, 2.4.7, 2.4.11; ACCESSIBILITY §5).
6. **Give every control a name a screen reader says, containing its visible label** — an icon-only button named for
   its action; inputs keep a visible label, not only a placeholder (WCAG 4.1.2, 2.5.3, 3.3.2; ACCESSIBILITY §4, §9).
7. **Make targets at least 24 × 24 px, and aim for the platform's 44 pt or 48 dp unless the design brief sets its
   own size**, with no two overlapping (WCAG 2.5.8; 2.5.5 at AAA; ACCESSIBILITY §1, §6).
8. **Never use colour as the only signal** — an error has an icon or words, a link in text has an underline, a chart
   has labels or patterns (WCAG 1.4.1; ACCESSIBILITY §2).
9. **Let text resize to 200 % and reflow at 320 px wide**, and never block pinch zoom (WCAG 1.4.4, 1.4.10, 1.4.12;
   ACCESSIBILITY §3).
10. **Follow the platform's reduced-motion setting: remove travel, keep the change of state** — a move becomes a fade
    or nothing, while motion the person drives and a wait indicator keep moving; above AA, adopted by default
    (WCAG 2.3.3 at AAA; ACCESSIBILITY §1, §8).
11. **Give images that carry meaning a text alternative; hide decorative ones** (WCAG 1.1.1; ACCESSIBILITY §4).
12. **Mark structure in the code, not only in the look** — headings, lists, landmarks, table headers, the screen's
    title and language (WCAG 1.3.1, 2.4.2, 3.1.1; ACCESSIBILITY §4).
13. **Give every gesture and every drag a plain alternative** — a tap or click for one pointer, and a named action for
    a screen reader (WCAG 2.5.1, 2.5.7; ACCESSIBILITY §6).
14. **Fire an action on release, over the control** — sliding off cancels, and a cancelled gesture commits nothing
    (WCAG 2.5.2; ACCESSIBILITY §6).
15. **Show on keyboard focus and on touch whatever hover shows**, gating hover by what the input can do (WCAG 2.1.1;
    ACCESSIBILITY §6).
16. **Make what appears on hover or focus dismissible with Escape, hoverable, and lasting** until the person leaves it
    (WCAG 1.4.13; ACCESSIBILITY §7).
17. **Take hidden things out of the focus order and the accessibility tree**; a modal takes focus in, closes on
    Escape and back, and returns focus to its opener (WCAG 2.4.3; ACCESSIBILITY §5).
18. **Make a composite widget one Tab stop with arrows inside**, and keep single-key shortcuts off while typing
    (WCAG 2.1.1, 2.1.4; ACCESSIBILITY §5).
19. **Announce a change that appears without moving focus** — a toast, "Saved", a result count — through a live
    region or the platform's announcement (WCAG 4.1.3; ACCESSIBILITY §10).
20. **Let every time limit pause, extend or switch off**, and pause any toast while hovered, focused or pressed
    (WCAG 2.2.1; ACCESSIBILITY §8).
21. **Name each field's purpose for autofill, name each error in words under its field, and let paste and password
    managers work** (WCAG 1.3.5, 3.3.1, 3.3.3, 3.3.8; ACCESSIBILITY §9).
22. **Work in both orientations, and give any device-motion action an on-screen control** (WCAG 1.3.4, 2.5.4;
    ACCESSIBILITY §6).
23. **Caption video, describe it, and let sound be stopped; word instructions and links so they stand alone; keep
    navigation, names and help the same on every screen** (WCAG 1.2.1–1.2.5, 1.3.3, 1.4.2, 1.4.5, 2.4.4, 2.4.5, 3.1.2,
    3.2.3, 3.2.4, 3.2.6; ACCESSIBILITY §13).

### Never

- **Call an element exempt from contrast unless it is disabled, decorative or a logotype** — a placeholder, a hint, a
  caption and a timestamp all carry meaning (WCAG 1.4.3, 1.4.11; ACCESSIBILITY §2).
- **Dim text with opacity to make it secondary** — use a colour whose painted value passes (ACCESSIBILITY §2).
- **Remove the focus outline without a replacement at 3:1** (WCAG 2.4.7; ACCESSIBILITY §5).
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
   focused thing goes away (Do 5, Do 17).
3. **Names** — each control's accessible name, each image's alternative, what is decorative (Do 6, Do 11).
4. **Targets** — each target's size with its hit area, and the gaps between them (Do 7).
5. **Alternatives** — for each gesture, drag, long press and hover: the tap, the visible control and the
   screen-reader action that does the same (Do 13, Do 15).
6. **Motion** — what reduced motion does to each move, and which moves are driven or show a wait (Do 10).
7. **Announcements and time** — what is announced, and what pauses or never times out (Do 19, Do 20).

### Checking the code

```sh
python3 .agents/skills/accessibility/scripts/a11y_check.py            # every UI file, against the baseline
python3 .agents/skills/accessibility/scripts/a11y_check.py <file> …   # the files a change touched
```

It finds what a pattern shows: the focus outline removed, pinch zoom blocked, a positive tabindex, an image with no
alternative, a page with no language, media that autoplays with no controls, a `<div>` or `<span>` with a click
handler and no role, an Android image with no description, and animation with no reduced-motion handling. A
sanctioned hit carries `a11y-exception` on its line with the reason.

Its limits: the outline check is per file and the reduced-motion check per tree, so one rule anywhere clears them; a
role without a tab stop and key handling passes; the markup checks read web markup and Android XML, so Swift and
Kotlin views get little from it. A pass says nothing about focus order, names that make sense, contrast over images,
gestures or motion — the walks find those. Run the platform's own auditor too (ACCESSIBILITY §12).

### Walking a screen

The walks are in ACCESSIBILITY §11: keyboard, screen reader, zoom and reflow, reduced motion, and touch. An agent
lists the walks a change needs and hands them to the person for the target; it never claims one passed from code.

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
- [ ] Composite widgets one Tab stop; single-key shortcuts off while typing (Do 18)
- [ ] Status changes announced; time limits pause (Do 19, Do 20)
- [ ] Fields name their purpose; errors in words under their field; paste works; both orientations (Do 21, Do 22)
- [ ] Media captioned and described; instructions and links stand alone; navigation, names and help consistent (Do 23)
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

## Sources

| Topic | Where |
| --- | --- |
| The floors, with how to meet and test each per platform | [references/criteria.md](references/criteria.md) |
| WCAG 2.2, the success criteria cited here | The W3C's WCAG 2.2 Recommendation and its Understanding documents |
| Keyboard patterns for menus, dialogs, tabs, listboxes | The W3C's WAI-ARIA Authoring Practices Guide |
| Target sizes, reduced motion and assistive tech on the platforms | Apple Human Interface Guidelines (Accessibility); Material Design and Android Developers (Accessibility); MDN (`prefers-reduced-motion`, ARIA live regions) |
| The contrast formula | WCAG 2.2's definitions of contrast ratio and relative luminance — `contrast.py` |
