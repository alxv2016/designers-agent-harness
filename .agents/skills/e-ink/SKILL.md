---
name: e-ink
description: Designs and builds for e-ink (e-paper, electrophoretic, EPD) displays, carried in the skill (references/e-ink.md, and references/drivers.md for the controllers in code) with a panel spec template — how the film works (bistability, slow refresh, ghosting, DC balance, temperature, grey levels, fading); controllers and the bus (SPI, BUSY polarity, reset, run-time detection, RAM planes and windows, rotation and bit order, power states, deep sleep, shared-bus locking, forbidden voltage and OTP commands; the SSD1677 and the SSD2677 — which takes no custom waveform — written out as drivers with their code and pitfalls, and the SSD16xx, UC81xx and IT8951 families compared); waveforms and LUTs (full, partial, greyscale, OTP and custom tables, forcing a temperature slot, frame rate, a budgeted fast-update method that keeps the drive balanced, tuning and measuring); the refresh policy (skip identical frames, partial limit, never two full refreshes back to back, two partials through white, ghost cleaning at a pause); LVGL glue (direct render mode, flush on the last area, byte-aligned dirty areas, no theme, pacing) and e-reader apps on the web and Android; visual design in 1 bit (dithered greys, solid text, opaque fills, depth by line and offset, 1-bit fonts, 2 px strokes, layout that never reflows); no motion, feedback before the glass, paging instead of scrolling; components and their 1-bit states; focus rings, editing mode and input during a refresh; touch decided on lift; accessibility, power and testing on the glass; plus e_ink_check.py (EK1–EK7). Portable — the folder works in any repo. Use when designing or building any screen, component or driver for an e-paper panel, writing a panel's spec, tuning a waveform, choosing a refresh policy, fixing ghosting, fading or a stuck BUSY line, or asked "will this work on e-ink?".
metadata:
  scope: portable
---

# E-ink

How to design and build for an e-paper display, from the controller's waveforms to a focus ring. The rules are kept
in this skill at [references/e-ink.md](references/e-ink.md) (cited `E_INK §n`), the controllers and their drivers in
code at [references/drivers.md](references/drivers.md) (`E_INK_DRIVERS §n`), the evidence behind each technique at
[references/validation.md](references/validation.md) (`E_INK_VALIDATION §n`), the panel's spec template at
[templates/panel-spec.md](templates/panel-spec.md), and the check at [scripts/e_ink_check.py](scripts/e_ink_check.py);
this page holds the rules and the steps. The project's own panel spec and design brief decide its values; the
reference wins over this page — fix the page.

**With the other skills.** This skill adds what e-paper changes to the design skills — `ui-designer` (the gates: a
draft in both refresh forms), `design-system` (tokens recorded per refresh form), `accessibility` (the floors on every
refresh), `typography` (1-bit fonts, sizes from density), `layout` (fixed regions, pages), `motion` (nothing moves),
`touch-and-gesture` (decided on lift) — and to `esp-idf-setup` for a device you drive yourself. Where they disagree on
an e-paper screen, this skill's rule for the glass wins, and the floors never move.

**Portable.** This folder is self-contained and links to nothing outside itself; it names the rest of a kit in
backticks. Copy it into any repo's `.agents/skills/` (or `.claude/skills/`) and it works there. In the agent-harness
kit, `verify.py run` runs the check on `EINK_PATHS`, and the `e-ink` agent applies this skill.

## When to use

- Starting a product with an e-paper screen — the panel's spec first.
- Designing a screen or a component that will be shown on e-paper.
- Writing or changing a panel driver, a refresh policy or the toolkit glue.
- Tuning a waveform, or choosing a refresh mode on an e-reader.
- Ghosting, fading, a stuck BUSY line, a slow or failed refresh.
- Reviewing an e-paper UI, or asked "will this work on e-ink?".

## Rules

### Do

1. **Write the panel's spec before a driver or a screen**, from the datasheet and measurements, each value with its
   source (E_INK §16).
2. **Design every screen in its 1-bit partial form first**, at native size, then its full form; judge both on the
   glass (E_INK §1, §7).
3. **Let the person judge the glass** — a screenshot shows the frame asked for, never the ink (E_INK §15).
4. **Keep one refresh per interaction, and skip a frame identical to the glass** (E_INK §5).
5. **Clean ghosts with a full refresh at a pause, after a counted number of partials; never two full refreshes back to
   back** (E_INK §5).
6. **Draw UI greys as fixed dithers, text and lines solid, words only in black on white or the light dither**
   (E_INK §7).
7. **Nothing moves; answer every press within 100 ms without the glass, then draw the result** (E_INK §8).
8. **Turn pages, never scroll by pixel; decide a swipe once, at the lift** (E_INK §9, §12).
9. **Reserve every state's stroke at rest, and show focus as a ring outside the control** (E_INK §10, §11).
10. **Read input on its own task during a refresh, and queue each press with room for its release** (E_INK §11).
11. **Size type, strokes and targets from the panel's density** — millimetres converted to panel pixels (E_INK §7,
    §12).
12. **Detect the controller, set BUSY polarity from it, and keep one driver per family** — written from its datasheet
    and the driver reference, never ported from another family's code (E_INK §3; E_INK_DRIVERS §1, §4).
13. **Write both RAM planes in full for every image refresh on controllers that drive the whole RAM** (E_INK §3.3).
14. **Keep the drive balanced in any custom waveform, and check its polarity on the glass** (E_INK §4).
15. **Draw a designed last frame before deep sleep** (E_INK §14).
16. **Instrument every refresh with a timing breakdown, and say how proven a technique is** — measured, seen,
    host-tested or unverified, as E_INK_VALIDATION §8 records it; repeat the checks on a new panel (E_INK §15).
17. **Plan waveform work by what the controller allows** — the SSD1677 takes a custom table; the SSD2677 takes none, so
    its levers are the OTP slot and the frame rate (E_INK_DRIVERS §1, §6.3).

### Never

- **Animate, blink, spin or scroll smoothly** (E_INK §8; EK1, EK6, EK7).
- **Use translucency, a shadow, a blur or a gradient** (E_INK §7; EK2, EK3, EK4).
- **Draw a stroke under 2 px, text with anti-aliasing, or a weight under 600** (E_INK §7; EK5).
- **Make grey, colour or a light the only signal** (E_INK §7, §13).
- **Write the panel's voltage registers, or send an OTP-programming command** (E_INK §3.5).
- **Port command code from one controller family to another** (E_INK §3.5).
- **Block the UI task on a busy line, or retry a failed standby on it** (E_INK §18).
- **Copy a refresh time or a waveform from another panel as a value** — measure yours (E_INK §1).

## Procedure

`E` is `python3 .agents/skills/e-ink/scripts/e_ink_check.py`, from the repo root.

### Writing the panel's spec

1. **Gather** — the panel's and the controller's datasheets, the vendor's sample driver, the board's schematic.
2. **Copy the template** into the project's docs as its panel spec, and fill each field with its source (E_INK §16).
3. **Ask the person what only they know** — the board revisions, the use (reading, a dashboard, a device), the
   lighting.
4. **Measure on the board** — refresh time per mode with its conditions; BUSY polarity; ghosting after a page walk.
5. **Fill the design limits** — smallest text, thinnest stroke and target in panel pixels from the density (E_INK §7,
   §12).

### Designing a screen or a component

1. **Read the panel's spec and the design brief** — the levels, the dither codes, the limits, the refresh times.
2. **Draft at native size in both forms** — the 1-bit partial form and the full form — with every state that changes
   the layout (the `ui-designer` skill's first gate).
3. **Draw states in 1 bit** — focus as a ring outside, chosen as inversion or a mark, disabled one step toward the
   page with the reason in words (E_INK §10).
4. **Plan the refreshes** — what each interaction redraws, that it is one refresh, where a full refresh falls, what a
   new screen costs (E_INK §5).
5. **Replace motion** with a step and a non-visual cue; turn lists into pages (E_INK §8, §9).
6. **Check the floors on both forms**, and the words for every state (E_INK §13).
7. **Show the drafts and stop** for the person's yes.

### Building

1. **Driver** — one per family behind one panel interface; detection; BUSY, reset, planes and power from the spec;
   the allow-list of commands (E_INK §3). For an SSD1677 or an SSD2677, follow its section of the driver reference;
   for another controller, its bring-up order (E_INK_DRIVERS §5, §6, §8).
2. **Refresh policy** — in the display layer, as an ordered list of rules, the pure parts host-tested (E_INK §5).
3. **Toolkit glue** — direct render mode, pack on the last area, byte-aligned dirty areas, no theme, input on its own
   task (E_INK §6, §11).
4. **Components** — from the tokens, states reserved at rest, hit areas extended, focus in view without animation
   (E_INK §10, §11).
5. **Run `E`**, fix each hit; build; run on the board; judge the glass with the person.

### Tuning a waveform

1. **Start from the factory waveforms** — measure each mode and each forced temperature slot (E_INK §4.3).
2. **Try the frame rate within the datasheet's list** before a custom table.
3. **A custom table, only where the controller takes one** (the SSD1677, not the SSD2677) — load the factory one
   first, overwrite only the table, keep the drive balanced, check polarity on the glass, set guardrails (E_INK §4.4;
   E_INK_DRIVERS §5.6, §7).
4. **Benchmark with the fixed fixture**, the median of 30 frames per preset, with conditions recorded (E_INK §4.5).
5. **The person picks the default on the glass.**

### Reviewing an e-paper UI (read-only)

1. `E <files>` — EK1–EK7.
2. **Read what the check cannot** — grey as the only signal, words on a dark dither, anti-aliased fonts, a reflow on
   a state change, a ring that changes a size, a refresh per keystroke, two refreshes per press.
3. **Report** each finding with the line, the rule (`E_INK §n`) and the fix; list what only the glass can settle.

## Checks

```sh
python3 .agents/skills/e-ink/scripts/e_ink_check.py            # every e-ink UI file, against the baseline
python3 .agents/skills/e-ink/scripts/e_ink_check.py FILE …     # some files
python3 .agents/skills/e-ink/scripts/e_ink_check.py --test     # the self-test
```

- [ ] (script) `E` — prints `EK1–EK7 e-ink patterns — 0 hits`; baseline 0
- [ ] The panel's spec exists, each value with its source and each measurement with its conditions (E_INK §16)
- [ ] Every screen drafted in both refresh forms, and both judged on the glass (E_INK §1, §7)
- [ ] One refresh per interaction; the partial limit and the back-to-back rule in the policy (E_INK §5)
- [ ] No grey, colour or light as the only signal; words on every state (E_INK §7, §13)
- [ ] Focus visible for buttons, never confused with chosen; every action reachable by buttons (E_INK §11, §13)
- [ ] Every press answered within 100 ms without the glass (E_INK §8)
- [ ] No voltage or OTP command in the driver; one driver per family (E_INK §3.5)

## Traps

- **A screen looks right in the mock and falls apart after a tap** → it was drawn in greys → draw the 1-bit form first
  (Do 2).
- **Ghosts build until the screen is unreadable** → no partial limit, or no clean at a pause → count partials (Do 5).
- **A press seems ignored** → the result arrives half a second later with no cue → a tick within 100 ms (Do 7).
- **Neighbours jump when a control is chosen** → a border that appears only in that state → reserve it at rest (Do 9).
- **The device freezes for seconds** → the UI task waits on BUSY → never block it on the busy line (Never).
- **The black fades** → the supply powered off after the refresh → keep it on between refreshes (E_INK §18).
- **A borrowed waveform draws the inverse** → polarity differs per panel → check on the glass (Do 14).

## Sources

| Topic | Where |
| --- | --- |
| Every rule, the panel, waveforms, refresh, design, components, focus, touch, traps | [references/e-ink.md](references/e-ink.md) |
| The SSD1677 and SSD2677 drivers in code, the common controllers, bringing up a new one | [references/drivers.md](references/drivers.md) |
| What was measured, seen on the glass and host-tested, what is not yet validated, confidence by technique | [references/validation.md](references/validation.md) |
| The panel spec | [templates/panel-spec.md](templates/panel-spec.md) |
| The check | [scripts/e_ink_check.py](scripts/e_ink_check.py) |
| Controllers, waveform modes, LVGL, WCAG 2.2, EN 301 549 | The reference's Sources (E_INK §19) |
