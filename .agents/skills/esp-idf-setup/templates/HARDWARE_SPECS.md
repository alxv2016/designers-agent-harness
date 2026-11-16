# <Project> — Hardware Specs

The board as firmware sees it: the limits that break the hardware when crossed, the chip and its memory, the console,
the display, every pin the code uses, and the order it comes up in. People read it before wiring a driver or picking a
pin; coding agents read it before they generate or change the firmware. Source of truth: `<the schematic, its
revision, and the datasheets — which wins where two disagree>`. Related: `APP_ARCHITECTURE` — how the firmware is put
together from these facts.

**Stability.** Code comments cite this doc's `§n`. Do not renumber; add new material under the next free number. A
value changes here first, then in `components/board_config` — never only in code. The `esp-idf-setup` skill reads the
Firmware facts and Pins tables by their rows, wherever they sit.

| Tag | Meaning |
| --- | --- |
| `[SCH]` | From the schematic |
| `[DS]` | From a part's datasheet |
| `[MEAS]` | Measured on the board |
| `[?]` | Unverified — tracked in Open items |

| § | Section | Look here for |
| --- | --- | --- |
| 1 | [Critical constraints](#1-critical-constraints) | What breaks the hardware or the boot when crossed |
| 2 | [Firmware facts](#2-firmware-facts) | The chip, its flash and PSRAM, the console, the display |
| 3 | [Pins](#3-pins) | Every signal the firmware drives or reads, by GPIO |
| 4 | [Bring-up order](#4-bring-up-order) | Rails, buses and devices, in the order they come up |
| 5 | [Traps](#5-traps) | Symptoms, their causes and their fixes |
| 6 | [Open items](#6-open-items) | What is still unverified, and what settles it |

---

## 1. Critical constraints

**What breaks the hardware, the boot or the radio when crossed.**

- **`<Strapping pins>`** — `<which GPIOs, the level they need at reset, and what a wrong level does>` `[DS]`.
- **`<Pins the flash and PSRAM take>`** — `<which GPIOs are never free on this module>` `[DS]`.

## 2. Firmware facts

**The facts the firmware is generated from — one row each, the value alone in its cell.**

| Fact | Value | Source |
| --- | --- | --- |
| Chip | `<ESP32-S3>` | `[SCH]` |
| Module | `<ESP32-S3-WROOM-1-N16R8, or none for a bare chip>` | `[SCH]` |
| Flash | `<16 MB>` | `[DS]` |
| PSRAM | `<octal, quad or none>` | `[DS]` |
| Console | `<USB Serial/JTAG, or UART through a bridge>` | `[SCH]` |
| Display | `<the controller, ST7789 — or none>` | `[SCH]` |
| Display interface | `<SPI>` | `[SCH]` |
| Display resolution | `<240 x 320>` | `[DS]` |
| Display pixel clock | `<40 MHz>` | `[DS]` |
| Display colour inversion | `<yes or no>` | `[MEAS]` |

## 3. Pins

**Every signal the firmware uses, by name and GPIO; the name becomes its constant in `board_config.h`.**

Display signals keep these names: `LCD_SCLK`, `LCD_MOSI`, `LCD_CS`, `LCD_DC`, `LCD_RST` and `LCD_BL` (the last two
may be absent).

| Signal | GPIO | Notes | Source |
| --- | --- | --- | --- |
| `<LCD_SCLK>` | `<12>` | `<what it is, its level, its pull>` | `[SCH]` |

## 4. Bring-up order

**The order `board::Init()` brings the board up in: power first, then the buses, then the devices on them.**

1. `<A rail, and what enables it>` `[SCH]`.

## 5. Traps

- **`<Symptom>`** → `<cause>` → `<fix>`.

## 6. Open items

| Item | Status | Unblocked by |
| --- | --- | --- |
| `<question>` | Open | `<a measurement, a datasheet, the person>` |
