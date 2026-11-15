#!/usr/bin/env python3
"""The touch-and-gesture skill's check: patterns in UI files that break touch, gestures or mobile layout, from
references/touch.md (cited `TOUCH §n`). It finds what a pattern shows; the device walk finds the rest.

    python3 .agents/skills/touch-and-gesture/scripts/touch_check.py            # every UI file, against the baseline
    python3 .agents/skills/touch-and-gesture/scripts/touch_check.py FILE …     # some files, no baseline
    python3 .agents/skills/touch-and-gesture/scripts/touch_check.py --test     # the self-test

Which files: in a repo with the agent-harness kit, UI_PATHS from `.agents/project.py` (empty there means none yet);
in any other repo, every tracked file with a UI extension outside vendored and generated folders. A line that carries
`touch-exception` is skipped — write the reason beside it (a canvas or map that takes every gesture, with its plain
alternative named).

  T1  a surface that claims every axis (`touch-action: none`, `touch-none`, `touchAction = 'none'`)   TOUCH §2
  T2  a height on `100vh` (`height`, `minHeight`, `--var`, `h-screen`, `h-[100vh]`) in a file with no `dvh`, `svh` or
      `-webkit-fill-available`   TOUCH §7
  T3  a text field (input, textarea, contenteditable) that takes focus unasked (`autofocus`, `autoFocus`)   TOUCH §7
  T4  selection off for the whole page (html, body, :root, *, #root — CSS, `@apply`, or a body class)   TOUCH §5
  T5  the tap highlight removed in a file that draws no pressed style (`:active`, `active:`, `data-[pressed]:`,
      `whileTap`)   TOUCH §5

What it cannot see: how a drag feels, whether a gesture claims the right axis, whether a sheet scrolls before it
drags, whether the keyboard covers a field, a `.focus()` call in a script — the device walk (TOUCH §9) finds those. T2
and T5 look across the file, so a reset or a fallback in another file is not seen, and Tailwind's base styles already
remove the tap highlight project-wide. The web checks read CSS, Tailwind classes and markup; native code is not read.
Comments (`/* */`, `<!-- -->`, `//`) are skipped; strings are scanned like code. T3 reads a tag whose name holds input,
textarea, textfield, textinput or searchfield, or one marked contenteditable — a wrapper named otherwise is not seen. A named file that cannot be read exits 2. A pass is a floor,
never a review.

Prints one line per hit — `file:line: T<n> what — fix` — then a count. A whole-tree run over BASELINE exits 1; a run
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
          ".astro", ".erb", ".liquid", ".hbs", ".njk"}
SKIP_DIRS = ("node_modules/", "vendor/", "third_party/", "build/", "dist/", "out/", "coverage/", ".cache/", ".venv/",
             "Pods/", ".agents/", ".claude/", ".codex/", ".github/")

VARIANT = r"(?<![\w-])(?:[\w-]+:)*"  # Tailwind variants such as md: or active:
TOUCH_NONE = re.compile(r"\btouch-action\s*:\s*none\b|" + VARIANT + r"touch-none\b"
                        r"|touchAction\s*[:=]\s*['\"`]none['\"`]")
VH = re.compile(r"(?:\b(?:min-|max-)?height|\b[a-z]*Height|\bblock-size|--[\w-]+)\s*:[^;{}\n]*?(?<![\w.])100vh\b"
                r"|" + VARIANT + r"(?:min-|max-)?h-(?:screen\b|\[[^\]]*100vh)")
NEW_VH = re.compile(r"\d+(?:d|s)vh\b|(?<![\w-])(?:[\w-]+:)*(?:min-)?h-(?:d|s)vh\b|-webkit-fill-available")
TEXT_TAG = re.compile(r"<([\w.]*(?:input|textarea|textfield|textinput|searchfield)[\w.]*|[\w.]+(?=[^>]*\bcontenteditable))\b",
                      re.I)
NOT_TEXT = re.compile(r"\btype\s*=\s*['\"{]*(?:button|submit|reset|checkbox|radio|range|color|file|hidden|image)\b", re.I)
AUTOFOCUS = re.compile(r"(?<![\w-])autofocus\b(?!\s*=\s*['\"]?false)|\bautoFocus\b(?!\s*=\s*\{(?!\s*true\s*\}))")
ROOT_SELECT = re.compile(r"(?:^|[{},;])\s*(?:html|body|:root|\*|#root|#app|#__next)(?:\s*,\s*(?:html|body|:root|\*|#root"
                         r"|#app|#__next))*\s*\{[^{}]*?(?:(?:-webkit-)?user-select\s*:\s*none|@apply[^;{}]*\bselect-none\b)"
                         r"|<(?:html|body)\b[^>]*\bclass(?:Name)?\s*=\s*['\"][^'\"]*(?<![\w-])select-none\b", re.M)
TAP_HIGHLIGHT = re.compile(r"-webkit-tap-highlight-color\s*:\s*(?:transparent|#0000(?:0000)?\b|rgba\(\s*0\s*,\s*0\s*,\s*0"
                           r"\s*,\s*0\s*\)|rgb\(\s*0\s+0\s+0\s*/\s*0%?\s*\))|(?<![\w-])tap-highlight-transparent\b"
                           r"|WebkitTapHighlightColor\s*:\s*['\"`](?:transparent|#0000|rgba\(0,\s*0,\s*0,\s*0\))")
PRESSED = re.compile(r":active\b|(?<![\w-])active:|\bdata-pressed\b|\[data-state=['\"]?pressed|data-\[(?:state=)?pressed\]:"
                     r"|(?<![\w-])pressed:|\bwhileTap\b")
COMMENT = re.compile(r"/\*.*?\*/|<!--.*?-->|(?<![:/\w])//[^\n]*", re.S)


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


def block_around(text: str, pos: int) -> str:
    """The CSS rule around a position, or its line outside a rule; the class attribute's line for markup."""
    open_, close = text.rfind("{", 0, pos), text.rfind("}", 0, pos)
    if open_ > close:
        end = text.find("}", pos)
        return text[open_:end if end != -1 else len(text)]
    start = text.rfind("\n", 0, pos) + 1
    end = text.find("\n", pos)
    return text[start:end if end != -1 else len(text)]


def tag_at(text: str, start: int) -> str:
    """The whole tag that opens at `start`: quotes, template literals and nested {…} are kept whole, so a `>` inside
    `{e => set(e.target.value)}` does not end it."""
    stack: list[str] = []
    i = start + 1
    while i < len(text):
        c, top = text[i], (stack[-1] if stack else "")
        if top in ("\"", "'", "`"):
            if c == "\\":
                i += 1
            elif c == top:
                stack.pop()
            elif top == "`" and text.startswith("${", i):
                stack.append("${")
                i += 1
        elif c in "\"'`":
            stack.append(c)
        elif c == "{":
            stack.append("{")
        elif c == "}":
            if stack:
                stack.pop()
        elif c == ">" and not stack and text[i - 1] != "=":
            return text[start:i + 1]
        i += 1
    return text[start:]


def scan_text(name: str, text: str) -> list[tuple[int, str]]:
    """Every hit in one file's text: (line, message). Comments are read as blanks, so a note naming a pattern never
    counts; a `touch-exception` marker in a comment still does."""
    lines = text.splitlines()
    code = COMMENT.sub(lambda m: re.sub(r"[^\n]", " ", m.group()), text)
    hits: list[tuple[int, str]] = []

    def add(pos: int, msg: str) -> None:
        n = line_of(text, pos)
        if not (0 < n <= len(lines) and "touch-exception" in lines[n - 1]):
            hits.append((n, msg))

    for m in TOUCH_NONE.finditer(code):
        add(m.start(), "T1 the surface claims every axis — name the axis the browser keeps (pan-y, pan-x, manipulation); "
                       "only a drag handle, a slider thumb, a canvas or a map takes none, marked (TOUCH §2)")
    if not NEW_VH.search(code):
        for m in VH.finditer(code):
            add(m.start(), "T2 a full height on 100vh alone hides a bottom action under the browser's bar — add dvh or "
                           "svh after the 100vh fallback (TOUCH §7)")
    for t in TEXT_TAG.finditer(code):
        tag = tag_at(code, t.start())
        if not NOT_TEXT.search(tag) and (m := AUTOFOCUS.search(tag)):
            add(t.start() + m.start(), "T3 a text field focused unasked opens the keyboard on touch — focus it on a "
                                       "tap, or only with a fine pointer (TOUCH §7)")
    for m in ROOT_SELECT.finditer(code):
        add(m.end(), "T4 selection off for the whole page — turn it off on control labels only; content stays "
                     "selectable (TOUCH §5)")
    if not PRESSED.search(code):
        for m in TAP_HIGHLIGHT.finditer(code):
            add(m.start(), "T5 the tap highlight is removed and this file draws no pressed style (:active) — draw one, "
                           "or keep the highlight (TOUCH §5)")
    return sorted(hits)


def self_test() -> int:
    cases = [
        ("a.css", ".carousel { touch-action: none; }", ["T1"]),
        ("b.css", ".carousel { touch-action: pan-y; }", []),
        ("c.tsx", '<div className="md:touch-none">', ["T1"]),
        ("c2.js", "el.style.touchAction = 'none'", ["T1"]),
        ("c3.js", "const s = { touchAction: `none` }", ["T1"]),
        ("c4.css", ".handle { touch-action: none; } /* touch-exception: drag handle; move up/down buttons */", []),
        ("d.css", ".page { min-height: 100vh; }", ["T2"]),
        ("e.css", ".page { min-height: 100vh; }\n@supports (height: 100dvh) { .page { min-height: 100dvh; } }", []),
        ("e2.css", ".page { height: 100vh; height: -webkit-fill-available; }", []),
        ("e3.css", ".slide { transform: translateY(100vh); }", []),
        ("e4.css", "/* the page used 100vh */ .page { min-height: 50%; }", []),
        ("f.tsx", '<main className="md:h-screen">', ["T2"]),
        ("g.tsx", '<main className="h-dvh">', []),
        ("h.html", '<input type="search" autofocus>', ["T3"]),
        ("i.tsx", "<textarea autoFocus />", ["T3"]),
        ("j.tsx", "<input autoFocus={isDesktop} />", []),
        ("j2.html", "<dialog open><button autofocus>Cancel</button></dialog>", []),
        ("j3.html", '<input type="checkbox" autofocus>', []),
        ("k.css", "html, body { user-select: none; }", ["T4"]),
        ("k2.css", "@layer base {\n  body {\n    -webkit-user-select: none;\n  }\n}", ["T4"]),
        ("k3.css", "body { @apply select-none; }", ["T4"]),
        ("k4.html", '<body class="antialiased select-none">', ["T4"]),
        ("l.css", ".btn-label { user-select: none; }", []),
        ("n.css", "a { -webkit-tap-highlight-color: transparent; }", ["T5"]),
        ("n2.css", "a { -webkit-tap-highlight-color: rgb(0 0 0 / 0); }", ["T5"]),
        ("o.css", "a { -webkit-tap-highlight-color: transparent; }\na:active { background: var(--pressed); }", []),
        ("i2.tsx", "<input onChange={e => set(e.target.value)} autoFocus />", ["T3"]),
        ("i3.tsx", "<input value={a > b ? 1 : 2} autoFocus={true} />", ["T3"]),
        ("i4.tsx", "<TextField label='Name' autoFocus />", ["T3"]),
        ("d2.tsx", "const s = { minHeight: '100vh' }", ["T2"]),
        ("d3.tsx", '<main className="min-h-[100vh]">', ["T2"]),
        ("d4.css", ":root { --app-h: 100vh; }", ["T2"]),
        ("o3.tsx", 'a { -webkit-tap-highlight-color: transparent }\n<button className="data-[pressed]:bg-gray-100">', []),
        ("o4.tsx", "const s = { WebkitTapHighlightColor: 'transparent' }", ["T5"]),
        ("o5.tsx", "const s = { WebkitTapHighlightColor: 'transparent' }\n<motion.button whileTap={{ scale: 0.97 }} />", []),
        ("c5.ts", "// touch-action: none was removed here\nconst x = 1", []),
        ("c6.css", ".a { background: url(http://x.test/a.png); touch-action: none; }", ["T1"]),
        ("o2.tsx", 'a { -webkit-tap-highlight-color: #0000 }\n<button aria-pressed="true">', ["T5"]),
    ]
    bad = 0
    for name, text, want in cases:
        got = sorted(msg.split()[0] for _, msg in scan_text(name, text))
        if got != sorted(want):
            bad += 1
            print(f"FAIL {name}: want {want}, got {got}")
    print(f"touch_check self-test: {len(cases) - bad}/{len(cases)} passed")
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
        except OSError as e:
            if named:
                print(f"touch check — cannot read {f}: {e.strerror}")
                return 2
            continue
        hits += [f"{f}:{n}: {msg}" for n, msg in scan_text(f, text)]
    for h in hits:
        print(h)
    limit = 0 if named else BASELINE
    print(f"T1–T5 touch patterns — {len(hits)} hits in {len(files)} UI files"
          + ("" if named else f" (baseline {BASELINE})"))
    if len(hits) > limit:
        print("FAIL — fix each hit, or mark a sanctioned one `touch-exception` with its reason")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
