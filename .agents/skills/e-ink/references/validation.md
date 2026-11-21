# E-Ink Validation

The evidence behind the `e-ink` skill: which of its techniques were measured on real e-paper boards, which were judged
by a person on the glass, which are proven by tests that run on a computer, and which are not yet validated — with the
boards, builds, methods and numbers. People read it to know how far to trust a rule before relying on it; coding agents
read it, through the `e-ink` skill, before they present a technique as proven, and to see which checks to repeat on a
new panel.

**Where it lives.** In the `e-ink` skill, beside [its SKILL.md](../SKILL.md), [E_INK](e-ink.md) and
[E_INK_DRIVERS](drivers.md). The skill folder is self-contained: copy it into any repo's `.agents/skills/` and this
comes with it.

**Evidence, strongest first.** Every result below names one: **measured** — timed on a board, with its build and
conditions; **seen** — judged by the person on the glass, the same day and build as the measurement; **host-tested** —
asserted by a test that runs on a computer, with no board; **datasheet** — from the controller's datasheet or the panel
vendor's driver; **derived** — worked out from the above; **unverified** — believed, not yet measured or seen.

**Stability.** Cite this doc as `E_INK_VALIDATION §n`. Do not renumber; add new evidence under the next free number,
and move an item out of §7 the day it is measured or seen.

| § | Section | Look here for |
| --- | --- | --- |
| 1 | [The test bench](#1-the-test-bench) | The two boards, the builds, the conditions, the benchmark |
| 2 | [Measured on the SSD2677](#2-measured-on-the-ssd2677) | Refresh times, frame rates, the undocumented steps bisected |
| 3 | [Measured on the SSD1677](#3-measured-on-the-ssd1677) | Refresh times, new screens, temperature slots, scans |
| 4 | [Seen on the glass](#4-seen-on-the-glass) | Ghosting, fading, polarity, presets, windows — the person's verdicts |
| 5 | [Host-tested](#5-host-tested) | Dithers, disabled words, line boxes, the scroll thumb, the swipe |
| 6 | [Bench checks](#6-bench-checks) | The boot check, input through the real path, screenshots, the page walk |
| 7 | [Not yet validated](#7-not-yet-validated) | What is open, and what would settle it |
| 8 | [Confidence by technique](#8-confidence-by-technique) | Each technique in the skill and the strongest evidence behind it |

---

## 1. The test bench

**Two 800×480, 235 ppi panels on two revisions of one ESP32-S3 board, one with each controller, on ESP-IDF v6.1.1 and
LVGL 9.6.0, powered over USB at room temperature.**

| Board | Controller | Finish | Used for |
| --- | --- | --- | --- |
| Revision A | SSD2677 — UC81xx-style, no custom waveform | Matte | OTP waveforms, temperature slots, frame rate, the partial window, fading |
| Revision B | SSD1677 — SSD16xx, takes a custom waveform | Glossy | OTP waveforms, new screens through white, temperature slots, the budgeted scans |

- **One firmware image for both** — the controller detected at boot by its ID (E_INK_DRIVERS §4), so every software
  rule ran on both panels.
- **The benchmark** — a black bar growing and shrinking by 36 px a frame on a white track; 30 partial frames per
  preset, the median taken, each preset started from a full refresh, the forced full refresh left out of the times;
  each preset run three times.
- **Times** are per refresh, from the call to the panel's return: total, and the drive alone (until BUSY clears);
  and per frame of the benchmark's animation.
- **Recorded with each result** — the date, the firmware build, ESP-IDF and LVGL versions, USB power, room temperature.
  Updating LVGL from 9.5.0 to 9.6.0 added 1–5 ms a frame (measured).

---

## 2. Measured on the SSD2677

| Refresh | Total | Drive | Frame of the benchmark | Evidence |
| --- | --- | --- | --- | --- |
| Full | 1007–1050 ms | 876 ms | — | Measured |
| Partial, the waveform's own rate | 429 ms | 416 ms | 458 ms, 2.18 fps | Measured |
| Partial, 75 Hz | 433 ms | 416 ms | 456 ms, 2.19 fps | Measured — no faster |
| Partial, 85 Hz | 381 ms | 369 ms | 408 ms, 2.45 fps | Measured; no ghosting seen |
| Partial, 65 Hz | — | 462 ms | 677 ms | Datasheet (the vendor's driver); unverified on this driver |
| Partial, a forced 35 °C or 50 °C slot | — | 404 ms | 621 ms, no change | Datasheet (the vendor's driver); unverified on this driver |
| Grey | 1237–1253 ms | 1036–1052 ms | — | Measured, 2026-11-20; the vendor's driver took 1759 ms |

- **The vendor's undocumented steps, each left out in turn** (measured):

| Left out | Full, drive | Partial, drive | Frame at 85 Hz |
| --- | --- | --- | --- |
| None — the vendor's sequence, the whole frame streamed | 876 ms | 416 ms | 439 ms |
| `0xA5` | 406 ms — the wrong waveform | 405 ms | 428 ms |
| `0x62`, `0xE7`, `0xE9` or `0xE0`'s bit 4, each alone | 875–876 ms | 416 ms | 440 ms |

- **A whole frame streams in 39 ms** — 96,000 bytes at 20 MHz, encoded while the last chunk sends (measured); the
  vendor's driver took 113–124 ms at 10 MHz.
- **A drive after a standby adds 83 ms** to power the supply on (measured).
- **With the whole frame streamed instead of the partial window**, the benchmark gave 489, 488 and 440 ms a frame
  (measured): the window shortens the upload, not the drive.

---

## 3. Measured on the SSD1677

| Refresh | Total | Drive | Frame of the benchmark | Evidence |
| --- | --- | --- | --- | --- |
| Full | 1572–1579 ms | 1508 ms | — | Measured |
| Partial, the vendor's sequence | 512–519 ms | 470–471 ms | 543 ms, 1.84 fps | Measured |
| Partial, the waveform kept | 508–515 ms | 467 ms | 541 ms, 1.84 fps | Measured — no real gain |
| A new screen, two partials through white | Median 1026 ms over 15 changes in use; 1248 ms over 73 changes each after a standby | — | — | Measured |
| Grey | 1312 ms | 1209–1210 ms | — | Measured, 2026-11-20 |
| Partial, a forced 50 °C or 70 °C | — | 467 ms | — | Measured — the OTP holds one partial from room temperature to 70 °C |
| Partial, a forced 90 °C | — | 1505 ms | — | Measured |
| Scans 2 × 12 | 27–39 ms a scan | 19–20 ms | 85 ms, 11.8 fps | Measured; the default, chosen on the glass |
| Scans 3 × 10 | — | — | 100 ms, 10.0 fps | Measured |
| Scans 4 × 10 | — | — | 124 ms, 8.1 fps | Measured |

- **A scan drives about 10 ms a frame** — 2 frames 19–20 ms, 7 frames 69 ms (measured).
- **A scan's upload is 0–10 ms** — only the rows and byte columns in play (measured).
- **Re-powering for every drive cost about 80 ms a drive** (measured) — the reason a scan drives with the display step
  alone (E_INK_DRIVERS §5.4).
- **A pixel finishes in about 12 scans at 2 × 12, about 0.35 s** (derived from the scan time and the budget).
- **Scans are 6.4 times as fast a frame as the OTP partial** (derived: 85 ms against 543 ms).

---

## 4. Seen on the glass

**What the person judged on the panels — the results a measurement cannot give.**

| What was seen | Board | Evidence |
| --- | --- | --- |
| The scans draw clean frames: no earlier position of the bar stays on the glass | SSD1677 | Seen |
| A custom table copied from another device drew the inverse — the bar's past positions black, its present one white; swapping VSL and VSH1 fixed it | SSD1677 | Seen |
| One partial on a new screen leaves the old page's ghost; two partials through white leave none and do not flash as a full refresh does | SSD1677 | Seen |
| Ten page changes, then a full refresh, left no trace over a run of 80 | SSD1677 | Seen |
| No ghost before the full refresh after 20 partials, on either board; on the SSD2677, over a day of page changes, drags and scrolls | Both | Seen |
| Partials at 85 Hz showed no ghosting — chosen as the SSD2677's default | SSD2677 | Seen |
| Scans at 2 × 12 chosen as the SSD1677's default | SSD1677 | Seen |
| Black fades within seconds when the supply powers off after a refresh; three panel-setting variants still faded; with the supply kept on, black held | SSD2677 | Seen |
| The partial window drew cleanly; memory outside it never shows | SSD2677 | Seen |
| The dither patterns read alike on the glossy and the matte finish | Both | Seen |
| The image stayed on the glass through deep sleep with the panel's rail switched off | Both | Seen |

---

## 5. Host-tested

**Rules with no hardware in them run as tests on a computer in about a second; those that depend on the toolkit link
LVGL's real sources and drive them with a scripted finger.**

| Test | What it asserts |
| --- | --- |
| The glass's rules | The dark dither draws 1 pixel in 4 white and the light dither 3 in 4, each at a fixed place in the 4 × 4 cell; each dither code is one step above its plain grey; the two sparse dithers for disabled words draw 1 in 8 and 1 in 16 black; the wait between full refreshes |
| Disabled words on LVGL's real renderer | Words and marks painted in a sparse dither keep the code in every ink pixel, with no grey edge, and the 1-bit packing draws exactly the pattern — for 1-bit fonts and 1-bit marks |
| Line boxes on LVGL's real labels | A stacked label's padding is the spare split half above and half below, the odd pixel above; one line is one line box tall; at both parities, dotted and wrapped |
| The scroll thumb | For 1–60 pages: only the first and last page reach the ends; positions strictly increase; interior pages stay clear of the ends; short lists keep their proportional places |
| The swipe's decision | A slow 30 px drag turns nothing; 64 px turns a page and 63 does not; a 30 px flick turns; a fast drag shorter than a flick's distance does not; the 100 ms window's edges; a pull-back; a rested finger; the sample buffer's overflow; the timer's wrap |
| The swipe on LVGL's real scroll events | The put-back never re-enters as a new drag (scroll events at most two deep); a 64 px drag turns exactly one page and it stays turned; a second swipe starts from the new page; a flick turns; a drag from a disabled child turns once; a scroll made by a key or by focus is left alone |

- **A pure test cannot see the toolkit's own events** — the re-entering scroll that overflowed the stack showed only
  in the test against LVGL's real code (E_INK §18).

---

## 6. Bench checks

- **The boot check** — resets the board over its serial port and reads the log: one boot, the reset reason, the
  external RAM, the controller and revision detected, the first refresh done, no BUSY timeout, panic, brownout or
  error line. A line that never arrived is "not seen", never a pass.
- **Input through the real path** — a bench console presses the buttons through the same input task the person's
  presses use, spaced 1.8 s apart (longer than any full refresh), and runs the benchmark.
- **Screenshots** — the 1-bit frame the firmware asked for, pulled over the console; the glass is still judged by eye.
- **The page walk** — screens changed every few seconds over many cycles, to watch ghosting build.
- **On-device test screens** — full, partial, four greys, a 1 px checkerboard toggled against a plain area, a preset
  cycler, a type-scale page and every component in every state.

---

## 7. Not yet validated

| Item | Evidence today | What would settle it |
| --- | --- | --- |
| One short pulse a frame, at the corrected polarity, against the budgeted scans | Unverified — tried only with the polarity reversed | A single-pulse preset judged on the SSD1677's glass |
| Whether the SSD2677 needs the vendor's undocumented `0x62`, `0xE7`, `0xE9` and `0xE0` bit 4 | None changes a refresh's time (measured); the glass not judged without them | A build without each, full and partial judged on the glass |
| What each SSD2677 OTP temperature band holds | The OTP reads back (6,144 bytes, measured) in an undocumented layout | The module's specification |
| The SSD2677's idle current with the supply left on, against a standby | Unmeasured | The current read on battery, idle, both ways |
| The SSD2677 at 65 Hz, and a forced hotter slot, on this driver | Datasheet (the vendor's driver); unverified on this driver | The benchmark with those presets |
| Ghosting over a long run of scans, before the full refresh that follows 150 scan frames (E_INK §5, item 8) | Unverified | A long animation, the glass checked before the full refresh |
| Scans below 15 °C and above 35 °C | The window is a guess | The scans judged on the glass in the cold and the heat |
| The panel's life under scans | Unverified | A long run, checked against a fresh full refresh |
| How disabled words in a sparse dither read on the glass | Host-tested; the person's brief | The disabled states judged on both finishes |
| The swipe's thresholds under a finger | Host-tested | Swipes judged under a finger on the glass |
| Real contrast against the nominal levels; whether 20 px text and 2 px lines read at a metre | Derived from the levels | A light meter on the panel; a reading test |
| Whether a full refresh counts as more than three flashes a second | Unverified | A measurement against WCAG 2.3.1 |

---

## 8. Confidence by technique

**The strongest evidence behind each technique the skill teaches — measured and seen are proven on a panel; host-tested
is proven in code; the rest is to be checked on yours.**

| Technique | Where it is taught | Strongest evidence |
| --- | --- | --- |
| Detecting the controller by its ID; one image for two panels | E_INK_DRIVERS §4 | Seen — on every boot of both boards, by the boot check |
| BUSY polarity per family; the busy timeouts | E_INK_DRIVERS §5.1, §6.1 | Seen — every refresh on both boards; a wrong polarity fails at once |
| Streaming in double-buffered chunks | E_INK_DRIVERS §3.2 | Measured — 39 ms a frame |
| Both RAM planes written in full (SSD1677) | E_INK_DRIVERS §5.4 | Seen — the fix for stale elements lighting up |
| The `0xA5` latch on the SSD2677 | E_INK_DRIVERS §6.3 | Measured — 406 ms against 876 ms without it |
| Temperature slots on the SSD2677 | E_INK_DRIVERS §6.3 | Datasheet and the vendor's driver; the band contents unverified |
| Frame rate 85 Hz on the SSD2677 | E_INK §4.3; E_INK_DRIVERS §6.6 | Measured and seen |
| Keeping the SSD2677's supply on | E_INK §2; E_INK_DRIVERS §6.6 | Seen; its battery cost unmeasured |
| The custom table and its polarity (SSD1677) | E_INK_DRIVERS §5.6 | Seen |
| The budgeted scans | E_INK §4.4; E_INK_DRIVERS §7 | Measured and seen, 15–35 °C; long runs, temperature limits and panel life unverified |
| A full refresh after 20 partials | E_INK §5 | Seen on both boards |
| Never two full refreshes back to back | E_INK §5 | Host-tested |
| A new screen in two partials through white (SSD1677) | E_INK §5 | Measured and seen |
| Skipping a frame identical to the glass | E_INK §5 | Seen — in use on both boards; no dedicated test |
| UI greys as fixed dithers | E_INK §7 | Host-tested and seen on both finishes |
| Disabled words in a sparse dither | E_INK §10.2 | Host-tested; the glass not yet judged |
| 1-bit fonts and line boxes | E_INK §7 | Host-tested on LVGL's real labels |
| Input on its own task during a refresh; a press never lost | E_INK §11 | Seen — in use on both boards, and driven through the real input path on the bench |
| The swipe decided on lift; one page per swipe | E_INK §12 | Host-tested, including against LVGL's real scroll; thresholds not judged under a finger |
| The scroll thumb's placement | E_INK §9 | Host-tested |
| Touch targets from millimetres; contrast with dithers | E_INK §7, §12 | Derived |
| Colour panels and front lights | E_INK §17 | Unverified — neither board has them |
| IT8951, UC8151, UC8179 and the SSD1680 class | E_INK_DRIVERS §1 | Datasheet — not run on these boards |
