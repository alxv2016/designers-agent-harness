# ESP-IDF Setup

How an ESP-IDF firmware project is set up from the board's hardware spec, and why it is shaped as it is: the installed
toolchain and the version it pins, the spec the project is generated from and the questions that fill it, the files a
project holds, the app's structure — `main`, the features, `app_hooks`, `app_shell`, the board — and the rules that
keep it, the optional display with LVGL, the editor and the Espressif tools. People read it to know what the setup
makes and why; coding agents read it, through the `esp-idf-setup` skill, before they set up a project or add a feature
to one.

**Where it lives.** In the `esp-idf-setup` skill, beside the steps, the templates and the script that apply it —
[its SKILL.md](../SKILL.md). The skill folder is self-contained: copy it into any repo's `.agents/skills/` and it
works there. The board's own facts — its chip, its memory, its pins — live in the project's hardware spec in `docs/`,
never here; this doc holds what is true of any ESP-IDF project. Source of truth: Espressif's ESP-IDF Programming Guide
and the Installation Manager's docs win for how ESP-IDF behaves; `scripts/esp_idf.py` and the templates win for what
the setup writes.

**Stability.** Cite this doc as `ESP_IDF_SETUP §n`. Do not renumber; add new material under the next free number.

| § | Section | Look here for |
| --- | --- | --- |
| 1 | [The environment](#1-the-environment) | Finding ESP-IDF, the version to pin, activating it, what to do when it is missing |
| 2 | [The hardware spec](#2-the-hardware-spec) | Where the spec lives, the facts the setup needs, asking for the missing ones |
| 3 | [The project](#3-the-project) | The files, `sdkconfig.defaults`, the partitions, managed components, the minimal build |
| 4 | [The app's structure](#4-the-apps-structure) | `main`, features, `app_hooks`, `app_shell`, the board; the layering rules E1–E5 |
| 5 | [The display and LVGL](#5-the-display-and-lvgl) | The question to ask, the port, home and its hello world, a panel the template lacks |
| 6 | [Editor and tools](#6-editor-and-tools) | clangd, VS Code, the Espressif MCP servers |
| 7 | [In the agent-harness kit](#7-in-the-agent-harness-kit) | What the setup adds to the project's settings, its build skill and its docs |
| 8 | [Traps](#8-traps) | Symptoms, their causes and their fixes |

---

## 1. The environment

**The project is built with an ESP-IDF already on the machine: the setup finds it, reads its version, and pins the
newest stable release the person agrees to — it never installs one.**

- **Where ESP-IDF lives.** The Espressif Installation Manager (EIM, the `eim` command) is the default and recommended
  installer from ESP-IDF v6.0 on, per Espressif's installation guide; it records every install, its activation script and the selected one in
  `~/.espressif/tools/eim_idf.json`. Older installs sit under `~/esp/` or are named by `$IDF_PATH`. Each tree states
  its own version in `tools/cmake/version.cmake`, so reading it needs nothing sourced.
- **Activating it.** `idf.py` is not on `PATH` until the shell sources the install's activation script
  (`activate_idf_v<version>.sh` from EIM) or its `export.sh`. Every build, flash and monitor runs in such a shell.
- **The version to pin.** The newest stable release is the one on GitHub's latest-release page for `espressif/esp-idf`.
  The Espressif docs say how to install and use a release, but their examples name older versions, so the number comes
  from the release, and the person confirms it. When the installed one is older, the person chooses: pin the installed
  one, or install the newer with `eim install -i v<version>` and pin that.
- **Missing.** With no ESP-IDF, the setup stops and says how to install it — EIM's `eim install` installs the latest
  stable release — and does not install it itself: an install is gigabytes in the person's home folder, outside the
  repo.
- **Pinned, then moved on purpose.** The version is pinned to its minor series in `main/idf_component.yml` (`idf: '>=6.1,<6.2'` for 6.1) and named
  in the project's docs. A newer release is adopted as a change of its own, with its migration notes read.

`esp_idf.py doctor --latest` reports the installs, the one to use with its activation command, and the latest release.

## 2. The hardware spec

**The project is generated from a hardware spec in `docs/`; with none, the person is asked, and the answers are
written to a spec before anything is generated.**

- **Which doc it is.** A doc in `docs/` named like a hardware spec (`*HARDWARE*`, `*BOARD*SPEC*`, `*HW*SPEC*`) that
  names an ESP32 chip outside the template's `<…>` placeholders — an unfilled template is not a spec yet. The skill's
  template, `templates/HARDWARE_SPECS.md`, has two tables the script reads — the firmware facts and the pins, each
  under its heading, the first row for a fact winning and a second one reported — and sections for the critical
  constraints, the bring-up order, traps and open items.
- **What the chip rules out is asked, not passed on**: PSRAM on a chip with none (the C2, C3, C6 and H2), octal PSRAM
  off the S3, USB Serial/JTAG on a chip without it (the ESP32, S2 and C2), and a console that names both a USB
  Serial/JTAG and a UART. A flash size in megabits is asked as megabytes.
- **The facts the setup needs.**

| Fact | Why | Asked as |
| --- | --- | --- |
| Chip | The build target, the toolchain, which pins exist | "Which ESP32 — S3, C6, …?" |
| Flash | The flash size option and the partition table | "How much flash, in MB?" |
| PSRAM | Whether it is on, and octal or quad | "Is there PSRAM — octal, quad or none?" |
| Console | USB Serial/JTAG on the chip, or UART through a bridge | "How does the board connect over USB?" |
| Display | Whether to ask about LVGL (§5), and the panel's bring-up | "Is there a display — which controller?" |
| Display interface, resolution | The bus and the draw buffers | "SPI or another bus? How many pixels?" |
| Pins | `board_config.h`, one constant per signal | "Which GPIO for each signal?" |

- **A spec that lacks a fact.** `esp_idf.py spec` lists what is missing; each item is a question for the person. A
  module's name often answers two at once — an ESP32-S3-WROOM-1-N16R8 has 16 MB of flash and 8 MB of octal PSRAM — but
  the answer is confirmed, not assumed. What nobody knows yet is written with `[?]` and an open item.
- **A spec in another shape.** A spec written before the template — prose, other tables — is read by the agent, and its
  facts passed to `generate` as a JSON file (`--facts`); the spec stays the source.
- **The spec first, then the code.** A pin or a size changes in the spec, then in `board_config.h` — never only in
  code — so the spec stays true.

## 3. The project

**An ESP-IDF project is a CMake project with `main/`, its components, the build settings and a partition table; the
setup writes each once and never overwrites a file that exists.**

| File | Holds | Committed |
| --- | --- | --- |
| `CMakeLists.txt` | The project: `project.cmake`, `MINIMAL_BUILD`, the firmware's version | Yes |
| `main/` | `main.cpp`, `app_features.def`, its `CMakeLists.txt`, `idf_component.yml` | Yes |
| `components/` | `app_hooks`, `app_shell`, `board_config`, `board`, the features | Yes |
| `sdkconfig.defaults` | The settings that differ from ESP-IDF's defaults, each with its reason | Yes |
| `sdkconfig` | The full configuration, generated from the defaults | No |
| `partitions.csv` | The flash layout, sized to the flash | Yes |
| `dependencies.lock` | The resolved versions of the managed components | Yes |
| `managed_components/`, `build/` | Downloads and build output | No |

- **`sdkconfig.defaults` is the source.** `idf.py set-target` and `reconfigure` generate `sdkconfig` from it; an edit
  to `sdkconfig` is lost the next time it is regenerated. After a change to the defaults, `rm sdkconfig && idf.py
  reconfigure` applies it.
- **The partition table** starts with one factory app filling the flash after NVS and the PHY data. Over-the-air
  updates need `otadata` and two app slots; that is a decision for when the product updates in the field.
- **Managed components** are declared in `idf_component.yml`, resolved once into `dependencies.lock`, and changed on
  purpose with `idf.py update-dependencies`. A version range names a major release (`^2`), so the lock — not the range
  — decides the build.
- **`MINIMAL_BUILD`** builds only `main` and what it requires, so every component a file uses is named in its
  `CMakeLists.txt` and a component nobody requires is not built; ESP-IDF's common components are always built.
- **`idf.py reconfigure` before the first build** writes the compile database the editor reads and downloads the
  managed components; `set-target` runs once, since it regenerates `sdkconfig`. The order is the skill's procedure.

## 4. The app's structure

**`main` composes, `app_shell` sequences, each feature registers with `app_hooks`, and the board brings the hardware
up: every dependency points at the hooks or down at the board, never at a feature.**

- **`main`** does what ESP-IDF requires — the default event loop, NVS — then calls `app_shell::Install()`, each
  feature's `Install()`, and `app_shell::Run()`. It includes no feature's header.
- **A feature is one line.** `main/app_features.def` holds one `FEATURE(<component>)` per feature. The preprocessor
  reads the lines to declare and call each `<component>::Install()`; CMake reads the same lines to make each a
  requirement of `main`. Wiring a feature therefore cannot drift from building it, and deleting the line removes it.
- **`app_hooks`** is the registry: boot steps by phase (`kBoardUp`, `kReady`, `kLate`) and, with a screen, what
  features add to home. Registration happens in `Install()`, on the main task, before `Run()` seals it; a late or
  overflowing registration is logged by name and dropped. Its tables are fixed-size, so registering allocates nothing.
  `Install()` only registers; a feature starts its tasks and services in a `kReady` step, once the board and the shell
  are up.
- **`app_shell`** sequences the boot: seal the hooks, bring the board up, run each phase's steps, start the screen. It
  is a component rather than a file in `main/` so that every dependency it gains is written into its `CMakeLists.txt`
  and shows in review. It holds no driver logic, no protocol and no feature's loop.
- **`board_config`** holds every pin and size from the spec; **`board`** brings the rails, buses and devices up in the
  spec's order and returns the first error, so the shell stops the boot with it in the log.
- **Adding a feature**: a component with `<name>.cpp` defining `<name>::Install()`, which registers with `app_hooks`;
  `PRIV_REQUIRES` for what it uses; no header unless another component needs one; then the `FEATURE(<name>)` line. The
  template's `hello` feature has this shape.

The layering check, `esp_idf.py check`, holds these rules:

| Rule | Fails when |
| --- | --- |
| E1 | `app_shell` requires a listed feature |
| E2 | `app_hooks` requires a listed feature or `app_shell` |
| E3 | `main` requires a project component other than `app_shell` and the listed features |
| E4 | A file outside a feature includes one of that feature's headers |
| E5 | `app_features.def` lists a feature that is not a component |

## 5. The display and LVGL

**With a display in the spec, the person is asked whether to add the LVGL port with a home screen and a hello-world
demo; without a yes, the project has no UI code.**

- **The question.** "The spec lists a <controller> display. Add the LVGL port, with a home screen showing a
  hello-world demo?" The answer is passed as `--lvgl` or `--no-lvgl`; the script refuses to guess.
- **With a yes.** `board::InitDisplay()` brings the panel up; `app_shell` starts Espressif's LVGL port on it — LVGL's
  task, tick and lock, and two DMA-capable draw buffers of 40 lines — and shows home; `app_hooks` gains
  `OnHomeBuilt`, and the `hello` feature adds a "Hello world" label through it. LVGL is touched only under the port's
  lock.
- **The panel the template brings up.** An ST7789 on SPI, the one controller ESP-IDF's `esp_lcd` carries with no
  extra component: the bus, the panel IO, reset, init, the colour inversion the spec gives, and the backlight pin when
  there is one.
- **Any other controller** gets a `board_display.cpp` that stops the build with `#error`, naming the controller. The
  bring-up is written there from the spec and the controller's `esp_lcd_<controller>` component, found in the ESP
  Component Registry and added to `main/idf_component.yml`; the line with `#error` goes when it builds and the panel
  lights.
- **Touch, rotation, more screens** are later changes of their own: a touch controller's `esp_lcd_touch` component
  joins the port, a rotation is the port's `rotation` setting, and a router comes when there is a second screen.

## 6. Editor and tools

**The editor reads the build's compile database through clangd, and the agent reads Espressif's docs and component
registry through their MCP servers.**

- **clangd.** `.clangd` points at `build/compile_commands.json` and removes the GCC flags clang rejects — more on the
  Xtensa chips (ESP32, S2, S3) than on the RISC-V ones. ESP-IDF ships its own `esp-clangd`, which understands the
  toolchain's standard library; a system clangd may not.
- **VS Code.** `.vscode/settings.json` turns the C/C++ extension's engine off in favour of clangd and names the target;
  paths to a particular machine's ESP-IDF stay out of the repo.
- **The Espressif MCP servers**, added to `.mcp.json`: `esp-en-docs` (`https://mcp.espressif.com/docs`) searches the
  ESP-IDF and chip documentation, and `esp-component-registry` (`https://components.espressif.com/mcp`) finds components
  and their versions. Facts about ESP-IDF's APIs, Kconfig options and peripherals come from them before a web search
  or memory; the project's own docs still win for the board's decisions.

## 7. In the agent-harness kit

**In a repo with the kit, the setup also fills in the project's settings, its build skill and its docs; the kit's own
gates for a board — what is generated, flashing, eFuses, the hold on a project with no spec — are its guard's, set out
in its `HARNESS` doc.**

- **`.agents/project.py`** (the guard asks before it is edited): `CODE_PATHS` gains `main/`, `components/`,
  `CMakeLists.txt`, `sdkconfig.defaults` and `partitions.csv`; `TARGET` names the board over USB; `CHECKS` gains the
  build (`idf.py build`, from an activated shell).
- **`build-run-test`** is filled in with the commands: activate, `set-target` once, `reconfigure`, `build`,
  `flash` and `monitor` with the port — and flashing is the person's to approve.
- **Docs**: the hardware spec and `APP_ARCHITECTURE` are listed in the README; AGENTS.md's layering line says how the
  parts may depend on each other (§4).
- **`verify.py run`** runs the layering check when `main/` or `components/` change.

## 8. Traps

- **`idf.py: command not found`** → the shell has not sourced ESP-IDF → source the activation script `doctor` prints.
- **An edit to `sdkconfig.defaults` changes nothing** → `sdkconfig` already exists and wins → `rm sdkconfig && idf.py
  reconfigure`.
- **The editor cannot find any include** → no compile database yet, or a stale one → `idf.py reconfigure`, then
  restart clangd.
- **A component's header is not found under `MINIMAL_BUILD`** → the component is not in this file's `REQUIRES` or
  `PRIV_REQUIRES` → name it there; a header in a public header needs `REQUIRES`.
- **The panel stays black with the backlight on** → the reset, DC or CS pin, or the pixel clock, differs from the
  spec, or the panel needs the other colour inversion → check each against the spec, and lower the pixel clock first.
- **Colours are wrong on the panel** → RGB565 bytes in the wrong order, or the panel's colour order differs → the
  port's `swap_bytes`, or the panel's `rgb_ele_order`.
- **A boot step never runs** → it was registered after `Seal()`, outside `Install()` → register it from the feature's
  `Install()`; the log names the late registration.
