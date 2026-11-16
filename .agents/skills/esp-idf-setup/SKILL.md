---
name: esp-idf-setup
description: Sets up an ESP-IDF firmware project in a repo from the board's hardware spec in docs/, carried in the skill (references/esp-idf.md) — checking the ESP-IDF already installed (the Espressif Installation Manager's record, the version each tree declares, the latest stable release on GitHub) and advising an install with EIM when there is none; finding the spec, and when there is none or it lacks a fact, asking the person and writing their answers to a spec from the skill's template first; generating the project — main with app_features.def, app_hooks, app_shell, board_config, board, a hello-world feature, sdkconfig.defaults, partitions.csv, the editor's settings and the Espressif MCP servers — and, with a display and the person's yes, the LVGL port with a home screen and a hello-world demo; pinning ESP-IDF and the managed components; the layering rules E1–E5 and adding a feature; plus esp_idf.py (doctor, spec, generate, check). Portable — the folder works in any repo. Use when asked to set up, create or scaffold an ESP-IDF or ESP32 project or dev environment, when docs/ has hardware specs and the firmware does not exist yet, when adding a feature to a project with main/app_features.def, or when idf.py, the ESP-IDF version or the app's layering is in question.
metadata:
  scope: portable
---

# ESP-IDF setup

How an ESP-IDF firmware project is set up from the board's hardware spec, and how a feature is added to it. The
principles and their reasons are kept in this skill at [references/esp-idf.md](references/esp-idf.md) (cited
`ESP_IDF_SETUP §n`); this page indexes them in one-line rules and holds the steps. The board's facts come from the
project's hardware spec in `docs/`, which wins over the reference, and the reference over this page.

**Portable.** This folder is self-contained and links to nothing outside itself: the reference, the templates
([templates/](templates/)) and the script ([scripts/esp_idf.py](scripts/esp_idf.py)). Copy it into any repo's
`.agents/skills/` (or `.claude/skills/`) and it works there: the script reads the doc prefix and the project's name
from `.agents/project.py` when the repo has one, and needs neither. It needs git and Python 3.9+, and ESP-IDF on the
machine to build what it makes. In the agent-harness kit, the guard holds a new project until docs/ has a spec, and
`verify.py run` runs the layering check (ESP_IDF_SETUP §7).

## When to use

- The person asks to set up, create or scaffold an ESP-IDF or ESP32 project, firmware or dev environment.
- `docs/` holds a board's hardware spec and the firmware does not exist yet.
- A feature is added to a project that has `main/app_features.def`.
- `idf.py` will not run, the ESP-IDF version is in question, or a change crosses the app's layers.

## Rules

### Do

1. **Check ESP-IDF first, and never install it** — `esp_idf.py doctor --latest`; with none, say how to install it
   with EIM and stop (ESP_IDF_SETUP §1).
2. **Pin the newest stable release the person agrees to** — the script reads it from GitHub; an older install is
   theirs to keep or replace (ESP_IDF_SETUP §1).
3. **Generate from the hardware spec in `docs/`, and write the spec first when there is none** — ask the person for
   each missing fact and write their answers from `templates/HARDWARE_SPECS.md` (ESP_IDF_SETUP §2).
4. **Confirm a fact a module's name implies** — the flash and PSRAM in a module's name are asked, not assumed; what
   nobody knows is written with `[?]` and an open item (ESP_IDF_SETUP §2).
5. **Ask before adding LVGL when the spec has a display** — "Add the LVGL port, with a home screen showing a
   hello-world demo?" — and pass the answer as `--lvgl` or `--no-lvgl` (ESP_IDF_SETUP §5).
6. **Keep the app's shape**: `main` composes, `app_shell` sequences, a feature is one `FEATURE(<name>)` line and
   registers with `app_hooks`, `board` brings the hardware up (ESP_IDF_SETUP §4).
7. **Register, never act, in a feature's `Install()`** — boot steps and home builders; tasks start in a `kReady` step
   (ESP_IDF_SETUP §4).
8. **Take every pin and size from `board_config.h`, and change the spec before it** (ESP_IDF_SETUP §2).
9. **Edit `sdkconfig.defaults`, never `sdkconfig`**, and change a managed component's version only on purpose, with
   `idf.py update-dependencies` (ESP_IDF_SETUP §3).
10. **Look up ESP-IDF APIs, Kconfig options and components with the Espressif MCP servers** before a web search or
    memory (ESP_IDF_SETUP §6).

### Never

- **Generate before the spec exists**, or guess a fact the spec lacks.
- **Overwrite a file that exists** — the script keeps it and says so; a change to it is a change of its own.
- **Break a layering rule, E1–E5** — features meet only through `app_hooks` (ESP_IDF_SETUP §4).
- **Put driver logic, a protocol or a feature's loop in `app_shell`.**
- **Flash, erase or burn an eFuse without the person** — flashing is theirs to approve, and an eFuse burn is theirs to
  run.

## Procedure

### Setting up a project

1. **ESP-IDF.** `python3 .agents/skills/esp-idf-setup/scripts/esp_idf.py doctor --latest`. None: tell the person how
   to install it and stop. Older than the latest: ask which version to pin.
2. **The spec.** `esp_idf.py spec`. No spec: ask the person the questions in ESP_IDF_SETUP §2, copy
   `templates/HARDWARE_SPECS.md` to `docs/<PREFIX>_HARDWARE_SPECS.md`, fill it with their answers, and list it in the
   README. Facts missing: ask for each, write it to the spec, run `spec` again until nothing is missing.
3. **LVGL.** With a display in the spec, ask the person the question in Do 5.
4. **Generate.** `esp_idf.py generate --project <name> --idf-version <version> --lvgl|--no-lvgl` — `--dry-run` first
   to show the person what it will write. It writes the project, `docs/<PREFIX>_APP_ARCHITECTURE.md`, and merges
   `.gitignore` and `.mcp.json`; it never overwrites.
5. **A display beyond the ST7789.** Write its bring-up in `components/board/board_display.cpp` from the spec and the
   controller's `esp_lcd` component in the registry, and remove the `#error` (ESP_IDF_SETUP §5).
6. **Build.** In a shell with ESP-IDF activated (the line `doctor` prints): `idf.py set-target <chip>`, `idf.py
   reconfigure`, `idf.py build`. Read the first error, fix it, build again.
7. **In the agent-harness kit**, fill in `.agents/project.py`, `build-run-test` and AGENTS.md's layering line, and list
   `APP_ARCHITECTURE` in the README (ESP_IDF_SETUP §7).
8. **On the board**, with the person's yes: `idf.py -p <port> flash monitor`, and the log shows the board, "Hello
   world" and the firmware's version — on the panel too with LVGL. What the panel looks like is the person's to judge.

### Adding a feature

1. Create `components/<name>/` shaped like `components/hello`: `CMakeLists.txt` with `PRIV_REQUIRES app_hooks …`, and
   `<name>.cpp` defining `<name>::Install()`, which registers with `app_hooks`.
2. Add `FEATURE(<name>)` to `main/app_features.def`.
3. `esp_idf.py check`, then `idf.py build`.

## Checks

```sh
python3 .agents/skills/esp-idf-setup/scripts/esp_idf.py doctor --latest   # ESP-IDF on this machine, the latest
python3 .agents/skills/esp-idf-setup/scripts/esp_idf.py spec              # the spec's facts, and what it lacks
python3 .agents/skills/esp-idf-setup/scripts/esp_idf.py check             # the layering, E1–E5
python3 .agents/skills/esp-idf-setup/scripts/esp_idf.py --test            # the script's own cases
```

- [ ] (script) ESP-IDF found, and its version the one pinned in `main/idf_component.yml`
- [ ] (script) The spec has every fact the project needs — `spec` exits 0
- [ ] (script) The layering rules **E1–E5** (ESP_IDF_SETUP §4) — `check` reports 0 hits
- [ ] `idf.py build` passes with no warning in `main/` or `components/`
- [ ] The person said which ESP-IDF version to pin, and yes or no to LVGL
- [ ] On the board, flashed with the person's yes: the boot log, and the panel when there is one

## Traps

- **`generate` refuses with "No hardware spec in docs/"** → the spec is missing, or does not name an ESP32 chip, or is
  named unlike a spec → write it from the template (Do 3).
- **`generate` stops at "ask the person whether to add the LVGL port"** → the spec has a display and no answer was
  passed → ask, then `--lvgl` or `--no-lvgl` (Do 5).
- **The build stops at `#error "board: bring up the … panel"`** → the controller is not the ST7789 → write its
  bring-up (Procedure step 5).
- More traps — the shell, `sdkconfig`, the compile database, `MINIMAL_BUILD`, the panel — in ESP_IDF_SETUP §8.

## Sources

| Topic | Where |
| --- | --- |
| The principles, the spec's facts, the app's structure, the rules | [references/esp-idf.md](references/esp-idf.md) |
| Installing ESP-IDF, EIM, activation | ESP-IDF Programming Guide, Get Started; Espressif Installation Manager docs |
| The build system, `MINIMAL_BUILD`, components, `REQUIRES` | ESP-IDF Programming Guide, Build System |
| Managed components, `idf_component.yml`, `dependencies.lock` | IDF Component Manager docs; ESP Component Registry |
| `sdkconfig.defaults`, Kconfig, partition tables | ESP-IDF Programming Guide, Project Configuration, Partition Tables |
| `esp_lcd`, SPI panels, the ST7789 | ESP-IDF Programming Guide, LCD |
| The LVGL port, LVGL | `espressif/esp_lvgl_port` README; LVGL documentation |
| Releases | github.com/espressif/esp-idf, latest release |
