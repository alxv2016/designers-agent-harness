#!/usr/bin/env python3
"""The accessibility skill's check: patterns in UI files that break a floor in references/criteria.md (cited
`ACCESSIBILITY §n`) whatever the screen looks like. It finds what a pattern can show; the walks find the rest.

    python3 .agents/skills/accessibility/scripts/a11y_check.py            # every UI file, against the baseline
    python3 .agents/skills/accessibility/scripts/a11y_check.py FILE …     # some files, no baseline
    python3 .agents/skills/accessibility/scripts/a11y_check.py --test     # the self-test

Which files: in a repo with the agent-harness kit, UI_PATHS from `.agents/project.py` (empty there means none yet);
in any other repo, every tracked file with a UI extension outside vendored and generated folders. A line that carries
`a11y-exception` is skipped — write the reason beside it, and in the project's design brief when it has one.

  A1  outline removed in a file with no :focus-visible style            WCAG 2.4.7   ACCESSIBILITY §5
  A2  pinch zoom blocked in a viewport (user-scalable=no, maximum-scale under 2)  WCAG 1.4.4   ACCESSIBILITY §3
  A3  a positive tabindex                                                WCAG 2.4.3   ACCESSIBILITY §5
  A4  an <img> with no alt (alt="" marks decoration)                     WCAG 1.1.1   ACCESSIBILITY §4
  A5  an <html> with no lang                                             WCAG 3.1.1   ACCESSIBILITY §4
  A6  a <video> or <audio> that autoplays with no controls               WCAG 2.2.2   ACCESSIBILITY §8
  A7  a click handler on a <div> or <span> with no role (a role without   WCAG 2.1.1   ACCESSIBILITY §4, §5
      a tab stop and key handling is not caught)
  A8  an Android ImageView or ImageButton with no contentDescription     WCAG 1.1.1   ACCESSIBILITY §4
  A9  animation in the UI and no reduced-motion handling anywhere in it  WCAG 2.3.3   ACCESSIBILITY §8
      (a whole-tree run only)

What it cannot see: A1 is file-level (one :focus-visible rule anywhere in the file clears it); A9 is tree-level (one
reduced-motion branch anywhere clears it); A4–A7 read web markup only and A8 Android XML only, so Swift and Kotlin
views get A1–A3 and A9 at most; comments and strings are scanned like code. A pass is a floor, never a review.

Prints one line per hit — `file:line: A<n> what — fix` — then a count. A whole-tree run over BASELINE exits 1; a run
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
MARKUP = {".html", ".htm", ".jsx", ".tsx", ".vue", ".svelte", ".astro", ".erb", ".liquid", ".hbs", ".njk", ".js",
          ".ts", ".mjs"}

OUTLINE = re.compile(r"\boutline\s*:\s*['\"]?(?:none|0(?:px)?)\b|\boutline-(?:style\s*:\s*none|width\s*:\s*0)\b")
VIEWPORT = re.compile(r"user-scalable\s*=\s*(?:no|0|false)\b|maximum-scale\s*=\s*(?:0?\.\d+|1(?:\.\d+)?)(?![\d.])", re.I)
TABINDEX = re.compile(r"\btab[iI]ndex\s*=\s*(?:[\"']\s*|\{\s*)?[1-9]")
IMG = re.compile(r"<img\b")
HTML = re.compile(r"<html\b")
MEDIA = re.compile(r"<(?:video|audio)\b")
CLICKABLE = re.compile(r"<(?:div|span)\b")
ANDROID_IMAGE = re.compile(r"<(?:ImageView|ImageButton|androidx\.appcompat\.widget\.AppCompatImage(?:View|Button))\b"
                           r"[^>]*>", re.S)
ANIMATES = re.compile(r"@keyframes\b|\btransition\s*:(?!\s*none\b)|\banimation(?:-name)?\s*:(?!\s*none\b)|\bwithAnimation\b|\.animation\(|"
                      r"\banimate\w*AsState\b|\bAnimatedVisibility\b|\bObjectAnimator\b|\bmotion\.\w+|\.animate\(")
REDUCED = re.compile(r"prefers-reduced-motion|useReducedMotion|accessibilityReduceMotion|isReduceMotionEnabled|"
                     r"reduceMotion|ANIMATOR_DURATION_SCALE|animatorDurationScale|areAnimatorsEnabled|motion-safe|"
                     r"motion-reduce|disableAnimations")


def tag_at(text: str, start: int) -> str:
    """The whole tag that opens at `start`, across lines: quotes, template literals and nested {…} are kept whole, so
    a `>` inside `{() => x > 1}`, `style={{…}}` or `${a > b}` does not end it. A stack holds each open `{`, `${` and
    quote, so the `}` that closes a `${` returns to its template literal."""
    stack: list[str] = []  # "{", "${" or a quote character
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
                                                                         and f"/{SKIP_DIRS[0]}" not in f)
    return [f for f in tracked if Path(f).suffix in UI_EXT and keep(f) and (ROOT / f).is_file()]


def line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def scan_text(name: str, text: str) -> list[tuple[int, str]]:
    """Every hit in one file's text: (line, message)."""
    ext = Path(name).suffix
    lines = text.splitlines()
    hits: list[tuple[int, str]] = []

    def add(n: int, msg: str) -> None:
        if not (0 < n <= len(lines) and "a11y-exception" in lines[n - 1]):
            hits.append((n, msg))

    if "focus-visible" not in text and "focusVisible" not in text:
        for m in OUTLINE.finditer(text):
            add(line_of(text, m.start()), "A1 the focus outline removed and no :focus-visible style in this file — "
                                          "give focus a replacement at 3:1 (WCAG 2.4.7, ACCESSIBILITY §5)")
    for m in VIEWPORT.finditer(text):
        add(line_of(text, m.start()), "A2 pinch zoom blocked — drop user-scalable=no and any maximum-scale under 2 "
                                      "(WCAG 1.4.4, ACCESSIBILITY §3)")
    if ext in MARKUP:
        for m in TABINDEX.finditer(text):
            add(line_of(text, m.start()), "A3 a positive tabindex — order focus by the view order, tabindex 0 or -1 "
                                          "(WCAG 2.4.3, ACCESSIBILITY §5)")
        for m in IMG.finditer(text):
            if not re.search(r"\balt\s*=|\{\s*\.\.\.", tag_at(text, m.start())):
                add(line_of(text, m.start()), "A4 an <img> with no alt — say what it means, or alt=\"\" for decoration "
                                              "(WCAG 1.1.1, ACCESSIBILITY §4)")
        for m in HTML.finditer(text):
            if not re.search(r"\blang\s*=", tag_at(text, m.start())):
                add(line_of(text, m.start()), "A5 an <html> with no lang — declare the page's language "
                                              "(WCAG 3.1.1, ACCESSIBILITY §4)")
        for m in MEDIA.finditer(text):
            tag = tag_at(text, m.start())
            if re.search(r"\bautoplay\b", tag, re.I) and not re.search(r"\bcontrols\b", tag, re.I):
                add(line_of(text, m.start()), "A6 media that autoplays with no controls — give it a pause, or do not "
                                              "autoplay (WCAG 2.2.2, ACCESSIBILITY §8)")
        for m in CLICKABLE.finditer(text):
            tag = tag_at(text, m.start())
            if re.search(r"\bon[cC]lick\b|@click\b|\(click\)|on:click\b", tag) and not re.search(r"\brole\s*=", tag):
                add(line_of(text, m.start()), "A7 a click handler on a <div> or <span> — use a <button> or a link "
                                              "(WCAG 2.1.1, 4.1.2, ACCESSIBILITY §4, §5)")
    if ext == ".xml":
        for m in ANDROID_IMAGE.finditer(text):
            tag = m.group(0)
            if "contentDescription" not in tag and "importantForAccessibility" not in tag:
                add(line_of(text, m.start()), "A8 an image with no contentDescription — describe it, or set "
                                              "importantForAccessibility=\"no\" for decoration (WCAG 1.1.1, "
                                              "ACCESSIBILITY §4)")
    return hits


def scan(files: list[str], whole: bool = True) -> list[str]:
    """The hits in these files; A9 only on a whole-tree run, since the reduced-motion branch may sit in a file not
    named."""
    out, animated, reduced = [], None, False
    for f in files:
        try:
            text = (ROOT / f).read_text(errors="replace")
        except OSError:
            continue
        out += [f"{f}:{n}: {msg}" for n, msg in sorted(scan_text(f, text))]
        if animated is None:
            m = ANIMATES.search(text)
            if m and "a11y-exception" not in text.splitlines()[line_of(text, m.start()) - 1]:
                animated = f"{f}:{line_of(text, m.start())}"
        reduced = reduced or bool(REDUCED.search(text))
    if whole and animated and not reduced:
        out.append(f"{animated}: A9 the UI animates and no file handles reduced motion — follow the platform's "
                   f"setting (WCAG 2.3.3, ACCESSIBILITY §8)")
    return out


def self_test() -> int:
    cases = [
        ("a.css", "button:focus { outline: none; }", ["A1"]),
        ("b.css", "button:focus { outline: none; }\nbutton:focus-visible { outline: 2px solid var(--focus); }", []),
        ("c.html", '<meta name="viewport" content="width=device-width, maximum-scale=1">', ["A2"]),
        ("d.html", '<meta name="viewport" content="width=device-width, maximum-scale=5">', []),
        ("e.tsx", "<div tabIndex={2}>x</div>", ["A3"]),
        ("f.tsx", "<div tabIndex={0} role=\"button\" onClick={go}>x</div>", []),
        ("g.html", '<img src="a.png">\n<img src="b.png" alt="">\n<img\n  src="c.png"\n  alt="Chart of sales">', ["A4"]),
        ("h.html", "<html>\n<body></body></html>", ["A5"]),
        ("i.html", '<html lang="en">', []),
        ("j.html", '<video src="v.mp4" autoplay muted loop></video>', ["A6"]),
        ("k.html", '<video src="v.mp4" autoplay muted controls></video>', []),
        ("l.jsx", "<div className=\"row\" onClick={() => open(id)}>Open</div>", ["A7"]),
        ("m.vue", '<span @click="toggle">Toggle</span>', ["A7"]),
        ("n.xml", '<ImageView android:src="@drawable/logo" />', ["A8"]),
        ("o.xml", '<ImageView android:src="@drawable/x" android:importantForAccessibility="no" />', []),
        ("p.css", "a:focus { outline: none; } /* a11y-exception: the ring is drawn by .focus-ring */", []),
        ("q.tsx", "<img {...props} />", []),
        ("t.tsx", "<img src={a} style={{ width: 10 }} />", ["A4"]),
        ("u.tsx", "<img src={`/a/${id}.png`} />", ["A4"]),
        ("v.tsx", "<div style={{ color: 'red' }} onClick={go}>x</div>", ["A7"]),
        ("w.tsx", "<div onClick={() => setOpen({ open: n > 1 })}>x</div>", ["A7"]),
        ("x.tsx", "<div className={cn('a', {b: c})} onClick={go}>x</div>", ["A7"]),
        ("y.tsx", "<img src={a} style={{ width: 10 }} alt={label} />", []),
        ("ab.tsx", "<img src={`/a/${id}.png`} />\n<img src=\"b\" alt=\"x\" />", ["A4"]),
        ("ac.tsx", "<html className={`t-${theme}`}>\n<img src=\"b\" alt=\"x\" />", ["A5"]),
        ("ad.tsx", "<div className={`a ${on ? `b-${n}` : ''}`} onClick={go}>x</div>", ["A7"]),
        ("z.html", '<meta name="viewport" content="width=device-width, maximum-scale=1.5, user-scalable=false">', ["A2", "A2"]),
        ("aa.css", "a:focus { outline: 0px; }", ["A1"]),
    ]
    bad = 0
    for name, text, want in cases:
        got = sorted(msg.split()[0] for _, msg in scan_text(name, text))
        if got != sorted(want):
            bad += 1
            print(f"FAIL {name}: want {want}, got {got}")
    # A9 is whole-tree: animation with no reduced-motion handling anywhere.
    a9 = [("r.css", ".menu { transition: opacity 200ms; }", True),
          ("s0.css", ".menu { transition: none; animation: none; }", False),
          ("s.css", ".menu { transition: opacity 200ms; }\n@media (prefers-reduced-motion: reduce) { .menu { "
                    "transition: none; } }", False)]
    for name, text, want in a9:
        got = bool(ANIMATES.search(text)) and not REDUCED.search(text)
        if got != want:
            bad += 1
            print(f"FAIL {name}: A9 want {want}, got {got}")
    total = len(cases) + len(a9)
    print(f"a11y_check self-test: {total - bad}/{total} passed")
    return 1 if bad else 0


def main(argv: list[str]) -> int:
    if argv[:1] == ["--test"]:
        return self_test()
    named = bool(argv)
    files = argv if named else ui_files()
    hits = scan(files, whole=not named)
    for h in hits:
        print(h)
    limit = 0 if named else BASELINE
    print(f"A1–A9 accessibility patterns — {len(hits)} hits in {len(files)} UI files"
          + ("" if named else f" (baseline {BASELINE})"))
    if len(hits) > limit:
        print("FAIL — fix each hit, or mark a sanctioned one `a11y-exception` with its reason")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
