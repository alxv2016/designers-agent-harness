# {{title}}

How the firmware is put together: `main` composes the app, `app_shell` sequences it, features plug in through
`app_hooks`, and `board` brings the hardware up from the hardware spec ({{spec_link}}). People read it to know where
new code goes; coding agents read it before they add a feature, a driver or a dependency. Source of truth: the code
in `main/` and `components/`; this doc says why it is shaped so.

**Stability.** Code comments cite this doc's `§n`. Do not renumber; add new material under the next free number.

| § | Section | Look here for |
| --- | --- | --- |
| 1 | [The shape](#1-the-shape) | The parts, and which may depend on which |
| 2 | [Rules](#2-rules) | Where code goes, and what never goes where |
| 3 | [Boot order](#3-boot-order) | What `app_shell::Run()` does, phase by phase |
| 4 | [Adding a feature](#4-adding-a-feature) | The steps, and what the line in `app_features.def` does |
| 5 | [Dependencies and versions](#5-dependencies-and-versions) | ESP-IDF, the managed components, the lock file |
| 6 | [Decisions](#6-decisions) | Why the shell is a component, why a feature is one line |

---

## 1. The shape

**`main` composes, `app_shell` sequences, features register with `app_hooks`, and every arrow points at the hooks or
down at the board — never at a feature.**

| Part | Holds | May depend on |
| --- | --- | --- |
| `main/` | `app_main`: the event loop, NVS, then `app_shell::Install()`, each feature's `Install()`, `app_shell::Run()` | `app_shell`, the features listed in `app_features.def` |
| `main/app_features.def` | One `FEATURE(<component>)` line per feature — its whole wiring | — |
| `components/app_shell` | Startup order, what stops the boot{{lvgl_shape}} | `app_hooks`, `board`, `board_config` |
| `components/app_hooks` | The registry: boot steps by phase{{lvgl_hooks}}; sealed before the first read | Nothing of the app's |
| `components/board_config` | Every pin and size, from {{spec_doc}} | Nothing of the app's |
| `components/board` | The bring-up: rails, buses, devices, in the spec's order | `board_config` |
| `components/<feature>` | One feature: its `Install()` and what it registers | `app_hooks`, `board`, `board_config`, shared components |

`MINIMAL_BUILD` is on: a component is built only when something requires it, so a feature that is not listed is not
built.

## 2. Rules

**Each part keeps to its job; `verify.py run` (or the `esp-idf-setup` skill's check) fails the layering rules
E1–E5.**

### Do

1. **Register, never act, in `Install()`** — boot steps{{lvgl_install}} with `app_hooks`; no hardware, no tasks,
   nothing drawn.
2. **Bring hardware up in `board`**, in the spec's order, and return the first error so the shell stops the boot.
3. **Take every pin and size from `board_config.h`**, and change the spec before the header.
4. **Start a feature's tasks and services in a `kReady` boot step**, when the board and the shell are up.

### Never

- **Name a feature in `app_shell` or `app_hooks`** — not in their sources, not in their `CMakeLists.txt` (E1, E2).
- **Require a component from `main` other than `app_shell`, ESP-IDF's own and the listed features** (E3).
- **Include a feature's header from outside the feature** — features meet only through `app_hooks` (E4).
- **List a feature that is not a component** (E5).
- **Put driver logic, protocol handling or a feature's loop in the shell.**

## 3. Boot order

**`app_shell::Run()` seals the hooks, then runs each phase's steps in registration order — the core's first.**

1. `app_hooks::Seal()` — a registration after this is logged and ignored.
2. `board::Init()`, then the `kBoardUp` steps.
@@if lvgl
3. `board::InitDisplay()`, the LVGL port on that panel, then home: the shell's content, then each feature's
   `OnHomeBuilt` builder, under the LVGL lock. A display that does not come up stops the boot.
4. The `kReady` steps — features start their services and tasks.
5. The `kLate` steps — the core logs the firmware's name, version and ESP-IDF version.
@@else
3. The `kReady` steps — features start their services and tasks.
4. The `kLate` steps — the core logs the firmware's name, version and ESP-IDF version.
@@endif

## 4. Adding a feature

**A feature is a component with an `Install()` in its own namespace, and one line in `main/app_features.def`; the
`esp-idf-setup` skill holds the steps.**

- **`components/hello` is the shape to copy**: a `CMakeLists.txt` that requires only what the feature uses, and a
  `<name>.cpp` whose `<name>::Install()` registers with `app_hooks`.
- **No header unless another component needs one** — and never another feature, which would break E4.
- **The line is the whole wiring**: `FEATURE(<name>)` makes the component a requirement of `main` and calls its
  `Install()`; deleting the line removes the feature and, under `MINIMAL_BUILD`, everything only it required (§1).

## 5. Dependencies and versions

**ESP-IDF is pinned to the v{{idf_version}} series; managed components are resolved once and locked.**

- **ESP-IDF** — `idf: '>={{idf_version}},<{{idf_next}}'` in `main/idf_component.yml`. A newer release is adopted on purpose, with
  its migration notes read, never by drifting.
- **Managed components** — declared in `main/idf_component.yml`, resolved into `dependencies.lock` (committed) and
  downloaded into `managed_components/` (not committed). Change a version with `idf.py update-dependencies`.
- **`sdkconfig.defaults`** is the source; `sdkconfig` is generated from it and not committed.

## 6. Decisions

- **`app_shell` is a component, not a file in `main/`.** `main/` exports no headers and can include anything in the
  build, so a shell there has no declared dependency surface. As a component, every new dependency is written into
  its `CMakeLists.txt`, and growth shows in review.
- **A feature is one line.** The same `FEATURE(<name>)` lines are read by the preprocessor (to declare and call each
  `Install()`) and by CMake (to require the component), so wiring a feature cannot drift from building it.
- **`app_hooks` tables are fixed-size.** No allocation at registration; an overflow is logged by name, and the fix
  is to raise the size beside the table.
