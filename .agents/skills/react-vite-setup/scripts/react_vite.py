#!/usr/bin/env python3
"""The react-vite-setup skill's script: checks Node and Playwright's browsers, writes and reads the web app spec in
docs/, generates the React, Vite and TypeScript app with Playwright and Storybook from the skill's templates, writes
the design tokens' CSS from DESIGN.md, and checks the app's layering (REACT_VITE_SETUP §1–§5).

    react_vite.py doctor [--latest] [--json]   # Node, npm, Playwright's browsers; with --latest, the newest releases
    react_vite.py spec [--spec PATH]           # the web app spec in docs/: the facts it gives, the ones it lacks (JSON)
    react_vite.py spec --init [--name N] [--title T] [--lang L] [--node N] [--browsers B] [--viewports V]
                              [--dev-port P] [--preview-port P] [--storybook-port P]
                                               # writes the spec from the template, each fact not given a default
    react_vite.py generate [--versions latest|tested|FILE] [--spec PATH] [--root DIR] [--dry-run]
                                               # the app, from the spec; never overwrites a file
    react_vite.py tokens [--design PATH] [--out PATH]   # DESIGN.md's tokens as CSS custom properties, a block a theme
    react_vite.py check [--root DIR]           # the app's layering, W1–W5
    react_vite.py --test                       # the script's own cases

`spec --init` takes its defaults from a working project (REACT_VITE_SETUP §2) and tags each `[DEFAULT]`, so the person
sees what was chosen for them. `generate` refuses while docs/ holds no web app spec. With `--versions latest` (the
default) it asks the npm registry for each package's newest release, and names any whose major is newer than the set
this skill was last proven with (TESTED); offline, it uses that set. In a repo with the agent-harness kit, the doc
prefix and the project's name come from `.agents/project.py`. Python 3.9+, standard library only.

Exit: 0 fine, 1 a finding, a refusal or no usable Node, 2 usage.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
TEMPLATES = SKILL / "templates"
SEC = chr(0xA7)  # the section sign, built so a citation made at run time is not read as one in this file

# --- the repo and the kit's settings ------------------------------------------------------------------------------


def repo_root() -> Path:
    out = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip()
    return Path(out or ".").resolve()


def kit_settings(root: Path) -> dict:
    """DOC_PREFIX and PROJECT_NAME from `.agents/project.py` when the repo has the kit; empty otherwise."""
    settings = {"DOC_PREFIX": "", "PROJECT_NAME": ""}
    path = root / ".agents" / "project.py"
    if path.is_file():
        text = path.read_text(encoding="utf-8", errors="replace")
        for name in settings:
            m = re.search(rf'^{name}\s*=\s*"([^"]*)"', text, re.M)
            if m and not m.group(1).startswith("<"):
                settings[name] = m.group(1)
    return settings


def doc_name(path: Path, prefix: str) -> str:
    """How code comments cite a doc: its file name without the prefix and `.md`."""
    stem = path.stem
    return stem[len(prefix) + 1:] if prefix and stem.startswith(prefix + "_") else stem


def fetch_json(url: str, timeout: float = 10):
    """A JSON document from the web, or None when the network or the host says no."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "react-vite-setup", "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310 — fixed https hosts
            return json.loads(r.read().decode())
    except (OSError, ValueError):
        return None


# --- doctor: Node, npm and Playwright's browsers (REACT_VITE_SETUP §1) ---------------------------------------------

MIN_NODE = 20  # the oldest major the stack's packages accept (Vite needs 20.19 or 22.12 and newer)
INSTALL_NODE = "https://nodejs.org/en/download"


def run_version(cmd: list[str]) -> str | None:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.TimeoutExpired):
        return None
    m = re.search(r"(\d+\.\d+\.\d+)", out.stdout)
    return m.group(1) if out.returncode == 0 and m else None


def version_key(v: str | None) -> tuple:
    return tuple(int(x) for x in re.findall(r"\d+", v or "")[:3])


def browser_cache(home: Path, env: dict) -> Path:
    """Where Playwright keeps its browsers on this machine."""
    if env.get("PLAYWRIGHT_BROWSERS_PATH") not in (None, "", "0"):
        return Path(env["PLAYWRIGHT_BROWSERS_PATH"]).expanduser()
    system = platform.system()
    if system == "Darwin":
        return home / "Library" / "Caches" / "ms-playwright"
    if system == "Windows":
        return Path(env.get("LOCALAPPDATA", home / "AppData" / "Local")) / "ms-playwright"
    return Path(env.get("XDG_CACHE_HOME", home / ".cache")) / "ms-playwright"


def browsers_installed(cache: Path) -> dict:
    """Each browser in Playwright's cache, with its builds: `chromium-1223` → chromium: [1223]."""
    found: dict = {}
    if cache.is_dir():
        for d in sorted(cache.iterdir()):
            m = re.fullmatch(r"(chromium|chromium_headless_shell|webkit|firefox)-(\d+)", d.name)
            if m and d.is_dir():
                found.setdefault(m.group(1), []).append(int(m.group(2)))
    return found


def browsers_needed(root: Path, engines: list[str]) -> dict:
    """The build of each browser the project's own Playwright drives — from its `browsers.json` in node_modules —
    for the engines the spec names, and Chromium with its headless shell for the stories. Empty before
    `npm install`."""
    path = root / "node_modules" / "playwright-core" / "browsers.json"
    try:
        listed = {b["name"].replace("-", "_"): int(b["revision"])
                  for b in json.loads(path.read_text(encoding="utf-8"))["browsers"]}
    except (OSError, ValueError, KeyError, TypeError):
        return {}
    want = set(engines) | {"chromium", "chromium_headless_shell"}  # the stories run in Chromium, whatever the spec
    return {name: rev for name, rev in listed.items() if name in want}


def browsers_missing(needed: dict, have: dict) -> list[str]:
    return [f"{name} {rev}" for name, rev in sorted(needed.items()) if rev not in have.get(name, [])]


def latest_node_lts() -> str | None:
    index = fetch_json("https://nodejs.org/dist/index.json")
    if not isinstance(index, list):
        return None
    for release in index:
        if isinstance(release, dict) and release.get("lts"):
            return str(release.get("version", "")).lstrip("v") or None
    return None


def latest_version(package: str) -> str | None:
    data = fetch_json("https://registry.npmjs.org/" + urllib.parse.quote(package, safe="@") + "/latest")
    return data.get("version") if isinstance(data, dict) else None


def cmd_doctor(args) -> int:
    root = repo_root()
    home = Path.home()
    node, npm = run_version(["node", "--version"]), run_version(["npm", "--version"])
    nvmrc = root / ".nvmrc"
    managers = [m for m, ok in (("nvm", (Path(os.environ.get("NVM_DIR", home / ".nvm")) / "nvm.sh").is_file()),
                                ("fnm", bool(shutil.which("fnm"))), ("volta", bool(shutil.which("volta")))) if ok]
    cache = browser_cache(home, dict(os.environ))
    spec = pick_spec(root, None)
    engines = (read_spec(spec)[0].get("browsers") if spec else None) or ["chromium", "webkit"]
    have = browsers_installed(cache)
    needed = browsers_needed(root, engines)
    report = {"node": node, "npm": npm, "version_managers": managers,
              "nvmrc": nvmrc.read_text().strip() if nvmrc.is_file() else None,
              "playwright_cache": str(cache), "playwright_browsers": have, "playwright_needs": needed,
              "playwright_missing": browsers_missing(needed, have)}
    if args.latest:
        report["latest_node_lts"] = latest_node_lts()
        report["latest"] = {p: latest_version(p) for p in TESTED}
    usable = node is not None and version_key(node)[:1] >= (MIN_NODE,)
    if args.json:
        print(json.dumps(report, indent=2))
        return 0 if usable else 1
    if node is None:
        print(f"Node: not found. Install an LTS release — from {INSTALL_NODE}, or with a version manager (nvm, fnm, "
              "volta) — then run doctor again. The skill never installs Node (REACT_VITE_SETUP " + SEC + "1).")
        return 1
    print(f"Node: {node}" + ("" if usable else f" — older than {MIN_NODE}, which the stack needs: install an LTS "
                                                 f"release ({INSTALL_NODE})") + f"   npm: {npm or 'not found'}")
    print("Version managers: " + (", ".join(managers) or "none found"))
    if report["nvmrc"]:
        pinned = report["nvmrc"].lstrip("v").split(".")[0]
        print(f".nvmrc: {report['nvmrc']}" + ("" if node.split(".")[0] == pinned else
                                              f" — this shell runs {node}: `nvm use` (or fnm, volta) first"))
    print(f"Playwright's browsers ({cache}): " + (", ".join(f"{b} {max(v)}" for b, v in sorted(have.items()))
                                                    or "none"))
    if needed:
        missing = report["playwright_missing"]
        print("This project's Playwright needs " + ", ".join(f"{n} {r}" for n, r in sorted(needed.items())) + (
            f" — missing {', '.join(missing)}: `npx playwright install {' '.join(engines_with_chromium(engines))}`, "
            "with the person's yes "
            "(it downloads them into the folder above)" if missing else " — all installed"))
    elif not have:
        print("No browsers yet: after `npm install`, `npx playwright install` with the person's yes")
    if args.latest:
        lts = report["latest_node_lts"]
        print(f"Latest Node LTS: {lts or 'unknown (offline?)'}" + (
            f" — this machine runs {node}" if lts and lts.split('.')[0] != node.split('.')[0] else ""))
        newer = [f"{p} {v} (tested {TESTED[p]})" for p, v in report["latest"].items()
                 if v and version_key(v)[:1] > version_key(TESTED[p])[:1]]
        unknown = [p for p, v in report["latest"].items() if v is None]
        print("Packages: " + ("a newer major than the skill was proven with — " + "; ".join(newer) if newer
                              else "the newest releases are the majors the skill was proven with"))
        if unknown:
            print("Not reached: " + ", ".join(unknown))
    return 0 if usable else 1


# --- spec: the web app spec in docs/ (REACT_VITE_SETUP §2) -----------------------------------------------------------

SPEC_NAMES = ("*web*app*spec*", "*web*spec*", "*app*spec*")
SPEC_FILE = "WEB_APP_SPEC.md"
PLACEHOLDER = re.compile(r"<[^<>\n]*>")
BROWSER_WORD = re.compile(r"\b(chromium|webkit|firefox|chrome|safari)\b", re.I)
BROWSERS = {"chromium": "Desktop Chrome", "webkit": "Desktop Safari", "firefox": "Desktop Firefox"}
BROWSER_ALIASES = {"chromium": "chromium", "chrome": "chromium", "google chrome": "chromium", "webkit": "webkit",
                   "safari": "webkit", "firefox": "firefox"}
FACT_ROWS = {"name": "name", "title": "title", "language": "lang", "lang": "lang", "node": "node",
             "dev server port": "dev_port", "dev port": "dev_port", "preview port": "preview_port",
             "storybook port": "storybook_port", "browsers": "browsers", "viewports": "viewports",
             "sizes": "viewports"}
VIEWPORT = re.compile(r"(\d{3,4})\s*[x×]\s*(\d{3,4})")
# The defaults, from the project this skill was drawn from (REACT_VITE_SETUP §2): its Node, its servers' ports, and
# the sizes its mocks are drawn at — a phone and a laptop — in the engines of Chrome and Safari.
DEFAULTS = {"lang": "en", "node": "22", "dev_port": "5173", "preview_port": "4173", "storybook_port": "6006",
            "browsers": "chromium, webkit", "viewports": "390x844, 1280x800"}


def spec_named_docs(root: Path) -> list[Path]:
    """Every doc in docs/ named like a web app spec, filled in or not."""
    docs = root / "docs"
    return sorted(p for p in docs.rglob("*.md") if any(fnmatch.fnmatch(p.name.lower(), n) for n in SPEC_NAMES)) \
        if docs.is_dir() else []


def find_specs(root: Path) -> list[Path]:
    """Docs named like a web app spec that name a browser outside a template's `<…>` placeholders."""
    docs = root / "docs"
    if not docs.is_dir():
        return []
    found = []
    for p in sorted(docs.rglob("*.md")):
        if any(fnmatch.fnmatch(p.name.lower(), n) for n in SPEC_NAMES):
            text = PLACEHOLDER.sub("", p.read_text(encoding="utf-8", errors="replace"))
            if BROWSER_WORD.search(text):
                found.append(p)
    return found


def pick_spec(root: Path, given: str | None) -> Path | None:
    if given:
        p = (root / given).resolve()
        return p if p.is_file() and (root / "docs").resolve() in p.parents else None
    specs = find_specs(root)
    return specs[0] if len(specs) == 1 else None


def cell(text: str) -> str:
    text = PLACEHOLDER.sub("", text.replace("\\|", "\x00")).replace("\x00", "|")
    return text.strip().strip("`").strip()


def read_facts(text: str) -> tuple[dict, list[str]]:
    """The rows of every `| Fact | Value |` table: the first row for a fact wins, and a second is a note."""
    raw, notes, in_table = {}, [], False
    for line in text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            in_table = False
            continue
        cells = [c for c in re.split(r"(?<!\\)\|", s)[1:-1]]
        if not cells:
            continue
        if not in_table:
            in_table = len(cells) > 1 and [cell(c).lower() for c in cells[:2]] == ["fact", "value"]
            continue
        if set(s) <= set("|-: "):
            continue
        key = FACT_ROWS.get(cell(cells[0]).lower())
        if key and len(cells) > 1:
            value = cell(cells[1])
            if key in raw and value != raw[key]:
                notes.append(f"{cell(cells[0])}: a second row says {value!r}; the first, {raw[key]!r}, is used")
            raw.setdefault(key, value)
    return raw, notes


def normalize(raw: dict) -> tuple[dict, list[str]]:
    """The spec's values as the generator takes them, and what to ask the person about each one that is missing or
    unclear — never a guess."""
    facts, missing = {}, []
    name = raw.get("name", "")
    if re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,213}", name):
        facts["name"] = name
    else:
        missing.append("name — the package's name: lowercase letters, digits, `-`, `.` and `_`")
    if raw.get("title"):
        facts["title"] = raw["title"]
    else:
        missing.append("title — the app's name as people read it, for the page's <title>")
    lang = raw.get("lang", "")
    if re.fullmatch(r"[a-z]{2,3}(-[A-Za-z0-9]{2,8})*", lang):
        facts["lang"] = lang
    else:
        missing.append("language — the page's language as a BCP 47 tag, such as en or fr-CA")
    m = re.fullmatch(r"v?(\d+)(?:\.[\dx]+)*(?:\s*\(?LTS\)?)?", raw.get("node", ""), re.I)
    if m and int(m.group(1)) >= MIN_NODE:
        facts["node_major"] = int(m.group(1))
    else:
        missing.append(f"node — a major release, {MIN_NODE} or newer, such as 22")
    ports = {}
    for key, label in (("dev_port", "dev server port"), ("preview_port", "preview port"),
                       ("storybook_port", "storybook port")):
        v = raw.get(key, "")
        if re.fullmatch(r"[0-9]{1,5}", v) and 1024 <= int(v) <= 65535:
            ports[key] = int(v)
        else:
            missing.append(f"{label} — a port from 1024 to 65535")
    if len(set(ports.values())) < len(ports):
        missing.append("ports — the dev server, the preview and Storybook each need a port of their own")
    facts.update(ports)
    words = [w.strip().lower() for w in re.split(r",|\band\b|/|;", raw.get("browsers", "")) if w.strip()]
    browsers, unknown = [], []
    for w in words:
        b = BROWSER_ALIASES.get(w)
        if b is None:
            unknown.append(w)
        elif b not in browsers:
            browsers.append(b)
    if unknown:
        missing.append(f"browsers — {', '.join(unknown)} is not a Playwright engine: chromium, webkit or firefox")
    elif browsers:
        facts["browsers"] = browsers
    else:
        missing.append("browsers — the engines the end-to-end tests run in: chromium, webkit, firefox")
    sizes = [(int(w), int(h)) for w, h in VIEWPORT.findall(raw.get("viewports", ""))]
    if sizes:
        facts["viewports"] = sizes
    else:
        missing.append("viewports — the sizes the app is tested at, as width x height: 390x844, 1280x800")
    return facts, missing


def read_spec(path: Path) -> tuple[dict, list[str], list[str]]:
    raw, notes = read_facts(path.read_text(encoding="utf-8", errors="replace"))
    facts, missing = normalize(raw)
    return facts, missing, notes


def no_spec_message(root: Path) -> str:
    return ("No web app spec in docs/. Write it first: `react_vite.py spec --init` fills it with the defaults "
            f"(REACT_VITE_SETUP {SEC}2) — tell the person each one, and pass the ones they name (--name, --title, "
            "--browsers …). A doc named like a web app spec that names no browser is not one yet.")


def section_of(text: str, doc: str, words: tuple) -> str:
    """`DOC §n` for the first numbered heading holding one of the words, so a code comment can cite it."""
    for line in text.splitlines():
        m = re.match(r"#{2,4}\s+(\d+(?:\.\d+)*)\.?\s+(.*)", line)
        if m and any(w in m.group(2).lower() for w in words):
            return f"{doc} {SEC}{m.group(1)}"
    return doc


def spec_path(root: Path, prefix: str) -> Path:
    return root / "docs" / (f"{prefix}_{SPEC_FILE}" if prefix else SPEC_FILE)


def init_spec(root: Path, given: dict, dry: bool = False) -> tuple[Path, list[str]]:
    """The spec from the template: each fact the person gave, tagged `[PERSON]`; the rest the defaults, `[DEFAULT]`.
    A doc named like a spec already there — half written, naming no browser yet — is never replaced."""
    settings = kit_settings(root)
    existing = spec_named_docs(root)
    if existing:
        return existing[0], [f"{existing[0].relative_to(root).as_posix()} exists — fill it in there, never over it"]
    bad = [k for k, v in given.items() if v and re.search(r"[|<>{}\n]", str(v))]
    if bad:
        return spec_path(root, settings["DOC_PREFIX"]), [f"{k} — without |, <, >, {{ or }}, which break the spec's "
                                                         "table, the page or the docs" for k in bad]
    named = settings["PROJECT_NAME"]
    folder = re.sub(r"[^a-z0-9._-]+", "-", root.name.lower()).strip("-._") or "web-app"
    values = {"name": folder, "title": named or root.name, **DEFAULTS}
    tags = {k: "`[DEFAULT]`" for k in values}
    for k, v in given.items():
        if v not in (None, ""):
            values[k], tags[k] = str(v), "`[PERSON]`"
    path = spec_path(root, settings["DOC_PREFIX"])
    doc_title = f"{named} — Web App Spec" if named else "Web App Spec"
    text = render((TEMPLATES / SPEC_FILE).read_text(encoding="utf-8"), {
        "doc_title": doc_title, **values, **{f"tag_{k}": t for k, t in tags.items()}}, {}, SPEC_FILE)
    _, missing = normalize(read_facts(text)[0])
    if not missing and not dry:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return path, missing


def cmd_spec(args) -> int:
    root = Path(args.root).resolve() if args.root else repo_root()
    if args.init:
        given = {"name": args.name, "title": args.title, "lang": args.lang, "node": args.node,
                 "browsers": args.browsers, "viewports": args.viewports, "dev_port": args.dev_port,
                 "preview_port": args.preview_port, "storybook_port": args.storybook_port}
        path, missing = init_spec(root, given)
        if missing:
            print("Not written — " + "; ".join(missing))
            return 1
        print(f"created  {path.relative_to(root)} — tell the person each `[DEFAULT]` fact; list it in the README")
        return 0
    spec = pick_spec(root, args.spec)
    if spec is None:
        print(no_spec_message(root) if not find_specs(root) else "Several specs in docs/ — pass --spec.")
        return 1
    facts, missing, notes = read_spec(spec)
    print(json.dumps({"spec": str(spec.relative_to(root)), "facts": facts, "missing": missing, "notes": notes},
                     indent=2))
    return 1 if missing else 0


# --- tokens: DESIGN.md's tokens as CSS custom properties (REACT_VITE_SETUP §5) -------------------------------------

THEME_COLUMN = re.compile(r"\b(?:light|dark|contrast|theme|dim)\b", re.I)
SKIP_COLUMNS = {"kind", "use", "notes", "for", "why", "source", "not for"}


def css_name(token: str, part: str = "") -> str:
    name = re.sub(r"[^a-z0-9-]+", "-", token.lower().replace(".", "-")).strip("-")
    return f"--{name}" + (f"-{re.sub(r'[^a-z0-9]+', '-', part.lower()).strip('-')}" if part else "")


def theme_slug(theme: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", theme.lower()).strip("-")


def css_value(raw: str, part: str = "") -> str | None:
    """A brief's cell as CSS: `4 px` → `4px`, `120 ms` → `120ms`; a type size or line height in rem, so it follows
    the browser's text size (WCAG 1.4.4); a dash is no value."""
    v = raw.strip().strip("`").strip()
    if v in ("", "—", "–", "-"):
        return None
    # As Prettier writes CSS, so the file passes its check: hex in lowercase, strings in single quotes. A design
    # check that compares the brief's colours with the code reads hex digits in any case.
    v = re.sub(r"#[0-9A-Fa-f]{3,8}\b", lambda h: h.group().lower(), v).replace('"', "'")
    m = re.fullmatch(r"(-?\d+(?:\.\d+)?)\s*(px|ms|s|%|rem|em)", v)
    if m:
        if m.group(2) == "px" and part.lower() in ("size", "line height"):
            rem = float(m.group(1)) / 16
            return f"{rem:.4f}".rstrip("0").rstrip(".") + "rem"
        return m.group(1) + m.group(2)
    return v


def design_tokens(text: str) -> tuple[list[str], list[tuple[str, dict]]]:
    """Every `| Token | … |` table's rows: the themes it names, and each custom property with its value per theme
    (`None` for a value that holds in every theme). The first row for a token wins."""
    themes, tokens, seen = [], [], set()
    header, cols = None, None
    for line in text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            header = None
            continue
        cells = [c.strip() for c in re.split(r"(?<!\\)\|", s)[1:-1]]
        if header is None:
            header = cells
            if not cells or cells[0].strip("` ").lower() != "token":
                cols = None
                continue
            cols = []
            for i, h in enumerate(cells[1:], 1):
                low = h.lower()
                if low in SKIP_COLUMNS:
                    continue
                kind = "theme" if THEME_COLUMN.search(h) else "value" if low == "value" else "part"
                cols.append((i, kind, h))
                if kind == "theme" and h not in themes:
                    themes.append(h)
            continue
        if cols is None or set(s) <= set("|-: "):
            continue
        m = re.fullmatch(r"`([a-z0-9][a-z0-9.-]*)`", cells[0]) if cells else None
        if not m:
            continue
        token = m.group(1)
        lows = [h.lower() for h in header]
        at = lows.index("use") if "use" in lows else len(cells)
        use = cells[at] if at < len(cells) else ""  # a short row has no Use cell
        rows: dict = {}
        for i, kind, h in cols:
            if i >= len(cells):
                continue
            if kind == "part":
                v = css_value(cells[i], h)
                if v is not None:
                    rows.setdefault(css_name(token, h), {})[None] = v
            else:
                v = css_value(cells[i])
                if v is not None:
                    rows.setdefault(css_name(token), {})[None if kind == "value" else h] = v
        if not rows and token.startswith("font.") and "," in use:
            rows[css_name(token)] = {None: css_value(use)}  # a font's stack sits in its Use column
        for name, values in rows.items():
            if name not in seen:
                seen.add(name)
                tokens.append((name, values))
    return themes, tokens


def tokens_css(text: str | None, source: str = "DESIGN.md") -> str:
    head = (f"/* Written from {source} by the react-vite-setup skill (`react_vite.py tokens`): a custom property per\n"
            f"   role, a block per theme. {source} decides every value — change it there, then write this file again\n"
            f"   (REACT_VITE_SETUP {SEC}5). */")
    if text is None:
        return head + ("\n\n/* No design brief yet: write DESIGN.md with the design-system skill, then\n"
                       "   `react_vite.py tokens --out src/styles/tokens.css`. */\n:root {\n}\n")
    themes, tokens = design_tokens(text)
    first = themes[0] if themes else None
    scheme = {t: ("dark" if "dark" in t.lower() else "light") for t in themes}

    def block(selector: str, theme: str | None, indent: str = "") -> str:
        """`:root` (theme None or the first) holds every token; a later theme's block only what differs by theme."""
        lines = [f"{indent}{selector} {{"]
        if theme:
            lines.append(f"{indent}  color-scheme: {scheme[theme]};")
        for name, values in tokens:
            v = values.get(None, values.get(first)) if theme in (None, first) else values.get(theme)
            if v is not None:
                lines.append(f"{indent}  {name}: {v};")
        return "\n".join(lines + [f"{indent}}}"])

    out = [head, block(":root", first)]
    for theme in themes[1:]:
        out.append(block(f"[data-theme='{theme_slug(theme)}']", theme))
        if "dark" in theme.lower() and first:
            out.append("@media (prefers-color-scheme: dark) {\n"
                       + block(f":root:not([data-theme='{theme_slug(first)}'])", theme, "  ") + "\n}")
    return "\n\n".join(out) + "\n"


def cmd_tokens(args) -> int:
    root = repo_root()
    design = Path(args.design) if args.design else root / "DESIGN.md"
    css = tokens_css(design.read_text(encoding="utf-8", errors="replace") if design.is_file() else None, design.name)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(css, encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        sys.stdout.write(css)
    return 0 if design.is_file() else 1


# --- generate: the app from the templates (REACT_VITE_SETUP §3–§9) ---------------------------------------------------

# The set this skill was last proven with together: generated, installed, built, and every test layer passing
# (REACT_VITE_SETUP §1). `--versions latest` names any package whose newest major is past these.
TESTED = {
    "react": "19.3.1", "react-dom": "19.3.1",
    "@types/react": "19.3.0", "@types/react-dom": "19.3.0",
    "typescript": "7.0.2", "vite": "8.3.8", "@vitejs/plugin-react": "6.3.0",
    "vitest": "5.1.0", "@vitest/browser-playwright": "5.1.0",
    "playwright": "1.65.1", "@playwright/test": "1.65.1", "@axe-core/playwright": "4.14.0",
    "storybook": "10.6.7", "@storybook/react-vite": "10.6.7", "@storybook/addon-docs": "10.6.7",
    "@storybook/addon-a11y": "10.6.7", "@storybook/addon-vitest": "10.6.7",
    "oxlint": "1.94.0", "prettier": "3.10.1",
}
DEPENDENCIES = ("react", "react-dom")
# TypeScript changes behaviour in minor releases, so it moves by patch (`~`); the rest by minor (`^`).
TILDE = {"typescript"}
GITIGNORE = ("node_modules/", "dist/", "storybook-static/", "playwright-report/", "test-results/", "blob-report/",
             "coverage/", "*.tsbuildinfo", "*storybook.log", ".env*.local")


def resolve_versions(mode: str, node_major: int) -> tuple[dict, list[str]]:
    """Each package's version and the notes to show: `latest` from the registry, `tested` the proven set, or a JSON
    file of {package: version}."""
    notes: list[str] = []
    if mode == "tested":
        versions = dict(TESTED)
    elif mode == "latest":
        versions, offline = {}, []
        for p, tested in TESTED.items():
            v = None if offline else latest_version(p)  # one miss means the registry is out of reach: stop asking
            if v is None:
                offline.append(p)
                v = tested
            elif not re.fullmatch(r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?", v):
                notes.append(f"{p}: the registry's answer is not a version — the tested {tested} is used")
                v = tested
            elif version_key(v)[:1] > version_key(tested)[:1]:
                notes.append(f"{p} {v} is a newer major than the skill was proven with ({tested}) — read its "
                             "migration notes, or pass --versions tested")
            versions[p] = v
        if offline:
            notes.append("the registry did not answer for " + ", ".join(offline) + " — the tested versions are used")
    else:
        given = json.loads(Path(mode).read_text(encoding="utf-8"))
        versions = {p: str(given.get(p, v)).lstrip("^~") for p, v in TESTED.items()}
        for p, v in versions.items():
            if not re.fullmatch(r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?", v):
                notes.append(f"{p}: {mode} gives no version — the tested {TESTED[p]} is used")
                versions[p] = TESTED[p]
    versions["@types/node"] = f"{node_major}"
    return versions, notes


def dependency_lines(versions: dict, dev: bool) -> str:
    names = sorted(p for p in versions if (p in DEPENDENCIES) != dev)
    rng = {p: ("~" if p in TILDE else "^") + (versions[p] if p != "@types/node" else versions[p]) for p in names}
    return ",\n".join(f'    "{p}": "{rng[p]}"' for p in names)


def engines_with_chromium(browsers: list[str]) -> list[str]:
    """The engines to install: the spec's, and Chromium, which the stories run in whatever the spec names."""
    return (["chromium"] if "chromium" not in browsers else []) + list(browsers)


def playwright_projects(browsers: list[str], viewports: list[tuple]) -> str:
    lines = []
    for b in browsers:
        for w, h in viewports:
            lines.append(f"    {{\n      name: '{b}-{w}x{h}',\n      use: {{\n        ...devices['{BROWSERS[b]}'],\n"
                         f"        viewport: {{ width: {w}, height: {h} }},\n      }},\n    }},")
    return "\n".join(lines)


def theme_items(themes: list[str]) -> tuple[str, str]:
    themes = themes or ["Light"]
    items = "\n".join(f"          {{ value: '{theme_slug(t)}', title: '{t}' }}," for t in themes)
    return items, theme_slug(themes[0])


def render(text: str, values: dict, flags: dict, where: str = "template") -> str:
    """`@@if name` / `@@if !name` / `@@else` / `@@endif` keep or drop lines; `{{name}}` takes its value. A name with
    no value is an error, so a template never ships a hole."""
    out, stack = [], []
    for line in text.splitlines(keepends=True):
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

    def value(m):
        if m.group(1) not in values:
            raise KeyError(f"{where}: no value for {{{{{m.group(1)}}}}}")
        return str(values[m.group(1)])
    return re.sub(r"\{\{(\w+)\}\}", value, "".join(out))


def merge_gitignore(path: Path, dry: bool) -> str:
    """The lines the app's tools need ignored, appended — the file's own lines and line endings are left as they
    are."""
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    have = {line.strip() for line in text.splitlines()}
    have |= {h.lstrip("/") for h in have} | {h.rstrip("/") + "/" for h in have if h}
    add = [g for g in GITIGNORE if g not in have]
    if add and not dry:
        lead = "" if not text else ("\n" if text.endswith("\n") else "\n\n")
        with path.open("a", encoding="utf-8") as f:
            f.write(lead + ("\n" if text else "") + "# The web app: written by its tools, or this machine's own\n"
                    + "\n".join(add) + "\n")
    return f"added {', '.join(add)}" if add else "kept"


JUNK = {".DS_Store", "Thumbs.db", "desktop.ini"}  # what an OS leaves in a folder, never a template
VAR = re.compile(r"var\(\s*(--[\w-]+)\s*\)")


def missing_vars(root: Path) -> list[str]:
    """A `var(--x)` with no fallback in the app's CSS whose property tokens.css does not set."""
    tokens = root / "src" / "styles" / "tokens.css"
    have = set(re.findall(r"(--[\w-]+)\s*:", tokens.read_text(encoding="utf-8"))) if tokens.is_file() else set()
    hits = []
    for css in sorted((root / "src").rglob("*.css")):
        if css == tokens:
            continue
        for name in sorted(set(VAR.findall(css.read_text(encoding="utf-8", errors="replace"))) - have):
            hits.append(f"{css.relative_to(root).as_posix()} uses {name}, which tokens.css does not set")
    return hits


def generate(root: Path, facts: dict, versions: dict, spec: Path, dry: bool) -> list[str]:
    settings = kit_settings(root)
    prefix, named = settings["DOC_PREFIX"], settings["PROJECT_NAME"]
    spec_doc = doc_name(spec, prefix)
    arch = root / "docs" / (f"{prefix}_APP_ARCHITECTURE.md" if prefix else "APP_ARCHITECTURE.md")
    design = root / "DESIGN.md"
    design_text = design.read_text(encoding="utf-8", errors="replace") if design.is_file() else None
    themes = design_tokens(design_text)[0] if design_text else []
    items, first = theme_items(themes)
    spec_text = spec.read_text(encoding="utf-8", errors="replace")
    values = {
        **{k: facts[k] for k in ("name", "title", "lang", "node_major", "dev_port", "preview_port", "storybook_port")},
        "spec_doc": spec_doc, "spec_link": f"[{spec_doc}]({spec.name})",
        "spec_facts": section_of(spec_text, spec_doc, ("facts",)),
        "arch_file": arch.name, "arch_title": f"{named} — App Architecture" if named else "App Architecture",
        "deps": dependency_lines(versions, dev=False), "dev_deps": dependency_lines(versions, dev=True),
        "playwright_projects": playwright_projects(facts["browsers"], facts["viewports"]),
        "ci_browsers": " ".join(engines_with_chromium(facts["browsers"])), "theme_items": items, "first_theme": first,
    }
    writes = []
    for src in sorted((TEMPLATES / "project").rglob("*")):
        if src.is_dir() or src.name in JUNK or src.name.endswith("~"):
            continue
        rel = src.relative_to(TEMPLATES / "project").as_posix()
        # `.tpl`: a file whose placeholders the editor would read as broken code or config where it sits
        rel = rel[:-len(".tpl")] if rel.endswith(".tpl") else rel
        writes.append((root / rel, render(src.read_text(encoding="utf-8"), values, {}, rel)))
    writes.append((root / "src" / "styles" / "tokens.css", tokens_css(design_text)))
    writes.append((arch, render((TEMPLATES / "APP_ARCHITECTURE.md").read_text(encoding="utf-8"), values, {},
                                "APP_ARCHITECTURE")))
    report = []
    for dest, text in writes:
        rel = dest.relative_to(root).as_posix()
        if dest.exists():
            report.append(f"kept     {rel} (exists — never overwritten)")
            continue
        if not dry:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(text, encoding="utf-8")
        report.append(f"created  {rel}")
    report.append(f"merged   .gitignore: {merge_gitignore(root / '.gitignore', dry)}")
    if not dry:
        report += [f"warning  {h} — add the role to DESIGN.md (design-system skill), or change the CSS"
                   for h in missing_vars(root)]
    if design_text is None:
        report.append("warning  no DESIGN.md: tokens.css has no values yet — write the brief with the design-system "
                      "skill, then `react_vite.py tokens --out src/styles/tokens.css`")
    return report


def cmd_generate(args) -> int:
    root = Path(args.root).resolve() if args.root else repo_root()
    spec = pick_spec(root, args.spec)
    if spec is None:
        print(no_spec_message(root) if not find_specs(root) else "Several specs in docs/ — pass --spec.")
        return 1
    facts, missing, notes = read_spec(spec)
    for note in notes:
        print(f"note: {note}")
    if missing:
        print("The spec lacks: " + "; ".join(missing) + f". Write each to {spec.relative_to(root)} — the person's "
              f"answer, or the default — then generate (REACT_VITE_SETUP {SEC}2).")
        return 1
    if args.versions not in ("latest", "tested") and not Path(args.versions).is_file():
        print("--versions: latest, tested, or a JSON file of {package: version}", file=sys.stderr)
        return 2
    versions, vnotes = resolve_versions(args.versions, facts["node_major"])
    for note in vnotes:
        print(f"note: {note}")
    for line in generate(root, facts, versions, spec, args.dry_run):
        print(line)
    print("next: `npm install`, then `npx playwright install " + " ".join(engines_with_chromium(facts["browsers"]))
          + "` with the person's "
          "yes, then `npm run check`, `npm run test:stories` and `npm run test:e2e` (REACT_VITE_SETUP " + SEC + "1)"
          + (" — dry run, nothing written" if args.dry_run else ""))
    if (root / ".agents" / "project.py").is_file():
        print("in the agent-harness kit: fill in .agents/project.py with the person's yes (REACT_VITE_SETUP "
              + SEC + "10):\n" + KIT_SETTINGS.format(dev_port=facts["dev_port"], title=facts["title"]))
    return 0


KIT_SETTINGS = """\
  CODE_PATHS = ("src/", "e2e/", ".storybook/", "public/", "index.html", "package.json", "vite.config.ts",
                "vitest.config.ts", "playwright.config.ts", "tsconfig.json", "tsconfig.app.json", "tsconfig.node.json")
  UI_PATHS = ("src/app/", "src/features/", "src/components/", "src/styles/", "*.css")
  TOKEN_FILES = ("src/styles/tokens.css",)
  UX_STRINGS = {{"paths": ("src/", "index.html"), "calls": (), "names": ({title!r},), "baseline": 0}}
  ALLOWED_HOSTS += ("npmjs.org", "npmjs.com", "nodejs.org")   # and the same hosts in .codex/config.toml
  CHECKS = {{
      "types": {{"run": ["npm", "run", "typecheck"], "when": ("src/", "e2e/", ".storybook/", "*.ts", "*.json")}},
      "lint": {{"run": ["npm", "run", "lint"], "when": ("src/", "e2e/", ".storybook/", "*.ts")}},
      "format": {{"run": ["npm", "run", "format:check"], "when": ("src/", "e2e/", ".storybook/", "*.ts", "*.json")}},
      "unit": {{"run": ["npm", "test"], "when": ("src/",)}},
      "stories": {{"run": ["npm", "run", "test:stories"], "when": ("src/", ".storybook/")}},
      "e2e": {{"run": ["npm", "run", "test:e2e"], "when": ("src/", "e2e/", "index.html", "playwright.config.ts"),
               "wait": True}},
      "build": {{"run": ["npm", "run", "build"], "when": ("src/", "index.html", "package.json", "vite.config.ts")}},
  }}
  TARGET = "the app in a browser at localhost:{dev_port}, Storybook beside it"\
"""


# --- check: the app's layering, W1–W5 (REACT_VITE_SETUP §4) --------------------------------------------------------

SOURCE = (".ts", ".tsx", ".js", ".jsx", ".mts", ".mjs")
# Each pattern is linear: a quoted module after `from`, after a bare `import`, or as a call's first argument —
# `import(…)`, `require(…)`, `import.meta.glob(…)`.
IMPORT = re.compile(r"""\bfrom\s*['"]([^'"\n]+)['"]|\bimport\s*['"]([^'"\n]+)['"]"""
                    r"""|\b(?:import\.meta\.glob|import|require)\s*\(\s*['"]([^'"\n]+)['"]""")
SECRET_VAR = re.compile(r"\bVITE_[A-Z0-9_]*(?:SECRET|PASSWORD|PRIVATE|TOKEN|KEY|AUTH|CREDENTIAL)[A-Z0-9_]*\b")
# The env files Vite reads per mode, which a project may commit; `.env` and `*.local` are this machine's own.
ENV_FILES = (".env.example", ".env.production", ".env.development", ".env.staging", ".env.test")
COMPONENT_EXPORT = re.compile(r"^export\s+(?:default\s+)?(?:function\s+[A-Z]|const\s+[A-Z]\w*\s*[:=]|default\s)", re.M)


def strip_comments(text: str) -> str:
    """The source with its comments blanked — newlines kept — and its strings left whole, so `'./*.tsx'` in a string
    never opens a comment."""
    out, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        if c in "'\"`":
            j = i + 1
            while j < n and text[j] != c and not (c != "`" and text[j] == "\n"):
                j += 2 if text[j] == "\\" else 1
            out.append(text[i:j + 1])
            i = j + 1
        elif text.startswith("//", i):
            j = text.find("\n", i)
            i = n if j < 0 else j
        elif text.startswith("/*", i):
            j = text.find("*/", i + 2)
            j = n if j < 0 else j + 2
            out.append("\n" * text.count("\n", i, j))
            i = j
        else:
            out.append(c)
            i += 1
    return "".join(out)


def imports_of(text: str) -> list[str]:
    return [next(g for g in m.groups() if g) for m in IMPORT.finditer(strip_comments(text))]


def resolve(rel: str, spec: str) -> str | None:
    """The repo path an import names — `@/x` is `src/x` — or None for a package."""
    if spec.startswith("@/"):
        return "src/" + spec[2:]
    if spec.startswith("."):
        return os.path.normpath(os.path.join(os.path.dirname(rel), spec)).replace(os.sep, "/")
    return None


def layer(path: str) -> tuple[str, str]:
    """The part of the app a path is in — ("feature", name), ("components", ""), ("app", ""), ("lib", "") … — for a
    file and for a folder imported through its index (`@/features/hello`, `@/app`)."""
    parts = path.split("/")
    if len(parts) > 1 and parts[0] == "src":
        top = parts[1].split(".")[0]
        if top == "features":
            return "feature", parts[2].split(".")[0] if len(parts) > 2 else ""
        if top in ("components", "app", "lib", "hooks", "styles"):
            return top, ""
    return "other", ""


def is_react_vite_app(root: Path) -> bool:
    pkg = root / "package.json"
    if not pkg.is_file() or not any((root / f"vite.config.{e}").is_file() for e in ("ts", "mts", "js", "mjs")):
        return False
    try:
        data = json.loads(pkg.read_text(encoding="utf-8"))
    except ValueError:
        return False
    if not isinstance(data, dict):
        return False
    deps = [d for d in (data.get("dependencies"), data.get("devDependencies")) if isinstance(d, dict)]
    return any("react" in d for d in deps)


def layering_hits(root: Path) -> list[str]:
    hits = []
    src = root / "src"
    files = sorted(p for p in src.rglob("*") if p.is_file() and p.suffix in SOURCE) if src.is_dir() else []
    for p in files:
        rel = p.relative_to(root).as_posix()
        text = p.read_text(encoding="utf-8", errors="replace")
        here, name = layer(rel)
        for spec in imports_of(text):
            target = resolve(rel, spec)
            if target is None:
                continue
            there, other = layer(target)
            if here == "components" and there in ("feature", "app"):
                hits.append(f"W1 {rel}: imports {spec} — a component knows no feature and not the app shell")
            elif here == "feature" and there == "feature" and other != name:
                hits.append(f"W2 {rel}: imports {spec} — features meet in src/app/, never in each other")
            elif here in ("lib", "hooks") and there in ("components", "feature", "app"):
                hits.append(f"W3 {rel}: imports {spec} — src/{here}/ holds what any part may use, and uses no part")
        if (here == "components" and p.suffix == ".tsx" and not re.search(r"\.(stories|test|spec)$", p.stem)
                and p.stem != "index" and COMPONENT_EXPORT.search(text)
                and not (p.parent / f"{p.stem}.stories.tsx").is_file()):
            hits.append(f"W4 {rel}: no {p.stem}.stories.tsx beside it — every component is documented and tested "
                        "by its stories")
    for p in files + [root / f for f in ("index.html",) + ENV_FILES if (root / f).is_file()]:
        rel = p.relative_to(root).as_posix()
        for n, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if "secret-exception" in line:
                continue
            for var in sorted(set(SECRET_VAR.findall(line))):
                hits.append(f"W5 {rel}:{n}: {var} — a VITE_ variable ships in the bundle, so a secret never gets "
                            "one; keep it on a server, or mark a public one `secret-exception` with its reason")
    return hits


def cmd_check(args) -> int:
    root = Path(args.root).resolve() if args.root else repo_root()
    if not is_react_vite_app(root):
        print("react-vite layering: no React and Vite app here (package.json with react, and a vite.config) — "
              "nothing checked")
        return 0
    hits = layering_hits(root)
    for h in hits:
        print(h)
    print(f"react-vite layering: {len(hits)} hit(s) (baseline 0)")
    return 1 if hits else 0


# --- the self-test ------------------------------------------------------------------------------------------------

DESIGN_SAMPLE = """# Demo — Design

| Token | Kind | Light | Dark | Use |
| --- | --- | --- | --- | --- |
| `color.bg.canvas` | surface | `#FFFFFF` | `#111317` | The page |
| `color.text.primary` | text | `#1B1D21` | `#F2F3F5` | Body text |

| Foreground | Background | Floor | Light | Dark |
| --- | --- | --- | --- | --- |
| `color.text.primary` | `color.bg.canvas` | 4.5 | 16.83 | 16.01 |

| Token | Size | Line height | Weight | Use |
| --- | --- | --- | --- | --- |
| `font.sans` | — | — | — | `system-ui, sans-serif` |
| `text.body` | 16 px | 24 px | 400 | Everything people read |

| Token | Value | Use |
| --- | --- | --- |
| `space.lg` | 16 px | Edges |
| `duration.fast` | 120 ms | Hover |
| `easing.enter` | `cubic-bezier(0.22, 1, 0.36, 1)` | Arriving |

| Token | Light | Dark | Use |
| --- | --- | --- | --- |
| `elevation.raised` | `0 1px 2px rgba(0, 0, 0, 0.12)` | `none` | A card |
"""


def self_test() -> int:
    bad, count = [], [0]

    def expect(name, got, want):
        count[0] += 1
        if got != want:
            bad.append(f"FAIL  {name}: want {want!r}, got {got!r}")

    # render: conditions, values, and a hole is an error
    t = "a\n@@if x\nb\n@@else\nc\n@@endif\n{{v}}\n"
    expect("render x", render(t, {"v": 1}, {"x": True}), "a\nb\n1\n")
    expect("render !x", render(t, {"v": 1}, {}), "a\nc\n1\n")
    expect("render keeps ${{ expr }}", render("${{ github.ref }}\n", {}, {}), "${{ github.ref }}\n")
    for broken, err in (("{{nope}}", KeyError), ("@@if x\n", ValueError)):
        try:
            render(broken, {}, {"x": True})
            bad.append(f"FAIL  render {broken!r}: no error")
        except err:
            pass

    # the spec's facts: read, normalized, and asked when unclear — never guessed
    raw = {"name": "demo", "title": "Demo", "lang": "en", "node": "22", "dev_port": "5173", "preview_port": "4173",
           "storybook_port": "6006", "browsers": "Chrome, Safari and chromium", "viewports": "390 × 844, 1280x800"}
    facts, missing = normalize(raw)
    expect("no missing", missing, [])
    expect("browsers aliased, once each", facts.get("browsers"), ["chromium", "webkit"])
    expect("viewports", facts.get("viewports"), [(390, 844), (1280, 800)])
    expect("node", normalize({**raw, "node": "v22.12 LTS"})[0].get("node_major"), 22)
    expect("old node asked", any(m.startswith("node") for m in normalize({**raw, "node": "18"})[1]), True)
    expect("edge asked", any("edge" in m for m in normalize({**raw, "browsers": "chromium, edge"})[1]), True)
    expect("shared port asked", any(m.startswith("ports") for m in normalize({**raw, "preview_port": "5173"})[1]),
           True)
    expect("bad name asked", any(m.startswith("name") for m in normalize({**raw, "name": "My App"})[1]), True)
    expect("a non-ASCII digit is asked, never a crash",
           any(m.startswith("dev server port") for m in normalize({**raw, "dev_port": "51\u00b2"})[1]), True)
    expect("no viewports asked", any(m.startswith("viewports") for m in normalize({**raw, "viewports": "big"})[1]),
           True)
    table = ("## 1. Facts\n\n| Fact | Value | Source |\n| --- | --- | --- |\n| Name | `demo` | x |\n"
             "| Browsers | chromium \\| webkit | x |\n| Name | other | x |\n| Title | `<My App>` | x |\n\n"
             "| Name | outside the table |\n\n| Fact | Carried by |\n| --- | --- |\n| Name | `package.json` |\n")
    raw2, notes = read_facts(table)
    expect("first row wins, a placeholder is empty", (raw2.get("name"), raw2.get("title")), ("demo", ""))
    expect("escaped pipe", raw2.get("browsers"), "chromium | webkit")
    expect("second row noted", len(notes), 1)
    expect("section", section_of(table, "WEB_APP_SPEC", ("facts",)), f"WEB_APP_SPEC {SEC}1")

    # tokens: every Token table, a block per theme, the brief's digits kept, type sizes in rem
    themes, toks = design_tokens(DESIGN_SAMPLE)
    expect("themes", themes, ["Light", "Dark"])
    names = dict(toks)
    expect("colour per theme", names.get("--color-bg-canvas"), {"Light": "#ffffff", "Dark": "#111317"})
    expect("pairs table skipped", "--color-text-primary" in names and len(names["--color-text-primary"]) == 2, True)
    expect("type parts in rem", (names.get("--text-body-size"), names.get("--text-body-line-height"),
                                 names.get("--text-body-weight")), ({None: "1rem"}, {None: "1.5rem"}, {None: "400"}))
    expect("font stack from Use", names.get("--font-sans"), {None: "system-ui, sans-serif"})
    expect("units", (names["--space-lg"], names["--duration-fast"]), ({None: "16px"}, {None: "120ms"}))
    css = tokens_css(DESIGN_SAMPLE)
    root_block = css.split("[data-theme='dark']")[0]
    expect("light in :root", "--color-bg-canvas: #ffffff;" in root_block and "color-scheme: light;" in root_block,
           True)
    expect("one-value tokens in :root only", css.count("--space-lg: 16px;"), 1)
    expect("dark block and media", css.count("--color-bg-canvas: #111317;"), 2)
    expect("dark follows the system unless light is chosen", ":root:not([data-theme='light'])" in css, True)
    expect("elevation per theme", "--elevation-raised: none;" in css, True)
    expect("no brief", ":root {\n}" in tokens_css(None), True)
    short = "| Token | Light | Dark | Use |\n| --- | --- | --- | --- |\n| `color.a` | #FFF |\n"
    expect("a short row, no crash", design_tokens(short)[1], [("--color-a", {"Light": "#fff"})])
    dims = "| Token | Value | Dimension | Use |\n| --- | --- | --- | --- |\n| `size.a` | 4 px | width | x |\n"
    expect("a Dimension column is no theme", design_tokens(dims)[0], [])

    # versions: ranges, @types/node from the spec's Node
    lines = dependency_lines({**TESTED, "@types/node": "22"}, dev=True)
    expect("tilde for typescript", f'"typescript": "~{TESTED["typescript"]}"' in lines, True)
    expect("node types", '"@types/node": "^22"' in lines, True)
    expect("react is a dependency", '"react"' in dependency_lines(TESTED, dev=False)
           and '"react"' not in lines, True)
    expect("projects", playwright_projects(["chromium", "webkit"], [(390, 844), (1280, 800)]).count("name:"), 4)
    expect("theme items", theme_items(["Light", "High contrast"]),
           ("          { value: 'light', title: 'Light' },\n"
            "          { value: 'high-contrast', title: 'High contrast' },", "light"))

    # imports: every form, comments skipped
    src = ("import a from './a'\nimport type { B } from \"@/b\"\nimport {\n  c,\n  d as e,\n} from '../c'\n"
           "export { f } from './f'\nimport './side.css'\nconst g = await import('./g')\n"
           "// import h from './h'\n/* import i from './i' */\nimport React, { useState } from 'react'\n")
    expect("imports", imports_of(src), ["./a", "@/b", "../c", "./f", "./side.css", "./g", "react"])
    globbed = ("const pages = import.meta.glob('./*.tsx')\nimport b from '@/features/x/x'\n"
               "const s = 'http://x/*' // a URL in a string opens no comment\nimport c from '../c' /* */\n")
    expect("a glob string opens no comment", imports_of(globbed), ["./*.tsx", "@/features/x/x", "../c"])
    import time
    began = time.monotonic()
    imports_of(("import" + " " * 20000 + "\n") * 5)
    expect("long runs of spaces stay fast", time.monotonic() - began < 1, True)
    expect("a folder import is its part", [layer(p) for p in ("src/features/hello", "src/app", "src/components",
                                                              "src/features", "src/lib/cx")],
           [("feature", "hello"), ("app", ""), ("components", ""), ("feature", ""), ("lib", "")])
    expect("resolve alias", resolve("src/app/App.tsx", "@/features/x/y"), "src/features/x/y")
    expect("resolve relative", resolve("src/features/a/a.tsx", "../b/b"), "src/features/b/b")
    expect("package", resolve("src/x.ts", "react"), None)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "Demo App"
        (root / "docs").mkdir(parents=True)
        expect("no spec", pick_spec(root, None), None)
        (root / "docs" / "NOTES.md").write_text("chromium named, but not a spec by its name\n")
        expect("not a spec", find_specs(root), [])
        (root / "docs" / "WEB_APP_SPEC.md").write_text("| Browsers | `<chromium, webkit>` |\n")
        expect("placeholders are not a spec", find_specs(root), [])
        (root / "docs" / "WEB_APP_SPEC.md").unlink()

        # spec --init: the defaults, tagged, and a fact the person gave
        path, missing = init_spec(root, {"title": "Demo", "browsers": "chromium"})
        text = path.read_text()
        expect("init writes", (missing, path.name), ([], "WEB_APP_SPEC.md"))
        expect("init name from the folder", read_spec(path)[0]["name"], "demo-app")
        expect("init person's fact", read_spec(path)[0]["browsers"], ["chromium"])
        expect("init tags", ("`[PERSON]`" in text, "`[DEFAULT]`" in text, "{{" in text, "<" in text.split("---")[0]),
               (True, True, False, False))
        expect("init found", find_specs(root), [path])
        before = path.read_text(encoding="utf-8")
        expect("init never writes over a spec", (init_spec(root, {})[1] != [], path.read_text(encoding="utf-8")),
               (True, before))
        fresh = Path(tmp) / "fresh"
        (fresh / "docs").mkdir(parents=True)
        (fresh / "docs" / "WEB_APP_SPEC.md").write_text("# Half written\n\n| Fact | Value |\n| --- | --- |\n"
                                                         "| Name | mine |\n", encoding="utf-8")
        half = (fresh / "docs" / "WEB_APP_SPEC.md").read_text(encoding="utf-8")
        expect("a half-written spec, naming no browser, is kept",
               (bool(init_spec(fresh, {})[1]), (fresh / "docs" / "WEB_APP_SPEC.md").read_text(encoding="utf-8")),
               (True, half))
        (fresh / "docs" / "WEB_APP_SPEC.md").unlink()
        expect("init refuses an old node", any(m.startswith("node") for m in init_spec(fresh, {"node": "16"},
                                                                                       dry=True)[1]), True)
        expect("init refuses a | in the title", any(m.startswith("title") for m in init_spec(fresh, {"title": "A | B"},
                                                                                            dry=True)[1]), True)
        expect("nothing written on a refusal", list((fresh / "docs").iterdir()), [])

        # generate twice — with a brief and without — and the app checks clean
        (root / "DESIGN.md").write_text(DESIGN_SAMPLE)
        (root / ".gitignore").write_text("node_modules\r\n")
        facts, missing, _ = read_spec(path)
        versions, _ = resolve_versions("tested", facts["node_major"])
        report = generate(root, facts, versions, path, False)
        texts = {p.relative_to(root).as_posix(): p.read_text() for p in root.rglob("*") if p.is_file()}
        holes = [f for f, s in texts.items() if "@@" in s or re.search(r"\{\{\w+\}\}", s)]
        expect("no holes", holes, [])
        expect("no .tpl", [f for f in texts if f.endswith(".tpl")], [])
        expect("package.json is JSON", json.loads(texts["package.json"])["name"], "demo-app")
        expect("tsconfigs are JSONC", [json.loads(re.sub(r"/\*.*?\*/", "", texts[f])) is not None for f in
                                      ("tsconfig.json", "tsconfig.app.json", "tsconfig.node.json")], [True] * 3)
        expect("engines", json.loads(texts["package.json"])["engines"]["node"], ">=22")
        expect("ports", ("port: 5173, strictPort: true" in texts["vite.config.ts"],
                         "--port 6006" in json.loads(texts["package.json"])["scripts"]["storybook"]), (True, True))
        expect("one browser, two sizes", texts["playwright.config.ts"].count("devices['Desktop Chrome']"), 2)
        expect("spec cited", f"WEB_APP_SPEC {SEC}1" in texts["playwright.config.ts"], True)
        expect("themes in the toolbar", "{ value: 'dark', title: 'Dark' }" in texts[".storybook/preview.tsx"], True)
        expect("tokens written", "--color-bg-canvas: #ffffff;" in texts["src/styles/tokens.css"], True)
        expect("ci browsers", "playwright install --with-deps chromium" in texts[".github/workflows/web.yml"], True)
        expect("ci expressions kept", "${{ github.ref }}" in texts[".github/workflows/web.yml"], True)
        expect("arch doc", "docs/APP_ARCHITECTURE.md" in texts, True)
        expect("gitignore appended", (root / ".gitignore").read_bytes().startswith(b"node_modules\r\n")
               and "node_modules/" not in texts[".gitignore"].split("# The web app")[1], True)
        expect("the sample brief lacks roles the templates use", any("--color-accent" in r for r in report), True)
        expect("clean", layering_hits(root), [])
        expect("a react app", is_react_vite_app(root), True)
        again = generate(root, facts, versions, path, False)
        (root / "src/main.tsx").write_text("// the person's own entry\n", encoding="utf-8")
        again = generate(root, facts, versions, path, False)
        expect("never overwrites", ([r for r in again if r.startswith("created")],
                                    (root / "src/main.tsx").read_text(encoding="utf-8")),
               ([], "// the person's own entry\n"))
        dry = Path(tmp) / "dry"
        (dry / "docs").mkdir(parents=True)
        dpath, _ = init_spec(dry, {})
        generate(dry, read_spec(dpath)[0], versions, dpath, True)
        expect("dry run writes nothing", sorted(p.name for p in dry.rglob("*") if p.is_file()), ["WEB_APP_SPEC.md"])

        # each layering rule, broken once
        (root / "src/features/other").mkdir(parents=True)
        (root / "src/features/other/other.tsx").write_text("export const x = 1\n")
        (root / "src/components/ui/card.tsx").write_text(
            "import { Hello } from '@/features/hello/hello'\nexport function Card() { return null }\n")
        (root / "src/features/hello/peek.ts").write_text("import { x } from '../other/other'\n")
        (root / "src/lib/bad.ts").write_text("import { Button } from '../components/ui/button'\n")
        (root / "src/app/env.ts").write_text("export const k = import.meta.env.VITE_STRIPE_SECRET_KEY\n"
                                             "export const m = import.meta.env.VITE_MAPS_TOKEN // secret-exception: "
                                             "a public, referrer-locked key\n")
        expect("rules", sorted(h[:2] for h in layering_hits(root)), ["W1", "W2", "W3", "W4", "W5"])
        expect("W5 names, never values", any("VITE_STRIPE_SECRET_KEY" in h for h in layering_hits(root)), True)
        expect("not a react app", is_react_vite_app(dry), False)
        for f in ("src/components/ui/card.tsx", "src/features/hello/peek.ts", "src/lib/bad.ts", "src/app/env.ts"):
            (root / f).unlink()
        # the same rules through a folder's index, and W5 in the page and a mode's env file
        (root / "src/components/ui/card.tsx").write_text(
            "import { Hello } from '@/features/hello'\nimport { App } from '../../app'\n"
            "export function Card() { return null }\n", encoding="utf-8")
        (root / "src/components/ui/card.stories.tsx").write_text("export default {}\n", encoding="utf-8")
        (root / "src/features/hello/peek.ts").write_text("import { x } from '@/features/other'\n", encoding="utf-8")
        (root / "src/hooks").mkdir()
        (root / "src/hooks/use-x.ts").write_text("import { Button } from '@/components'\n", encoding="utf-8")
        (root / ".env.production").write_text("VITE_OPENAI_API_KEY=x\n", encoding="utf-8")
        hits = layering_hits(root)
        expect("folder imports", sorted(h[:2] for h in hits), ["W1", "W1", "W2", "W3", "W5"])
        expect("W5 in a mode's env file", any(h.startswith("W5 .env.production:1: VITE_OPENAI_API_KEY") for h in hits),
               True)
        expect("W5 never reads .env.local", ".env.local" in ENV_FILES, False)
        odd = Path(tmp) / "odd"
        odd.mkdir()
        (odd / "vite.config.ts").write_text("", encoding="utf-8")
        for pkg in ('{"dependencies": null}', "[]", '{"devDependencies": {"react": "19"}}'):
            (odd / "package.json").write_text(pkg, encoding="utf-8")
            expect(f"package.json {pkg}", is_react_vite_app(odd), "react" in pkg)

        # a spec without Chromium: CI and doctor still bring Chromium, which the stories run in
        expect("chromium always installed", engines_with_chromium(["webkit"]), ["chromium", "webkit"])
        webkit = Path(tmp) / "webkit"
        (webkit / "docs").mkdir(parents=True)
        wpath, _ = init_spec(webkit, {"browsers": "webkit"})
        generate(webkit, read_spec(wpath)[0], versions, wpath, False)
        expect("webkit spec, ci installs chromium too",
               "--with-deps chromium webkit" in (webkit / ".github/workflows/web.yml").read_text(encoding="utf-8"),
               True)

        # the registry: one miss stops the asking, and an answer not shaped like a version is not used
        global latest_version
        real, calls = latest_version, []

        def fake(p, answers=iter(["<script>", None])):
            calls.append(p)
            return next(answers, "9.9.9")
        latest_version = fake
        try:
            got, notes = resolve_versions("latest", 22)
        finally:
            latest_version = real
        expect("registry: a bad answer, then a miss stops the asking", (len(calls), got["react"], got["react-dom"],
                                                                         got["vite"]),
               (2, TESTED["react"], TESTED["react-dom"], TESTED["vite"]))
        expect("registry: offline noted", any("did not answer" in n for n in notes), True)

        # doctor: the browsers in Playwright's cache
        cache = Path(tmp) / "ms-playwright"
        for d in ("chromium-1223", "chromium-1217", "webkit-2370", "ffmpeg-1011"):
            (cache / d).mkdir(parents=True)
        (cache / "chromium_headless_shell-1223").mkdir()
        expect("browsers", browsers_installed(cache), {"chromium": [1217, 1223], "chromium_headless_shell": [1223],
                                                       "webkit": [2370]})
        pw = root / "node_modules" / "playwright-core"
        pw.mkdir(parents=True)
        (pw / "browsers.json").write_text(json.dumps({"browsers": [
            {"name": "chromium", "revision": "1255"}, {"name": "chromium-headless-shell", "revision": "1255"},
            {"name": "firefox", "revision": "1572"}, {"name": "webkit", "revision": "2370"}]}))
        expect("needed for a webkit spec: chromium too", sorted(browsers_needed(root, ["webkit"])),
               ["chromium", "chromium_headless_shell", "webkit"])
        needed = browsers_needed(root, ["chromium", "webkit"])
        expect("needed: the spec's engines and the headless shell", needed,
               {"chromium": 1255, "chromium_headless_shell": 1255, "webkit": 2370})
        expect("missing builds", browsers_missing(needed, browsers_installed(cache)),
               ["chromium 1255", "chromium_headless_shell 1255"])
        expect("nothing needed before npm install", browsers_needed(dry, ["chromium"]), {})
        expect("cache from env", browser_cache(Path(tmp), {"PLAYWRIGHT_BROWSERS_PATH": str(cache)}), cache)
        expect("version order", version_key("5.1.0") < version_key("5.10.0") < version_key("10.0"), True)

    for line in bad:
        print(line)
    print(f"react-vite self-test: {count[0] - len(bad)}/{count[0]} cases pass")
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
    s.add_argument("--init", action="store_true")
    for flag in ("name", "title", "lang", "node", "browsers", "viewports", "dev-port", "preview-port",
                 "storybook-port"):
        s.add_argument(f"--{flag}")
    g = sub.add_parser("generate")
    g.add_argument("--versions", default="latest")
    g.add_argument("--spec")
    g.add_argument("--root")
    g.add_argument("--dry-run", action="store_true")
    t = sub.add_parser("tokens")
    t.add_argument("--design")
    t.add_argument("--out")
    c = sub.add_parser("check")
    c.add_argument("--root")
    args = ap.parse_args()
    return {"doctor": cmd_doctor, "spec": cmd_spec, "generate": cmd_generate, "tokens": cmd_tokens,
            "check": cmd_check}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
