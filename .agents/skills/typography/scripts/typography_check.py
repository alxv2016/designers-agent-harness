#!/usr/bin/env python3
"""The typography skill's check: patterns in UI files that stop text from scaling or reading well, from
references/typography.md (cited `TYPOGRAPHY §n`). It finds what a line of code shows; reading the screen at its largest
text size finds the rest.

    python3 .agents/skills/typography/scripts/typography_check.py            # every UI file, against the baseline
    python3 .agents/skills/typography/scripts/typography_check.py FILE …     # some files, no baseline
    python3 .agents/skills/typography/scripts/typography_check.py --test     # the self-test

Which files: in a repo with the agent-harness kit, UI_PATHS from `.agents/project.py` (empty there means none yet);
in any other repo, every tracked file with a UI extension outside vendored and generated folders. A line that carries
`typography-exception` is skipped — write the reason beside it.

  Y1  Web: a font size in px — CSS `font-size` or `font`, a font-size custom property, Tailwind `text-[…px]`, a JS
      style's `fontSize`                                                                       TYPOGRAPHY §11, §13
  Y2  Web: a line height in px — CSS `line-height`, Tailwind `leading-[…px]`                       TYPOGRAPHY §6
  Y3  Android: text sized in dp or px — XML `android:textSize`, `COMPLEX_UNIT_DIP`/`_PX`, `.dp.toSp()`
                                                                                               TYPOGRAPHY §11, §13
  Y4  iOS: a fixed size that ignores Dynamic Type — `.system(size:)` with no `@ScaledMetric` in the file,
      `.custom(…, size:)` without `relativeTo:`,
      `UIFont.systemFont(ofSize:)` or `UIFont(name:size:)` in a file with no `UIFontMetrics`   TYPOGRAPHY §11, §13
  Y5  Web: justified text with no hyphenation in its rule or class list                          TYPOGRAPHY §7
  Y6  a light weight — CSS 100–300 and `lighter`, Tailwind `font-thin`/`-extralight`/`-light`, SwiftUI `.ultraLight`/
      `.thin`/`.light`, Compose `FontWeight.Thin`/`ExtraLight`/`Light`, Flutter `w100`–`w300`, Android
      `sans-serif-light`/`-thin`                                                                TYPOGRAPHY §8
  Y7  Web: capitals by style — `text-transform`, `textTransform`, the `uppercase` class inside a quoted class value —
      with no letter spacing in its rule, style object or class list                            TYPOGRAPHY §6, §8
  Embedded (ESP-IDF, LVGL) — C and C++ files:
  Y8  one of LVGL's built-in fonts (`lv_font_montserrat_…`, `_unscii_`, `_dejavu_`, `_simsun_`, `_source_han_sans_`)
      set on one object with `lv_obj_set_style_text_font`, not through the role's shared style   TYPOGRAPHY §12

What it cannot see: a role used for the wrong job, two top levels, a long measure, a missing glyph, text that truncates
where it should wrap, a heading at the wrong level in code. Its limits: Y1 counts a root `font-size` in px too, since
it overrides the browser's setting; Y4 reads `relativeTo:` only on the same line; Y5 and Y7 read one CSS rule, or one
class list in quotes; Y6 cannot tell display text from reading text, so a light display weight carries a
`typography-exception`; Y8 reads only the per-object setter, so the brief's header and its shared styles pass, and
it skips C comments, never a `/*` inside a string. The web rules do not run in C and C++ files. A pass is a floor,
never a review.

Prints one line per hit — `file:line: Y<n> what — fix` — then a count and how many UI files it read, by kind; a named
file that cannot be read or has no UI extension is said and not counted, and reading none is said plainly. A
whole-tree run over BASELINE exits 1; a run on named files exits 1 on any hit. Python 3.9+, standard library only.
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
C_EXT = {".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx"}  # Embedded (ESP-IDF, LVGL): Y8
UI_EXT = WEB_EXT | NATIVE_EXT | C_EXT
SKIP_DIRS = ("node_modules/", "vendor/", "third_party/", "build/", "dist/", "out/", "coverage/", ".cache/", ".venv/",
             "Pods/", "managed_components/", ".agents/", ".claude/", ".codex/", ".github/")

FONT_PX = re.compile(r"(?<![-\w])font-size\s*:\s*\d+(?:\.\d+)?px\b|(?<![\w-])text-\[\d+(?:\.\d+)?px\]"
                     r"|(?<![-\w])font\s*:\s*(?:[\w-]+\s+)*?\d+(?:\.\d+)?px\b"
                     r"|\bfontSize\s*:\s*(?:\d+(?:\.\d+)?\s*[,}\n]|[`'\"]\d+(?:\.\d+)?px[`'\"])")
# a custom property that carries a font size in px — the usual route for a role token on the web
FONT_VAR_PX = re.compile(r"--((?:font|text|type)[\w-]*)\s*:\s*\d+(?:\.\d+)?px\b")
NOT_SIZE = re.compile(r"line|leading|letter|tracking|spacing|radius|gap|weight|offset|indent|shadow|stroke|width"
                      r"|measure|column|max|min|container")
LINE_PX = re.compile(r"(?<![-\w])line-height\s*:\s*\d+(?:\.\d+)?px\b|(?<![\w-])leading-\[\d+(?:\.\d+)?px\]")
ANDROID_FIXED = re.compile(r"android:textSize\s*=\s*\"\d+(?:\.\d+)?(?:dp|dip|px)\"|\bCOMPLEX_UNIT_(?:DIP|PX)\b"
                           r"|\.dp\.toSp\(\)")
SWIFT_FIXED = re.compile(r"\.system\(\s*size\s*:|\.custom\([^)\n]*\bsize\s*:")
UIKIT_FIXED = re.compile(r"\bUIFont\.(?:systemFont|boldSystemFont|monospacedSystemFont)\(\s*ofSize\s*:"
                         r"|\bUIFont\(\s*name\s*:[^)\n]*\bsize\s*:")
JUSTIFY = re.compile(r"(?<![-\w])text-align\s*:\s*justify\b|\btextAlign\s*:\s*[`'\"]justify\b"
                     r"|(?<![\w-])text-justify\b(?!\s*:)")
LIGHT = re.compile(r"(?<![-\w])font-weight\s*:\s*(?:[123]00|lighter)\b|(?<![\w-])font-(?:thin|extralight|light)\b"
                   r"|\bsans-serif-(?:light|thin)\b|\bFontWeight\.w[123]00\b"
                   r"|\b(?:fontWeight|weight)\s*[(:]\s*\.(?:ultraLight|thin|light)\b|\bFontWeight\.(?:Thin|ExtraLight|Light)\b")
UPPER = re.compile(r"(?<![-\w])text-transform\s*:\s*uppercase\b|\btextTransform\s*:\s*[`'\"]uppercase\b")
UPPER_CLASS = re.compile(r"(?<![\w-])uppercase(?![\w-])")  # a utility class, read only in a class list
# what opens a class value: a class attribute, or a class-joining helper's call
CLASS_OPEN = re.compile(r"(?:\bclass(?:Name)?\s*=\s*\{?\s*|\b(?:clsx|classnames|cn|cva|twMerge)\s*\([^)]*|\btw)$")
SPACED = re.compile(r"letter-spacing\s*:|\bletterSpacing\s*:|(?<![\w-])tracking-")
HYPHENATED = re.compile(r"\bhyphens\s*:\s*[`'\"]?auto\b|(?<![\w-])hyphens-auto\b")
# a built-in font set on one object; a shared style (`lv_style_set_text_font`) built from the brief is the place for it
LV_FONT = re.compile(r"\blv_obj_set_style_text_font\s*\([^;]*?&\s*lv_font_(?:montserrat|unscii|dejavu|simsun"
                     r"|source_han_sans)_\w+")

C_TOKENS = re.compile(r"\"(?:\\.|[^\"\\\n])*\"|'(?:\\.|[^'\\\n])*'|/\*.*?(?:\*/|\Z)|//[^\n]*", re.S)


def blank_c_comments(text: str) -> str:
    """The text with C and C++ comments turned to spaces, newlines kept, so positions and line numbers still hold.
    Strings and character literals are read first and kept, so a `/*` or `//` inside one opens no comment."""
    def blank(m: re.Match) -> str:
        token = m.group(0)
        return token if token[0] in "\"'" else re.sub(r"[^\n]", " ", token)
    return C_TOKENS.sub(blank, text)


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


def context(text: str, pos: int) -> str:
    """The CSS rule around pos, or the quoted class list or line it sits in."""
    start, end = text.rfind("{", 0, pos), text.find("}", pos)
    if start != -1 and text.rfind("}", 0, pos) < start and end != -1:
        return text[start:end]
    line_start = text.rfind("\n", 0, pos) + 1
    line_end = text.find("\n", pos)
    line = text[line_start:line_end if line_end != -1 else len(text)]
    col = pos - line_start
    quotes = [m for m in re.finditer(r"[`'\"][^`'\"\n]*[`'\"]", line) if m.start() <= col < m.end()]
    return quotes[0].group(0) if quotes else line


def in_class_list(text: str, pos: int) -> bool:
    """Whether pos sits inside a quoted class value — a class attribute's, or a class-joining helper's argument."""
    start = text.rfind("\n", 0, pos) + 1
    end = text.find("\n", pos)
    line = text[start:end if end != -1 else len(text)]
    col = pos - start
    for q in re.finditer(r"[`'\"][^`'\"\n]*[`'\"]", line):
        if q.start() < col < q.end():
            return bool(CLASS_OPEN.search(line[:q.start()]))
    return False


def web_native_hits(name: str, text: str):
    """Y1–Y7 in one web or native file's text: (position, message)."""
    suffix = Path(name).suffix
    if suffix in WEB_EXT:
        for m in FONT_PX.finditer(text):
            yield (m.start(), "Y1 a font size in px ignores the browser's text size — rem, from the brief's role "
                              "(TYPOGRAPHY §11)")
        for m in FONT_VAR_PX.finditer(text):
            if not NOT_SIZE.search(m.group(1)):
                yield (m.start(), "Y1 a font-size token in px ignores the browser's text size — rem (TYPOGRAPHY §11)")
        for m in LINE_PX.finditer(text):
            yield (m.start(), "Y2 a line height in px does not grow with the text — a unitless ratio from the role "
                              "(TYPOGRAPHY §6)")
        for m in JUSTIFY.finditer(text):
            if not HYPHENATED.search(context(text, m.start())):
                yield (m.start(), "Y5 justified text without hyphenation opens rivers of space — start-aligned, or "
                                  "hyphens: auto with the language set (TYPOGRAPHY §7)")
        uppers = list(UPPER.finditer(text)) + [m for m in UPPER_CLASS.finditer(text) if in_class_list(text, m.start())]
        for m in uppers:
            if not SPACED.search(context(text, m.start())):
                yield (m.start(), "Y7 capitals with no letter spacing — add the role's tracking for capitals "
                                  "(TYPOGRAPHY §6, §8)")
    if suffix in (".xml", ".kt", ".java"):
        for m in ANDROID_FIXED.finditer(text):
            yield (m.start(), "Y3 text sized in dp or px ignores the person's font scale — sp, from the brief's role "
                              "(TYPOGRAPHY §11)")
    if suffix == ".swift":
        lines = text.split("\n")
        for m in SWIFT_FIXED.finditer(text):
            line = lines[line_of(text, m.start()) - 1]
            if "relativeTo" not in line and not (m.group(0).startswith(".system") and "@ScaledMetric" in text):
                yield (m.start(), "Y4 a fixed font size ignores Dynamic Type — a text style, a custom font with "
                                  "relativeTo:, or a size from @ScaledMetric (TYPOGRAPHY §11)")
        if "UIFontMetrics" not in text:
            for m in UIKIT_FIXED.finditer(text):
                yield (m.start(), "Y4 a fixed UIFont size ignores Dynamic Type — a text style, or UIFontMetrics' "
                                  "scaledFont (TYPOGRAPHY §11)")
    if suffix in WEB_EXT or suffix in NATIVE_EXT:
        for m in LIGHT.finditer(text):
            yield (m.start(), "Y6 a light weight is hard to read at text sizes — Regular or heavier; display text "
                              "takes a typography-exception (TYPOGRAPHY §8)")


def lvgl_hits(text: str):
    """Y8 in one C or C++ file's text: (position, message)."""
    for m in LV_FONT.finditer(blank_c_comments(text)):
        yield (m.start(), "Y8 one of LVGL's built-in fonts named on a screen — the role's font from the brief's header "
                          "(TYPOGRAPHY §12)")


def scan_text(name: str, text: str) -> list[tuple[int, str]]:
    """Every hit in one file's text: (line, message)."""
    lines = text.split("\n")  # as line_of counts: splitlines would also break at a form feed and shift every line
    hits: list[tuple[int, str]] = []
    found = lvgl_hits(text) if Path(name).suffix in C_EXT else web_native_hits(name, text)
    for pos, msg in found:
        n = line_of(text, pos)
        if not (0 < n <= len(lines) and "typography-exception" in lines[n - 1]):
            hits.append((n, msg))
    return sorted(set(hits))


def self_test() -> int:
    cases = [
        ("a.css", ".a { font-size: 14px; }", ["Y1"]),
        ("b.css", ".a { font-size: 0.875rem; line-height: 1.43; }", []),
        ("c.tsx", '<p className="text-[13px]">', ["Y1"]),
        ("d.tsx", "const s = { fontSize: 14, color: c }", ["Y1"]),
        ("e.tsx", "const s = { fontSize: '1rem' }", []),
        ("f.css", ".a { line-height: 20px; }", ["Y2"]),
        ("g.tsx", '<p className="leading-[20px]">', ["Y2"]),
        ("h.xml", '<TextView android:textSize="14dp" />', ["Y3"]),
        ("i.xml", '<TextView android:textSize="14sp" />', []),
        ("j.kt", "view.setTextSize(TypedValue.COMPLEX_UNIT_DIP, 14f)", ["Y3"]),
        ("k.kt", "Text(\"a\", fontSize = 14.sp)", []),
        ("l.swift", "Text(\"a\").font(.system(size: 17))", ["Y4"]),
        ("m.swift", "Text(\"a\").font(.custom(\"Inter\", size: 17, relativeTo: .body))", []),
        ("n.swift", "Text(\"a\").font(.custom(\"Inter\", size: 17))", ["Y4"]),
        ("o.swift", "label.font = UIFont.systemFont(ofSize: 15)", ["Y4"]),
        ("p.swift", "label.font = UIFontMetrics(forTextStyle: .body).scaledFont(for: UIFont(name: \"Inter\", size: 17)!)",
         []),
        ("q.swift", "Text(\"a\").font(.body)", []),
        ("r.css", ".a { text-align: justify; }", ["Y5"]),
        ("s.css", ".a { text-align: justify; hyphens: auto; }", []),
        ("t.tsx", '<p className="text-justify hyphens-auto">', []),
        ("u.css", ".a { font-weight: 300; }", ["Y6"]),
        ("v.css", ".a { font-weight: 300; } /* typography-exception: the display number at 64 px */", []),
        ("w.swift", "Text(\"a\").fontWeight(.light)", ["Y6"]),
        ("x.kt", "Text(\"a\", fontWeight = FontWeight.Light)", ["Y6"]),
        ("y.tsx", '<p className="font-light">', ["Y6"]),
        ("z.css", ".a { font-weight: 400; }", []),
        ("aa.css", ".eyebrow { text-transform: uppercase; }", ["Y7"]),
        ("ab.css", ".eyebrow { text-transform: uppercase; letter-spacing: 0.08em; }", []),
        ("ac.tsx", '<span className="uppercase text-xs">', ["Y7"]),
        ("ad.tsx", '<span className="uppercase tracking-wider">', []),
        ("ae.tsx", "const t = s.toUpperCase()", []),
        ("af.swift", "Text(\"a\").font(.title).bold()", []),
        ("ag.swift", "view.preferredColorScheme(.light)", []),
        ("ai.ts", "const hint = 'Include an uppercase letter'", []),
        ("aj.tsx", "const s = { textTransform: 'uppercase', letterSpacing: 1 }", []),
        ("ak.tsx", "const s = { textTransform: 'uppercase' }", ["Y7"]),
        ("al.tsx", '<span className="md:uppercase">', ["Y7"]),
        ("am.tsx", '<span className={cn("uppercase", "tracking-wide")}>', []),
        ("an.tsx", '<p className="sm:font-light md:text-justify">', ["Y5", "Y6"]),
        ("ao.css", ".a { text-justify: inter-word; }", []),
        ("ap.css", ".a { font: 14px/1.4 system-ui; }", ["Y1"]),
        ("aq.css", ":root { --text-body: 14px; --text-body-line: 20px; --font-size-sm: 0.875rem; }", ["Y1"]),
        ("ar.swift", "@ScaledMetric var size: CGFloat = 17\nText(\"a\").font(.system(size: size))", []),
        ("as.xml", '<TextView android:fontFamily="sans-serif-light" />', ["Y6"]),
        ("at.dart", "TextStyle(fontWeight: FontWeight.w300)", ["Y6"]),
        ("au.css", ".a { font-weight: lighter; }", ["Y6"]),
        ("av.tsx", '<p className="text-lg">Add uppercase and number</p>', []),
        ("aw.css", ".g { font: 1rem/20px sans-serif; }", []),
        ("ax.css", ".g { font: 600 14px/1.4 system-ui; }", ["Y1"]),
        ("ay.css", ":root { --text-measure: 640px; }", []),
        ("ah.swift", "Text(\"a\").font(.system(.body, weight: .thin))", ["Y6"]),
        # Embedded (ESP-IDF, LVGL)
        ("ba.c", "lv_obj_set_style_text_font(label, &lv_font_montserrat_14, 0);", ["Y8"]),
        ("bb.c", "lv_obj_set_style_text_font(label, TEXT_BODY_FONT, 0);", []),
        ("bc.h", "#define TEXT_BODY_FONT (&lv_font_montserrat_16)", []),
        ("bd.c", "// lv_obj_set_style_text_font(l, &lv_font_montserrat_14, 0);\nlv_obj_set_style_text_font(l, kTitle, 0);",
         []),
        ("be.c", "lv_obj_set_style_text_font(l, &lv_font_montserrat_28, 0);  // typography-exception: the boot splash",
         []),
        ("bg.c", "lv_style_set_text_font(&style_title, &lv_font_montserrat_28);", []),
        ("bf.c", "const char *k = \"font-size: 14px\";", []),
    ]
    bad = 0
    for name, text, want in cases:
        got = sorted(msg.split()[0] for _, msg in scan_text(name, text))
        if got != sorted(want):
            bad += 1
            print(f"FAIL {name}: want {want}, got {got}")
    globs = [("components/ui_toast/toast.cpp", ("components/ui_*/",), True),
             ("components/audio/a.cpp", ("components/ui_*/",), False)]
    for path, patterns, want in globs:
        if matches(path, patterns) != want:
            bad += 1
            print(f"FAIL matches({path!r}, {patterns}): want {want}")
    with tempfile.TemporaryDirectory() as tmp:
        good = Path(tmp, "ok.c")
        good.write_text("lv_obj_set_style_text_font(label, TEXT_BODY_FONT, 0);\n")
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
    print(f"typography_check self-test: {total - bad}/{total} passed")
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
    out.append(f"Y1–Y8 typography patterns — {len(hits)} hits in {len(read)} UI files ({by_kind})"
               + ("" if named else f" (baseline {BASELINE})"))
    if not read:
        why = ("no named file is a readable UI file" if named
               else "UI_PATHS in .agents/project.py is empty or matches no file" if ui_patterns() is not None
               else "no tracked file has a UI extension")
        out.append(f"read no UI files — nothing was checked: {why}")
    if len(hits) > limit:
        out.append("FAIL — fix each hit, or mark a sanctioned one `typography-exception` with its reason")
        return out, 1
    return out, 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
