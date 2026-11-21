# E-Ink

How to design and build for an electrophoretic (e-ink, e-paper) display: how the film works, how controllers and
waveforms drive it, a refresh policy that keeps ghosts away, the UI toolkit glue, visual design that survives 1-bit
partial refreshes, motion and feedback at a few frames a second, paging instead of scrolling, components, focus and
input, touch, accessibility, power, testing on the glass, what a panel's spec must record, and the traps. People read
it to design a screen or a component for e-paper with reasons; coding agents read it, through the `e-ink` skill,
before they write a panel spec, draw a mock, write a driver or a refresh policy, tune a waveform or review an e-paper
UI.

**Where it lives.** In the `e-ink` skill, beside [its SKILL.md](../SKILL.md), with the driver reference
[E_INK_DRIVERS](drivers.md) (the SSD1677 and SSD2677 in code, the common controllers, bringing up a new one), the
evidence behind every technique in [E_INK_VALIDATION](validation.md) (measured, seen on the glass, host-tested, or
not yet validated), the [panel spec template](../templates/panel-spec.md) and the
[check](../scripts/e_ink_check.py). The skill folder is self-contained: copy it into any repo's `.agents/skills/` and
these come with it.

**Platforms.** The principles hold for any e-paper screen. Guidance labelled **Embedded (ESP-IDF, LVGL)** is for a
device you drive yourself; **Web** and **Android** cover apps that run on e-readers and e-ink tablets, where the system
owns the driver and the waveform modes but your design still meets the same glass.

**Numbers.** Every refresh time, size and limit given here is an example measured on one panel or a datasheet's
value, labelled as such. Panels, controllers, waveforms and temperatures differ: measure yours and record it in its
spec (§16).

**Stability.** Cite this doc as `E_INK §n`. Do not renumber; add new material under the next free number.

| § | Section | Look here for |
| --- | --- | --- |
| 1 | [Using this reference](#1-using-this-reference) | The glass decides; the 1-bit form first; measure, then decide |
| 2 | [How e-paper works](#2-how-e-paper-works) | Particles, bistability, slow refresh, ghosting, DC balance, temperature, grey levels |
| 3 | [Panels, controllers and the bus](#3-panels-controllers-and-the-bus) | SPI, BUSY, reset, detection, RAM planes and windows, power states, sleep, forbidden commands |
| 4 | [Waveforms](#4-waveforms) | Full, partial, grey; factory and custom tables; temperature slots; frame rate; a fast budgeted method |
| 5 | [The refresh policy](#5-the-refresh-policy) | When to draw full, partial, grey or nothing; ghost cleaning; never two full refreshes back to back |
| 6 | [The UI toolkit](#6-the-ui-toolkit) | LVGL's render mode, flush and rounder; frame buffers; pacing; web and Android modes |
| 7 | [Visual design](#7-visual-design) | Black and white first, dithered greys, contrast, opaque fills, depth, type, strokes, icons, layout |
| 8 | [Motion, feedback and latency](#8-motion-feedback-and-latency) | The refresh is the motion; feedback before the glass; waiting; self-updates |
| 9 | [Lists, scrolling and paging](#9-lists-scrolling-and-paging) | Pages, not pixels; page sizing; the last page; the position indicator |
| 10 | [Components](#10-components) | The kit, its sizes and states in 1 bit, hit areas, reserved strokes |
| 11 | [Focus and input](#11-focus-and-input) | The ring, focus order, editing, back, input during a refresh, a second press |
| 12 | [Touch](#12-touch) | Targets, deciding on lift, swipes, who owns a drag |
| 13 | [Accessibility](#13-accessibility) | Contrast on every refresh, size, buttons first, latency feedback, flashing, closed functionality |
| 14 | [Power and lifecycle](#14-power-and-lifecycle) | Energy per refresh, standby, deep sleep, the last frame, temperature |
| 15 | [Testing on the glass](#15-testing-on-the-glass) | Timing breakdowns, fixtures, benchmarks, host tests, judging the glass |
| 16 | [The panel spec](#16-the-panel-spec) | What a panel's spec must record |
| 17 | [Colour panels and front lights](#17-colour-panels-and-front-lights) | What changes with colour film and a light |
| 18 | [Traps](#18-traps) | Symptom, cause, fix |
| 19 | [Sources](#19-sources) | Where these rules come from |

---

## 1. Using this reference

**The glass is the only judge: design in the 1-bit partial form first, measure on the panel, and let the person
decide what looks right on it.**

- **Most frames are partial refreshes, and a partial is 1 bit** — design and review every screen in that form first,
  then its full form (§5, §7).
- **A screenshot shows the frame you asked for, not the ink** — ghosting, fading, polarity and dither are judged by
  eye or in a photograph of the panel, and the person's verdict is recorded (§15).
- **Measure before deciding** — refresh time, ghosting and drive limits depend on the controller, the waveform and
  the temperature; a number from another panel is a starting point, never a value.
- **Tag each fact by where it came from** — the datasheet, vendor code, measured, seen on the glass, derived or
  unverified — and date measurements (§16).

---

## 2. How e-paper works

**Charged particles move through a fluid when a voltage is applied; they stay put without power, move slowly, and
leave traces when they are not driven all the way.**

- **The film** — black and white pigment particles of opposite charge sit in microcapsules or microcups between a
  common electrode (VCOM) and each pixel's electrode; the pixel's voltage relative to VCOM pulls one colour to the
  front.
- **Bistable** — the image stays with the power off; driving costs energy, holding costs none. The last frame before
  sleep stays on the glass, so it is designed (§14).
- **Slow** — particles move physically, so the controller drives each transition as a sequence of voltage pulses over
  many frames: the waveform (§4). A full refresh takes about a second, a partial a few hundred milliseconds (examples:
  full 0.9–1.5 s, partial 370–520 ms, four-grey 1.0–1.3 s, measured on two 800×480 panels at room temperature).
- **Ghosting** — a faint copy of earlier images, from pixels not driven all the way, charge left by uneven driving,
  and partial waveforms that skip the clearing phases. It builds over partial refreshes; a full refresh, which
  flashes black and white, clears it.
- **DC balance** — over every transition, each pixel's net drive returns to zero: as much one way as the other. An
  unbalanced drive can leave a ghost in the film for good.
- **Temperature** — particles slow in the cold. Controllers keep a waveform per temperature band and pick one from a
  sensor; cold waveforms are longer. Read temperature from an ambient sensor, not one beside a warm processor.
- **Grey levels** — many panels show 4 or 16 levels only through a dedicated greyscale full refresh; every partial
  is 1 bit, and a grey thresholds to black or white (example: levels 0–1 black, 2–3 white).
- **Paper, not ink** — the white is paper-grey and the black is not ink-black, so the nominal 21:1 between the
  extreme levels is an upper bound; the finish (glossy or matte) varies by panel revision.
- **Fading** — on some controllers, cutting the drive supply right after a refresh lets black fade visibly within
  seconds; holding the supply between refreshes, or a hold or discharge phase, keeps it (§3, §18).

---

## 3. Panels, controllers and the bus

**A controller takes commands and pixel data over SPI, signals BUSY while it drives, and holds the waveform tables;
each family has its own commands, polarities and traps, so one driver per family.**

- **Two controllers this reference draws on** — the **SSD1677**, an SSD16xx-family part that takes a custom waveform,
  and the **SSD2677**, a Solomon Systech part with a UC81xx-style command set that takes **no custom waveform**. Their
  drivers, in code, with each one's pitfalls, and the other common controllers (SSD1680-class, UC8151, UC8179,
  IT8951) are in [E_INK_DRIVERS](drivers.md); this section holds the rules every controller shares.

### 3.1 The bus

- **Four-wire SPI** — chip select, clock, data, a data/command line (low for a command byte, high for its data), reset
  and BUSY. Reads (ID, temperature) often come back on the same data line in three-wire half-duplex mode.
- **Clock limits differ for reads and writes** — example: reads up to 2.5 MHz, writes up to 20 MHz; two device
  handles on one chip select, driven by hand, give a slow one for reads and a fast one for writes.
- **Stream a frame in chunks, encoding the next while the current one is on the wire** — example: an 800×480 frame is
  48,000 bytes at 1 bit per pixel and 96,000 at 2; at 20 MHz the second takes about 39 ms; double-buffered 4 KB DMA
  chunks beat the vendor's driver by three times.
- **A shared bus needs one lock for the whole panel sequence** — a command and its data span several transactions; a
  storage card's transaction in the middle corrupts the refresh, and the result looks like ghosting. Mount a card on a
  shared bus first so it enters SPI mode before panel traffic, initialise the bus once, never free it, and set unused
  pins to "not connected" (−1), never 0.

### 3.2 BUSY, reset and detection

- **BUSY's polarity differs by family** — SSD16xx-family parts (the SSD1677) hold it high while busy; UC81xx-style
  parts (the SSD2677) hold it
  low. Wrong polarity makes every wait return at once or time out. Set it from the detected controller.
- **Wait with a timeout and yield while polling** — examples: 8 s for one family, 30 s for another. A timeout is an
  error: treat the panel state as unknown, reset, and draw the next frame full.
- **Reset pulses differ** — examples: 10 ms low then 10 ms high, or 20 ms low then 10 ms high.
- **Detect the controller at run time when one firmware drives several panels** — reset, send an ID command, read a
  byte; a failed read is an error, never a silent fallback; then create that family's driver behind one interface.

### 3.3 RAM, windows and pixel order

- **Two RAM planes on SSD16xx parts** — a "new" image and an "old" (or red) image; a partial refresh compares them per
  pixel. Keep a copy of the last frame shown, to write the old plane.
- **A RAM window scopes where writes land, not what is driven** — on these parts every refresh drives the whole RAM,
  so stale data outside a window lights up on the next refresh. Write both planes in full for every image refresh.
- **A partial window on UC81xx parts drives only the box** — the upload shrinks, but drive time does not, because the
  gates still scan the whole panel; a full or grey refresh, or a reset, turns partial mode off.
- **Rotation and byte order are the driver's job** — native RAM is often landscape; map the UI's coordinates during
  packing, with one build option for 180° that turns touch with it. Some parts mirror X in hardware; others need each
  row streamed right to left.
- **Bit order and polarity** — example: 1 bit per pixel, most significant bit first, 1 = white; 2 bits per pixel,
  0 = black … 3 = white. Some parts want 2 bits even for monochrome partials (old and new interleaved): use 256-entry
  lookup tables to widen bytes.
- **Align horizontal windows to whole bytes** — X ranges move in steps of 8 pixels on many parts; round a dirty area
  out to byte columns (§6).

### 3.4 Power states and sleep

- **Power the drive supply once and drive many times** — re-enabling the clock and the high-voltage supply for each
  drive cost about 80 ms per drive on one part. Track whether the supply is on.
- **SSD16xx display-update control** — a byte selects clock on, analog (high-voltage) on, load temperature, load
  waveform, display, analog off and clock off; examples: one value draws a full refresh and leaves the supply on,
  another draws a partial with the loaded waveform, another only powers on. Read your datasheet's table and keep the
  sequences you use as named constants.
- **Deep sleep** — draw the full refresh, wait for BUSY, then send the deep-sleep command (examples: `0x10` with `0x03`
  on SSD16xx; power off then `0x07` with check byte `0xA5` on UC81xx). Waking needs a hardware reset and a full
  re-initialisation. Never sleep mid-refresh; if the sleep command failed, keep the rail powered.
- **Rails** — a load-switched supply needs its settle time after enable (example: 100 ms). Coming out of standby adds
  the supply's start-up to the next drive (example: 83 ms).

### 3.5 What never to send

- **Never write the gate, source or VCOM voltage registers** — use the panel's own values from its OTP, loaded after
  each reset.
- **Never send OTP-programming commands** — one family's partial-window opcodes are another family's OTP program and
  burn commands. Never port command code between families; keep an allow-list of the commands each driver may send,
  and check it automatically.
- **Keep undocumented vendor steps until each is proven unneeded** — one left out made the full refresh drive a
  partial-length waveform (§18).

### 3.6 Driver state and layers

- **Track the state** — initialised, powered, in standby, which waveform is loaded (latch only when it changes),
  whether a valid last frame exists, whether RAM holds images or masks. Any failure clears it all, so the next refresh
  resets and draws full.
- **Layers** — a bus (SPI, data/command, reset, BUSY with polarity and timeout, streaming; no locking inside); one
  driver per family behind one panel interface (refresh by mode, settle, optional fast scans, standby, sleep, set
  temperature, set tuning, the last refresh's timing breakdown); board code that detects and picks the driver; a
  display layer that owns the refresh policy, packing, rotation and the toolkit glue.

---

## 4. Waveforms

**A waveform is the table of voltage pulses that moves each pixel from its old state to its new one; its length sets
the refresh time, its completeness sets the ghosting, and its balance protects the film.**

### 4.1 What a waveform holds

- **Per transition, a sequence of phases** — each a voltage level (0 V, a positive drive, a negative drive, sometimes
  a second positive level) for a number of frames; phase groups repeat; VCOM has its own row; a frame rate sets the
  frame period.
- **Example layout (an SSD16xx-family part)** — a custom table of about 105 bytes: phase levels for five tables at 2
  bits each, each group's phase lengths in frames and its repeat count, then the frame rate. The two RAM bits of a
  pixel choose which table drives it; one table drives VCOM. Byte counts, phase counts and level encodings differ
  across families: read your datasheet.

### 4.2 Kinds of waveform

| Kind | Clears ghosts | Speed | Levels | Use |
| --- | --- | --- | --- | --- |
| Full (GC-style) | Yes — flashes black and white | Slowest | 2, or many | First frame, the ghost-cleaning refresh, large changes |
| Partial or fast (DU, A2-style) | Little — ghosts build | Fast | 2 | Most interactions |
| Greyscale (GC16, GL16-style) | Yes | Slow | 4 or 16 | A still image or photograph |

- **IT8951-family controllers name these modes** INIT, DU, GC16, GL16 and A2; e-readers expose the same trade-off as
  refresh modes (§6).

### 4.3 Factory and custom waveforms

- **Panel makers program waveforms per temperature band into the controller's OTP** — use them first.
- **Some controllers take a custom table** (SSD16xx parts such as the SSD1677); others have no documented table-write
  command, and their only levers are the frame rate and which OTP slot is picked — the **SSD2677 takes no custom
  waveform**: its panel-setting bit only skips the OTP load (E_INK_DRIVERS §6.3).
- **Load the factory waveform and voltages first, then overwrite only the table** — the panel keeps its own VCOM and
  voltages.
- **Pick an OTP slot by forcing a temperature** — a "fixed temperature" setting plus a written value, then a load
  command. The value then indexes a slot, not the real temperature, and makers rarely document what each band holds:
  sweep it and measure each slot's drive time (example: the same partial from room temperature to 70 °C, a much slower
  one at 90 °C).
- **The frame rate is a lever** — a faster frame rate shortens the same waveform (example: 85 Hz cut a partial from
  416 to 369 ms with no ghost seen; 75 Hz was no faster). Keep a datasheet allow-list of rates and refuse others.

### 4.4 A fast budgeted method

For small changes on controllers that take custom tables, drive in short scans instead of one long waveform:

- **The planes hold masks, not images** — one plane means "push toward black", the other "push toward white",
  neither means hold. The custom table drives one short phase toward each colour and holds the rest.
- **Each changed pixel gets a budget of scans toward its new colour** — kept as a small counter per pixel (bit-sliced
  across planes); each scan drives every pixel with budget left, then counts down. A pixel that changes again before
  it finishes starts a fresh budget the other way — the same total drive each way, so the drive stays balanced.
- **Power on once, then drive each scan with the display step alone** — re-powering per scan costs most of the gain.
- **Upload only the rows and byte columns in play, unioned with the last scan's box** — so the last scan's masks are
  cleared to hold.
- **Tune frames per scan and the budget together, and let the person judge the glass** (example presets: 2 frames ×
  12 scans gave about 85 ms per animation frame and about 0.35 s for a pixel to finish; 3 × 10 and 4 × 10 were
  slower). Enforce limits (example: 1–8 frames, budget 2–15).
- **Why budgets** — with one short pulse per frame, a pixel that has not finished is never driven again; a budget
  keeps driving it until done while new changes start at once.
- **Guardrails** — only within a measured temperature window, else the factory partial; only for small changes
  (example: up to 15 % of pixels), else the factory partial; never for full refreshes; never "re-saturate" unchanged
  pixels, which drives one way and builds charge.
- **Settle before switching** — before changing tuning, sleeping, or after a failed scan, drive any part-driven pixel
  the rest of the way with the factory partial (write the old plane as frame XOR touched, so each touched pixel reads
  as a full transition). Never cut a budget short.

### 4.5 Tuning and measuring a waveform

- **Benchmark with a fixed fixture** — a black bar growing and shrinking across a white track, 30 partial frames per
  preset, the median taken, each preset starting from a full refresh, the forced full refresh left out of the times.
- **Record with each measurement** — date, firmware build, toolkit and SDK version, power source, room temperature;
  a toolkit upgrade can add milliseconds per frame.
- **Verify polarity on the glass before trusting a borrowed table** — which voltage drives white differs between
  panels (§18).
- **Bisect undocumented vendor commands** — leave each out, compare drive times, then judge the glass.

---

## 5. The refresh policy

**Draw nothing when nothing changed, a partial for most changes, a full refresh to clean ghosts at a quiet moment,
and greyscale only for a still image — one refresh per interaction.**

1. **Skip a partial whose 1-bit frame equals the glass** — example: a tap that only moved focus, with nothing drawn
   differently.
2. **Greyscale when an image asks for it**, on a still screen.
3. **Full on the first frame, when asked, or when the partial count would pass its limit** (example: a full after 20
   partials; the full resets the count).
4. **Never two full refreshes back to back** — a full or grey refresh asked for too soon after the last waits out the
   previous one's measured duration; it is held, never dropped. A failed refresh sets no wait, so recovery never waits
   on a timeout.
5. **A failed partial is redrawn full at once from a reset.**
6. **A new screen** — one partial on some panels; on others, two partials through white (everything white, then the
   new screen), counted as two, because one partial leaves the old page's ghost. A full refresh per page is clean but
   slower and flashes.
7. **A small change goes to a fast method where one exists** (§4.4); otherwise the factory partial.
8. **Clean ghosts at a pause, never mid-motion** — after a run of fast scans (example: 150 scan frames), a full
   refresh at the next idle pause.
   A large high-contrast overlay closing also earns a full refresh.
9. **Standby after an idle second, where the panel holds its image** (§14).

- **One refresh per interaction** — a focus move and a value change from one press land in one frame; the toolkit's
  render pass collects every dirty area and hands the frame over once (§6).
- **Self-updates have floors** — a readout at most every 5 s, a clock once a minute (examples); each is a refresh,
  and on a still screen the partial count makes them a periodic full refresh too.
- **A refresh that must wait shows the latest state when it runs.**

---

## 6. The UI toolkit

**Let the toolkit redraw only what changed into a full-screen buffer, pack it to the panel's format, and send one
frame per render pass.**

### 6.1 Embedded (ESP-IDF, LVGL)

- **Direct render mode with a full-screen 8-bit buffer** (`LV_COLOR_FORMAT_L8`) — LVGL redraws only invalidated areas
  into it; the flush callback packs each area into a persistent 1-bit native frame (rotate, then threshold or dither)
  and hands the frame to the driver only on the last area (`lv_display_flush_is_last`).
- **The driver finds the changed box by comparing with the last frame** — rows first, then byte columns.
- **Round dirty areas to byte columns** with LVGL's invalidation rounder (`LV_EVENT_INVALIDATE_AREA`), where the
  controller's windows move in steps of 8.
- **Buffers** — the 8-bit render buffer can sit in external RAM; the 1-bit frame, written bit by bit, in internal RAM;
  a separate frame for greyscale; a copy of the glass to skip identical frames. After a grey refresh the 1-bit "old
  frame" is stale, so the next 1-bit frame is full.
- **Thresholds and dithers** — 8-bit values below the midpoint are black, the rest white; reserved values one step off
  the plain greys are drawn as fixed dither patterns locked to the panel's pixel grid (§7).
- **Compile no LVGL theme** — a theme brings pressed tints, transitions and shadows; style every widget from the
  project's tokens, with `anim_duration` 0 on toggles.
- **Pace the toolkit to the glass** — a frame waits for its refresh; a background fast-scan task runs below LVGL's
  priority and yields after each scan while a frame waits for the shared engine lock.
- **Read input on its own task** (§11).

### 6.2 Web and Android on e-readers

- **The system owns the waveform** — e-ink tablets and readers expose refresh modes (a fast monochrome mode, a
  quality mode, a periodic full refresh) per app or per view; choose the fast mode for interaction and the quality
  mode for reading, and let the system's ghost cleaning run.
- **The same design rules hold** — no animation or smooth scroll, opaque fills, no shadows or gradients, black and
  white controls, paging, feedback that does not depend on motion; the check reads CSS for them.
- **Respect the system's reduced-motion and contrast settings** — e-readers often set them; treat motion as off
  whatever they say.

---

## 7. Visual design

**Black and white carry the system; every grey a control needs is a fixed dither, text is solid, strokes are at least
2 px, and nothing relies on a tone a partial refresh cannot show.**

- **Design every screen in its 1-bit partial form first**, at native size, then its full form; judge both on each
  panel the product ships with.
- **True greys only for images** — a photograph or artwork drawn with a greyscale full refresh on a still screen; the
  next partial collapses it.
- **A UI grey is a dither** — a fixed pattern locked to the pixel grid, which survives every refresh (example: dark
  grey = 1 white pixel in 4, light grey = 3 in 4). A greyscale refresh reads the same codes as true greys.
- **Text and lines are never dithered** — a grey text role draws solid: dark grey as black, light grey as white. So
  grey secondary text becomes black after a partial and is never the only difference between two things. The one
  exception is a disabled control's words (§10.2).
- **Words only in black on white or on the light dither** — derived from each dither's average luminance against the
  panel's nominal levels: black on the light dither about 16:1; white on the dark dither about 3.5:1, and its edges
  break up. A dither's edge against white is about 1.3:1: identify
  controls by a solid part and words, never by a dithered edge.
- **No mid-grey text, no translucency** — translucency blends to greys that then threshold; fills are opaque.
- **Depth is a line and a hard offset** — a 4 px outline and a solid 6 px offset on two sides (example values),
  never a blur, a shadow or a gradient, which are greys a partial throws away or bands into steps.
- **Type** — compile fonts at 1 bit per pixel (no anti-aliasing), so strokes stay solid; a pixel font on a grid at
  sizes that are whole multiples of its cell puts every stroke on whole pixels; weights of at least 600; minimum
  size from the panel's pixel density (example: 20 px at 235 ppi, about 6 pt), body larger (example: 30 px);
  hierarchy from size and weight, never grey alone; tabular figures so changing numbers redraw the same box; no
  letter spacing; ship only the glyph ranges the strings use, and check every drawn string against them.
- **Strokes** — nothing under 2 px; examples: 3 px control outlines, 4 px focus ring and overlay edge, 6 px editing
  ring.
- **Icons** — 1-bit art made from large source art by box-averaging, thresholding at half and packing as 1-bit alpha;
  no stroke under 2 px; a word beside every meaningful icon, except a small closed set of conventional glyphs.
- **Layout that never moves** — fixed regions in the same place on every screen; every state's stroke reserved at
  rest, so no variant changes size; labels shortened, never wrapped or cut, on controls; whole-pixel sizes, never
  scaled at run time. A reflow redraws a large area, and a large area costs a slower refresh or a full one.
- **Corner radii nest** — an inner radius is the outer radius minus the gap.
- **Tokens record both forms** — colours stored as panel levels with their hex; each colour role's full-refresh and
  partial-refresh value; contrast pairs proven on both; spacing, strokes and radii in panel pixels; motion as steps;
  the refresh constants (partial limit, feedback time, wait delay, self-update floor) beside them.

---

## 8. Motion, feedback and latency

**Nothing animates: the refresh is the motion. Every press is answered at once without the glass, and then by its
result.**

- **No animation, no spinner, no blinking cursor, no marquee** — each frame of motion is a refresh, so a 300 ms
  transition is a run of partials that ghosts. Every motion token is a step: zero duration, one jump.
- **No pressed state** — a pressed tint arrives with the result, half a second later. Answer a press with an immediate
  non-visual cue (a short tick within 100 ms, before the panel changes), then draw the result.
- **An ignored press gets the tick alone; only a hold in progress is drawn while it lasts** (a recording, a hold to
  confirm).
- **Change state in one frame** — a toggle's thumb, fill and state word change together; programmatic setters emit no
  change event, so they never trigger a second refresh.
- **Progress steps, never glides** — a segmented bar stepping no faster than the self-update floor, with the step in
  words.
- **A wait shows nothing for its first second, then still words** saying what is happening ("Saving the note"), never
  "Loading" and never a spinner.
- **Nothing leaves on a timer** — a message stays until the next screen change; a dismissal timer spends a refresh and
  breaks the no-time-limits rule.
- **Full-screen inversion is a mode, not an effect** — it costs a full refresh and ghosts more; keep inversion to mean
  "chosen" (§10).

---

## 9. Lists, scrolling and paging

**Content turns by page and never scrolls by pixel: a page turn is one refresh, a pixel scroll is a refresh per step.**

- **A page is a whole number of rows** — height = rows × row height + (rows − 1) × gap.
- **Pad the last page** to a full page, so every page is as tall as the first and the toolkit never clamps a short
  last page back into the previous one.
- **A text view's page is its lines minus one**, so the last line of a page opens the next.
- **Momentum, elastic overscroll and scroll chaining off** — a swipe turns one page, decided on lift (§12).
- **Keep focus in view without animation** (§11).
- **The position indicator** — a lane of separate pieces (track, gap, thumb, gap, track), the thumb never shorter
  than a dot; only the first and last page touch the ends, interior pages stand clear of them; long lists spread
  interior pages evenly, so every turn visibly moves the thumb; hidden when everything fits; in the same place on
  every page.
- **The position in words** — "Page 2 of 3" beside the indicator, updated on each turn.
- **Guard scrolls the code makes** — a "settling" flag around every scroll the paging logic makes itself, or its own
  scroll events re-enter the handlers until the stack overflows.

---

## 10. Components

**Every control is a 1-bit drawing whose states never change its size: focus is a ring outside it, chosen is
inversion or a mark, disabled is one step toward the page with the reason in words.**

### 10.1 Rules every component follows

- **No pressed state, no theme** — remove every inherited style; only the root of a widget takes presses; its parts
  pass events up and never swallow a touch.
- **Reserve each state's stroke at rest** — a border that appears only in some states is drawn transparent at rest
  and made opaque in that state, so neighbours never move.
- **Hit area over drawn area** — a control drawn smaller than the target extends its click area instead of growing;
  indicators take no presses and no focus.
- **Words carry what colour would elsewhere** — on/off, failed, disabled and position each in words.
- **One API shape** — a constructor that returns the widget (or a struct of its parts), setters for state that take
  an "enabled" flag and its reason, and emit no event; user actions emit the change event.

### 10.2 States in 1 bit

| State | Drawn as |
| --- | --- |
| Focused | A ring outside the control, with white between (example: 4 px, 4 px clear) |
| Editing | A thicker ring (example: 6 px) and words saying what the buttons do |
| Chosen, on | Inversion (black fill, white words), a black edge, or a mark (a dot, a check) — never the ring, never grey alone |
| Disabled | The fill and the edge one step toward the page — black becomes dither, dither becomes white — inside a solid outline; the words in a sparse dither one step lighter than their ground (example: one black pixel in sixteen on a light-dither face, one in eight on the white page), the one text drawn as a pattern, exempt from contrast as an inactive control (WCAG 1.4.3) and never the only sign of the state; the reason in solid words; skipped by the buttons; explain rather than disable where possible |
| Busy | The label says what it is doing |
| Done, failed | In words |

### 10.3 The kit

| Component | Shape (example values on a 235 ppi panel) | E-paper choices |
| --- | --- | --- |
| Button | 64 px high; action (black fill), outline (3 px), tonal (light dither), text-only | One action per screen; the 3 px edge reserved on every variant; label shortened by arithmetic (characters × advance), never wrapped; destructive by its words |
| Icon button | 64 px square, glyph from a closed set | Its action named in words nearby; Close never deletes |
| Toggle and row | Track 96 × 44, thumb 52 × 36 | Thumb jumps in the frame the state changes; the state in words; the whole row toggles; the hit area extended to the target |
| Value row, list row | 64 or 80 px; name, value or a supporting line | No dividers inside the ring's reach; value ends in "…" only when the full words are one press away |
| Chip, segment | 64 px high; chosen as a black edge or a black pill | Each segment a focus stop; the track's inset equals the ring's reach |
| Radio, choice card | Card with a ring mark (one) or a box (many) | Chosen is the mark alone; the card never changes |
| Slider or stepper | Dithered track, black fill, white knob | OK enters editing, UP/DOWN step, OK leaves; one partial per step; value in words |
| Progress, steps, page dots | Thin round-capped pieces | Not controls; failure drawn hollow and said in words |
| Text view | Words on a fixed line height, no box | Read by pages; OK opens for reading, UP/DOWN turn pages |
| Dialog, sheet | 4 px outline and a solid offset | One action plus Cancel; focus opens on Cancel when destructive; a full refresh on closing a large one |
| Status line | Words in a fixed region | Stays until the next screen change; no toast |

---

## 11. Focus and input

**Focus is a ring drawn outside the control that never changes layout, moves with the buttons, stays in view without
animating, and comes back to where the person left it.**

- **The ring is an outline under keyboard-style focus only** (LVGL: outline width and padding under
  `LV_STATE_FOCUS_KEY`) — an outline is not layout, so showing it reflows nothing; its radius follows the control's.
- **The ring's reach sets the spacing** — focus stops at least twice the reach apart (example: 16 px), and every
  container between a control and the page widens its extra draw area (`LV_EVENT_REFR_EXT_DRAW_SIZE`) so the ring is
  not clipped.
- **One focus group per screen, wrapping** — each screen clears the group, adds its controls in reading order, Back
  last. Clearing the group also leaves editing mode.
- **Touch never shows the ring** — a tap still moves focus, so going back returns there, but the frame is identical
  and skipped; a screen opened by touch shows no ring. The first button press can reveal the ring without moving it.
- **Going back restores focus to the control that opened the screen**; a destructive dialog opens on Cancel;
  overlays take focus and return it on close.
- **Keep focus in view without animation** — turn off the toolkit's scroll-on-focus (LVGL:
  `LV_OBJ_FLAG_SCROLL_ON_FOCUS`), and on focus scroll to view with animation off, plus the ring's reach, in one shared
  place.
- **In a paged list**, focus leaving the page turns to the page that holds it; a swipe moves focus to the new page's
  first row.
- **Editing mode for a slider or a text view** — OK from the buttons enters it, a tap never does; losing focus leaves
  it; while editing, UP/DOWN reach the control as keys; the editing ring outranks the focus ring; words say what the
  buttons do. Remove arrow-key scrolling where a key handler turns pages, or both fire.
- **Back is a long hold of OK** (example: 1 s), measured by the input task so it works even when a refresh blocked the
  UI, and run after the current event because it deletes the screen focus points into.
- **Read input on its own task during a refresh** — a task above the UI's priority polls buttons and touch (example:
  every 10 ms), sounds the tick at once, and queues each press and release for the toolkit to replay one per read. A
  short press inside a 1.6 s refresh is never lost and moves focus once.
- **Queue a press only if there is room for its release** — a lost release leaves a stuck key or finger; a key that
  finds the queue full is seen again on the next poll.
- **OK acts on release; UP and DOWN on press** — a hold can then become Back. Held UP or DOWN repeats at the
  long-press time, and repeats are paced by the refresh.
- **A second OK before the first one's frame lands is dropped, but still ticks** — it would act on a screen the person
  has not seen; UP and DOWN always move focus to the latest place.

---

## 12. Touch

**Targets are physical sizes converted to panel pixels, every action fires on lift, and a swipe is decided once at the
lift with nothing following the finger.**

- **Targets from millimetres, not from phone pixels** — at least WCAG 2.2's 24 CSS px (6.35 mm), and aim for about
  9 mm; convert with the panel's density (example: 64 px = 6.9 mm at 235 ppi).
- **Actions on release** (LVGL: `LV_EVENT_CLICKED`, never `LV_EVENT_PRESSED`).
- **A swipe turns one page and is decided on lift** — the paged view claims vertical drags (chaining, momentum,
  gesture bubbling and the scrollbar off), puts its scroll straight back on each move so nothing moves under the
  finger, keeps a ring of recent samples, and decides once at the lift.
- **Example thresholds, to be judged under a finger** — turn on net travel of one target (64 px), or on a flick of
  24 px with 12 px in the same direction in the last 100 ms; a rested finger places and turns nothing; a drag pulled
  back turns nothing; one swipe is one page however fast; nothing wraps at the ends.
- **Decide at the lift event** (LVGL: `LV_EVENT_SCROLL_THROW_BEGIN`), not at scroll end, which arrives after a refresh
  of a second or more and reads a flick as a rest. Gesture events do not fire while another object scrolls.
- **Read only finger drags on the view** — check the active input device and the scroll object, so a scroll made by
  a key, by focus or by the code is ignored.
- **Who owns a drag** — a vertical drag that starts on a list or a text view belongs to it and cancels the tap; a
  slider takes horizontal drags (set on lift, to the nearest step) and leaves vertical ones to the page.
- **Every gesture has a button path** — DOWN and UP turn pages; OK, UP and DOWN step a slider.

---

## 13. Accessibility

**The floors hold on every refresh the panel makes, with every action reachable by buttons and every press answered
before the glass can answer.**

- **Contrast on both forms** — 4.5:1 for text and 3:1 for non-text (WCAG 2.2, 1.4.3 and 1.4.11), met on the full and
  the partial form; nominal level ratios are upper bounds, so measure the real white and black where you can.
- **Size** — nothing under the minimum the panel's density gives (§7); large text by WCAG's definition only where it
  meets it in points; a larger-text setting where people need one.
- **Buttons first** — every action reachable with a few physical buttons, for wet hands, gloves or a tremor; focus
  always visible for button users; focus never confused with chosen.
- **Latency feedback** — a tick within 100 ms on every press, a distinct tone and words for every outcome; a person who
  cannot hear the tick needs another early cue (a haptic, a status light).
- **Motion and flashing** — nothing animates, so reduced motion is the default; full refreshes are rare and never back
  to back, and the flash of a full refresh is checked against the three-flashes threshold (WCAG 2.3.1).
- **No time limits** (WCAG 2.2.1) — nothing dismisses itself; sleep never loses work.
- **Colour, grey or a light never the only signal** — state in words; a status light's meaning also on the screen.
- **Closed functionality** (EN 301 549) — without a screen reader or speech, say openly who the device does not serve,
  and put every outcome in visible words and a sound.
- **Light** — e-paper reads like print in sunlight; with a front light, check contrast with it on and off (§17).

---

## 14. Power and lifecycle

**Energy goes into driving, so change the glass only when something changed, over the smallest area, in the fewest
refreshes, and sleep with a designed frame on the glass.**

- **Skip identical frames; batch changes; respect the self-update floors** (§5).
- **Standby after an idle moment** — turn the drive supply off after about a second idle where the panel holds its
  image; keep it on where powering off makes black fade, and measure idle current both ways before choosing.
- **Deep sleep with a designed last frame** — draw it full, sleep the controller, then cut the panel's rail; on wake,
  reset, re-initialise and draw full. Assume the panel's state is unknown after any wake or failure.
- **Temperature** — re-read the ambient sensor on a slow cadence while idle (example: once a minute), never during
  fast scans, and pass it to the driver, so waveform choice follows the room.
- **A clock or an always-on display** — a fixed small box with tabular digits, once a minute; count the full
  refreshes the partial limit adds on a still screen.

---

## 15. Testing on the glass

**Instrument every refresh, test the rules on the host, drive the device through its real input path, and judge the
glass by eye. What has been validated this way, and what has not, is in [E_INK_VALIDATION](validation.md).**

- **A timing breakdown per refresh** — render, pack, waveform latch, stream, power-on, drive (until BUSY clears), and
  the temperature used; counters for full, partial, grey, skipped, fast scans, errors and partials since the last
  full; one line per refresh in the log.
- **On-device fixtures** — a full refresh, a small partial, four greys, a 1 px checkerboard toggled against a plain
  area (a ghosting fixture), a preset cycler, a type-scale page, a page of every component and state, a refresh
  benchmark, and a page walk that changes screens every few seconds for many cycles to watch ghosts build.
- **A bench console** that presses buttons through the real input path, spaced longer than a full refresh, runs the
  benchmark and pulls a screenshot.
- **Pure rules on the host** — dither patterns, the back-to-back wait, the swipe decision, page arithmetic, the
  indicator's thumb — in a header with no hardware dependency; the toolkit's real scroll and input code on the host
  with a scripted finger, for what a pure test cannot see.
- **The boot check** — controller detected, first refresh done, no BUSY timeout or error lines in the serial log; "not
  seen" is never a pass.
- **Watch the glass for** inverted scan areas, an old page's trace, black fading seconds later, stale regions lighting
  up, grey fills collapsing, ragged text edges.
- **Temperature** — sweep forced temperatures to find the waveform slots; test any custom waveform in the cold and the
  heat before widening its window.

---

## 16. The panel spec

**Before a driver or a screen, write the panel's spec from its datasheet and measurements, and keep it current — the
skill's [template](../templates/panel-spec.md) holds the fields.**

- **The panel** — diagonal, resolution, pixel density, native orientation, film (black and white, greys, colour),
  finish, front light.
- **The controller** — part per revision and how to tell them apart (ID command, finish); interface and clock limits;
  pins with active levels and idle states; BUSY polarity; reset pulse; busy timeout.
- **The memory** — bits per pixel, bit order, which value is white, RAM planes, window alignment, mirroring, rotation.
- **The waveforms** — modes available, OTP or custom, temperature source and bands, frame rates allowed.
- **Power** — which refreshes leave the supply on, standby, deep sleep, rails and settle time, fading behaviour.
- **Forbidden commands** — voltage and OTP registers; the allow-list.
- **Shared-bus constraints.**
- **Measured refresh times per mode** — with date, build, power and temperature.
- **Open items and traps** for this panel.

---

## 17. Colour panels and front lights

**Colour film is slower, has fewer partial modes and changes the palette; a front light changes contrast — design for
the film you ship.**

- **Three- and four-colour panels** (black, white and red or yellow) drive the colour particles with long waveforms
  (often many seconds) and usually offer no partial refresh: design for few, deliberate updates, never interaction at
  a partial's pace.
- **Colour-filter panels** (a filter over greyscale film) show colour at a fraction of the greyscale resolution and
  lower saturation: keep text and controls in black and white, colour only in images and accents.
- **Colour is still never the only signal.**
- **A front light** lifts the white and lowers the ratio between levels; check contrast pairs with it on and off, and
  that it does not wash out dithers.

---

## 18. Traps

### 18.1 Driver and waveform

- **The scanned area shows the inverse of what was drawn** → a borrowed waveform's polarity is reversed for this panel
  → swap the drive voltages; check polarity on the glass first.
- **Frames stall until every fast scan finishes** → the background scan task retakes the shared lock the moment it is
  released → a "frame waiting" flag the scan task yields to after each scan.
- **Every drive costs about 80 ms extra** → the clock and supply are re-enabled per drive → power on once, then drive
  with the display step alone.
- **Pixels outside the current scan area move later** → the last scan's masks stayed in RAM → upload the union of
  this and the last box.
- **The device freezes for seconds when left idle** → a standby sent with the clock already off holds BUSY until the
  timeout, retried on the UI task → track the powered state, skip a standby that is already done, never retry on the
  UI task.
- **Black fades seconds after a refresh** → the supply is powered off right after the refresh → keep it on between
  refreshes; power off before deep sleep.
### 18.2 Refresh and bus

- **The old page's ghost after a page change** → one partial cannot clear it → two partials through white, or a full.
- **A ghost after a large overlay closes** → a partial cannot clear that much contrast → a full refresh on closing.
- **Elements drawn earlier light up after a partial** → a windowed RAM write left stale data, and the whole RAM is
  driven → write both planes in full.
- **Ghosting after storage writes** → another device's transaction inside a refresh on a shared bus → one lock for the
  whole panel sequence; never cover it with a full refresh.
- **Every refresh times out, or returns at once, on one board revision** → BUSY polarity → set it from the detected
  controller.
- **A light grey turns white** → a partial thresholds it → a dither for UI greys; a greyscale refresh for images.
- **The full refresh drives a partial-length waveform** → an undocumented vendor step left out → keep vendor steps
  until each is proven unneeded.
- **A command meant for one family programs another's OTP** → command code ported between families → never port;
  keep an allow-list per driver.
### 18.3 Toolkit and input

- **The toolkit's scroll-on-focus draws a run of partials** → it animates → scroll to view with animation off.
- **A flick reads as a rested finger** → the swipe is decided at scroll end, after a refresh → decide at the lift.
- **The stack overflows on the first drag** → the code's own put-back scroll re-enters the scroll handlers → a
  settling flag, and a test against the real toolkit.
- **An editing control keeps eating UP and DOWN on the next screen** → editing mode stayed on → leave it when the
  group is cleared and when focus is lost.
- **A text view turns two pages per key** → arrow-key scrolling stacked with a key handler → remove one.
- **The ring or the indicator is clipped** → a child is clipped to its parent's extra draw area → widen it on every
  container up to the page.
- **A disabled row keeps grey words on the dither** → a child's own colour outranks the parent's state style → set the
  disabled look on each child — the sparse-dither words and the stepped fill (§10.2) — or pass the state down.
- **A glyph is missing on the glass** → a character outside the compiled font's ranges → check every drawn string
  against the ranges.
- **The screenshot is clean and the glass is not** → a screenshot shows the frame asked for → judge the glass.

---

## 19. Sources

| Topic | Where |
| --- | --- |
| Controller commands, RAM planes, display-update control, deep sleep, custom tables | Solomon Systech SSD1677, SSD1680 and SSD1681 datasheets; UltraChip UC8151 and UC8179 datasheets |
| Waveform modes INIT, DU, GC16, GL16, A2 | ITE IT8951 documentation; E Ink's published waveform mode descriptions |
| How electrophoretic film works, DC balance, temperature bands | E Ink and panel makers' application notes |
| Render modes, flush, rounding, groups, focus, scroll, events | LVGL documentation (version 9): Display, Input devices, Groups, Scroll, Events |
| Contrast, target size, flashing, timing | WCAG 2.2 — 1.4.3, 1.4.11, 2.5.8, 2.3.1, 2.2.1 |
| Closed functionality | EN 301 549 |
| The refresh policy, the budgeted fast method's mechanics, component and focus patterns, the traps | Measured and judged on the glass of e-paper devices the authors built; each value here an example to measure again |
