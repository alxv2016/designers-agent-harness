#!/usr/bin/env python3
"""The motion skill's check: patterns in UI files that make motion read badly or render slowly, from
references/motion.md (cited `MOTION §n`). It finds what a pattern shows; a recording on the target finds the rest.

    python3 .agents/skills/motion/scripts/motion_check.py            # every UI file, against the baseline
    python3 .agents/skills/motion/scripts/motion_check.py FILE …     # some files, no baseline
    python3 .agents/skills/motion/scripts/motion_check.py --test     # the self-test

Which files: in a repo with the agent-harness kit, UI_PATHS from `.agents/project.py` (empty there means none yet);
in any other repo, every tracked file with a UI extension outside vendored and generated folders. A line that carries
`motion-exception` is skipped — write the reason beside it.

  M1  every property animates (`transition: all`, `transition-all`, `transitionProperty: 'all'`)   MOTION §7
  M2  an entrance from zero scale (`scale(0)`, `scaleEffect(0)`, `initialScale = 0f`, `fromXScale="0"`)  MOTION §4
  M3  an ease-in curve where it may start an arrival, a hover or a press (`ease-in`, `.easeIn`)   MOTION §2
  M4  a layout property animated (a transition list, a keyframe, `transition-[height]`)   MOTION §7
  M5  a hover that moves the hovered element itself (`:hover { transform: translate… }`, `hover:translate-…`)  MOTION §4
  M6  smooth scrolling in a file with no reduced-motion query or API                   MOTION §8
  Embedded (ESP-IDF, LVGL) — C and C++ files:
  M7  a duration given as a literal number (`lv_anim_set_duration(&a, 300)`, `lv_obj_fade_in(obj, 300, 0)`,
      `lv_screen_load_anim(scr, type, 300, 0, false)`, a style transition's time)          MOTION §3
  M8  something that travels on the linear path — an `lv_anim_t` moving x, y or translate with no path set (it
      defaults to `lv_anim_path_linear`) or set to linear, or an `lv_screen_load_anim` slide, which is always linear
                                                                                             MOTION §2
  M9  a full-screen opacity fade — `lv_screen_load_anim` with a FADE type, `lv_obj_fade_in/out` on the active screen
      or the top layer                                                                       MOTION §7

What it cannot see: curves and durations that feel wrong, a missing origin, a restart instead of a retarget, frames
dropped on a real device. Its limits: M2 and M3 skip an exit — inside a CSS rule, one whose selector names leaving (exit,
leave, out, dismiss — never a state such as closed or hidden, which also governs the arrival); elsewhere, a line that
does — since an accelerate curve or a shrink to
nothing is fine there; M5 reads a rule whose last selector is the hovered element, never its content; M3 reads keyword curves, never a
project token (`var(--ease-in)`) or a raw `cubic-bezier`; M6 is per file, so a query in another file does not count;
the web checks read CSS, Tailwind classes and JS objects, and the native ones only SwiftUI and Compose names; comments
and strings are scanned like code, except that M7–M9 skip C comments (never a `/*` or `//` inside a string). M7 passes
a duration of 0 (no motion) and any argument that names something (`kMotionEnterMs`, `lv_anim_speed_clamped(…)`); M8
reads one `lv_anim_t` from its `lv_anim_init` to its `lv_anim_start` in the same file, sees a path set by
`lv_anim_set_path_cb` (a name, `ns::Name` or `&name`) or by `a.path_cb =`, and knows only LVGL's own setters
(`lv_obj_set_x`, `lv_obj_set_y`, `lv_obj_set_style_translate_x`/`_y`, bare, `&`-taken or cast) — a project-defined
exec callback such as `anim_x_cb` is not followed, whatever it moves; it skips a loop (`LV_ANIM_REPEAT_INFINITE`).
M9 cannot see an opacity animation written by hand on a full-screen object. The accessibility skill's A9 finds
animation with no reduced-motion handling anywhere in the tree. A pass is a floor, never a review.

Prints one line per hit — `file:line: M<n> what — fix` — then a count and how many UI files it read, by kind; a named
file that cannot be read or has no UI extension is said and not counted, and reading none is said plainly, since a pass
that read nothing checked nothing. A whole-tree run over BASELINE exits 1; a run
on named files exits 1 on any hit. Python 3.9+, standard library only.
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
C_EXT = {".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx"}  # Embedded (ESP-IDF, LVGL): M7–M9 read these
UI_EXT = WEB_EXT | NATIVE_EXT | C_EXT
SKIP_DIRS = ("node_modules/", "vendor/", "third_party/", "build/", "dist/", "out/", "coverage/", ".cache/", ".venv/",
             "Pods/", "managed_components/", ".agents/", ".claude/", ".codex/", ".github/")

EXIT = re.compile(r"(?<![a-z])(?:exit\w*|leav\w*|out|dismiss\w*)(?![a-z])", re.I)  # only words that mean leaving
ALL = re.compile(r"\btransition(?:Property|-property)?\s*:\s*[`'\"]?all\b|(?<![\w-])transition-all\b")
ZERO_SCALE = re.compile(r"\bscale\(\s*0(?:\.0+)?\s*(?:,\s*0(?:\.0+)?\s*)?\)|\bscale\s*:\s*0(?:\.0+)?\s*[,;}\]\n]"
                        r"|\bscaleEffect\(\s*0(?:\.0+)?\s*\)|\.scale\(\s*scale\s*:\s*0(?:\.0+)?\s*\)"
                        r"|initialScale\s*=\s*0(?:\.0+)?f?\b|fromXScale\s*=\s*[\"']0(?:\.0+)?[\"']")
EASE_IN = re.compile(r"(?:transition|animation)(?:-timing-function)?\s*:[^;{}]*?(?<![-\w])ease-in(?![-\w])"
                     r"|class(?:Name)?\s*=\s*[\"'{`][^\"'`]*?(?<![-\w:])ease-in(?![-\w])"
                     r"|\.easeIn\b(?!Out)|[\"']easeIn[\"']", re.S)
LAYOUT_WORDS = r"(?<![-\w])(?:width|height|top|left|right|bottom|margin(?:-\w+)?|padding(?:-\w+)?|max-height|min-height|grid-template-rows)(?![-\w])"
LAYOUT = re.compile(r"\btransition(?:-property)?\s*:[^;{}]*?" + LAYOUT_WORDS + r"|(?<![\w-])transition-\[(?:width|height|margin|padding|top|left)", re.S)
KEYFRAMES = re.compile(r"@keyframes\s+[\w-]+\s*\{")
HOVER_MOVE = re.compile(r":hover\s*(?:,[^{};]*)?\{[^{}]*?(?:\btransform\s*:[^;{}]*translate|(?<![-\w])translate\s*:|(?<![-\w])(?:top|margin-top)\s*:)"
                        r"|(?<![\w:-])hover:-?translate-")
SMOOTH = re.compile(r"scroll-behavior\s*:\s*smooth|behavior\s*:\s*['\"]smooth['\"]|(?<![\w:-])scroll-smooth\b")
REDUCED = re.compile(r"@media[^{]*prefers-reduced-motion|matchMedia\([^)]*prefers-reduced-motion|useReducedMotion|"
                     r"accessibilityReduceMotion|isReduceMotionEnabled|motion-safe:|motion-reduce:")

# Embedded (ESP-IDF, LVGL). Each call whose duration argument M7 reads, with that argument's index; the older names
# are the ones LVGL's api_map headers still map (`lv_anim_set_time` → `lv_anim_set_duration`, `_anim_time` →
# `_anim_duration`).
DURATION_ARG = {"lv_anim_set_duration": 1, "lv_anim_set_time": 1, "lv_anim_set_reverse_duration": 1,
                "lv_anim_set_reverse_time": 1, "lv_anim_set_playback_time": 1, "lv_anim_set_playback_duration": 1,
                "lv_obj_fade_in": 1, "lv_obj_fade_out": 1, "lv_screen_load_anim": 2, "lv_scr_load_anim": 2,
                "lv_style_transition_dsc_init": 3, "lv_obj_set_style_anim_duration": 1,
                "lv_obj_set_style_anim_time": 1, "lv_style_set_anim_duration": 1, "lv_style_set_anim_time": 1}
LV_CALL = re.compile(r"\b(" + "|".join(sorted(DURATION_ARG, key=len, reverse=True)) + r")\s*\(")
NUMBER = re.compile(r"\b(?:0[xX][0-9a-fA-F]+|\d+(?:\.\d*)?(?:[eE][-+]?\d+)?)[uUlLfF]*\b")
CAST = re.compile(r"\(\s*(?:const\s+)?(?:unsigned|signed|int|long|short|u?int(?:8|16|32|64)_t|size_t|float|double)"
                  r"(?:\s+(?:int|long))?\s*\)")
ANIM_INIT = re.compile(r"\blv_anim_init\s*\(\s*&?\s*([\w.\[\]]+(?:->[\w.\[\]]+)*)\s*\)")
# An exec callback that moves: LVGL's own setter, bare, `&`-taken, C-cast or reinterpret_cast.
TRAVEL_CB = (r"(?:\(\s*\w+\s*\)\s*|reinterpret_cast\s*<\s*\w+\s*>\s*\(\s*)?&?\s*"
             r"(?:lv_obj_set_[xy]|lv_obj_set_style_translate_[xy])\b")
PATH_NAME = r"(&?\s*\w+(?:::\w+)*)"  # a path callback: `name`, `ns::Name`, `&name`
SCREEN_SLIDE = re.compile(r"\blv_scr(?:een)?_load_anim\s*\([^;]*?\bLV_SCR(?:EEN)?_LOAD_ANIM_(?:MOVE|OVER|OUT)_\w+")
SCREEN_FADE = re.compile(r"\blv_scr(?:een)?_load_anim\s*\([^;]*?\bLV_SCR(?:EEN)?_LOAD_ANIM_FADE_\w+"
                         r"|\blv_obj_fade_(?:in|out)\s*\(\s*(?:lv_screen_active|lv_scr_act|lv_layer_top)\s*\(\s*\)")


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


def number_value(literal: str) -> float:
    if literal.lower().startswith("0x"):
        return int(literal.rstrip("uUlL"), 16)
    return float(literal.rstrip("uUlLfF"))


def literal_duration(arg: str) -> bool:
    """Whether an argument is a number written in place: it names nothing (a token, a call) and is not 0, which
    means no motion."""
    numbers = NUMBER.findall(arg)
    rest = NUMBER.sub("", CAST.sub("", arg))
    return bool(numbers) and not re.search(r"\w", rest) and any(number_value(n) for n in numbers)


def linear_travel(text: str):
    """M8 for each lv_anim_t: from its lv_anim_init to its lv_anim_start, an x, y or translate setter on a linear
    path."""
    for m in ANIM_INIT.finditer(text):
        var = re.escape(m.group(1))
        start = re.compile(r"\blv_anim_start\s*\(\s*&?\s*" + var + r"\s*\)").search(text, m.end())
        if not start:
            continue
        block = text[m.end():start.start()]
        if re.search(r"\blv_anim_init\s*\(\s*&?\s*" + var + r"\s*\)", block):
            continue  # a later init of the same variable owns this start
        travel = re.search(r"\blv_anim_set_exec_cb\s*\(\s*&?\s*" + var + r"\s*,\s*" + TRAVEL_CB, block)
        if not travel or re.search(r"\blv_anim_set_repeat_count\s*\([^;]*LV_ANIM_REPEAT_INFINITE", block):
            continue
        paths = list(re.finditer(r"\blv_anim_set_path_cb\s*\(\s*&?\s*" + var + r"\s*,\s*" + PATH_NAME + r"\s*\)"
                                 r"|(?<![\w.>])" + var + r"\s*(?:\.|->)\s*path_cb\s*=\s*" + PATH_NAME, block))
        path = paths[-1] if paths else None  # the last one set wins
        name = re.sub(r"^&\s*|^.*::", "", (path.group(1) or path.group(2))) if path else None
        if path is None or name == "lv_anim_path_linear":
            yield m.end() + (path.start() if path else travel.start())


def lvgl_hits(text: str):
    """M7–M9 in one C or C++ file's text: (position, message)."""
    code = blank_c_comments(text)
    for m in LV_CALL.finditer(code):
        args = call_args(code, m.end() - 1)
        index = DURATION_ARG[m.group(1)]
        if len(args) > index and literal_duration(args[index][1]):
            yield (args[index][0], "M7 a duration written as a number — take it from the brief's motion token, "
                                   "a named constant (MOTION §3)")
    for pos in linear_travel(code):
        yield (pos, "M8 something that travels on the linear path — lv_anim_init leaves lv_anim_path_linear; set "
                    "the brief's decelerate or standard path (MOTION §2)")
    for m in SCREEN_SLIDE.finditer(code):
        yield (m.start(), "M8 an lv_screen_load_anim slide runs on the linear path — slide the screens with an "
                          "lv_anim_t on the brief's path (MOTION §2)")
    for m in SCREEN_FADE.finditer(code):
        yield (m.start(), "M9 a full-screen opacity fade — it renders both screens and blends every pixel each frame; "
                          "a cut, a slide, or a fade of the area that changes (MOTION §7)")


def exit_context(text: str, pos: int) -> bool:
    """Whether the match sits in an exit: inside a CSS rule, its selector names one; elsewhere, its own line does."""
    open_, close = text.rfind("{", 0, pos), text.rfind("}", 0, pos)
    if open_ > close:
        selector = text[max(close + 1, text.rfind(";", 0, open_) + 1):open_]
        if "(" not in selector:
            return bool(EXIT.search(selector))
    start = text.rfind("\n", 0, pos) + 1
    end = text.find("\n", pos)
    return bool(EXIT.search(text[start:end if end != -1 else len(text)]))


def keyframe_layout(text: str):
    """M4 inside @keyframes blocks: each layout property a keyframe animates."""
    for m in KEYFRAMES.finditer(text):
        depth, i = 1, m.end()
        while i < len(text) and depth:
            depth += {"{": 1, "}": -1}.get(text[i], 0)
            i += 1
        p = re.search(LAYOUT_WORDS + r"\s*:", text[m.end():i])
        if p:  # one hit per keyframes block
            yield m.end() + p.start()


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


def scan_text(name: str, text: str) -> list[tuple[int, str]]:
    """Every hit in one file's text: (line, message)."""
    lines = text.split("\n")  # as line_of counts: splitlines would also break at a form feed and shift every line
    hits: list[tuple[int, str]] = []

    def add(pos: int, msg: str) -> None:
        n = line_of(text, pos)
        if not (0 < n <= len(lines) and "motion-exception" in lines[n - 1]):
            hits.append((n, msg))

    if Path(name).suffix in C_EXT:  # Embedded (ESP-IDF, LVGL): the LVGL rules, and none of the web or native ones
        for pos, msg in lvgl_hits(text):
            add(pos, msg)
        return sorted(hits)
    for m in ALL.finditer(text):
        add(m.start(), "M1 every property animates — name the properties that move (MOTION §7)")
    for m in ZERO_SCALE.finditer(text):
        if not exit_context(text, m.start()):
            add(m.start(), "M2 an entrance from zero scale — start near full size with opacity rising (MOTION §4)")
    for m in EASE_IN.finditer(text):
        if not exit_context(text, m.start()):
            add(m.start(), "M3 an ease-in curve on what may be an arrival, hover or press — it starts slow; a "
                           "decelerate curve there, an accelerate only on an exit (MOTION §2)")
    for m in LAYOUT.finditer(text):
        add(m.start(), "M4 a layout property animates — move by transform, grow by scale; a grid-template-rows reveal "
                       "to auto is the usual sanctioned case (MOTION §7)")
    for pos in keyframe_layout(text):
        add(pos, "M4 a keyframe animates a layout property — move by transform, grow by scale (MOTION §7)")
    for m in HOVER_MOVE.finditer(text):
        add(m.start(), "M5 the hovered element moves itself — move its content instead (MOTION §4)")
    if not REDUCED.search(re.sub(r"/\*.*?\*/|<!--.*?-->", "", text, flags=re.S)):
        for m in SMOOTH.finditer(text):
            add(m.start(), "M6 smooth scrolling with no reduced-motion check — smooth only under no-preference "
                           "(MOTION §8)")
    return sorted(hits)


def self_test() -> int:
    cases = [
        ("a.css", ".m { transition: all 200ms; }", ["M1"]),
        ("b.tsx", '<div className="transition-all duration-200">', ["M1"]),
        ("c.css", ".m { transition: opacity 200ms, transform 200ms; }", []),
        ("d.css", "@keyframes in { from { transform: scale(0); } }", ["M2"]),
        ("e.css", "@keyframes in { from { transform: scale(0.96); opacity: 0; } }", []),
        ("f.swift", "view.scaleEffect(0)", ["M2"]),
        ("g.kt", "scaleIn(initialScale = 0f)", ["M2"]),
        ("h.css", ".m { transition: transform 200ms ease-in; }", ["M3"]),
        ("i.css", ".m { transition: transform 200ms ease-in-out; }", []),
        ("j.swift", "withAnimation(.easeIn(duration: 0.2)) { open = true }", ["M3"]),
        ("k.swift", "withAnimation(.easeInOut(duration: 0.2)) { open = true }", []),
        ("l.css", ".panel { transition: height 200ms, opacity 200ms; }", ["M4"]),
        ("m.css", ".panel { transition: transform 200ms; }", []),
        ("n.css", ".card:hover { transform: translateY(-2px); }", ["M5"]),
        ("o.css", ".card:hover .inner { color: red; }\n.card .inner { transform: translateY(0); }", []),
        ("p.css", "html { scroll-behavior: smooth; }", ["M6"]),
        ("q.css", "@media (prefers-reduced-motion: no-preference) { html { scroll-behavior: smooth; } }", []),
        ("r.css", ".m { transition: all 200ms; } /* motion-exception: a one-off colour fade, two properties */", []),
        ("s.css", ".m { transition: margin-left 200ms; }", ["M4"]),
        ("t.tsx", '<div class="transition ease-in duration-200">', ["M3"]),
        ("u.css", ".m {\n  transition:\n    opacity 1s,\n    height 1s;\n}", ["M4"]),
        ("v.css", ".m { transition: opacity var(--width-dur); }", []),
        ("w.css", ".toast-exit { animation: fade 100ms ease-in forwards; }", []),
        ("x.css", ".m { transition: opacity 200ms var(--ease-in); }", []),
        ("y.css", ".fill { transform: scale(0, 1); }", []),
        ("z.scss", ".a:hover { &::after { transform: translateX(4px); } }", []),
        ("aa.css", ".card:hover, .card:focus { transform: translateY(-2px); }", ["M5"]),
        ("ab.tsx", '<div className="hover:-translate-y-1 transition-transform">', ["M5"]),
        ("ac.tsx", '<div className="group"><span className="group-hover:translate-x-1" /></div>', []),
        ("ad.html", '<html class="scroll-smooth">', ["M6"]),
        ("ae.css", "/* TODO prefers-reduced-motion */ html { scroll-behavior: smooth; }", ["M6"]),
        ("af.css", "@keyframes grow { from { height: 0; } to { height: 200px; } }", ["M4"]),
        ("ag.js", "el.style.transitionProperty = 'all'", []),
        ("ah.js", "const s = { transitionProperty: 'all' }", ["M1"]),
        ("ai.kt", "fadeOut(tween(100, easing = FastOutLinearInEasing))", []),
        ("aj.css", ".card:hover .inner { transform: translateY(-2px); }", []),
        ("ak.css", ".card:hover::after { transform: translateX(2px); }", []),
        ("al.tsx", "<motion.div initial={{ scale: 0, opacity: 0 }} />", ["M2"]),
        ("am.dart", "Transform.scale(scale: 0.0, child: c)", ["M2"]),
        ("an.css", ".layout-grid { transition: transform 200ms ease-in; }", ["M3"]),
        ("ao.css", ".close{opacity:0}.panel{transition:transform .2s ease-in}", ["M3"]),
        ("ap.css", ".toast.is-exiting {\n  animation: fade 100ms\n    ease-in forwards;\n}", []),
        ("ar.css", ".drawer.closed { transition: transform 200ms ease-in; }", ["M3"]),
        ("as.css", ".toast--leaving { animation: fade 100ms ease-in forwards; }", []),
        ("aq.css", "/* @media (prefers-reduced-motion) */ html { scroll-behavior: smooth; }", ["M6"]),
        # Embedded (ESP-IDF, LVGL)
        ("ba.c", "lv_anim_set_duration(&a, 300);", ["M7"]),
        ("bb.c", "lv_anim_set_duration(&a, MOTION_ENTER_MS);", []),
        ("bc.cpp", "lv_anim_set_time(&a, 250U);", ["M7"]),
        ("bd.c", "lv_anim_set_duration(&a, 0);  /* reduced motion: the change lands at once */", []),
        ("be.c", "lv_anim_set_duration(&a, lv_anim_speed_clamped(400, 120, 300));", []),
        ("bf.c", "lv_style_transition_dsc_init(&tr, props, lv_anim_path_ease_out, 200, 0, NULL);", ["M7"]),
        ("bg.c", "lv_style_transition_dsc_init(&tr, props, lv_anim_path_ease_out, MOTION_SHORT_MS, 0, NULL);", []),
        ("bh.c", "// lv_anim_set_duration(&a, 300);\nlv_anim_set_duration(&a, kExitMs);", []),
        ("bi.c", "lv_anim_set_duration(&a, 120);  // motion-exception: the press flash, below the token scale", []),
        ("bj.c", "lv_anim_t a;\nlv_anim_init(&a);\nlv_anim_set_var(&a, card);\n"
                 "lv_anim_set_exec_cb(&a, (lv_anim_exec_xcb_t)lv_obj_set_y);\n"
                 "lv_anim_set_values(&a, 40, 0);\nlv_anim_set_duration(&a, ENTER_MS);\nlv_anim_start(&a);", ["M8"]),
        ("bk.c", "lv_anim_init(&a);\nlv_anim_set_exec_cb(&a, (lv_anim_exec_xcb_t)lv_obj_set_y);\n"
                 "lv_anim_set_path_cb(&a, lv_anim_path_ease_out);\nlv_anim_start(&a);", []),
        ("bl.cpp", "lv_anim_init(&anim_);\nlv_anim_set_exec_cb(&anim_, lv_obj_set_x);\n"
                   "lv_anim_set_path_cb(&anim_, lv_anim_path_linear);\nlv_anim_start(&anim_);", ["M8"]),
        ("bm.c", "lv_anim_init(&a);\nlv_anim_set_exec_cb(&a, lv_obj_set_x);\n"
                 "lv_anim_set_repeat_count(&a, LV_ANIM_REPEAT_INFINITE);\nlv_anim_start(&a);", []),
        ("bn.c", "lv_anim_init(&a);\nlv_anim_set_exec_cb(&a, spinner_angle_cb);\nlv_anim_start(&a);", []),
        ("bo.c", "lv_screen_load_anim(next, LV_SCREEN_LOAD_ANIM_MOVE_LEFT, SCREEN_MS, 0, false);", ["M8"]),
        ("bp.c", "lv_screen_load_anim(next, LV_SCREEN_LOAD_ANIM_NONE, 0, 0, false);", []),
        ("bq.c", "lv_screen_load_anim(next, LV_SCREEN_LOAD_ANIM_FADE_IN, SCREEN_MS, 0, false);", ["M9"]),
        ("br.c", "lv_scr_load_anim(next, LV_SCR_LOAD_ANIM_FADE_ON, 500, 0, false);", ["M7", "M9"]),
        ("bs.c", "lv_obj_fade_in(lv_screen_active(), FADE_MS, 0);", ["M9"]),
        ("bt.c", "lv_obj_fade_in(badge, FADE_MS, 0);", []),
        ("bu.css", ".m { transition: transform 200ms; } /* lv_anim_set_duration(&a, 300) */", []),
        ("bv.h", "static const char *k = \"scale(0)\"; /* transition: all */", []),
        # M8 sees a path in the spellings code uses, and the casts an exec callback takes
        ("bw.cpp", "lv_anim_init(&a);\nlv_anim_set_exec_cb(&a, (lv_anim_exec_xcb_t)lv_obj_set_y);\n"
                   "lv_anim_set_path_cb(&a, ui_theme::PathEmphasizedDecelerate);\nlv_anim_start(&a);", []),
        ("bx.c", "lv_anim_init(&a);\nlv_anim_set_exec_cb(&a, (lv_anim_exec_xcb_t)lv_obj_set_y);\n"
                 "lv_anim_set_path_cb(&a, &path);\nlv_anim_start(&a);", []),
        ("by.c", "lv_anim_init(&a);\nlv_anim_set_exec_cb(&a, (lv_anim_exec_xcb_t)lv_obj_set_y);\n"
                 "a.path_cb = lv_anim_path_ease_out;\nlv_anim_start(&a);", []),
        ("bz.c", "lv_anim_init(&a);\nlv_anim_set_exec_cb(&a, (lv_anim_exec_xcb_t)lv_obj_set_y);\n"
                 "a.path_cb = lv_anim_path_linear;\nlv_anim_start(&a);", ["M8"]),
        ("ca.cpp", "lv_anim_init(&a);\nlv_anim_set_exec_cb(&a, reinterpret_cast<lv_anim_exec_xcb_t>(lv_obj_set_y));\n"
                   "lv_anim_start(&a);", ["M8"]),
        ("cb.c", "lv_anim_init(&a);\nlv_anim_set_exec_cb(&a, (lv_anim_exec_xcb_t)&lv_obj_set_y);\nlv_anim_start(&a);",
         ["M8"]),
        ("cc.c", "lv_anim_init(&a);\nlv_anim_set_exec_cb(&a, anim_x_cb);\nlv_anim_start(&a);", []),
        ("cd.c", "lv_anim_init(&a);\nlv_anim_set_exec_cb(&a, lv_obj_set_x_ofs);\nlv_anim_start(&a);", []),
        # a form feed does not shift lines, so an exception on the hit's line still holds
        ("ce.c", "\f\nlv_anim_set_duration(&a, 300);  // motion-exception: a test", []),
        ("cf.c", "\f\nlv_anim_set_duration(&a, 300);", ["M7"]),
        # a comment opener inside a string opens no comment
        ("cg.c", "const char *u = \"/*\";\nlv_anim_set_duration(&a, 300);\nconst char *v = \"*/\";", ["M7"]),
        ("ch.c", "char c = '\"'; /* lv_anim_set_duration(&a, 300); */", []),
        ("ci.hxx", "lv_anim_set_duration(&a, 300);", ["M7"]),
    ]
    bad = 0
    for name, text, want in cases:
        got = sorted(msg.split()[0] for _, msg in scan_text(name, text))
        if got != sorted(want):
            bad += 1
            print(f"FAIL {name}: want {want}, got {got}")
    # UI_PATHS matching: a folder with a glob holds the files beneath it.
    globs = [("components/ui_toast/toast.cpp", ("components/ui_*/",), True),
             ("components/ui_toast/src/a.cpp", ("components/ui_*/",), True),
             ("components/audio/a.cpp", ("components/ui_*/",), False),
             ("main/ui/home.c", ("main/ui/",), True), ("main/app.c", ("*.css",), False)]
    for path, patterns, want in globs:
        if matches(path, patterns) != want:
            bad += 1
            print(f"FAIL matches({path!r}, {patterns}): want {want}")
    # The count is of UI files read: a missing or non-UI named file is said, never counted.
    with tempfile.TemporaryDirectory() as tmp:
        good = Path(tmp, "ok.c")
        good.write_text("lv_anim_set_duration(&a, kEnterMs);\n")
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
    total = len(cases) + len(globs) + 3
    print(f"motion_check self-test: {total - bad}/{total} passed")
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
        hits += [f"{f}:{n}: {msg}" for n, msg in scan_text(f, text)]
    out += hits
    limit = 0 if named else BASELINE
    kinds = [("web", WEB_EXT), ("native", NATIVE_EXT), ("C/C++", C_EXT)]
    by_kind = ", ".join(f"{sum(Path(f).suffix in ext for f in read)} {kind}" for kind, ext in kinds)
    out.append(f"M1–M9 motion patterns — {len(hits)} hits in {len(read)} UI files ({by_kind})"
               + ("" if named else f" (baseline {BASELINE})"))
    if not read:
        why = ("no named file is a readable UI file" if named
               else "UI_PATHS in .agents/project.py is empty or matches no file" if ui_patterns() is not None
               else "no tracked file has a UI extension")
        out.append(f"read no UI files — nothing was checked: {why}")
    if len(hits) > limit:
        out.append("FAIL — fix each hit, or mark a sanctioned one `motion-exception` with its reason")
        return out, 1
    return out, 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
