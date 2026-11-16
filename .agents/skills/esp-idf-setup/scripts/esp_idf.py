#!/usr/bin/env python3
"""The esp-idf-setup skill's script: checks the installed ESP-IDF, reads the board's hardware spec in docs/, generates
the project from the skill's templates, and checks the app's layering (ESP_IDF_SETUP §1–§4).

    esp_idf.py doctor [--latest] [--json]   # the installed ESP-IDF versions, the selected one, the latest release
    esp_idf.py spec [--spec PATH]           # the hardware spec in docs/: the facts it gives, the ones it lacks (JSON)
    esp_idf.py generate --project NAME --idf-version X.Y (--lvgl | --no-lvgl) [--spec PATH] [--facts JSON]
                        [--root DIR] [--dry-run]
                                            # the project, from the spec; never overwrites a file
    esp_idf.py check [--root DIR]           # the app's layering, E1–E5
    esp_idf.py --test                       # the script's own cases

`doctor` reads ESP-IDF where the Espressif Installation Manager records it (`~/.espressif/tools/eim_idf.json`), then
`$IDF_PATH` and the usual folders; it reads each version from the install's own `version.cmake`, so nothing is sourced.
`--latest` asks GitHub for the newest stable release. `generate` refuses while docs/ holds no hardware spec: the spec
is written first, from the person's answers (ESP_IDF_SETUP §2). In a repo with the agent-harness kit, the doc prefix
and the project's name come from `.agents/project.py`. Python 3.9+, standard library only.

Exit: 0 fine, 1 a finding, a refusal or no ESP-IDF, 2 usage.
"""

from __future__ import annotations

import argparse
import fnmatch
import glob
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
TEMPLATES = SKILL / "templates"

# --- the repo and the kit's settings ------------------------------------------------------------------------------


def repo_root() -> Path:
    out = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip()
    return Path(out or ".").resolve()


def kit_settings(root: Path) -> dict:
    """DOC_PREFIX and PROJECT_NAME from `.agents/project.py` when the repo has the kit; empty otherwise."""
    settings = {"DOC_PREFIX": "", "PROJECT_NAME": ""}
    path = root / ".agents" / "project.py"
    if path.is_file():
        text = path.read_text(errors="replace")
        for name in settings:
            m = re.search(rf'^{name}\s*=\s*"([^"]*)"', text, re.M)
            if m and not m.group(1).startswith("<"):
                settings[name] = m.group(1)
    return settings


def doc_name(path: Path, prefix: str) -> str:
    """A doc as code cites it: its file name, without the project's prefix."""
    base = path.stem
    return base[len(prefix) + 1:] if prefix and base.startswith(prefix + "_") else base


# --- doctor: the installed ESP-IDF (ESP_IDF_SETUP §1) --------------------------------------------------------------

INSTALL_DOCS = "https://docs.espressif.com/projects/esp-idf/en/stable/esp32/get-started/index.html"


def idf_version(path: Path) -> str | None:
    """The version an ESP-IDF tree declares in tools/cmake/version.cmake, as `6.1` or `6.1.2`."""
    f = path / "tools" / "cmake" / "version.cmake"
    if not f.is_file():
        return None
    text = f.read_text(errors="replace")
    parts = [re.search(rf"IDF_VERSION_{k}\s+(\d+)", text) for k in ("MAJOR", "MINOR", "PATCH")]
    if not all(parts):
        return None
    major, minor, patch = (int(p.group(1)) for p in parts)
    return f"{major}.{minor}" + (f".{patch}" if patch else "")


def find_installs(home: Path, env_idf: str | None) -> list[dict]:
    """Every ESP-IDF on the machine: the Installation Manager's list first, then $IDF_PATH and the usual folders."""
    installs, seen = [], set()

    def add(path: Path, activate: str, source: str, selected: bool = False) -> None:
        path = path.expanduser()
        key = str(path.resolve()) if path.exists() else str(path)
        if key in seen or not (path / "tools" / "idf.py").is_file():
            return
        seen.add(key)
        installs.append({"path": str(path), "version": idf_version(path), "activate": activate, "source": source,
                         "selected": selected})

    for eim in (home / ".espressif" / "tools" / "eim_idf.json", home / ".espressif" / "eim_idf.json"):
        try:
            data = json.loads(eim.read_text())
        except (OSError, ValueError):
            continue
        for entry in data.get("idfInstalled", []):
            path = Path(entry.get("path", ""))
            activate = entry.get("activationScript") or str(path / "export.sh")
            add(path, f". {activate}", "the Installation Manager", entry.get("id") == data.get("idfSelectedId"))
    if env_idf:
        add(Path(env_idf), f". {Path(env_idf) / 'export.sh'}", "$IDF_PATH", not any(i["selected"] for i in installs))
    for pattern in (".espressif/*/esp-idf", "esp/esp-idf", "esp/*/esp-idf"):
        for p in sorted(glob.glob(str(home / pattern))):
            add(Path(p), f". {Path(p) / 'export.sh'}", "found on disk")
    return installs


def latest_release() -> str | None:
    """The newest stable ESP-IDF release on GitHub, as `6.1`; None when GitHub cannot be reached."""
    try:
        req = urllib.request.Request("https://api.github.com/repos/espressif/esp-idf/releases/latest",
                                     headers={"Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.load(r).get("tag_name", "").lstrip("v") or None
    except (OSError, ValueError):
        return None


def version_key(v: str | None) -> tuple:
    return tuple(int(x) for x in re.findall(r"\d+", v or ""))


def cmd_doctor(args) -> int:
    installs = find_installs(Path.home(), os.environ.get("IDF_PATH"))
    latest = latest_release() if args.latest else None
    chosen = next((i for i in installs if i["selected"]), None) or \
        max(installs, key=lambda i: version_key(i["version"]), default=None)
    if args.json:
        print(json.dumps({"installs": installs, "chosen": chosen, "latest": latest}, indent=2))
        return 0 if installs else 1
    if not installs:
        print("No ESP-IDF on this machine. Install it with the Espressif Installation Manager (EIM) — `eim install` "
              f"installs the latest stable release — then run this again. Getting started: {INSTALL_DOCS}")
        return 1
    for i in installs:
        mark = "*" if i is chosen else " "
        print(f"{mark} ESP-IDF {i['version'] or '?'}  {i['path']}  ({i['source']})")
    print(f"use: {chosen['activate']}   # puts idf.py on PATH for this shell")
    if args.latest:
        if latest is None:
            print("latest: GitHub could not be reached — confirm the version with the person")
        elif version_key(chosen["version"]) < version_key(latest):
            print(f"latest: ESP-IDF {latest} is newer than {chosen['version']} — ask the person which to pin; a newer "
                  f"one installs with `eim install -i v{latest}`")
        else:
            print(f"latest: ESP-IDF {latest} — the chosen install is current")
    return 0


# --- spec: the hardware spec in docs/ (ESP_IDF_SETUP §2) -----------------------------------------------------------

SEC = chr(0xA7)  # the section sign, built so a citation made at run time is not read as one in this file
SPEC_NAMES = ("*hardware*", "*board*spec*", "*hw*spec*")
PLACEHOLDER = re.compile(r"<[^<>\n]*>")
CHIP = re.compile(r"\bESP32(?:-?[A-Z][A-Z0-9]{0,3})?\b", re.I)
FACT_ROWS = {"chip": "chip", "module": "module", "flash": "flash", "psram": "psram", "console": "console",
             "display": "display", "display interface": "display_interface",
             "display resolution": "display_resolution", "display pixel clock": "display_pclk",
             "display colour inversion": "display_invert", "display color inversion": "display_invert",
             "display colour order": "display_order", "display color order": "display_order"}
FACTS_HEADING = ("firmware facts", "facts")
PINS_HEADING = ("pins", "pin map", "gpio", "gpio map")
PIN = re.compile(r"^(?:GPIO|IO)?[\s_]*(\d{1,2})(?!\d)(?!.*\d)", re.I)  # one GPIO only: `GPIO12 (strap)`, `IO10`
SIGNAL = re.compile(r"^[A-Z][A-Z0-9_]*$")
NONE = re.compile(r"^(?:(?:none|no|n/a|0)\b|[-—]\s*$)")
TARGETS = {"esp32", "esp32s2", "esp32s3", "esp32c2", "esp32c3", "esp32c5", "esp32c6", "esp32c61", "esp32h2",
           "esp32p4"}
XTENSA = {"esp32", "esp32s2", "esp32s3"}
NO_PSRAM = {"esp32c2", "esp32c3", "esp32c6", "esp32h2"}  # chips with no PSRAM interface
OCTAL_PSRAM = {"esp32s3"}
NO_USB_SERIAL_JTAG = {"esp32", "esp32s2", "esp32c2"}
ST7789_PINS = ("LCD_SCLK", "LCD_MOSI", "LCD_CS", "LCD_DC")
ST7789_OPTIONAL = ("LCD_RST", "LCD_BL")
ASSUMED = {"display_pclk_hz": 40_000_000, "display_invert": True, "display_order": "rgb"}


def find_specs(root: Path) -> list[Path]:
    """The docs in docs/ that read as a hardware spec: named like one, and naming an ESP32 chip outside a template's
    `<…>` placeholders."""
    found = []
    for p in sorted((root / "docs").rglob("*.md")):
        if any(fnmatch.fnmatch(p.name.lower(), n) for n in SPEC_NAMES) and \
                CHIP.search(PLACEHOLDER.sub("", p.read_text(errors="replace"))):
            found.append(p)
    return found


def headings(text: str) -> list[tuple]:
    """Each numbered `##`/`###` heading: (its number, its title in lower case, where its section starts and ends)."""
    marks = [(m.start(), len(m.group(1)), m.group(2), m.group(3).strip().lower())
             for m in re.finditer(r"^(#{2,3})\s+(\d+(?:\.\d+)*)\.?\s+(.+)$", text, re.M)]
    out = []
    for i, (start, level, num, title) in enumerate(marks):
        end = next((s for s, lv, _, _ in marks[i + 1:] if lv <= level), len(text))
        out.append((num, title, start, end))
    return out


def find_heading(text: str, words: tuple) -> tuple | None:
    """The first numbered heading whose title holds one of the words, whole, or its plural."""
    return next((h for h in headings(text)
                 if any(re.search(rf"\b{re.escape(w)}s?\b", h[1]) for w in words)), None)


def section_of(spec_text: str, spec_doc: str, words: tuple) -> str:
    """How code cites the spec's section that holds a kind of fact: the doc's name and the number of the heading
    found by its words — so a spec in another shape is cited right too; the name alone when no heading has them."""
    h = find_heading(spec_text, words)
    return f"{spec_doc} {SEC}{h[0]}" if h else spec_doc


def cell(text: str) -> str:
    return text.strip().strip("`*").strip().replace("\\|", "|")


def read_tables(text: str) -> tuple[dict, dict, list[str]]:
    """The firmware facts (`| Fact | Value |` rows) and the pins (`| SIGNAL | GPIO |` rows), each read under its
    heading when the spec has one, else anywhere; the first row wins. A `<…>` placeholder is left out, so it counts as
    missing. The notes say what was set aside: a second value for a fact, a pin cell that is not one GPIO."""
    raw, pins, notes = {}, {}, []

    def rows(words):
        h = find_heading(text, words)
        part = text[h[2]:h[3]] if h else text
        for line in part.splitlines():
            if line.lstrip().startswith("|"):
                cells = [cell(c) for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]
                if len(cells) >= 2 and cells[1] and "<" not in cells[1] and not set(cells[1]) <= set("-: "):
                    yield cells

    for cells in rows(FACTS_HEADING):
        key = FACT_ROWS.get(cells[0].lower())
        if key and key not in raw:
            raw[key] = cells[1]
        elif key and raw[key] != cells[1]:
            notes.append(f"{cells[0]}: kept `{raw[key]}`, set aside `{cells[1]}` — one row per fact")
    for cells in rows(PINS_HEADING):
        if not SIGNAL.match(cells[0]) or cells[0].lower() in FACT_ROWS:
            continue
        m = PIN.match(cells[1])
        if not m:
            if re.search(r"\d", cells[1]):
                notes.append(f"pin {cells[0]}: `{cells[1]}` is not one GPIO — write it as `GPIO<n>`")
        elif cells[0] not in pins:
            pins[cells[0]] = int(m.group(1))
    return raw, pins, notes


def normalize(raw: dict, pins: dict) -> tuple[dict, list[str]]:
    """The facts the generator needs, and the ones still missing or not possible on the chip — each a question for
    the person."""
    facts, missing = {"pins": pins}, []
    chip = re.sub(r"[^a-z0-9]", "", raw.get("chip", "").lower())
    if chip in TARGETS:
        facts["chip"] = chip
    else:
        missing.append("chip — which ESP32 (ESP32-S3, ESP32-C6, …)")
    flash = raw.get("flash", "")
    m = re.search(r"(\d+)\s*(?:MB|MiB)\b", flash)  # case-sensitive: `Mb`, `Mbit` are megabits
    if m and int(m.group(1)) in (1, 2, 4, 8, 16, 32, 64, 128):
        facts["flash_mb"] = int(m.group(1))
    else:
        missing.append("flash — its size in MB" + (" (the spec gives megabits: 128 Mbit is 16 MB)"
                                                   if re.search(r"Mb(?:it)?\b", flash) else ""))
    psram = raw.get("psram", "").lower()
    facts["psram"] = "none" if NONE.match(psram) else "octal" if "oct" in psram else "quad" if "quad" in psram \
        else None
    if facts["psram"] is None:
        missing.append("psram — octal, quad or none")
    elif facts["psram"] != "none" and chip in NO_PSRAM:
        missing.append(f"psram — the {chip} takes none; confirm the spec")
    elif facts["psram"] == "octal" and chip in TARGETS and chip not in OCTAL_PSRAM:
        missing.append(f"psram — octal PSRAM is the ESP32-S3's; confirm the mode for the {chip}")
    console = raw.get("console", "").lower()
    usb = bool(re.search(r"jtag|usb[\s-]*serial", console))
    uart = bool(re.search(r"uart|bridge|cp210|ch34|ftdi", console))
    facts["console"] = "usb_serial_jtag" if usb and not uart else "uart" if uart and not usb else None
    if facts["console"] is None:
        missing.append("console — the chip's USB Serial/JTAG, or a UART through a bridge")
    elif facts["console"] == "usb_serial_jtag" and chip in NO_USB_SERIAL_JTAG:
        missing.append(f"console — the {chip} has no USB Serial/JTAG; confirm the spec")
    display = raw.get("display", "").lower()
    if not display:
        missing.append("display — its controller (ST7789, …) or none")
        facts["display"] = None
    elif NONE.match(display):
        facts["display"] = None
    else:
        d = {"controller": re.sub(r"[^a-z0-9]", "", display.split()[0]),
             "interface": raw.get("display_interface", "").lower() or None}
        res = re.search(r"(\d+)\s*[x×]\s*(\d+)", raw.get("display_resolution", ""))
        d["width"], d["height"] = (int(res.group(1)), int(res.group(2))) if res else (None, None)
        if not res:
            missing.append("display resolution — width x height in pixels")
        if not d["interface"]:
            missing.append("display interface — SPI, QSPI, I80, RGB, …")
        clk = re.search(r"([\d.]+)\s*MHz", raw.get("display_pclk", ""), re.I)
        d["pclk_hz"] = int(float(clk.group(1)) * 1_000_000) if clk else None
        inv = raw.get("display_invert", "").lower()
        d["invert"] = True if inv in ("yes", "true", "on") else False if inv in ("no", "false", "off") else None
        order = raw.get("display_order", "").lower()
        d["order"] = "bgr" if "bgr" in order else "rgb" if "rgb" in order else None
        if d["controller"] == "st7789" and d["interface"] == "spi":
            missing += [f"pin {p}" for p in ST7789_PINS if p not in pins]
        facts["display"] = d
    return facts, missing


def read_spec(path: Path) -> tuple[dict, list[str], dict, list[str]]:
    raw, pins, notes = read_tables(path.read_text(errors="replace"))
    facts, missing = normalize(raw, pins)
    assumed = {}
    if facts.get("display"):
        d = facts["display"]
        for key, label, field in (("display_pclk_hz", "display pixel clock", "pclk_hz"),
                                  ("display_invert", "display colour inversion", "invert"),
                                  ("display_order", "display colour order", "order")):
            if d[field] is None:
                d[field] = assumed[label] = ASSUMED[key]
    return facts, missing, assumed, notes


def no_spec_message(root: Path) -> str:
    prefix = kit_settings(root)["DOC_PREFIX"]
    name = f"{prefix}_HARDWARE_SPECS.md" if prefix else "HARDWARE_SPECS.md"
    return (f"No hardware spec in docs/ (a doc named like `*HARDWARE*`, `*BOARD*SPEC*` or `*HW*SPEC*` that names an "
            f"ESP32 chip, a template's `<…>` placeholders aside). Ask the person for the chip or module, the flash, the "
            f"PSRAM, the console, the display and its pins, then write them to docs/{name} from "
            f"{TEMPLATES / 'HARDWARE_SPECS.md'} before generating (ESP_IDF_SETUP §2).")


def pick_spec(root: Path, given: str | None) -> Path | None:
    if given:
        p = (root / given).resolve() if not os.path.isabs(given) else Path(given)
        docs = (root / "docs").resolve()
        return p if p.is_file() and docs in p.parents and CHIP.search(p.read_text(errors="replace")) else None
    specs = find_specs(root)
    return specs[0] if len(specs) == 1 else None


def cmd_spec(args) -> int:
    root = Path(args.root).resolve() if args.root else repo_root()
    specs = find_specs(root)
    path = pick_spec(root, args.spec)
    if path is None:
        out = {"spec": None, "candidates": [str(p.relative_to(root)) for p in specs]}
        out["next"] = ("several specs — pass --spec" if len(specs) > 1 else no_spec_message(root))
        print(json.dumps(out, indent=2))
        return 1
    facts, missing, assumed, notes = read_spec(path)
    print(json.dumps({"spec": str(path.relative_to(root)), "facts": facts, "missing": missing, "assumed": assumed,
                      "notes": notes}, indent=2))
    return 1 if missing else 0


# --- generate: the project from the templates (ESP_IDF_SETUP §3–§5) -------------------------------------------------

MCP_SERVERS = {"esp-en-docs": {"type": "http", "url": "https://mcp.espressif.com/docs"},
               "esp-component-registry": {"type": "http", "url": "https://components.espressif.com/mcp"}}
GITIGNORE = ("build/", "managed_components/", "sdkconfig", "sdkconfig.old")
DEFAULT_COMPONENTS = {"esp_lvgl_port_version": "^2", "lvgl_version": "^9"}


def render(text: str, values: dict, flags: dict, where: str = "template") -> str:
    """`@@if name` / `@@if !name` / `@@else` / `@@endif` keep or drop lines; `{{name}}` takes its value. A name with
    no value is an error, so a template never ships a hole."""
    out, stack = [], []
    for n, line in enumerate(text.splitlines(keepends=True), 1):
        s = line.strip()
        if s.startswith("@@if "):
            name = s[5:].strip()
            want = not flags.get(name.lstrip("!"), False) if name.startswith("!") else flags.get(name, False)
            stack.append([want, all(k for k, _ in stack)])
            continue
        if s == "@@else":
            stack[-1][0] = not stack[-1][0]
            continue
        if s == "@@endif":
            stack.pop()
            continue
        if all(k for k, _ in stack):
            out.append(line)
    if stack:
        raise ValueError(f"{where}: an @@if with no @@endif")
    result = "".join(out)

    def value(m):
        if m.group(1) not in values:
            raise KeyError(f"{where}: no value for {{{{{m.group(1)}}}}}")
        return str(values[m.group(1)])
    return re.sub(r"\{\{(\w+)\}\}", value, result)


def const_name(signal: str) -> str:
    return "k" + "".join(w.capitalize() for w in signal.lower().split("_"))


def pins_block(pins: dict, pins_section: str, lvgl: bool) -> str:
    lines = []
    for name in sorted(pins):
        lines.append(f"inline constexpr gpio_num_t {const_name(name)} = GPIO_NUM_{pins[name]};  // {name} "
                     f"({pins_section})")
    if lvgl:
        for name in ST7789_OPTIONAL:
            if name not in pins:
                lines.append(f"inline constexpr gpio_num_t {const_name(name)} = GPIO_NUM_NC;  // {name}: not "
                             f"connected ({pins_section})")
    return "\n".join(lines) if lines else f"// No pins yet: each signal the firmware uses joins {pins_section}, then here."


def plan_values(facts: dict, project: str, idf: str, lvgl: bool, spec: Path, spec_doc: str,
                title: str) -> tuple[dict, dict]:
    text = spec.read_text(errors="replace")
    spec_facts = section_of(text, spec_doc, ("firmware facts", "facts", "overview", "chip"))
    spec_pins = section_of(text, spec_doc, ("pin", "gpio"))
    d = facts.get("display") or {}
    st7789 = lvgl and d.get("controller") == "st7789" and d.get("interface") == "spi"
    flags = {"lvgl": lvgl, "st7789": st7789, "psram": facts["psram"] != "none", "psram_octal": facts["psram"] == "octal",
             "usb_serial_jtag": facts["console"] == "usb_serial_jtag", "xtensa": facts["chip"] in XTENSA}
    values = {"project": project, "spec_doc": spec_doc, "spec_facts": spec_facts, "spec_pins": spec_pins,
              "spec_link": f"[{spec_doc}]({spec.name})", "idf_version": idf, "chip": facts["chip"],
              "idf_next": f"{idf.split('.')[0]}.{int(idf.split('.')[1]) + 1}",
              "display_order": (d.get("order") or "rgb").upper(),
              "flash_mb": facts["flash_mb"], "psram": facts["psram"], "title": title,
              "app_size": hex(facts["flash_mb"] * 1024 * 1024 - 0x10000),
              "toolchain": "xtensa-esp-elf" if flags["xtensa"] else "riscv32-esp-elf",
              "pins": pins_block(facts.get("pins", {}), spec_pins, st7789),
              "display_width": d.get("width"), "display_height": d.get("height"),
              "display_pclk_hz": d.get("pclk_hz"), "display_invert": "true" if d.get("invert") else "false",
              "display_controller": (d.get("controller") or "").upper(),
              "lvgl_shape": ", LVGL's start and the home screen" if lvgl else "",
              "lvgl_hooks": " and what features add to home" if lvgl else "",
              "lvgl_install": " and home builders" if lvgl else "",
              **DEFAULT_COMPONENTS, **facts.get("components", {})}
    return values, flags


def merge_gitignore(path: Path, dry: bool) -> str:
    """The lines ESP-IDF's build needs ignored, appended — the file's own lines and line endings are left as they
    are."""
    text = path.read_text() if path.is_file() else ""
    have = {line.strip() for line in text.splitlines()}
    add = [g for g in GITIGNORE if g not in have]
    if add and not dry:
        lead = "" if not text else ("\n" if text.endswith("\n") else "\n\n")
        with path.open("a") as f:
            f.write(lead + ("\n" if text else "") + "# ESP-IDF: generated by the build\n" + "\n".join(add) + "\n")
    return f"added {', '.join(add)}" if add else "kept"


def merge_mcp(path: Path, dry: bool) -> str:
    """The Espressif MCP servers added to `.mcp.json`; a file in a shape this does not know is left for a person."""
    try:
        data = json.loads(path.read_text()) if path.is_file() else {}
    except ValueError:
        return "kept — not valid JSON, add the Espressif servers by hand"
    servers = data.get("mcpServers", {}) if isinstance(data, dict) else None
    if not isinstance(servers, dict):
        return "kept — `mcpServers` is not an object, add the Espressif servers by hand"
    add = [k for k in MCP_SERVERS if k not in servers]
    if add and not dry:
        data["mcpServers"] = {**servers, **{k: MCP_SERVERS[k] for k in add}}
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    return f"added {', '.join(add)}" if add else "kept"


def generate(root: Path, facts: dict, project: str, idf: str, lvgl: bool, spec: Path, dry: bool) -> list[str]:
    settings = kit_settings(root)
    prefix = settings["DOC_PREFIX"]
    spec_doc = doc_name(spec, prefix)
    arch = root / "docs" / (f"{prefix}_APP_ARCHITECTURE.md" if prefix else "APP_ARCHITECTURE.md")
    named = settings["PROJECT_NAME"]
    values, flags = plan_values(facts, project, idf, lvgl, spec, spec_doc,
                                f"{named} — App Architecture" if named else "App Architecture")
    report, writes = [], []
    for src in sorted((TEMPLATES / "project").rglob("*")):
        if src.is_dir():
            continue
        rel = src.relative_to(TEMPLATES / "project").as_posix()
        # `.tpl`: a file the tools would read as live config where it sits (`.clangd`); `.lvgl`: only with LVGL
        if rel.endswith(".tpl"):
            rel = rel[:-len(".tpl")]
        if rel.endswith(".lvgl"):
            if not lvgl:
                continue
            rel = rel[:-len(".lvgl")]
        writes.append((root / rel, render(src.read_text(), values, flags, rel)))
    writes.append((arch, render((TEMPLATES / "APP_ARCHITECTURE.md").read_text(), values, flags, "APP_ARCHITECTURE")))
    for dest, text in writes:
        rel = dest.relative_to(root).as_posix()
        if dest.exists():
            report.append(f"kept     {rel} (exists — never overwritten)")
            continue
        if not dry:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(text)
        report.append(f"created  {rel}")
    report.append(f"merged   .gitignore: {merge_gitignore(root / '.gitignore', dry)}")
    report.append(f"merged   .mcp.json: {merge_mcp(root / '.mcp.json', dry)}")
    return report


def cmd_generate(args) -> int:
    root = Path(args.root).resolve() if args.root else repo_root()
    if not re.fullmatch(r"[a-z][a-z0-9_-]*", args.project):
        print("--project: lowercase letters, digits, `-` and `_`, starting with a letter", file=sys.stderr)
        return 2
    if not re.fullmatch(r"\d+\.\d+(\.\d+)?", args.idf_version):
        print("--idf-version: like 6.1", file=sys.stderr)
        return 2
    spec = pick_spec(root, args.spec)
    if spec is None:
        print(no_spec_message(root) if not find_specs(root) else "Several specs in docs/ — pass --spec.")
        return 1
    facts, missing, _, notes = read_spec(spec)
    for note in notes:
        print(f"note: {note}")
    if args.facts:
        extra = json.loads(Path(args.facts).read_text())
        facts.update({k: v for k, v in extra.items() if k != "pins"})
        facts["pins"] = {**facts.get("pins", {}), **extra.get("pins", {})}
        missing = normalize_missing(facts)
    if missing:
        print("The spec lacks: " + "; ".join(missing) + ". Ask the person, write the answers to "
              f"{spec.relative_to(root)}, then generate (ESP_IDF_SETUP §2).")
        return 1
    if args.lvgl and not facts.get("display"):
        print("--lvgl needs a display in the spec.", file=sys.stderr)
        return 2
    if facts.get("display") and args.lvgl is None:
        print("The spec has a display: ask the person whether to add the LVGL port with a home screen and a "
              "hello-world demo, then pass --lvgl or --no-lvgl (ESP_IDF_SETUP §5).")
        return 1
    for line in generate(root, facts, args.project, args.idf_version, bool(args.lvgl), spec, args.dry_run):
        print(line)
    print("next: activate ESP-IDF, then `idf.py set-target " + facts["chip"] + "` and `idf.py reconfigure` "
          "(ESP_IDF_SETUP §3)" + (" — dry run, nothing written" if args.dry_run else ""))
    return 0


def normalize_missing(facts: dict) -> list[str]:
    """What a facts file still leaves out, once it has been merged over the spec."""
    missing = [k for k in ("chip", "flash_mb", "psram", "console") if facts.get(k) in (None, "")]
    if "display" not in facts:
        missing.append("display")
    d = facts.get("display") or {}
    if d and (not d.get("width") or not d.get("height")):
        missing.append("display resolution")
    if d.get("controller") == "st7789" and d.get("interface") == "spi":
        missing += [f"pin {p}" for p in ST7789_PINS if p not in facts.get("pins", {})]
    return missing


# --- check: the app's layering (ESP_IDF_SETUP §4) ------------------------------------------------------------------

KEYWORDS = {"SRCS", "SRC_DIRS", "EXCLUDE_SRCS", "INCLUDE_DIRS", "PRIV_INCLUDE_DIRS", "REQUIRES", "PRIV_REQUIRES",
            "LDFRAGMENTS", "EMBED_FILES", "EMBED_TXTFILES", "KCONFIG", "KCONFIG_PROJBUILD", "WHOLE_ARCHIVE",
            "REQUIRED_IDF_TARGETS"}


def cmake_calls(text: str, name: str) -> list[list[str]]:
    """The arguments of every call to `name` in a CMake file, as words: comments dropped outside quotes, quotes
    opened, case ignored as CMake does, nested parentheses kept to their call."""
    calls, i = [], 0
    pattern = re.compile(rf"\b{re.escape(name)}\s*\(", re.I)
    while m := pattern.search(text, i):
        i, depth, words, word, quote = m.end(), 1, [], "", False
        while i < len(text) and depth:
            c = text[i]
            if quote:
                if c == '"' and text[i - 1] != "\\":
                    quote = False
                else:
                    word += c
            elif c == '"':
                quote = True
            elif c == "#":
                while i < len(text) and text[i] != "\n":
                    i += 1
                continue
            elif c in "()":
                depth += 1 if c == "(" else -1
                if depth:
                    word += c
            elif c.isspace():
                if word:
                    words.append(word)
                word = ""
            else:
                word += c
            i += 1
        if word:
            words.append(word)
        calls.append(words)
    return calls


def requires(cmake: Path) -> list[str]:
    """The components a CMakeLists.txt names in REQUIRES or PRIV_REQUIRES, across every idf_component_register call.
    A variable or generator expression (`${x}`, `$<…>`) is kept as written: what it expands to is not followed."""
    if not cmake.is_file():
        return []
    out = []
    for words in cmake_calls(cmake.read_text(errors="replace"), "idf_component_register"):
        taking = False
        for tok in words:
            if tok in KEYWORDS:
                taking = tok in ("REQUIRES", "PRIV_REQUIRES")
            elif taking:
                out.append(tok)
    return out


def features_of(root: Path) -> list[str]:
    f = root / "main" / "app_features.def"
    return re.findall(r"^FEATURE\(\s*([a-z0-9_]+)\s*\)", f.read_text(errors="replace"), re.M) if f.is_file() else []


def layering_hits(root: Path) -> list[str]:
    feats = features_of(root)
    comps = {p.name for p in (root / "components").glob("*") if (p / "CMakeLists.txt").is_file()}
    hits = []
    for part, rule in (("app_shell", "E1"), ("app_hooks", "E2")):
        named = [r for r in requires(root / "components" / part / "CMakeLists.txt")
                 if r in feats or (part == "app_hooks" and r == "app_shell")]
        hits += [f"{rule} components/{part}/CMakeLists.txt requires `{r}` — features reach the shell through "
                 f"app_hooks" for r in named]
    for r in requires(root / "main" / "CMakeLists.txt"):
        if r in comps and r != "app_shell" and r not in feats:
            hits.append(f"E3 main/CMakeLists.txt requires `{r}` — main requires app_shell and the listed features "
                        f"only")
    sources = [p for p in list((root / "main").rglob("*")) + list((root / "components").rglob("*"))
               if p.suffix in (".c", ".cc", ".cpp", ".h", ".hpp") and p.is_file()]
    for feat in feats:
        inc = root / "components" / feat / "include"
        headers = {p.relative_to(inc).as_posix() for p in inc.rglob("*") if p.is_file()} if inc.is_dir() else set()
        home = root / "components" / feat
        for src in sources:
            if home in src.parents:
                continue
            for n, line in enumerate(src.read_text(errors="replace").splitlines(), 1):
                m = re.match(r'\s*#\s*include\s*[<"]([^>"]+)[>"]', line)
                if m and m.group(1) in headers:
                    hits.append(f"E4 {src.relative_to(root).as_posix()} includes `{m.group(1)}` from the feature "
                                f"`{feat}` — features meet only through app_hooks")
        if feat not in comps:
            hits.append(f"E5 main/app_features.def lists `{feat}`, which is not a component in components/")
    return hits


def cmd_check(args) -> int:
    root = Path(args.root).resolve() if args.root else repo_root()
    if not (root / "main" / "app_features.def").is_file():
        print("esp-idf layering: no main/app_features.def — nothing to check")
        return 0
    hits = layering_hits(root)
    for h in hits:
        print(h)
    print(f"esp-idf layering: {len(hits)} hit(s) (baseline 0)")
    return 1 if hits else 0


# --- the self-test ------------------------------------------------------------------------------------------------

SPEC_FILLED = """# Demo — Hardware Specs

| Fact | Value | Source |
| --- | --- | --- |
| Chip | `ESP32-S3` | `[SCH]` |
| Module | ESP32-S3-WROOM-1-N16R8 | `[SCH]` |
| Flash | 16 MB | `[DS]` |
| PSRAM | octal | `[DS]` |
| Console | USB Serial/JTAG | `[SCH]` |
| Display | ST7789 | `[SCH]` |
| Display interface | SPI | `[SCH]` |
| Display resolution | 240 x 320 | `[DS]` |
| Display pixel clock | `<40 MHz>` | `[DS]` |
| Display colour inversion | yes | `[MEAS]` |

| Signal | GPIO | Notes | Source |
| --- | --- | --- | --- |
| `LCD_SCLK` | GPIO12 | | `[SCH]` |
| `LCD_MOSI` | 11 | | `[SCH]` |
| `LCD_CS` | 10 | | `[SCH]` |
| `LCD_DC` | 9 | | `[SCH]` |
| `LCD_BL` | 46 | | `[SCH]` |
| `STATUS_LED` | `<48>` | | `[SCH]` |
"""


def self_test() -> int:
    bad, count = [], [0]

    def expect(name, got, want):
        count[0] += 1
        if got != want:
            bad.append(f"FAIL  {name}: want {want!r}, got {got!r}")

    # render: conditions nest, else flips, a missing value or @@endif is an error
    t = "a\n@@if x\nb\n@@if !y\nc\n@@else\nd\n@@endif\n@@endif\n{{v}}\n"
    expect("render x", render(t, {"v": 1}, {"x": True}), "a\nb\nc\n1\n")
    expect("render !x", render(t, {"v": 1}, {"x": False}), "a\n1\n")
    expect("render x y", render(t, {"v": 1}, {"x": True, "y": True}), "a\nb\nd\n1\n")
    for broken, err in (("{{nope}}", KeyError), ("@@if x\n", ValueError)):
        try:
            render(broken, {}, {"x": True})
            bad.append(f"FAIL  render {broken!r}: no error")
        except err:
            pass

    # the spec: values read, placeholders missing, chip and units normalized
    raw, pins, _ = read_tables(SPEC_FILLED)
    facts, missing = normalize(raw, pins)
    expect("chip", facts.get("chip"), "esp32s3")
    expect("flash", facts.get("flash_mb"), 16)
    expect("psram", facts.get("psram"), "octal")
    expect("console", facts.get("console"), "usb_serial_jtag")
    expect("display", (facts["display"]["controller"], facts["display"]["width"], facts["display"]["invert"]),
           ("st7789", 240, True))
    expect("pins", pins, {"LCD_SCLK": 12, "LCD_MOSI": 11, "LCD_CS": 10, "LCD_DC": 9, "LCD_BL": 46})
    expect("missing", missing, [])
    _, gone = normalize({"chip": "ESP32-S3", "display": "none"}, {})
    expect("missing facts", gone, ["flash — its size in MB", "psram — octal, quad or none",
                                   "console — the chip's USB Serial/JTAG, or a UART through a bridge"])

    # what a datasheet or another author writes: read right, or asked — never guessed
    def one(**raw):
        return normalize({"chip": "ESP32-S3", "flash": "16 MB", "psram": "none", "console": "USB Serial/JTAG",
                          "display": "none", **raw}, {})

    expect("bridge console", one(console="UART0 via USB-UART bridge (CP2102)")[0]["console"], "uart")
    expect("both consoles asked", one(console="USB Serial/JTAG and a UART header")[0]["console"], None)
    expect("Mbit asked", one(flash="128 Mbit")[0].get("flash_mb"), None)
    expect("Mbit, then MB", one(flash="128 Mbit (16 MB)")[0]["flash_mb"], 16)
    expect("psram none (N8)", one(psram="none (N8)")[0]["psram"], "none")
    expect("no display", one(display="No display")[0]["display"], None)
    expect("a dash is none", one(display="-")[0]["display"], None)
    expect("C3 takes no PSRAM", any("takes none" in m for m in one(chip="ESP32-C3", psram="quad",
                                                                     console="UART")[1]), True)
    expect("octal off the S3", any("octal" in m for m in one(chip="ESP32-C5", psram="octal")[1]), True)
    expect("no USB-JTAG on the ESP32", any("no USB Serial/JTAG" in m for m in one(chip="ESP32")[1]), True)
    pins_spec = ("## 2. Firmware facts\n\n| Fact | Value |\n| --- | --- |\n| Flash | 16 MB |\n| Flash | 8 MB |\n"
                 "| Display | ST7789 \\| SPI |\n\n## 3. Pins\n\n| Signal | GPIO |\n| --- | --- |\n| LCD_CS | IO10 |\n"
                 "| LCD_DC | GPIO_9 |\n| LED | GPIO12 (strap) |\n| BUS | 12, 13 |\n\n## 4. Power\n\n"
                 "| Flash | 4 MB |\n| ADC | 12 |\n")
    raw, pins, notes = read_tables(pins_spec)
    expect("first fact wins", raw.get("flash"), "16 MB")
    expect("escaped pipe", raw.get("display"), "ST7789 | SPI")
    expect("pin formats, own section only", pins, {"LCD_CS": 10, "LCD_DC": 9, "LED": 12})
    expect("notes", [n.split(":")[0] for n in notes], ["Flash", "pin BUS"])
    _, gone = normalize({"chip": "ESP32-S3", "flash": "4MB", "psram": "none", "console": "uart", "display": "ST7789",
                         "display_interface": "SPI", "display_resolution": "240x240"}, {"LCD_SCLK": 1})
    expect("missing pins", gone, ["pin LCD_MOSI", "pin LCD_CS", "pin LCD_DC"])
    expect("const", const_name("LCD_SCLK"), "kLcdSclk")

    # the spec's sections are found by heading, so a code comment cites the one that holds the fact
    tpl = (TEMPLATES / "HARDWARE_SPECS.md").read_text()
    expect("facts section", section_of(tpl, "HW", ("firmware facts", "facts")), f"HW {SEC}2")
    expect("pins section", section_of(tpl, "HW", ("pin", "gpio")), f"HW {SEC}3")
    expect("no section", section_of("# T\n\nno numbered headings\n", "HW", ("pin",)), "HW")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "docs").mkdir()
        expect("no spec", pick_spec(root, None), None)
        (root / "docs" / "AGENT_NOTES.md").write_text("ESP32-S3 mentioned, but not a spec by its name\n")
        expect("not a spec", find_specs(root), [])
        spec = root / "docs" / "HARDWARE_SPECS.md"
        spec.write_text(SPEC_FILLED)
        expect("spec found", pick_spec(root, None), spec)
        expect("spec outside docs", pick_spec(root, "README.md"), None)
        facts, missing, assumed, notes = read_spec(spec)
        expect("assumed", assumed, {"display pixel clock": 40_000_000, "display colour order": "rgb"})
        expect("filled spec, no notes", notes, [])

        # an unfilled template names a chip only in its placeholders: not a spec yet
        spec.write_text((TEMPLATES / "HARDWARE_SPECS.md").read_text())
        expect("template unfilled", find_specs(root), [])
        spec.write_text(SPEC_FILLED)

        # .mcp.json in a shape the merge does not know is left alone, never a crash
        for odd in ('{"mcpServers": null}', "[]", '{"mcpServers": []}'):
            (root / ".mcp.json").write_text(odd)
            expect(f"mcp {odd}", merge_mcp(root / ".mcp.json", False).startswith("kept"), True)
            expect(f"mcp untouched {odd}", (root / ".mcp.json").read_text(), odd)
        (root / ".gitignore").write_text("node_modules/\r\n")
        merge_gitignore(root / ".gitignore", False)
        expect("gitignore appended", (root / ".gitignore").read_bytes().startswith(b"node_modules/\r\n"), True)

        # requires(): every call, any case, quotes and comments, nested parentheses
        cm = root / "CMakeLists.txt"
        cm.write_text('if(X)\n  IDF_COMPONENT_REGISTER(SRCS "a#b.cpp" PRIV_REQUIRES hello)  # c\nelse()\n'
                      '  idf_component_register(SRCS "a.cpp" REQUIRES $<$<CONFIG:Debug>:dbg> b)\nendif()\n')
        expect("requires", requires(cm), ["hello", "$<$<CONFIG:Debug>:dbg>", "b"])

        # generate twice — with LVGL into one tree, headless into another — and both check clean
        for lvgl in (True, False):
            out = root / ("ui" if lvgl else "headless")
            (out / "docs").mkdir(parents=True)
            (out / "docs" / "HARDWARE_SPECS.md").write_text(SPEC_FILLED)
            (out / ".gitignore").write_text("build/\n")
            report = generate(out, read_spec(out / "docs" / "HARDWARE_SPECS.md")[0], "demo", "6.1", lvgl,
                              out / "docs" / "HARDWARE_SPECS.md", False)
            texts = {p.relative_to(out).as_posix(): p.read_text() for p in out.rglob("*") if p.is_file()}
            holes = [f for f, s in texts.items() if "@@" in s or "{{" in s]
            expect(f"no holes lvgl={lvgl}", holes, [])
            expect(f"home lvgl={lvgl}", "components/app_shell/screen_home.cpp" in texts, lvgl)
            expect(f"display lvgl={lvgl}", "kLcdSclk = GPIO_NUM_12" in texts["components/board_config/include/"
                                                                          "board_config.h"], True)
            expect(f"backlight lvgl={lvgl}", "kLcdRst = GPIO_NUM_NC" in texts["components/board_config/include/"
                                                                          "board_config.h"], lvgl)
            expect(f"octal lvgl={lvgl}", "CONFIG_SPIRAM_MODE_OCT=y" in texts["sdkconfig.defaults"], True)
            expect(f"partitions lvgl={lvgl}", "0xff0000" in texts["partitions.csv"], True)
            expect(f"gitignore lvgl={lvgl}", texts[".gitignore"].count("build/"), 1)
            expect(f"mcp lvgl={lvgl}", sorted(json.loads(texts[".mcp.json"])["mcpServers"]), sorted(MCP_SERVERS))
            expect(f"arch lvgl={lvgl}", "docs/APP_ARCHITECTURE.md" in texts, True)
            expect(f".clangd lvgl={lvgl}", (".clangd" in texts, ".clangd.tpl" in texts), (True, False))
            expect(f"xtensa flags lvgl={lvgl}", "-mlongcalls" in texts[".clangd"], True)
            expect(f"clean lvgl={lvgl}", layering_hits(out), [])
            again = generate(out, read_spec(out / "docs" / "HARDWARE_SPECS.md")[0], "demo", "6.1", lvgl,
                             out / "docs" / "HARDWARE_SPECS.md", False)
            expect(f"never overwrites lvgl={lvgl}", [r for r in again if r.startswith("created")], [])
            expect(f"created lvgl={lvgl}", any(r.startswith("created  main/main.cpp") for r in report), True)

        # a controller the template cannot bring up gets a stub that stops the build
        other = root / "other"
        (other / "docs").mkdir(parents=True)
        (other / "docs" / "HARDWARE_SPECS.md").write_text(SPEC_FILLED.replace("| ST7789 |", "| GC9A01 |"))
        generate(other, read_spec(other / "docs" / "HARDWARE_SPECS.md")[0], "demo", "6.1", True,
                 other / "docs" / "HARDWARE_SPECS.md", False)
        expect("stub", "#error" in (other / "components/board/board_display.cpp").read_text(), True)

        # each layering rule, broken once
        h = root / "headless"
        (h / "components/hello/include").mkdir(parents=True)
        (h / "components/hello/include/hello.h").write_text("#pragma once\n")
        (h / "components/app_shell/app_shell.cpp").write_text('#include "hello.h"\n')
        cm = h / "components/app_shell/CMakeLists.txt"
        cm.write_text(cm.read_text().replace("PRIV_REQUIRES app_hooks", "PRIV_REQUIRES hello app_hooks"))
        hk = h / "components/app_hooks/CMakeLists.txt"
        hk.write_text(hk.read_text().replace("PRIV_REQUIRES log", "PRIV_REQUIRES log app_shell"))
        mn = h / "main/CMakeLists.txt"
        mn.write_text(mn.read_text().replace("PRIV_REQUIRES app_shell", "PRIV_REQUIRES app_shell board"))
        (h / "main/app_features.def").write_text("FEATURE(hello)\nFEATURE(ghost)\n")
        expect("rules", sorted(x[:2] for x in layering_hits(h)), ["E1", "E2", "E3", "E4", "E5"])

        # doctor: the Installation Manager's record, a version read from the tree
        home = root / "home"
        idf = home / ".espressif/v6.1/esp-idf"
        (idf / "tools/cmake").mkdir(parents=True)
        (idf / "tools/idf.py").write_text("")
        (idf / "tools/cmake/version.cmake").write_text("set(IDF_VERSION_MAJOR 6)\nset(IDF_VERSION_MINOR 1)\n"
                                                       "set(IDF_VERSION_PATCH 0)\n")
        (home / ".espressif/tools").mkdir(parents=True)
        (home / ".espressif/tools/eim_idf.json").write_text(json.dumps(
            {"idfSelectedId": "a", "idfInstalled": [{"id": "a", "path": str(idf),
                                                     "activationScript": "/x/activate_idf_v6.1.sh"}]}))
        found = find_installs(home, None)
        expect("installs", [(i["version"], i["selected"], i["activate"]) for i in found],
               [("6.1", True, ". /x/activate_idf_v6.1.sh")])
        expect("no installs", find_installs(root / "nobody", None), [])
        expect("version order", version_key("6.1") < version_key("6.1.2") < version_key("6.10"), True)

    for line in bad:
        print(line)
    print(f"esp-idf self-test: {count[0] - len(bad)}/{count[0]} cases pass")
    return 1 if bad else 0


# --- the command line ---------------------------------------------------------------------------------------------


def main() -> int:
    if sys.argv[1:] == ["--test"]:
        return self_test()
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("doctor")
    d.add_argument("--latest", action="store_true")
    d.add_argument("--json", action="store_true")
    s = sub.add_parser("spec")
    s.add_argument("--spec")
    s.add_argument("--root")
    g = sub.add_parser("generate")
    g.add_argument("--project", required=True)
    g.add_argument("--idf-version", required=True)
    g.add_argument("--lvgl", dest="lvgl", action="store_true", default=None)
    g.add_argument("--no-lvgl", dest="lvgl", action="store_false")
    g.add_argument("--spec")
    g.add_argument("--facts")
    g.add_argument("--root")
    g.add_argument("--dry-run", action="store_true")
    c = sub.add_parser("check")
    c.add_argument("--root")
    args = ap.parse_args()
    return {"doctor": cmd_doctor, "spec": cmd_spec, "generate": cmd_generate, "check": cmd_check}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
