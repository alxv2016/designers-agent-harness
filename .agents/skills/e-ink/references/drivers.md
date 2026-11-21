# E-Ink Drivers

How to write a driver for an e-paper controller, with the code for the parts that are hard to get right: the bus and
its BUSY line, detecting the controller, the SSD1677 and the SSD2677 in full — initialisation, RAM, refresh sequences,
waveforms, power and sleep, and each one's pitfalls — the budgeted fast-update engine, and how to bring up a
controller not covered here. People read it before they build a driver; coding agents read it, through the `e-ink`
skill, before they write or change one. The general rules — how the film works, the refresh policy, what never to
send — are in [E_INK](e-ink.md); this doc holds the controller-specific mechanics and the code.

**Where it lives.** In the `e-ink` skill, beside [its SKILL.md](../SKILL.md) and [E_INK](e-ink.md). The skill folder
is self-contained: copy it into any repo's `.agents/skills/` and this comes with it.

**The code.** C++ for ESP-IDF, cut to what matters; names are illustrative. Byte values come from the controllers'
datasheets and the panel vendor's reference driver, and each one is marked where it is undocumented. They are right
for one 800×480 panel per controller: check every value against your panel's datasheet and record it in your panel
spec before you send it.

**Stability.** Cite this doc as `E_INK_DRIVERS §n`. Do not renumber; add new material under the next free number.

| § | Section | Look here for |
| --- | --- | --- |
| 1 | [The common controllers](#1-the-common-controllers) | SSD1677, SSD2677, SSD1680-class, UC81xx, IT8951 compared |
| 2 | [The shape of a driver](#2-the-shape-of-a-driver) | Layers, the panel interface, the state to track, failure |
| 3 | [The bus](#3-the-bus) | Commands and data, reads, streaming, BUSY, reset |
| 4 | [Detecting the controller](#4-detecting-the-controller) | The ID command and choosing the driver |
| 5 | [The SSD1677](#5-the-ssd1677) | Init, RAM window and mirroring, planes, update sequences, grey, custom waveform, standby, sleep |
| 6 | [The SSD2677](#6-the-ssd2677) | Init, no custom waveforms, temperature slots, 2-bit streaming, the partial window, frame rate, power |
| 7 | [The budgeted scan engine](#7-the-budgeted-scan-engine) | Per-pixel budgets, masks, the bit-sliced count, settling |
| 8 | [Bringing up a new controller](#8-bringing-up-a-new-controller) | The order of work and what to measure |
| 9 | [Sources](#9-sources) | Datasheets, the reference driver, the method's origin |

---

## 1. The common controllers

**Know the family before the part: the command set, BUSY's polarity and whether you can load a waveform decide the
whole driver.**

| Controller | Maker | Command set | BUSY while busy | Custom waveform | Grey | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| SSD1677 | Solomon Systech | SSD16xx | High | Yes — a 105-byte table through `0x32` | 4 levels through the OTP grey waveform | Two RAM planes (`0x24` new, `0x26` old); mirrors X itself; drives the whole RAM on every refresh |
| SSD2677 | Solomon Systech | UC81xx-style | Low (BUSY_N) | **No** — no documented table write; the OTP waveform loaded at reset stands | 4 levels through an OTP slot | Waveform chosen by forcing a temperature slot; 2 bits per pixel streamed even for 1-bit frames; answers `0x07` to ID command `0x70`; a partial window (`0x83`); powering off between refreshes fades black |
| SSD1680, SSD1681, SSD1683 | Solomon Systech | SSD16xx | High | Yes — table size differs per part | Varies | Smaller panels; the SSD1677's patterns hold; check the table layout and RAM size |
| UC8151, UC8179 | UltraChip | UC81xx | Low | On parts with LUT registers (VCOM and per-transition tables) | Varies | Panel setting (`0x00`), power on `0x04`, refresh `0x12`, power off `0x02`, deep sleep `0x07` + `0xA5` |
| IT8951 | ITE | Its own, over SPI, I80 or USB | Its own ready line | Modes chosen per update (INIT, DU, GC16, GL16, A2) | 16 levels | A controller board with its own memory: load the image into it, then ask for an area and a mode |

- **The SSD2677 is not an SSD16xx part** — its name says Solomon Systech, its commands say UltraChip. Write its driver
  from its own datasheet; never port SSD1677 code to it (E_INK §3.5).
- **No custom waveform on the SSD2677** — its only levers are which OTP slot is picked (§6.3) and the frame rate
  (§6.6). A fast budgeted engine (§7) needs a controller that takes a custom table, such as the SSD1677.

---

## 2. The shape of a driver

**One driver per controller family behind one panel interface, a bus beneath it that knows nothing of panels, and
board code that detects the part and picks the driver.**

### 2.1 The panel interface

```cpp
enum class Mode : uint8_t { kFull, kPartial, kGray };

struct Box { uint16_t row0 = 1, row1 = 0, byte0 = 0, byte1 = 0;  // rows and byte columns, inclusive
             bool Empty() const { return row0 > row1; } };

struct Timing { uint32_t latch_ms, stream_ms, power_on_ms, drive_ms; int temperature_c; };

class Panel {
public:
    virtual ~Panel() = default;
    virtual const char *Name() const = 0;
    // One bit a pixel for kFull and kPartial (1 = white), two for kGray (0 = black … 3 = white).
    // A partial with no full refresh since start, sleep or a grey frame is drawn full.
    virtual esp_err_t Refresh(Mode mode, const uint8_t *frame) = 0;
    // Optional: drive part-way pixels the rest of the way; one pass of a short custom waveform.
    virtual esp_err_t Settle(const uint8_t *frame, const uint8_t *touched) { return ESP_ERR_NOT_SUPPORTED; }
    virtual bool ScanReady() const { return false; }
    virtual esp_err_t Scan(const uint8_t *black, const uint8_t *white, const Box &box) { return ESP_ERR_NOT_SUPPORTED; }
    virtual esp_err_t Standby() = 0;  // the drive's supply off; the next refresh turns it on
    virtual esp_err_t Sleep() = 0;    // deep sleep: the frame stays, the next refresh resets first
    virtual void SetTemperature(float celsius) {}
    virtual esp_err_t SetTuning(const Tuning &tuning) { return ESP_ERR_NOT_SUPPORTED; }
    const Timing &LastTiming() const { return timing_; }
protected:
    Timing timing_;
};
```

- **Optional capabilities default to "not supported"** — the display layer asks, and falls back to the factory partial.
- **A tuning struct carries every family's fields; each driver accepts only its own**, with values from its datasheet,
  and refuses the rest with an error.

### 2.2 The state to track, and failure

- **Track** — initialised (and in which mode), powered (clock and high-voltage supply on), in standby, which waveform
  or slot is latched, whether a valid last frame exists (`partial_ready`), whether the RAM holds images or masks.
- **Any failure clears it all** — the next refresh resets the controller and draws full:

```cpp
esp_err_t Fail(esp_err_t err) {
    if (err != ESP_OK) { mode_ = kNone; partial_ready_ = false; ram_masks_ = false; }
    return err;
}
```

- **Keep the last frame shown** — a partial needs it as the old plane (SSD1677) or the old half of each 2-bit pixel
  (SSD2677), and the display layer uses it to skip identical frames.
- **Time every step** — latch, stream, power-on, drive — into `Timing`, for the log (E_INK §15).

---

## 3. The bus

**Four wires plus data/command, reset and BUSY; reads come back on the data line; the bus never locks — the caller
holds the shared-bus lock for the whole sequence.**

### 3.1 Commands, data and reads

```cpp
// Two SPI devices on one hand-driven chip select: a slow one for reads, a fast one for writes.
spi_device_interface_config_t cfg = {};
cfg.mode = 0;
cfg.spics_io_num = -1;                               // the select is ours
cfg.flags = SPI_DEVICE_HALFDUPLEX | SPI_DEVICE_3WIRE; // reads on the data line, no MISO
cfg.clock_speed_hz = read_hz;  spi_bus_add_device(host, &cfg, &read_);
cfg.clock_speed_hz = write_hz; spi_bus_add_device(host, &cfg, &write_);

esp_err_t Command(uint8_t c) { cs(0); dc(0); Send(write_, &c, 1); dc(1); cs(1); }  // D/C low: a command byte
esp_err_t Data(const uint8_t *d, size_t n) { cs(0); dc(1); Send(write_, d, n); cs(1); }  // D/C high: its data

esp_err_t Read(uint8_t *out) {                        // one byte after its command, at the read clock
    cs(0); dc(1);
    spi_transaction_t t = {}; t.flags = SPI_TRANS_USE_RXDATA; t.rxlength = 8;
    esp_err_t err = spi_device_transmit(read_, &t);
    cs(1); *out = t.rx_data[0]; return err;
}
```

- **Clock limits are per direction** — example: the SSD2677 reads at 2.5 MHz at most and both parts write at up to
  20 MHz; use 2 MHz and 20 MHz.

### 3.2 Streaming a frame

```cpp
// Encodes chunk i+1 while chunk i is on the wire: two 4 KB DMA buffers in internal RAM.
esp_err_t Stream(size_t len, const std::function<void(uint8_t *dst, size_t off, size_t n)> &fill) {
    cs(0); dc(1);
    spi_transaction_t t[2] = {};
    int queued = -1; esp_err_t err = ESP_OK; size_t off = 0;
    for (int i = 0; off < len && err == ESP_OK; i ^= 1) {
        size_t n = std::min(len - off, kChunk);
        fill(chunks_[i], off, n);                       // while the other chunk sends
        if (queued >= 0) {
            spi_transaction_t *done;
            err = spi_device_get_trans_result(write_, &done, portMAX_DELAY);
            queued = -1;
        }
        if (err == ESP_OK) {
            t[i] = {}; t[i].length = n * 8; t[i].tx_buffer = chunks_[i];
            err = spi_device_queue_trans(write_, &t[i], portMAX_DELAY);
            queued = err == ESP_OK ? i : -1;            // a chunk that never queued has no result to wait for
        }
        off += n;
    }
    if (queued >= 0) {
        spi_transaction_t *done;
        esp_err_t last = spi_device_get_trans_result(write_, &done, portMAX_DELAY);
        if (err == ESP_OK) err = last;
    }
    cs(1); return err;
}
```

- **The fill function does the encoding** — bit reversal, 1-to-2-bit widening, windows — so the frame is never copied
  whole (example: an 800×480 frame at 2 bits per pixel is 96,000 bytes, about 39 ms at 20 MHz).

### 3.3 BUSY and reset

```cpp
esp_err_t WaitReady(int busy_level, uint32_t timeout_ms) {   // busy_level: 1 on SSD16xx, 0 on UC81xx-style parts
    int64_t start = esp_timer_get_time();
    while (gpio_get_level(busy_) == busy_level) {
        if ((esp_timer_get_time() - start) / 1000 > timeout_ms) return ESP_ERR_TIMEOUT;
        vTaskDelay(1);                                        // yield: never spin the UI's core
    }
    return ESP_OK;
}
void Reset(uint32_t low_ms, uint32_t high_ms) {
    rst(0); vTaskDelay(pdMS_TO_TICKS(low_ms));
    rst(1); vTaskDelay(pdMS_TO_TICKS(high_ms));
}
```

- **Never wait on BUSY from the UI task without a timeout, and never retry a timed-out wait there** — mark the state
  failed and let the next refresh reset (E_INK §18).

---

## 4. Detecting the controller

**When one firmware drives more than one panel revision, read the controller's ID after a reset and create its driver;
a failed read is an error, never a guess.**

```cpp
esp_err_t ReadId(Bus &bus, uint8_t *id) {
    bus.Reset(20, 10);                 // the longer of the two parts' reset timings
    ESP_RETURN_ON_ERROR(bus.Command(0x70), kTag, "ID command");
    return bus.Read(id);
}

// Board code, under the shared-bus lock, after the panel's rail has settled (example: 100 ms):
uint8_t id = 0;
ESP_RETURN_ON_ERROR(ReadId(bus, &id), kTag, "panel ID");
std::unique_ptr<Panel> panel = id == 0x07 ? ssd2677::Create(bus)   // the SSD2677 answers 0x07
                                          : ssd1677::Create(bus);  // the SSD1677 has no 0x70
```

- **Log the controller, the ID and the revision at boot** — the boot check reads it (E_INK §15).

---

## 5. The SSD1677

**An SSD16xx-family controller: two RAM planes compared per pixel, a display-update byte that composes each refresh
from steps, a custom waveform table, and BUSY high while it works.**

### 5.1 Constants

| What | Value | Note |
| --- | --- | --- |
| BUSY | High while busy | |
| Busy timeout | 8 s | Longer than the slowest refresh, measured |
| Reset | 10 ms low, 10 ms high | Then wait for BUSY |
| RAM | 800 × 480, 1 bit per pixel, `0x24` new, `0x26` old (red) | 48,000 bytes each |

### 5.2 Initialisation

```cpp
esp_err_t Init(State state) {                   // state: full, partial or grey
    if (state != kGray) { bus.Reset(10, 10); Wait(); }
    if (state == kFull || state == kGray) { bus.Command(0x12); Wait(); }      // software reset
    uint8_t border = state == kGray ? 0x00 : state == kPartial ? 0x80 : 0x01;
    bus.Write(0x18, {0x80});                     // temperature sensor: internal
    bus.Write(0x3C, {border});                   // border waveform, per mode
    bus.Write(0x0C, {0xAE, 0xC7, 0xC3, 0xC0, 0x80});  // booster soft start
    bus.Write(0x01, {479 & 0xFF, 479 >> 8, 0x02});    // driver output: gates 0…479
    bus.Write(0x11, {0x02});                     // data entry: X decrements — the controller mirrors X
    Window({0, 479, 0, 99});
    return Wait();
}
```

- **Never write `0x03`, `0x04` or `0x2C`** (gate, source and VCOM voltages) — the panel's own values load from its OTP
  after each reset (E_INK §3.5).
- **Reset and initialise only when the mode changes or after a failure** — not before every refresh.

### 5.3 The RAM window and mirroring

```cpp
// Frame rows row0…row1 and bytes byte0…byte1 → RAM X runs from 799 − 8·byte0 down (the X mirror).
esp_err_t Window(const Box &b) {
    uint16_t xs = 799 - 8 * b.byte0, xe = 799 - (8 * b.byte1 + 7);
    bus.Write(0x44, {xs & 0xFF, xs >> 8, xe & 0xFF, xe >> 8});            // RAM X start, end
    bus.Write(0x45, {b.row0 & 0xFF, b.row0 >> 8, b.row1 & 0xFF, b.row1 >> 8});  // RAM Y start, end
    bus.Write(0x4E, {xs & 0xFF, xs >> 8});                                 // RAM X counter
    return bus.Write(0x4F, {b.row0 & 0xFF, b.row0 >> 8});                  // RAM Y counter
}
```

### 5.4 Planes and the refresh sequences

```cpp
// Every image refresh writes BOTH planes in full: the controller drives the whole RAM, and stale bytes outside a
// window light up on the next refresh.
esp_err_t Planes(const uint8_t *old_plane, const uint8_t *new_plane) {
    Window({0, 479, 0, 99});
    Plane(0x26, old_plane);    // what the glass is taken to show
    return Plane(0x24, new_plane);
}

esp_err_t Drive(uint8_t sequence) {               // Display Update Control 2, then Master Activation
    bus.Write(0x22, {sequence});
    bus.Command(0x20);
    esp_err_t err = Wait();
    if (sequence & 0x03) powered_ = false;          // bits 0x02, 0x01: clock and analog off at the end
    else if ((sequence & 0xC0) == 0xC0) powered_ = true;  // bits 0x80, 0x40: clock and analog on
    return err;
}

Full(frame):    Prepare(kFull);    Planes(frame, frame);     Drive(0xF4);            // leaves the supply on
Partial(frame): Prepare(kPartial); Planes(previous_, frame); bus.Write(0x21, {0x00, 0x00});
                Drive(after_standby_ ? 0xFF : 0xFC);         // load temperature and waveform each time
```

| `0x22` value | Steps | Use |
| --- | --- | --- |
| `0xF4` | Clock and analog on, load temperature, load waveform, display; supply left on | Full refresh |
| `0xFC` | The same in partial mode | Partial refresh |
| `0xFF` | `0xFC`, then clock and analog off | Partial after standby — the supply is then off |
| `0xCC` | Clock and analog on, display with the loaded waveform | Partial that keeps its waveform (costs a power-up each time) |
| `0x0C` | Display step alone | A scan, with the supply already on (§7) |
| `0xC0` | Clock and analog on only | Power on, or leave standby |
| `0x03` | Clock and analog off | Standby — only when they are on |
| `0xB9` | Load the OTP waveform and voltages, then clock off | Before a custom table (§5.6) |
| `0xD7` | Grey refresh, powering off at the end | Greyscale |

### 5.5 Greyscale

```cpp
// Two bits a pixel become two planes: the high bit, inverted, to 0x24; the low bit, inverted, to 0x26.
for (size_t i = 0; i < 48000; ++i) {
    uint8_t a = frame[2 * i], b = frame[2 * i + 1], h = 0, l = 0;   // eight pixels, four per byte
    for (int p = 0; p < 8; ++p) {
        uint8_t px = ((p < 4 ? a : b) >> (6 - (p & 3) * 2)) & 0x03;
        h = (h << 1) | ((px >> 1) ^ 1);
        l = (l << 1) | ((px & 1) ^ 1);
    }
    high[i] = h; low[i] = l;
}
Prepare(kGray); Planes(low, high);
bus.Write(0x1A, {0x67, 0x00});     // forced temperature for the grey waveform (the vendor's value)
Drive(0xD7);
partial_ready_ = false;            // the old plane no longer holds a 1-bit frame
```

### 5.6 A custom waveform

```cpp
// Load the OTP waveform and the panel's voltages first, then overwrite only the 105 table bytes — VCOM and the
// voltages stay the panel's own.
bus.Write(0x22, {0xB9}); bus.Command(0x20); Wait(); powered_ = false;
uint8_t lut[105] = {};
// Bytes 0–49: five tables (LUT0–LUT4; LUT4 drives VCOM), 2 bits a phase: 00 VSS, 01 VSH1, 10 VSL.
// The pixel's two RAM bits (0x26, 0x24) pick its table: 00 → LUT0, 01 → LUT1, 10 → LUT2, 11 → LUT3.
lut[10] = 0x80;          // LUT1 (0x26 clear, 0x24 set), group 0 phase A at VSL  → toward white ON THIS PANEL
lut[20] = 0x40;          // LUT2 (0x26 set, 0x24 clear), group 0 phase A at VSH1 → toward black ON THIS PANEL
// Bytes 50–99: each group's four phase lengths in frames, then its repeat count.
lut[50] = scan_frames;   // group 0 phase A lasts N frames; every other phase is 0, so skipped; repeat 0: once
// Bytes 100–104: the frame rate.
for (int i = 100; i < 105; ++i) lut[i] = 0x44;     // about 10 ms a frame on one panel
bus.Command(0x32); bus.Data(lut, sizeof lut);
```

- **Check the polarity on the glass** — which of VSL and VSH1 drives white differs between panels; a table borrowed
  from another device drew the inverse (E_INK §18).
- **A factory partial replaces the custom table** — reload it after any OTP-waveform refresh.

### 5.7 Standby and deep sleep

```cpp
esp_err_t Standby() {
    if (mode_ == kNone || standby_) return ESP_OK;
    if (powered_) { bus.Write(0x22, {0x03}); bus.Command(0x20); Wait(); powered_ = false; }
    // Already off after a 0xFF partial: sending 0x03 with the clock off holds BUSY until the timeout.
    standby_ = after_standby_ = true;
    return ESP_OK;
}
esp_err_t Sleep() {
    bus.Write(0x10, {0x03});                     // deep sleep
    vTaskDelay(pdMS_TO_TICKS(100));
    mode_ = kNone; partial_ready_ = false;       // waking needs a reset and a full refresh
    return ESP_OK;
}
// Leaving standby in the same mode: bus.Write(0x22, {0xC0}); bus.Command(0x20); Wait();   (example: about 83 ms)
```

### 5.8 SSD1677 pitfalls

- **Stale elements light up after a partial** → a windowed RAM write → both planes in full (§5.4).
- **The device freezes for the busy timeout when idle** → `0x03` sent with the clock already off → track `powered_`.
- **About 80 ms extra per drive** → `0xCC` re-powers each time → power once with `0xC0`, then `0x0C` (§7).
- **A custom table draws the inverse** → polarity → swap VSL and VSH1 after checking the glass.
- **OTP programming** — `0x30`, `0x36`, `0x2A` and `0x08` program the OTP on this family: never send them.

---

## 6. The SSD2677

**A Solomon Systech part with a UC81xx-style command set: it takes no custom waveform, picks its OTP waveform by a
forced temperature, wants 2 bits per pixel for every refresh, and fades if powered off between refreshes.**

### 6.1 Constants

| What | Value | Note |
| --- | --- | --- |
| BUSY | Low while busy (BUSY_N) | The opposite of the SSD1677 |
| Busy timeout | 30 s | |
| Reset | 20 ms low, 10 ms high | |
| ID | `0x07` to command `0x70` | |
| Stream | 2 bits per pixel, 96,000 bytes a frame, each row right to left | No hardware X mirror here |

### 6.2 Initialisation

```cpp
esp_err_t Init() {                              // once, and again only after deep sleep or a failure
    bus.Reset(20, 10); Wait();
    window_on_ = false;                          // a reset turns partial mode off
    bus.Write(0x00, {0x2F, 0x0E}); Wait();       // panel setting (PSR): LUT_EN (byte 2, bit 7) = 0 — the OTP's waveform
    bus.Write(0x06, {0x0F, 0x8B, 0x93, 0xC1});  // booster
    bus.Write(0xE7, {0xC1});                     // vendor-only, undocumented
    bus.Write(0x30, {0x08});                     // PLL / frame rate: bit 3, the dynamic frame rate
    bus.Write(0x50, {0x77});                     // VCOM and data interval
    bus.Write(0x62, {0x76, 0x76, 0x76, 0x5A, 0x9D, 0x8A, 0x76, 0x62});  // vendor-only timing, undocumented
    bus.Write(0x61, {0x03, 0x20, 0x02, 0xA8});  // resolution: 800 × 680 sources and gates as the panel wires them
    bus.Write(0xE0, {0x10});                     // vendor-only bit 4, undocumented
    bus.Write(0x65, {0x00, 0x00, 0x00, 0x00});  // gate start
    bus.Write(0xE9, {0x01});                     // vendor-only, undocumented
    return Wait();
}
```

- **Keep the vendor's undocumented steps until each is proven unneeded on the glass** — leaving one out made a full
  refresh drive a partial-length waveform (E_INK §18).
- **A mode change is a waveform latch, not a reset** — reset and initialise once; resetting on every mode change, as
  the vendor's driver does, is slower.

### 6.3 No custom waveforms: temperature slots

The SSD2677 picks its OTP waveform by temperature. Forcing a temperature (TS_SET, register `0xE6`, a signed byte in
°C) selects a slot, so the value written indexes a waveform, not the room. The driver reads the room's temperature,
`c`, and writes the forced value for that mode and room band. The values below are the panel vendor's driver's for one
panel — sweep and measure yours:

| Mode | Room `c` ≤ 10 °C | 11–20 °C | 21–30 °C | Over 30 °C |
| --- | --- | --- | --- | --- |
| Full | `0xE8` (−24 °C) | `0xEB` (−21 °C) | `0xEE` (−18 °C) | `0xF1` (−15 °C) |
| Partial | `0x08` (8 °C) | `0x0F` (15 °C) | `0x19` (25 °C) | `0x23` (35 °C) |
| Grey | `0xF1` (−15 °C), for `c` ≤ 15 °C | `0xFA` (−6 °C) above | | |

```cpp
// c: the room's temperature in °C. Each returns the forced temperature (TS_SET) that selects the mode's OTP slot.
uint8_t FullSlot(int c)    { return c <= 10 ? 0xE8 : c <= 20 ? 0xEB : c <= 30 ? 0xEE : 0xF1; }
uint8_t PartialSlot(int c) { return c <= 10 ? 0x08 : c <= 20 ? 0x0F : c <= 30 ? 0x19 : 0x23; }
uint8_t GraySlot(int c)    { return c <= 15 ? 0xF1 : 0xFA; }

esp_err_t Latch(uint8_t slot) {
    if (slot == latched_) return ESP_OK;         // latch only when it changes
    bus.Write(0xE0, {0x12});                     // TSFIX: take the temperature from 0xE6 (bit 4 vendor-only)
    bus.Write(0xE6, {slot});                     // the forced temperature
    bus.Command(0xA5);                           // undocumented, REQUIRED: loads that temperature's waveform
    Wait(); vTaskDelay(pdMS_TO_TICKS(10));
    latched_ = slot; return ESP_OK;
}
```

- **What each OTP band holds is not documented** — sweep the forced values and measure each slot's drive time before
  trusting a mapping (E_INK §4.3).
- **The room's temperature chooses the slot** — read an ambient sensor where you can; the controller's own sensor
  (command `0x40`, one byte read back) sits beside warm parts.

### 6.4 Streaming 2 bits per pixel

```cpp
// Per source byte: its bits reversed (each row streams right to left), then spread to the low bit of each pair.
uint16_t Spread(uint8_t b) { uint16_t o = 0; for (int i = 7; i >= 0; --i) o = (o << 2) | ((b >> i) & 1); return o; }
uint8_t Reverse8(uint8_t b) { b = (b & 0xF0) >> 4 | (b & 0x0F) << 4; b = (b & 0xCC) >> 2 | (b & 0x33) << 2;
                              return (b & 0xAA) >> 1 | (b & 0x55) << 1; }
for (int i = 0; i < 256; ++i) spread_[i] = Spread(Reverse8(i));     // a 256-entry table, built once

// Full: each 1-bit pixel becomes white 11 or black 00. Partial: old pixel's bit high, new pixel's bit low.
uint16_t cur  = spread_[frame[src]];
uint16_t wide = full ? cur * 3 : (spread_[previous_[src]] << 1) | cur;
dst[k] = wide >> 8; dst[k + 1] = wide;          // two output bytes per source byte: chunks stay even

// src walks each row from its last byte to its first: src = row * 100 + (99 − col / 2)
bus.Command(0x10);                               // then Stream(96000, fill) (§3.2)
```

### 6.5 The partial window

```cpp
// PTLW (0x83): partial mode on for a box, off for a full or grey refresh. Sources run right to left.
esp_err_t SetWindow(const Box *box) {
    if (!box) {
        if (!window_on_) return ESP_OK;
        window_on_ = false;
        return bus.Write(0x83, {0x00, 0x00, 0x03, 0xBF, 0x00, 0x00, 0x02, 0xA7, 0x00});  // power-on window, mode off
    }
    uint16_t hrst = (99 - box->byte1) * 8, hred = (99 - box->byte0) * 8 + 7;
    window_on_ = true;
    return bus.Write(0x83, {hrst >> 8, hrst, hred >> 8, hred,                       // sources, right to left
                            box->row0 >> 8, box->row0, box->row1 >> 8, box->row1,  // gates (rows)
                            0x01});                                                 // partial mode on
}
// A partial: find the changed box against the last frame, SetWindow(&box), stream only the box's bytes (each row
// right to left, old and new interleaved). The upload shrinks; the drive time does not — the gates scan the glass.
```

### 6.6 Frame rate, power and the refresh

```cpp
// 0x30 frame-rate codes from the datasheet's allow-list: 0x02 50 Hz … 0x05 85 Hz; 0x08 the dynamic rate.
ESP_RETURN_ON_FALSE(rate == 0x08 || (rate >= 0x02 && rate <= 0x05), ESP_ERR_INVALID_ARG, kTag, "rate not allowed");

Draw(mode, frame):
    Latch(slot for mode and temperature);
    partial with a box ? (SetWindow(&box), StreamBox(frame, box)) : (SetWindow(nullptr), Stream(mode, frame));
    if (rate for mode != rate_) bus.Write(0x30, {rate});
    if (!powered_) { bus.Command(0x04); Wait(); powered_ = true; }   // power on, once
    bus.Write(0x12, {0x00}); Wait();                                  // refresh
    if (mode == kGray) PowerOff(), partial_ready_ = false;            // the grey drive does not stay on
    else memcpy(previous_, frame, 48000), partial_ready_ = true;

Standby() { return ESP_OK; }      // power-off (0x02) here lets black fade within seconds: keep the supply on
Sleep()   { PowerOff(); bus.Write(0x07, {0xA5}); }   // power off, then deep sleep with its check byte
```

### 6.7 SSD2677 pitfalls

- **No custom waveform** — there is no documented table write, and LUT_EN only skips the OTP load: do not plan a fast
  engine on this part.
- **Every wait returns at once, or every refresh times out** → BUSY polarity copied from an SSD16xx driver → low while
  busy.
- **The full refresh drives about half its length** → `0xA5` left out of the latch → keep it.
- **Black fades seconds after a refresh** → power-off after each refresh → keep the supply on; off only before deep
  sleep and after grey.
- **Never send `0x90` or `0x91`** — they enter OTP programming and burn it; on another family the same bytes are
  harmless partial-window commands, which is why command code is never ported (E_INK §3.5).

---

## 7. The budgeted scan engine

**On a controller that takes a custom table, small changes can be driven in short scans: each changed pixel gets a
budget of pushes toward its colour, delivered scan after scan, with the drive kept balanced.**

### 7.1 Budgets, as bit-planes

```cpp
// Four bit-planes hold each pixel's scans left (0–15), one bit per pixel per plane, as 32-bit words.
uint32_t *count[4];     // count[p][w] bit j: bit p of pixel (w, j)'s budget
uint32_t *target;       // the frame the pixels are heading to

// A new frame: each changed pixel's budget becomes the full budget toward its new colour. A pixel that changes
// again before it finishes starts a fresh budget the other way — the same total drive each way.
void StartScans(const uint32_t *frame, uint8_t budget) {
    for (size_t w = 0; w < kWords; ++w) {
        uint32_t changed = frame[w] ^ target[w];
        if (!changed) continue;
        for (int p = 0; p < 4; ++p)
            count[p][w] = (count[p][w] & ~changed) | (((budget >> p) & 1) ? changed : 0);
        target[w] = frame[w];
    }
}
```

### 7.2 One scan

```cpp
esp_err_t ScanOnce() {
    Box box{UINT16_MAX, 0, UINT16_MAX, 0};
    for (size_t w = 0; w < kWords; ++w) {
        uint32_t active = count[0][w] | count[1][w] | count[2][w] | count[3][w];   // budget left
        black[w] = active & ~target[w];     // 0 in the target = black: push toward black
        white[w] = active &  target[w];     // push toward white
        if (active) { /* grow box by this word's row and byte columns */ }
    }
    // The driver uploads the box's masks, unioned with the last scan's box so its masks are cleared to hold,
    // then drives with 0x0C — the table and the supply already loaded (§5.6, §5.4).
    esp_err_t err = panel.Scan(black, white, box);
    if (err == ESP_OK)
        for (size_t w = 0; w < kWords; ++w) {          // a bit-sliced decrement of every driven pixel's budget
            uint32_t borrow = black[w] | white[w];
            for (int p = 0; p < 4 && borrow; ++p) {
                uint32_t old = count[p][w];
                count[p][w] = old ^ borrow;
                borrow &= ~old;
            }
        }
    return err;
}
// Scan while any pixel has budget, then one all-hold scan (an empty box) to clear the masks.
```

### 7.3 Settling, and the guardrails

```cpp
// Before changing tuning, before sleep, or after a failed scan: drive every touched pixel the rest of the way with
// the OTP partial — the old plane says each touched pixel was the opposite colour, so it gets a full transition.
for (size_t i = 0; i < 48000; ++i) old_plane[i] = frame[i] ^ touched[i];
Partial(frame, old_plane);
```

- **Never cut a budget short** — settle instead.
- **Never scan a full refresh, and never re-push unchanged pixels to re-saturate them** — the second drives one way
  and builds charge (E_INK §4.4).
- **Run scans only inside a measured temperature window and only for small changes** (example: 15–35 °C, at most
  15 % of pixels); otherwise the factory partial (E_INK §4.4).
- **Pace the toolkit to the first scan of a change, and run later scans on a task below the UI's priority that yields
  while a frame waits** (E_INK §6).
- **Clean ghosts with a full refresh at a pause after many scan frames** (E_INK §5).

---

## 8. Bringing up a new controller

**Read before you write, send only what is documented or proven, and measure every step on the glass.**

1. **Collect** — the controller's and the panel's datasheets, the panel maker's reference driver, the board's
   schematic; note the licence of any code you adapt.
2. **Fill the panel spec** — family, BUSY polarity, reset, clocks, RAM layout, bit order, mirroring, waveform modes,
   whether a custom table exists, deep sleep, the forbidden commands (E_INK §16).
3. **Write the allow-list** — every command the driver may send, with its source; refuse all others; never include an
   OTP-programming or voltage command.
4. **Bring up the bus** — reset, BUSY with a timeout, read the ID; log it.
5. **Draw a full refresh of a known pattern** — a checkerboard and a border — and check orientation, mirroring and
   polarity on the glass.
6. **Add partial refresh** — the old frame kept, the right plane or interleave; measure its time; walk pages for
   ghosting.
7. **Add greyscale, standby and deep sleep** — check that the image survives sleep and power removal, and that black
   holds seconds after a refresh.
8. **Measure every mode with its conditions**, and record them in the panel spec.
9. **Only then** consider a custom waveform or a faster frame rate, if the controller allows it (E_INK §4).

---

## 9. Sources

| Topic | Where |
| --- | --- |
| SSD1677 commands, RAM planes, display-update control, the waveform table's layout | Solomon Systech, SSD1677 datasheet (sections on the command table and the waveform setting) |
| SSD2677 commands, PSR's LUT_EN, PTLW, the frame-rate codes, TS_SET | Solomon Systech, SSD2677 datasheet |
| The SSD1677 and SSD2677 initialisation values, the waveform slots and the undocumented vendor steps | The panel vendor's reference e-paper driver for these panels (Seeed Studio, MIT licence) |
| Driving a UC81xx-style part with one init and a latch per mode | GxEPD2 (Jean-Marc Zingg), its UC81xx drivers |
| The budgeted scan method — masks in the planes, per-pixel budgets, the bit-sliced count | [InkBoy](https://github.com/kuslota/InkBoy), its drive counters |
| UC8151, UC8179 and IT8951 command sets and modes | UltraChip and ITE datasheets |
| The measured values, the polarity seen on the glass, the pitfalls | Measured and judged on the glass of two 800×480 panels; examples to measure again |
