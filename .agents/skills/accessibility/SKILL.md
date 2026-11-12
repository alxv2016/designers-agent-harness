---
name: accessibility
description: The accessibility floors every screen meets, from WCAG 2.2 AA — text contrast 4.5:1 and 3:1 for large text and non-text (icons, borders, focus rings) measured against the colour actually painted, with contrast.py; colour never the only signal; keyboard and screen-reader access, focus order and a visible focus; target size; text that resizes and reflows; labels and names; motion that respects reduced-motion and never flashes. Use when designing or reviewing a screen, picking a colour pair, putting text or an icon over a fill or an image, making a control, adding an animation, or asked "is this accessible?" or "does this pass contrast?".
---

# Accessibility

The floors every screen meets, and how to check each one. The source is WCAG 2.2 at level AA (cited `WCAG <n.n.n>`),
plus the platform's own guidelines where they ask for more (Apple's Human Interface Guidelines, Material Design). A
project that sets a higher floor writes it in its design docs, and this skill follows it. The docs win if this skill
and a doc disagree — fix the skill.

## When to use

- Picking a text, icon or border colour against a background; text over a fill, a gradient or an image.
- Making a control: a button, a link, an input, a toggle, a custom component.
- Ordering focus; hiding or disabling something; opening a dialog or a sheet.
- Adding an animation, a transition, autoplay or anything that flashes.
- Reviewing a screen, or asked "is this accessible?" or "does this pass contrast?".

## Rules

### Do

1. **Give text 4.5:1 against what is painted under it, and large text 3:1** — large is 24 px regular or 18.66 px bold
   and up (WCAG 1.4.3).
2. **Give non-text 3:1** — icons that carry meaning, control borders, focus indicators, chart marks, a toggle's state
   (WCAG 1.4.11).
3. **Measure against the colour actually painted** — a translucent fill composited over what is behind it, the darkest
   or lightest part of an image under the text; `contrast.py` composites `#rrggbbaa` over the background for you.
4. **Make every action reachable with a keyboard alone**, with no trap: Tab in, Tab out, Escape closes what opened
   (WCAG 2.1.1, 2.1.2).
5. **Keep focus in reading order, and always visible** — a focus indicator at 3:1, never hidden by a sticky header or
   a toast (WCAG 2.4.3, 2.4.7, 2.4.11).
6. **Give every control a name a screen reader says** — the visible label, or an accessible name for an icon-only
   button; inputs keep a visible label, not only a placeholder (WCAG 4.1.2, 3.3.2).
7. **Make targets at least 24 × 24 px with their spacing, and aim for 44 × 44** — Apple asks 44 × 44 pt, Material
   48 × 48 dp (WCAG 2.5.8; 2.5.5 at AAA).
8. **Never use colour as the only signal** — an error has an icon or words, a link in text has an underline, a chart
   has labels or patterns (WCAG 1.4.1).
9. **Let text resize to 200 % and reflow at 320 px wide** without loss or sideways scrolling (WCAG 1.4.4, 1.4.10).
10. **Respect reduced motion** — under `prefers-reduced-motion` (or the platform's setting) a move becomes a fade or
    nothing; nothing flashes more than 3 times a second (WCAG 2.3.1, 2.3.3).
11. **Give images that carry meaning a text alternative; mark decorative ones as decorative** (WCAG 1.1.1).
12. **Mark structure in the code, not only in the look** — headings, lists, landmarks, table headers (WCAG 1.3.1).

### Never

- **Call an element exempt from contrast unless it is disabled or decorative** — those are the only exemptions
  (WCAG 1.4.3, 1.4.11). A placeholder, a hint, a caption and a timestamp all carry meaning.
- **Dim text with opacity to make it secondary** — use a token whose painted colour passes.
- **Remove the focus outline without a replacement at 3:1.**
- **Make an enabled control look disabled**, or a disabled one look enabled.
- **Autoplay motion with no way to pause it** when it runs longer than 5 s (WCAG 2.2.2).

## Procedure

### Checking a colour pair

```sh
python3 .agents/skills/accessibility/scripts/contrast.py "<fg>" "<bg>"            # text: floor 4.5
python3 .agents/skills/accessibility/scripts/contrast.py --min 3 "<fg>" "<bg>"    # large text, icons, borders, focus
```

1. Take the colours the screen paints — the token's value in the theme in use (light and dark both), composited when
   translucent.
2. Run the pair; a FAIL is a finding, and the fix is a token whose painted colour passes, never a smaller floor.
3. Record each pair in the mock's values file (`ui-designer` Gate 1, step 5), and a pair the product will keep painting
   as a row in DESIGN.md's contrast pairs (DESIGN §2.2) — the design check then recomputes it on every change.

### Walking a screen

1. Keyboard: Tab through every stop — order, visible focus, every action reachable, Escape closes, no trap.
2. Screen reader (VoiceOver, TalkBack, NVDA): every control says its name, role and state.
3. Zoom to 200 % and narrow to 320 px: nothing lost, nothing cut off.
4. Reduced motion on: every animation becomes calm.

A walk on the target is the person's to judge at gate 3; an agent hands it over and never claims it passed from code.

## Checks

- [ ] (script) Every text pair 4.5:1, large text and non-text 3:1 — `contrast.py`, against the painted colour, in each
  theme; the pairs in DESIGN §2.2 by `design_check.py`
- [ ] Focus order follows reading order; the focus indicator is visible at 3:1 (Do 5)
- [ ] Every control has a name; inputs keep a visible label (Do 6)
- [ ] Targets at least 24 × 24 px, aiming for 44 (Do 7)
- [ ] No meaning carried by colour alone (Do 8)
- [ ] Reduced motion handled; nothing flashes (Do 10)
- [ ] The walks handed to the person for the target — never claimed from code

## Traps

- **Passes in the mock, fails on the screen** → the mock measured the token, the screen paints it at 60 % opacity over
  a photo → measure the composited colour (Do 3).
- **Passes in light, fails in dark** → the pair was checked in one theme → check every theme the product ships.
- **A grey hint text fails at 3.9:1** → secondary text is not exempt → take the next token step down.
- **A custom control is skipped by Tab** → a styled `div` with no role or tab stop → use the platform's control, or
  give it a role, a tab stop and key handling.

## Sources

| Topic | Where |
| --- | --- |
| WCAG 2.2, the success criteria cited here | The W3C's WCAG 2.2 Recommendation and its Understanding documents |
| Target sizes on the platforms | Apple Human Interface Guidelines (Accessibility); Material Design (Accessibility) |
| The product's pairs and any floor above AA | [DESIGN.md](../../../DESIGN.md) §2.2, §9 |
| The gates these checks sit in | [`ui-designer`](../ui-designer/SKILL.md) |
