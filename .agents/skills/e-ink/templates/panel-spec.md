# <Project> — E-Paper Panel Spec

<One sentence: which panel this is, on which board, and what it is used for.> People read it to know what the panel
can and cannot do; coding agents read it, through the `e-ink` skill, before they write a driver, a refresh policy or
a screen for it. Every value carries where it came from — datasheet, vendor code, measured, seen on the glass, derived
or unverified — and every measurement its date, build, power and temperature.

| § | Section | Look here for |
| --- | --- | --- |
| 1 | [Panel](#1-panel) | Size, resolution, density, film, finish, light |
| 2 | [Controller and bus](#2-controller-and-bus) | Part per revision, detection, pins, clocks, BUSY, reset |
| 3 | [Memory and pixels](#3-memory-and-pixels) | Bits per pixel, bit order, white, planes, windows, mirroring, rotation |
| 4 | [Waveforms](#4-waveforms) | Modes, OTP or custom, temperature, frame rates |
| 5 | [Power](#5-power) | Supply states, standby, deep sleep, rails, fading |
| 6 | [Forbidden](#6-forbidden) | Commands never sent; the allow-list |
| 7 | [Refresh times](#7-refresh-times) | Measured per mode, with conditions |
| 8 | [Design limits](#8-design-limits) | Minimum text, stroke, target in panel pixels; grey and dither codes |
| 9 | [Traps](#9-traps) | Symptom, cause, fix for this panel |
| 10 | [Open items](#10-open-items) | What is not yet measured or seen |

---

## 1. Panel

| Field | Value | Source |
| --- | --- | --- |
| Diagonal | `<in>` | |
| Resolution (native) | `<w × h>`, used as `<w × h>` | |
| Pixel density | `<ppi>` (1 px = `<mm>`) | |
| Film | `<black and white / n greys / colour>` | |
| Finish | `<glossy / matte>`, per revision | |
| Front light | `<none / warm and cold>` | |

## 2. Controller and bus

| Field | Value | Source |
| --- | --- | --- |
| Controller per board revision | `<family and part>` | |
| How to tell them apart | `<ID command and answer>` | |
| Interface | `<4-wire SPI; reads 3-wire>` | |
| Clock | reads `<MHz>`, writes `<MHz>` | |
| Pins | CS, SCK, MOSI, D/C, RST, BUSY — `<GPIO, active level, idle state>` | |
| BUSY polarity | `<high / low while busy>` | |
| Reset pulse | `<ms low, ms high>` | |
| Busy timeout | `<s>` | |
| Shared bus | `<other devices; lock rule>` | |

## 3. Memory and pixels

| Field | Value | Source |
| --- | --- | --- |
| Bits per pixel | `<1 / 2 / 4>` per mode | |
| Bit order and white | `<MSB first, 1 = white>` | |
| RAM planes | `<new / old (red)>` | |
| Window alignment | `<8 px in X>` | |
| Mirroring and rotation | `<hardware X mirror; UI rotation>` | |
| 1-bit threshold | `<levels → black / white>` | |

## 4. Waveforms

| Field | Value | Source |
| --- | --- | --- |
| Modes | `<full, partial, grey levels, fast>` | |
| OTP or custom tables | `<OTP only / custom table command>` | |
| Temperature source | `<internal / ambient sensor>`; bands | |
| Frame rates allowed | `<list>` | |
| Custom waveform | `<none / method, presets, window, guardrails>` | |

## 5. Power

| Field | Value | Source |
| --- | --- | --- |
| Refreshes that leave the supply on | | |
| Standby | `<after n s idle; cost on the next drive>` | |
| Deep sleep | `<command; wake = reset + init + full>` | |
| Rails and settle time | `<rail; ms>` | |
| Fading with the supply off | `<yes / no>` | |

## 6. Forbidden

- `<voltage and VCOM registers>` — the panel's OTP values only.
- `<OTP programming commands>` — never sent.
- The commands this driver may send: `<allow-list>`.

## 7. Refresh times

| Mode | Drive | Total | Conditions (date, build, power, °C) |
| --- | --- | --- | --- |
| Full | | | |
| Partial | | | |
| Grey | | | |
| New screen | | | |

## 8. Design limits

| Limit | Panel pixels | From |
| --- | --- | --- |
| Smallest text | | `<mm or pt>` at this density |
| Thinnest stroke | 2 | breaks up and ghosts below |
| Touch target | | 6.35 mm minimum, about 9 mm comfortable |
| Dither codes | `<dark, light>` | the pattern for each |

## 9. Traps

| Symptom | Cause | Fix |
| --- | --- | --- |
| | | |

## 10. Open items

| Item | Status | Unblocked by |
| --- | --- | --- |
| | | |
