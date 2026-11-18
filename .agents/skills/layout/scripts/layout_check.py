#!/usr/bin/env python3
"""The layout skill's check: patterns in UI files that break a layout across window sizes, from references/layout.md
(cited `LAYOUT §n`). It finds what a line of code shows; the walk across tiers on the target finds the rest.

    python3 .agents/skills/layout/scripts/layout_check.py            # every UI file, against the baseline
    python3 .agents/skills/layout/scripts/layout_check.py FILE …     # some files, no baseline
    python3 .agents/skills/layout/scripts/layout_check.py --test     # the self-test

Which files: in a repo with the agent-harness kit, UI_PATHS from `.agents/project.py` (empty there means none yet);
in any other repo, every tracked file with a UI extension outside vendored and generated folders. A line that carries
`layout-exception` is skipped — write the reason beside it.

  G1  a layout chosen by device type — a user agent tested for a device, `userAgentData.mobile`,
      `userInterfaceIdiom`, an `isTablet` name; or sized by the device's screen — `screen.width`,
      `UIScreen.main.bounds`                                                                LAYOUT §1, §12
  G2  a screen breakpoint that is not one of the brief's tiers — `min-width`/`max-width` or range syntax
      (`width >= 768px`) in `@media`, `matchMedia` or a query string such as a `useMediaQuery` hook's, Tailwind
      `min-[…]:`/`max-[…]:`; a `max-width` on a tier itself, which overlaps the tier's `min-width`      LAYOUT §2
  G3  a width of `100vw` or Tailwind's `w-screen` — wider than the page by its scrollbar — unless the rule is
      `position: fixed`                                                                         LAYOUT §6
  G4  a spacing value off the base grid of 4 — CSS margin, padding, gap, inset; Tailwind `p-[…]`, `m-[…]`, `gap-[…]`
      and the half steps `-1.5`, `-2.5`, `-3.5`; SwiftUI `.padding(n)`, `spacing: n`; Compose `n.dp` in `padding`,
      `spacedBy`, `Spacer`; Android XML padding and margins; LVGL `pad_*` and `margin_*` style setters   LAYOUT §7
  G5  a fixed `width` or `min-width` at or above the smallest tier, outside a media or container query, in a rule
      with no `max-width`                                                                       LAYOUT §6
  Embedded (ESP-IDF, LVGL) — C and C++ files:
  G6  an object placed at literal coordinates — `lv_obj_set_pos(obj, 12, 40)`                  LAYOUT §12

The tiers: the `breakpoint.*` rows of the repo's DESIGN.md token tables when it has them, Bootstrap 5.3's 576, 768,
992, 1200 and 1400 otherwise; px, and em or rem at 16 px. A `max-width` 0.02 px under a tier counts as the tier.

What it cannot see: a gap on the grid but off the brief's scale, or a literal where a token belongs; a pane under its
minimum width; navigation in the wrong form for its tier; focus or state lost on a resize; text over the measure. Its
limits: G1 tests a user agent only on a line that also names a device (mobile, iphone, ipad, android, tablet), and an
`isMobile` name passes — it is usually a width test; G2 skips `@container`, and reads no native code: a width test in
Swift or Kotlin against a number that is not a tier is the reviewer's; G4 passes 0, 1 and 2 px as hairlines and
any value that names something (a token, `var(…)`, `lv_dpx(…)`); G5 reads CSS and Tailwind `w-[…]`/`min-w-[…]`,
never a JS style object or native code, and keys on the smallest tier, so a width under it that still breaks 320 px
reflow is the reviewer's — a table's `min-width` inside its own scroll box is a sanctioned `layout-exception`; G4's LVGL rule and G6 read C and C++ files (`.c`, `.cc`, `.cpp`, `.cxx`, `.h`,
`.hh`, `.hpp`, `.hxx`) and skip their comments, never a `/*` inside a string, and the web and native rules do not run
there. A pass is a floor, never a review.

Prints one line per hit — `file:line: G<n> what — fix` — then a count, how many UI files it read, by kind, and where
the tiers came from; a named file that cannot be read or has no UI extension is said and not counted, and reading none
is said plainly. A whole-tree run over BASELINE exits 1; a run on named files exits 1 on any hit. Python 3.9+,
standard library only.
"""

from __future__ import annotations

import fnmatch
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip()
            or ".")

# Hits sanctioned today, each with its reason. A new hit on a line you touched is yours to fix.
BASELINE = 0
WEB_EXT = {".html", ".htm", ".css", ".scss", ".sass", ".less", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".vue", ".svelte",
           ".astro", ".erb", ".liquid", ".hbs", ".njk"}
NATIVE_EXT = {".swift", ".kt", ".java", ".dart", ".xml"}
C_EXT = {".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx"}  # Embedded (ESP-IDF, LVGL): G4's LVGL rule and G6
UI_EXT = WEB_EXT | NATIVE_EXT | C_EXT
SKIP_DIRS = ("node_modules/", "vendor/", "third_party/", "build/", "dist/", "out/", "coverage/", ".cache/", ".venv/",
             "Pods/", "managed_components/", ".agents/", ".claude/", ".codex/", ".github/")

BOOTSTRAP = (576.0, 768.0, 992.0, 1200.0, 1400.0)  # Bootstrap 5.3, Breakpoints: sm, md, lg, xl, xxl
BASE = 4  # the base grid every spacing value lands on; an 8 base lands on it too
HAIRLINES = {0.0, 1.0, 2.0}

TIER_ROW = re.compile(r"^\|\s*`breakpoint\.[\w-]+`\s*\|\s*(\d+(?:\.\d+)?)\s*(?:px|dp|pt)?\s*\|", re.M)

# G1
DEVICE_WORD = r"(?:mobile|iphone|ipad|android|tablet)"
UA_DEVICE = re.compile(r"navigator\.userAgent\b[^\n]*?" + DEVICE_WORD + r"|" + DEVICE_WORD
                       + r"[^\n]*?navigator\.userAgent\b", re.I)
DEVICE = re.compile(r"navigator\.userAgentData\??\.mobile\b|\buserInterfaceIdiom\b|\bisTablet\b")
SCREEN = re.compile(r"\bUIScreen\.main\.bounds\b|(?<![\w.])(?:window\.)?screen\.(?:width|availWidth)\b")
# G2
# a media query: the prelude of `@media`, a `matchMedia` string, or any string that is a query, such as one passed to
# a `useMediaQuery` hook
MEDIA = re.compile(r"@media\b[^{;]*|matchMedia\s*\(\s*[`'\"][^`'\"]*|[`'\"]\s*\(\s*(?:(?:min|max)-)?width\b[^`'\"]*")
QUERY_WIDTH = re.compile(r"(?<![\w-])(min|max)-width\s*:\s*(\d+(?:\.\d+)?)(px|em|rem)\b")
RANGE_WIDTH = re.compile(r"(?<![\w-])width\s*(>=|<=|<|>)\s*(\d+(?:\.\d+)?)(px|em|rem)\b")  # media query level 4
RANGE_KIND = {">=": "min", "<=": "max", "<": "below", ">": "above"}
TW_QUERY = re.compile(r"(?<![\w-])(min|max)-\[(\d+(?:\.\d+)?)(px|em|rem)\]:")
# G3
VW = re.compile(r"(?<![-\w])(?:min-)?width\s*:\s*[`'\"]?100vw\b|(?<![\w:-])w-screen\b|(?<![\w-])w-\[100vw\]")
# G4
SIDES = r"(?:-(?:top|right|bottom|left|inline|block)(?:-(?:start|end))?)?"
CSS_SPACE = re.compile(r"(?<![-\w])(?:margin" + SIDES + r"|padding" + SIDES + r"|gap|row-gap|column-gap|inset"
                       + SIDES + r")\s*:\s*([^;{}\n]+)")
LENGTH = re.compile(r"(?<![\w.])(-?\d+(?:\.\d+)?)(px|rem)\b")
TW_SPACE = r"-?(?:p|px|py|pt|pr|pb|pl|ps|pe|m|mx|my|mt|mr|mb|ml|ms|me|gap|gap-x|gap-y|space-x|space-y|inset)"
TW_ARBITRARY = re.compile(r"(?<![\w-])" + TW_SPACE + r"-\[(-?\d+(?:\.\d+)?)(px|rem)\]")
TW_HALF = re.compile(r"(?<![\w-])" + TW_SPACE + r"-([123])\.5(?![\w.])")
SWIFT_SPACE = re.compile(r"\.padding\(\s*(?:\.\w+\s*,\s*)?(\d+(?:\.\d+)?)\s*\)|\bspacing\s*:\s*(\d+(?:\.\d+)?)\b")
COMPOSE_CALL = re.compile(r"\b(?:padding|spacedBy)\s*\(([^()]*)\)"
                          r"|\bSpacer\s*\(\s*(?:modifier\s*=\s*)?Modifier\s*\.\s*(?:width|height|size)\s*\(([^()]*)\)")
DP = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)\.dp\b")
XML_SPACE = re.compile(r"android:(?:padding|layout_margin)\w*\s*=\s*\"(\d+(?:\.\d+)?)dp\"")
LV_SPACE = re.compile(r"\blv_(?:obj_set_style|style_set)_(?:pad|margin)_(?:all|top|bottom|left|right|row|column|hor|ver"
                      r"|gap)\s*\(")
# G5
CSS_WIDTH = re.compile(r"(?<![-\w])(?:min-)?width\s*:\s*(\d+(?:\.\d+)?)(px|rem)\b")
TW_WIDTH = re.compile(r"(?<![\w-])(?:min-)?w-\[(\d+(?:\.\d+)?)(px|rem)\]")
QUERY_BLOCK = re.compile(r"@(?:media|container)\b[^{;]*\{")
# G6
SET_POS = re.compile(r"\blv_obj_set_pos\s*\(")
NUMBER = re.compile(r"\b(?:0[xX][0-9a-fA-F]+|\d+(?:\.\d*)?(?:[eE][-+]?\d+)?)[uUlLfF]*\b")
CAST = re.compile(r"\(\s*(?:const\s+)?(?:unsigned|signed|int|long|short|u?int(?:8|16|32|64)_t|size_t|float|double"
                  r"|lv_coord_t|int32_t)(?:\s+(?:int|long))?\s*\)")

C_TOKENS = re.compile(r"\"(?:\\.|[^\"\\\n])*\"|'(?:\\.|[^'\\\n])*'|/\*.*?(?:\*/|\Z)|//[^\n]*", re.S)


def blank_c_comments(text: str) -> str:
    """The text with C and C++ comments turned to spaces, newlines kept, so positions and line numbers still hold.
    Strings and character literals are read first and kept, so a `/*` or `//` inside one opens no comment."""
    def blank(m: re.Match) -> str:
        token = m.group(0)
        return token if token[0] in "\"'" else re.sub(r"[^\n]", " ", token)
    return C_TOKENS.sub(blank, text)


def call_args(text: str, open_paren: int) -> list:
    """The top-level arguments of the call whose `(` is at open_paren, as (start, text) pairs."""
    args, depth, start = [], 0, open_paren + 1
    for i in range(open_paren, len(text)):
        c = text[i]
        if c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
            if depth == 0:
                args.append((start, text[start:i]))
                return args
        elif c == "," and depth == 1:
            args.append((start, text[start:i]))
            start = i + 1
        elif c == ";":
            break
    return args


def literal(arg: str) -> float | None:
    """The number an argument is, when it is only a number (a cast allowed); None when it names something."""
    rest = NUMBER.sub("", CAST.sub("", arg)).replace("-", "")
    numbers = NUMBER.findall(arg)
    if len(numbers) != 1 or re.search(r"\w", rest):
        return None
    n = numbers[0].rstrip("uUlLfF")
    value = float(int(n, 16)) if n.lower().startswith("0x") else float(n)
    return -value if arg.strip().startswith("-") else value


def px(value: str, unit: str) -> float:
    return float(value) * (16.0 if unit in ("em", "rem") else 1.0)


def off_grid(value: float) -> bool:
    v = abs(value)
    return v not in HAIRLINES and abs(v / BASE - round(v / BASE)) > 1e-6


def parse_tiers(design: str) -> tuple:
    """The brief's breakpoint tiers from its token tables' `breakpoint.*` rows, smallest first; none when it names
    none. A tier of 0 (`xs`) is the start of every layout and is left out."""
    return tuple(sorted({float(v) for v in TIER_ROW.findall(design) if float(v) > 0}))


def project_tiers() -> tuple:
    """(tiers, where they came from): the repo's DESIGN.md when it names breakpoints, Bootstrap 5.3's otherwise."""
    design = ROOT / "DESIGN.md"
    if design.is_file():
        tiers = parse_tiers(design.read_text(errors="replace"))
        if tiers:
            return tiers, "DESIGN.md"
    return BOOTSTRAP, "Bootstrap 5.3"


def breakpoint_hit(kind: str, width: float, tiers: tuple) -> str | None:
    """G2's message for one query width, or None when it is a tier written right. `min` and `max` are the
    `min-width`/`max-width` features and range syntax's `>=` and `<=`; `below` and `above` are its `<` and `>`."""
    under = any(abs(width - (t - 0.02)) < 1e-6 for t in tiers)
    if (kind in ("min", "below") and width in tiers) or (kind in ("max", "above") and under):
        return None
    kind = {"below": "max", "above": "min"}.get(kind, kind)
    shown = ", ".join(f"{t:g}" for t in tiers)
    if kind == "max" and width in tiers:
        return (f"G2 a max-width on the tier itself ({width:g}px) overlaps that tier's min-width — "
                f"{width - 0.02:g}px (LAYOUT §2)")
    return (f"G2 a {kind}-width of {width:g}px is not one of the brief's tiers ({shown}) — use a tier, or the "
            f"component's container query (LAYOUT §2)")


def query_spans(text: str) -> list:
    """The (start, end) of every @media and @container block, so G5 can skip what is inside one."""
    spans = []
    for m in QUERY_BLOCK.finditer(text):
        depth, i = 1, m.end()
        while i < len(text) and depth:
            depth += {"{": 1, "}": -1}.get(text[i], 0)
            i += 1
        spans.append((m.start(), i))
    return spans


def rule_has(text: str, pos: int, pattern: str) -> bool:
    """Whether the CSS rule around pos also holds a declaration matching pattern."""
    start, end = text.rfind("{", 0, pos), text.find("}", pos)
    return start != -1 and bool(re.search(pattern, text[start:end if end != -1 else len(text)]))


def lvgl_hits(text: str):
    """G4's LVGL rule and G6 in one C or C++ file's text: (position, message)."""
    code = blank_c_comments(text)
    for m in LV_SPACE.finditer(code):
        args = call_args(code, m.end() - 1)
        if len(args) > 1:
            value = literal(args[1][1])
            if value is not None and off_grid(value):
                yield (args[1][0], f"G4 a spacing of {value:g} px is off the base grid of {BASE} — the brief's "
                                   f"spacing token (LAYOUT §7)")
    for m in SET_POS.finditer(code):
        args = call_args(code, m.end() - 1)
        if len(args) > 2:
            x, y = literal(args[1][1]), literal(args[2][1])
            if x is not None and y is not None and (x or y):
                yield (m.start(), "G6 an object placed at literal coordinates — a flex or grid container, or "
                                  "lv_obj_align to its parent (LAYOUT §12)")


def web_native_hits(name: str, text: str, tiers: tuple):
    """G1–G5 in one web or native file's text: (position, message)."""
    suffix = Path(name).suffix
    for m in UA_DEVICE.finditer(text):
        yield (m.start(), "G1 a layout chosen by the user agent — read the window's width (LAYOUT §1)")
    for m in DEVICE.finditer(text):
        yield (m.start(), "G1 a layout chosen by device type — read the window's width (LAYOUT §1)")
    for m in SCREEN.finditer(text):
        yield (m.start(), "G1 a layout sized by the device's screen, not the window — read the window's width "
                          "(LAYOUT §1)")
    if suffix in WEB_EXT:
        for q in MEDIA.finditer(text):
            if q.group(0).lstrip().startswith("@container"):
                continue
            for m in QUERY_WIDTH.finditer(q.group(0)):
                msg = breakpoint_hit(m.group(1), px(m.group(2), m.group(3)), tiers)
                if msg:
                    yield (q.start() + m.start(), msg)
            for m in RANGE_WIDTH.finditer(q.group(0)):
                msg = breakpoint_hit(RANGE_KIND[m.group(1)], px(m.group(2), m.group(3)), tiers)
                if msg:
                    yield (q.start() + m.start(), msg)
        for m in TW_QUERY.finditer(text):
            msg = breakpoint_hit(m.group(1), px(m.group(2), m.group(3)), tiers)
            if msg:
                yield (m.start(), msg)
        for m in VW.finditer(text):
            if rule_has(text, m.start(), r"position\s*:\s*fixed"):
                continue  # a fixed element is out of the page's flow and cannot scroll it sideways
            yield (m.start(), "G3 a 100vw width is wider than the page by its scrollbar and scrolls sideways — "
                              "width: 100% (LAYOUT §6)")
        for m in CSS_SPACE.finditer(text):
            for n in LENGTH.finditer(m.group(1)):
                value = px(n.group(1), n.group(2))
                if off_grid(value):
                    yield (m.start(1) + n.start(), f"G4 a spacing of {value:g} px is off the base grid of {BASE} — "
                                                   f"the brief's spacing token (LAYOUT §7)")
        for m in TW_ARBITRARY.finditer(text):
            value = px(m.group(1), m.group(2))
            if off_grid(value):
                yield (m.start(), f"G4 a spacing of {value:g} px is off the base grid of {BASE} — the brief's "
                                  f"spacing token (LAYOUT §7)")
        for m in TW_HALF.finditer(text):
            yield (m.start(), f"G4 a half step ({int(m.group(1)) * 4 + 2} px) is off the base grid of {BASE} — a "
                              f"whole step (LAYOUT §7)")
        spans = query_spans(text) + [(q.start(), q.end()) for q in MEDIA.finditer(text)]
        smallest = tiers[0] if tiers else BOOTSTRAP[0]
        for pattern in (CSS_WIDTH, TW_WIDTH):
            for m in pattern.finditer(text):
                value = px(m.group(1), m.group(2))
                inside = any(a <= m.start() < b for a, b in spans)
                capped = pattern is CSS_WIDTH and rule_has(text, m.start(), r"(?<![-\w])max-width\s*:")
                if value >= smallest and not inside and not capped:
                    yield (m.start(), f"G5 a fixed width of {value:g} px is wider than the smallest window — "
                                      f"max-width, a share of the parent, or the container's cap (LAYOUT §6)")
    if suffix == ".swift":
        for m in SWIFT_SPACE.finditer(text):
            value = float(m.group(1) or m.group(2))
            if off_grid(value):
                yield (m.start(), f"G4 a spacing of {value:g} pt is off the base grid of {BASE} — the brief's "
                                  f"spacing token (LAYOUT §7)")
    if suffix in (".kt", ".java"):
        for m in COMPOSE_CALL.finditer(text):
            body = m.group(1) if m.group(1) is not None else m.group(2)
            start = m.start(1) if m.group(1) is not None else m.start(2)
            for n in DP.finditer(body):
                if off_grid(float(n.group(1))):
                    yield (start + n.start(), f"G4 a spacing of {n.group(1)} dp is off the base grid of {BASE} — "
                                              f"the brief's spacing token (LAYOUT §7)")
    if suffix == ".xml":
        for m in XML_SPACE.finditer(text):
            if off_grid(float(m.group(1))):
                yield (m.start(), f"G4 a spacing of {m.group(1)} dp is off the base grid of {BASE} — the brief's "
                                  f"spacing token (LAYOUT §7)")


def ui_patterns() -> tuple | None:
    """UI_PATHS from the kit's settings, or None when the repo has no kit."""
    settings = ROOT / ".agents/project.py"
    if not settings.is_file():
        return None
    sys.path.insert(0, str(settings.parent))
    import project  # noqa: E402 — the kit's settings
    return tuple(getattr(project, "UI_PATHS", ()))


def matches(path: str, patterns) -> bool:
    """A folder ends in `/` and holds everything beneath it, a glob in it too (`components/ui_*/`); a glob; or a
    file."""
    def one(p: str) -> bool:
        glob = any(c in p for c in "*?[")
        if p.endswith("/"):
            return fnmatch.fnmatch(path, p + "*") if glob else path.startswith(p)
        return fnmatch.fnmatch(path, p) if glob else path == p
    return any(one(p) for p in patterns)


def ui_files() -> list[str]:
    tracked = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=ROOT,
                             capture_output=True, text=True).stdout.splitlines()
    patterns = ui_patterns()
    keep = (lambda f: matches(f, patterns)) if patterns is not None else (lambda f: not f.startswith(SKIP_DIRS)
                                                                         and "/node_modules/" not in f
                                                                         and "/managed_components/" not in f)
    return [f for f in tracked if Path(f).suffix in UI_EXT and keep(f) and (ROOT / f).is_file()]


def line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def scan_text(name: str, text: str, tiers: tuple = BOOTSTRAP) -> list[tuple[int, str]]:
    """Every hit in one file's text: (line, message)."""
    lines = text.split("\n")  # as line_of counts: splitlines would also break at a form feed and shift every line
    hits: list[tuple[int, str]] = []
    found = lvgl_hits(text) if Path(name).suffix in C_EXT else web_native_hits(name, text, tiers)
    for pos, msg in found:
        n = line_of(text, pos)
        if not (0 < n <= len(lines) and "layout-exception" in lines[n - 1]):
            hits.append((n, msg))
    return sorted(set(hits))


def self_test() -> int:
    cases = [
        # G1
        ("a.ts", "if (/iPhone|Android/i.test(navigator.userAgent)) showMobile()", ["G1"]),
        ("b.ts", "const mobile = navigator.userAgentData?.mobile", ["G1"]),
        ("c.ts", "log(navigator.userAgent)", []),
        ("d.swift", "if UIDevice.current.userInterfaceIdiom == .pad { split() }", ["G1"]),
        ("e.kt", "if (isTablet) TwoPane() else OnePane()", ["G1"]),
        ("f.ts", "const isMobile = useMediaQuery('(max-width: 767.98px)')", []),
        ("fa.ts", "if (/iPhone|Android/i.test(navigator.userAgent)) setTwoPane(true)", ["G1"]),
        ("fb.swift", "let w = UIScreen.main.bounds.width", ["G1"]),
        ("fc.ts", "const twoPane = window.screen.width >= 992", ["G1"]),
        ("fd.ts", "const wide = useMediaQuery('(min-width: 768px)')", []),
        ("fe.ts", "const wide = useMediaQuery('(min-width: 600px)')", ["G2"]),
        ("ff.css", "@media (width >= 768px) { .a { display: grid; } }", []),
        ("fg.css", "@media (width >= 600px) { .a { display: grid; } }", ["G2"]),
        ("fh.css", "@media (width < 768px) { .a { display: block; } }", []),
        ("fi.css", ".overlay { position: fixed; inset: 0; width: 100vw; }", []),
        # G2
        ("g.css", "@media (min-width: 768px) { .a { display: grid; } }", []),
        ("h.css", "@media (min-width: 600px) { .a { display: grid; } }", ["G2"]),
        ("i.css", "@media (max-width: 767.98px) { .a { display: block; } }", []),
        ("j.css", "@media (max-width: 768px) { .a { display: block; } }", ["G2"]),
        ("k.css", "@media (min-width: 48em) { .a { color: red; } }", []),
        ("l.css", "@media (min-width: 40em) { .a { color: red; } }", ["G2"]),
        ("m.css", "@container (min-width: 420px) { .card { display: flex; } }", []),
        ("n.ts", "window.matchMedia('(min-width: 1024px)')", ["G2"]),
        ("o.tsx", '<div className="min-[600px]:grid md:flex">', ["G2"]),
        ("p.tsx", '<div className="min-[992px]:grid">', []),
        ("q.css", "@media (min-width: 600px) { } /* layout-exception: a print preview, not a screen */", []),
        # G3
        ("r.css", ".hero { width: 100vw; }", ["G3"]),
        ("s.css", ".hero { max-width: 100vw; }", []),
        ("t.tsx", '<div className="w-screen h-40">', ["G3"]),
        # G4
        ("u.css", ".a { padding: 12px 13px; }", ["G4"]),
        ("v.css", ".a { padding: 12px 16px; margin: 0 1px; gap: 8px; }", []),
        ("w.css", ".a { margin-inline-start: 0.375rem; }", ["G4"]),
        ("x.css", ".a { padding: var(--space-md); gap: calc(var(--space-sm) * 2); }", []),
        ("y.tsx", '<div className="p-[13px] gap-4">', ["G4"]),
        ("z.tsx", '<div className="p-2.5 mt-0.5 gap-x-3.5">', ["G4", "G4"]),
        ("aa.swift", "VStack(spacing: 10) { Text(\"a\") }.padding(.horizontal, 12)", ["G4"]),
        ("ab.swift", "HStack(spacing: Space.md) { }.padding(16)", []),
        ("ac.kt", "Modifier.padding(horizontal = 16.dp, vertical = 6.dp)", ["G4"]),
        ("ad.kt", "Arrangement.spacedBy(8.dp); Spacer(Modifier.height(24.dp))", []),
        ("ae.kt", "Spacer(modifier = Modifier.width(18.dp))", ["G4"]),
        ("af.xml", '<View android:paddingStart="14dp" android:layout_marginTop="16dp" />', ["G4"]),
        ("ag.css", ".a { top: 13px; border-width: 3px; }", []),
        # G5
        ("ah.css", ".dialog { width: 600px; }", ["G5"]),
        ("ai.css", ".dialog { width: 600px; max-width: 100%; }", []),
        ("aj.css", "@media (min-width: 992px) { .side { width: 640px; } }", []),
        ("ak.css", ".icon { width: 24px; }", []),
        ("al.tsx", '<div className="w-[720px]">', ["G5"]),
        ("am.css", ".page { min-width: 80rem; }", ["G5"]),
        # Embedded (ESP-IDF, LVGL)
        ("ba.c", "lv_obj_set_style_pad_all(card, 10, 0);", ["G4"]),
        ("bb.c", "lv_obj_set_style_pad_row(list, SPACE_SM, 0);", []),
        ("bc.c", "lv_style_set_pad_column(&style, 12);", []),
        ("bd.cpp", "lv_obj_set_style_margin_left(obj, lv_dpx(10), 0);", []),
        ("be.c", "lv_obj_set_pos(btn, 12, 40);", ["G6"]),
        ("bf.c", "lv_obj_set_pos(btn, 0, 0);", []),
        ("bg.c", "lv_obj_set_pos(btn, x, y);", []),
        ("bh.c", "// lv_obj_set_pos(btn, 12, 40);\nlv_obj_align(btn, LV_ALIGN_BOTTOM_MID, 0, -SPACE_LG);", []),
        ("bi.c", "lv_obj_set_pos(cursor, 3, 5);  // layout-exception: a drawn cursor follows the touch point", []),
        ("bj.h", "static const char *k = \"padding: 13px; width: 100vw\";", []),
        ("bk.c", "lv_obj_set_style_pad_top(obj, (int32_t)6, 0);", ["G4"]),
        # a form feed does not shift lines, so an exception on the hit's line still holds
        ("bl.c", "\f\nlv_obj_set_pos(a, 3, 5);  // layout-exception: a test", []),
        # a comment opener inside a string opens no comment
        ("bm.c", "const char *u = \"/*\";\nlv_obj_set_pos(a, 3, 5);\nconst char *v = \"*/\";", ["G6"]),
    ]
    bad = 0
    for name, text, want in cases:
        got = sorted(msg.split()[0] for _, msg in scan_text(name, text))
        if got != sorted(want):
            bad += 1
            print(f"FAIL {name}: want {want}, got {got}")
    # The brief's tiers replace Bootstrap's when it names them.
    design = ("| Token | Value | Use |\n| --- | --- | --- |\n| `breakpoint.sm` | 576 px | x |\n"
              "| `breakpoint.md` | 768 px | x |\n| `space.md` | 12 px | x |\n")
    tier_cases = [(parse_tiers(design), (576.0, 768.0)), (parse_tiers("| `space.md` | 12 px | x |"), ())]
    for got, want in tier_cases:
        if got != want:
            bad += 1
            print(f"FAIL parse_tiers: want {want}, got {got}")
    custom = sorted(msg.split()[0] for _, msg in scan_text("t.css", "@media (min-width: 600px) {}", (600.0, 900.0)))
    if custom:
        bad += 1
        print(f"FAIL custom tiers: want [], got {custom}")
    # UI_PATHS matching: a folder with a glob holds the files beneath it.
    globs = [("components/ui_toast/toast.cpp", ("components/ui_*/",), True),
             ("components/audio/a.cpp", ("components/ui_*/",), False),
             ("main/ui/home.c", ("main/ui/",), True), ("main/app.c", ("*.css",), False)]
    for path, patterns, want in globs:
        if matches(path, patterns) != want:
            bad += 1
            print(f"FAIL matches({path!r}, {patterns}): want {want}")
    # The count is of UI files read: a missing or non-UI named file is said, never counted.
    with tempfile.TemporaryDirectory() as tmp:
        good = Path(tmp, "ok.c")
        good.write_text("lv_obj_set_style_pad_all(card, SPACE_MD, 0);\n")
        runs = [([str(Path(tmp, "missing.cpp"))], ["cannot be read", "in 0 UI files", "read no UI files"]),
                ([str(Path(tmp, "README.md"))], ["not a UI file", "in 0 UI files", "read no UI files"]),
                ([str(good)], ["in 1 UI files (0 web, 0 native, 1 C/C++)"])]
        for files, wants in runs:
            out = "\n".join(run(files, named=True)[0])
            for want in wants:
                if want not in out:
                    bad += 1
                    print(f"FAIL run({Path(files[0]).name}): no {want!r} in\n{out}")
            if len(wants) == 1 and "read no UI files" in out:
                bad += 1
                print(f"FAIL run({Path(files[0]).name}): said it read nothing")
    total = len(cases) + len(tier_cases) + 1 + len(globs) + 3
    print(f"layout_check self-test: {total - bad}/{total} passed")
    return 1 if bad else 0


def main(argv: list[str]) -> int:
    if argv[:1] == ["--test"]:
        return self_test()
    named = bool(argv)
    lines, code = run(argv if named else ui_files(), named)
    for line in lines:
        print(line)
    return code


def run(files: list, named: bool) -> tuple:
    """Scan the files; the lines to print and the exit code. Counts only the UI files actually read."""
    tiers, source = project_tiers()
    out: list[str] = []
    hits: list[str] = []
    read: list[str] = []
    for f in files:
        if Path(f).suffix not in UI_EXT:
            out.append(f"{f}: not a UI file — skipped")
            continue
        try:
            text = (ROOT / f).read_text(errors="replace")
        except OSError:
            out.append(f"{f}: cannot be read — not checked")
            continue
        read.append(f)
        hits += [f"{f}:{n}: {msg}" for n, msg in scan_text(f, text, tiers)]
    out += hits
    limit = 0 if named else BASELINE
    kinds = [("web", WEB_EXT), ("native", NATIVE_EXT), ("C/C++", C_EXT)]
    by_kind = ", ".join(f"{sum(Path(f).suffix in ext for f in read)} {kind}" for kind, ext in kinds)
    out.append(f"G1–G6 layout patterns — {len(hits)} hits in {len(read)} UI files ({by_kind}); tiers from {source}: "
               + ", ".join(f"{t:g}" for t in tiers) + ("" if named else f" (baseline {BASELINE})"))
    if not read:
        why = ("no named file is a readable UI file" if named
               else "UI_PATHS in .agents/project.py is empty or matches no file" if ui_patterns() is not None
               else "no tracked file has a UI extension")
        out.append(f"read no UI files — nothing was checked: {why}")
    if len(hits) > limit:
        out.append("FAIL — fix each hit, or mark a sanctioned one `layout-exception` with its reason")
        return out, 1
    return out, 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
