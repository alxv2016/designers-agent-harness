#!/usr/bin/env python3
"""The e-ink skill's check: patterns in UI files that an e-paper panel cannot show, or shows only by spending
refreshes, from references/e-ink.md (cited `E_INK §n`). It finds what a line shows; the glass shows the rest.

    python3 .agents/skills/e-ink/scripts/e_ink_check.py            # every e-ink UI file, against the baseline
    python3 .agents/skills/e-ink/scripts/e_ink_check.py FILE …     # some files, no baseline
    python3 .agents/skills/e-ink/scripts/e_ink_check.py --test     # the self-test

Which files: in a repo with the agent-harness kit, EINK_PATHS from `.agents/project.py` — the UI drawn on an e-paper
panel (empty there means none); in any other repo, every tracked UI file outside vendored and generated folders, since
the skill is used only where the screen is e-paper. A line that carries `e-ink-exception` is skipped — write the
reason beside it. Comment lines are skipped.

  EK1  an animation — `lv_anim_start`, `lv_obj_fade_in/out`, `lv_screen_load_anim`, `LV_ANIM_ON`, a non-zero
       `anim_duration`; CSS `animation:`, `transition:`, `@keyframes`, `scroll-behavior: smooth`        E_INK §8
  EK2  translucency — an `*_opa` style that is neither cover nor transparent; CSS `opacity` between 0 and 1,
       `rgba()`/`hsla()` with alpha under 1                                                              E_INK §7
  EK3  a shadow or a blur — a non-zero `shadow_width`/`shadow_spread`; CSS `box-shadow`, `text-shadow`,
       `filter: blur`, `backdrop-filter`                                                                 E_INK §7
  EK4  a gradient — `bg_grad`, `lv_grad_dsc_t`, a `bg_grad_dir` other than none; CSS `*-gradient(`           E_INK §7
  EK5  a 1 px stroke — a border, outline, line or arc width of 1; CSS `1px` on a border or an outline        E_INK §7
  EK6  moving text or a spinner — `lv_spinner_create`, a label's scrolling long mode; HTML `<marquee>`       E_INK §8
  EK7  momentum or elastic scrolling — `LV_OBJ_FLAG_SCROLL_MOMENTUM` or `_ELASTIC` added; CSS
       `-webkit-overflow-scrolling: touch`                                                               E_INK §9

What it cannot see: a grey used as the only signal, text drawn on a dark dither, a font compiled with anti-aliasing,
a layout that reflows on a state change, a focus ring that changes a control's size, a refresh per keystroke, a
waveform's polarity, ghosting. Its limits: EK2 and EK5 read literal values, so a token that resolves to a translucent
colour or a 1 px stroke passes; EK1 flags `LV_ANIM_ON` wherever it appears. A pass is a floor, never a review.

Prints one line per hit — `file:line: EK<n> what — fix` — then a count and how many files it read. A whole-tree run
over BASELINE exits 1; a run on named files exits 1 on any hit. Python 3.9+, standard library only.
"""

from __future__ import annotations

import fnmatch
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip()
            or ".")

# Hits sanctioned today, each with its reason. A new hit on a line you touched is yours to fix.
BASELINE = 0
WEB_EXT = {".html", ".htm", ".css", ".scss", ".sass", ".less", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".vue", ".svelte"}
C_EXT = {".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx"}
UI_EXT = WEB_EXT | C_EXT
SKIP_DIRS = ("node_modules/", "vendor/", "third_party/", "build/", "dist/", "out/", "coverage/", ".cache/", ".venv/",
             "managed_components/", ".agents/", ".claude/", ".codex/", ".github/")

NUM = r"(\d+)"
RULES_C = [
    ("EK1", re.compile(r"\blv_anim_start\s*\(|\blv_obj_fade_(?:in|out)\s*\(|\blv_screen_load_anim\s*\(|\bLV_ANIM_ON\b"),
     "an animation — every frame of it is a refresh; change state in one step"),
    ("EK1", re.compile(r"\blv_obj_set_style_anim_(?:duration|time)\s*\([^,]+,\s*(?!0\b)\d+"),
     "an animation duration — set it to 0"),
    ("EK2", re.compile(r"\blv_obj_set_style_\w*opa\s*\([^,]+,\s*(?!LV_OPA_COVER\b|LV_OPA_TRANSP\b|LV_OPA_0\b"
                       r"|LV_OPA_100\b|255\b|0\b)[\w]+"),
     "translucency — it blends to greys a partial refresh throws away; use an opaque fill"),
    ("EK3", re.compile(r"\blv_obj_set_style_shadow_(?:width|spread)\s*\([^,]+,\s*(?!0\b)\d+"),
     "a shadow — use a line and a hard offset for depth"),
    ("EK4", re.compile(r"\blv_obj_set_style_bg_grad\w*\s*\(|\blv_grad_dsc_t\b"),
     "a gradient — it bands into a few steps; use a solid fill or a fixed dither"),
    ("EK5", re.compile(r"\blv_obj_set_style_(?:border|outline|line|arc)_width\s*\([^,]+,\s*1\s*,"),
     "a 1 px stroke — it breaks up and ghosts; 2 px at least"),
    ("EK6", re.compile(r"\blv_spinner_create\s*\(|\bLV_LABEL_LONG(?:_MODE)?_SCROLL(?:_CIRCULAR)?\b"),
     "moving text or a spinner — show still words for a wait"),
    ("EK7", re.compile(r"\blv_obj_add_flag\s*\([^)]*LV_OBJ_FLAG_SCROLL_(?:MOMENTUM|ELASTIC)"),
     "momentum or elastic scrolling — turn whole pages instead"),
]
RULES_WEB = [
    ("EK1", re.compile(r"(?<![\w-])(?:animation|transition)\s*:(?!\s*none\b)|@keyframes\b|scroll-behavior\s*:\s*smooth"),
     "an animation — every frame of it is a refresh; change state in one step"),
    ("EK2", re.compile(r"(?<![\w-])opacity\s*:\s*0?\.\d+|\b(?:rgba|hsla)\s*\([^)]*,\s*0?\.\d+\s*\)"),
     "translucency — it blends to greys a partial refresh throws away; use an opaque fill"),
    ("EK3", re.compile(r"(?<![\w-])(?:box-shadow|text-shadow)\s*:(?!\s*none\b)|filter\s*:\s*[^;]*blur\(|"
                       r"backdrop-filter\s*:"), "a shadow or a blur — use a line and a hard offset for depth"),
    ("EK4", re.compile(r"\b(?:linear|radial|conic|repeating-linear|repeating-radial)-gradient\s*\("),
     "a gradient — it bands into a few steps; use a solid fill or a fixed dither"),
    ("EK5", re.compile(r"(?<![\w-])(?:border|outline)(?:-(?:top|right|bottom|left|width))?\s*:[^;]*(?<!\d)1px\b"),
     "a 1 px stroke — it breaks up and ghosts; 2 px at least"),
    ("EK6", re.compile(r"<marquee\b", re.I), "moving text — show still words"),
    ("EK7", re.compile(r"-webkit-overflow-scrolling\s*:\s*touch"), "momentum scrolling — turn whole pages instead"),
]


def blank_comments(text: str, c_like: bool) -> str:
    """Comment lines replaced by blanks of the same length, so line numbers hold."""
    out = []
    for line in text.split("\n"):
        s = line.lstrip()
        comment = s.startswith(("//", "/*", "*")) or (not c_like and s.startswith("<!--"))
        out.append(" " * len(line) if comment else line)
    return "\n".join(out)


def scan(name: str, text: str) -> list[tuple[int, str]]:
    c_like = Path(name).suffix in C_EXT
    code = blank_comments(text, c_like)
    rules = RULES_C if c_like else RULES_WEB
    lines = text.split("\n")
    hits = set()
    for i, line in enumerate(code.split("\n"), 1):
        if "e-ink-exception" in lines[i - 1]:
            continue
        for rule, pattern, msg in rules:
            if pattern.search(line):
                hits.add((i, f"{rule} {msg}"))
    return sorted(hits)


def eink_patterns() -> tuple | None:
    """EINK_PATHS from the kit's settings, or None when the repo has no kit."""
    settings = ROOT / ".agents/project.py"
    if not settings.is_file():
        return None
    sys.path.insert(0, str(settings.parent))
    import project  # noqa: E402 — the kit's settings
    return tuple(getattr(project, "EINK_PATHS", ()))


def matches(path: str, patterns) -> bool:
    def one(p: str) -> bool:
        glob = any(c in p for c in "*?[")
        if p.endswith("/"):
            return fnmatch.fnmatch(path, p + "*") if glob else path.startswith(p)
        return fnmatch.fnmatch(path, p) if glob else path == p
    return any(one(p) for p in patterns)


def ui_files() -> list[str]:
    tracked = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=ROOT,
                             capture_output=True, text=True).stdout.splitlines()
    patterns = eink_patterns()
    keep = (lambda f: matches(f, patterns)) if patterns is not None else (lambda f: not f.startswith(SKIP_DIRS)
                                                                         and "/node_modules/" not in f)
    return [f for f in tracked if Path(f).suffix in UI_EXT and keep(f) and (ROOT / f).is_file()]


def run(files: list, named: bool) -> tuple:
    out: list[str] = []
    hits: list[str] = []
    read = 0
    for f in files:
        if Path(f).suffix not in UI_EXT:
            out.append(f"{f}: not a UI file — skipped")
            continue
        try:
            text = (ROOT / f).read_text(errors="replace")
        except OSError:
            out.append(f"{f}: cannot be read — not checked")
            continue
        read += 1
        hits += [f"{f}:{n}: {msg}" for n, msg in scan(f, text)]
    out += hits
    limit = 0 if named else BASELINE
    out.append(f"EK1–EK7 e-ink patterns — {len(hits)} hits in {read} UI files"
               + ("" if named else f" (baseline {BASELINE})"))
    if not read:
        why = ("no named file is a readable UI file" if named
               else "EINK_PATHS in .agents/project.py is empty or matches no file" if eink_patterns() is not None
               else "no tracked file has a UI extension")
        out.append(f"read no UI files — nothing was checked: {why}")
    if len(hits) > limit:
        out.append("FAIL — fix each hit, or mark a sanctioned one `e-ink-exception` with its reason")
        return out, 1
    return out, 0


CASES = [
    # (file, line, rules it must raise)
    ("ui.c", "lv_obj_set_style_anim_duration(sw, 0, 0);", []),
    ("ui.c", "lv_obj_set_style_anim_duration(sw, 200, 0);", ["EK1"]),
    ("ui.c", "lv_obj_scroll_to_view(row, LV_ANIM_OFF);", []),
    ("ui.c", "lv_obj_scroll_to_view(row, LV_ANIM_ON);", ["EK1"]),
    ("ui.c", "lv_anim_start(&a);", ["EK1"]),
    ("ui.c", "lv_screen_load_anim(scr, LV_SCR_LOAD_ANIM_FADE_IN, 300, 0, false);", ["EK1"]),
    ("ui.c", "lv_obj_set_style_bg_opa(card, LV_OPA_COVER, 0);", []),
    ("ui.c", "lv_obj_set_style_bg_opa(card, LV_OPA_50, 0);", ["EK2"]),
    ("ui.c", "lv_obj_set_style_text_opa(label, 128, 0);", ["EK2"]),
    ("ui.c", "lv_obj_set_style_shadow_width(card, 0, 0);", []),
    ("ui.c", "lv_obj_set_style_shadow_width(card, 12, 0);", ["EK3"]),
    ("ui.c", "lv_obj_set_style_bg_grad_dir(card, LV_GRAD_DIR_VER, 0);", ["EK4"]),
    ("ui.c", "lv_obj_set_style_border_width(btn, 3, 0);", []),
    ("ui.c", "lv_obj_set_style_border_width(btn, 1, 0);", ["EK5"]),
    ("ui.c", "lv_obj_set_style_line_width(line, 1, LV_PART_MAIN);", ["EK5"]),
    ("ui.c", "lv_obj_t *s = lv_spinner_create(parent);", ["EK6"]),
    ("ui.c", "lv_label_set_long_mode(l, LV_LABEL_LONG_SCROLL_CIRCULAR);", ["EK6"]),
    ("ui.c", "lv_label_set_long_mode(l, LV_LABEL_LONG_DOT);", []),
    ("ui.c", "lv_obj_add_flag(list, LV_OBJ_FLAG_SCROLL_MOMENTUM);", ["EK7"]),
    ("ui.c", "lv_obj_clear_flag(list, LV_OBJ_FLAG_SCROLL_MOMENTUM);", []),
    ("ui.c", "// lv_anim_start(&a); kept for the benchmark only", []),
    ("ui.c", "lv_anim_start(&a); /* e-ink-exception: the refresh benchmark */", []),
    ("ui.css", ".row { transition: none; }", []),
    ("ui.css", ".row { transition: background 200ms; }", ["EK1"]),
    ("ui.css", "@keyframes spin { to { transform: rotate(1turn) } }", ["EK1"]),
    ("ui.css", "html { scroll-behavior: smooth; }", ["EK1"]),
    ("ui.css", ".x { opacity: 0.5; }", ["EK2"]),
    ("ui.css", ".x { opacity: 1; }", []),
    ("ui.css", ".x { color: rgba(0, 0, 0, 0.6); }", ["EK2"]),
    ("ui.css", ".card { box-shadow: 0 2px 8px #000; }", ["EK3"]),
    ("ui.css", ".card { box-shadow: none; }", []),
    ("ui.css", ".card { background: linear-gradient(#fff, #000); }", ["EK4"]),
    ("ui.css", ".btn { border: 1px solid #000; }", ["EK5"]),
    ("ui.css", ".btn { border: 3px solid #000; }", []),
    ("ui.css", ".btn { border-width: 11px; }", []),
    ("ui.html", "<marquee>News</marquee>", ["EK6"]),
    ("ui.css", ".list { -webkit-overflow-scrolling: touch; }", ["EK7"]),
]


def self_test() -> int:
    bad = 0
    for name, line, want in CASES:
        got = sorted({msg[:3] for _, msg in scan(name, line)})
        if got != sorted(want):
            bad += 1
            print(f"FAIL {name}: {line!r} — got {got}, want {want}")
    print(f"e_ink_check self-test — {'FAIL' if bad else 'pass'} ({len(CASES) - bad}/{len(CASES)} cases)")
    return 1 if bad else 0


def main(argv: list[str]) -> int:
    if argv[:1] == ["--test"]:
        return self_test()
    named = bool(argv)
    lines, code = run(argv if named else ui_files(), named)
    for line in lines:
        print(line)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
