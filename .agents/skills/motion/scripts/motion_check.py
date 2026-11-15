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

What it cannot see: curves and durations that feel wrong, a missing origin, a restart instead of a retarget, frames
dropped on a real device. Its limits: M2 and M3 skip an exit — inside a CSS rule, one whose selector names leaving (exit,
leave, out, dismiss — never a state such as closed or hidden, which also governs the arrival); elsewhere, a line that
does — since an accelerate curve or a shrink to
nothing is fine there; M5 reads a rule whose last selector is the hovered element, never its content; M3 reads keyword curves, never a
project token (`var(--ease-in)`) or a raw `cubic-bezier`; M6 is per file, so a query in another file does not count;
the web checks read CSS, Tailwind classes and JS objects, and the native ones only SwiftUI and Compose names; comments
and strings are scanned like code. The accessibility skill's A9 finds animation with no reduced-motion handling
anywhere in the tree. A pass is a floor, never a review.

Prints one line per hit — `file:line: M<n> what — fix` — then a count. A whole-tree run over BASELINE exits 1; a run
on named files exits 1 on any hit. Python 3.9+, standard library only.
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
UI_EXT = {".html", ".htm", ".css", ".scss", ".sass", ".less", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".vue", ".svelte",
          ".astro", ".erb", ".liquid", ".hbs", ".njk", ".swift", ".kt", ".java", ".dart", ".xml"}
SKIP_DIRS = ("node_modules/", "vendor/", "third_party/", "build/", "dist/", "out/", "coverage/", ".cache/", ".venv/",
             "Pods/", ".agents/", ".claude/", ".codex/", ".github/")

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
    return any((p.endswith("/") and path.startswith(p)) or (any(c in p for c in "*?[") and fnmatch.fnmatch(path, p))
               or path == p for p in patterns)


def ui_files() -> list[str]:
    tracked = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=ROOT,
                             capture_output=True, text=True).stdout.splitlines()
    patterns = ui_patterns()
    keep = (lambda f: matches(f, patterns)) if patterns is not None else (lambda f: not f.startswith(SKIP_DIRS)
                                                                         and "/node_modules/" not in f)
    return [f for f in tracked if Path(f).suffix in UI_EXT and keep(f) and (ROOT / f).is_file()]


def line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def scan_text(name: str, text: str) -> list[tuple[int, str]]:
    """Every hit in one file's text: (line, message)."""
    lines = text.splitlines()
    hits: list[tuple[int, str]] = []

    def add(pos: int, msg: str) -> None:
        n = line_of(text, pos)
        if not (0 < n <= len(lines) and "motion-exception" in lines[n - 1]):
            hits.append((n, msg))

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
    ]
    bad = 0
    for name, text, want in cases:
        got = sorted(msg.split()[0] for _, msg in scan_text(name, text))
        if got != sorted(want):
            bad += 1
            print(f"FAIL {name}: want {want}, got {got}")
    print(f"motion_check self-test: {len(cases) - bad}/{len(cases)} passed")
    return 1 if bad else 0


def main(argv: list[str]) -> int:
    if argv[:1] == ["--test"]:
        return self_test()
    named = bool(argv)
    files = argv if named else ui_files()
    hits = []
    for f in files:
        try:
            text = (ROOT / f).read_text(errors="replace")
        except OSError:
            continue
        hits += [f"{f}:{n}: {msg}" for n, msg in scan_text(f, text)]
    for h in hits:
        print(h)
    limit = 0 if named else BASELINE
    print(f"M1–M6 motion patterns — {len(hits)} hits in {len(files)} UI files"
          + ("" if named else f" (baseline {BASELINE})"))
    if len(hits) > limit:
        print("FAIL — fix each hit, or mark a sanctioned one `motion-exception` with its reason")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
