#!/usr/bin/env python3
"""The accessibility skill's check: patterns in UI files that break a floor in references/criteria.md (cited
`ACCESSIBILITY §n`) whatever the screen looks like. It finds what a pattern can show; the walks find the rest.

    python3 .agents/skills/accessibility/scripts/a11y_check.py            # every UI file, against the baseline
    python3 .agents/skills/accessibility/scripts/a11y_check.py FILE …     # some files, no baseline
    python3 .agents/skills/accessibility/scripts/a11y_check.py --test     # the self-test

Which files: in a repo with the agent-harness kit, UI_PATHS from `.agents/project.py` (empty there means none yet);
in any other repo, every tracked file with a UI extension — web, iOS, Android, Flutter, and C or C++ for firmware
drawn with LVGL — outside vendored and generated folders. A line that carries `a11y-exception` is skipped — write the
reason beside it, and in the project's design brief when it has one.

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
      (a whole-tree run only; in C and C++, only LVGL's lv_anim, fades
      and style transitions count as animation)
  A10 LVGL: an outline or border set to width 0 or transparent on        WCAG 2.4.7   ACCESSIBILITY §5
      LV_STATE_FOCUSED or LV_STATE_FOCUS_KEY, in a file that styles focus
      nowhere else
  A11 LVGL: text dimmed with text_opa between transparent and cover      WCAG 1.4.3   ACCESSIBILITY §2
      (LV_STATE_DISABLED, a style named for it, and a value held in a
      variable are not caught)
  A12 LVGL: an encoder or keypad input and no lv_indev_set_group         WCAG 2.1.1   ACCESSIBILITY §5
      anywhere — the input reaches nothing (a whole-tree run only; LVGL 9's
      lv_indev_set_type, LVGL 8's .type field, esp_lvgl_port's encoder,
      navigation buttons and USB keyboard)

What it cannot see: A1 and A10 are file-level (one focus style anywhere in the file clears them); A9 and A12 are
tree-level (one reduced-motion branch, one group bound anywhere clears them); A10 and A11 read only direct
lv_obj_set_style_* and lv_style_set_text_opa calls with literal values, so a style built in one place and added for a
focus state in another passes; A4–A7 read web markup only and A8 Android XML only, so Swift and Kotlin views get A1–A3
and A9 at most and C and C++ get A9–A12; comments and strings are scanned like code. An action bound to LVGL's
LV_EVENT_PRESSED is not flagged — the same event rightly carries press feedback — so the walks find it. A pass is a
floor, never a review.

Prints one line per hit — `file:line: A<n> what — fix` — then a count with how many UI files it read; a run that read
none says so. A named file that is not a UI file is skipped, and one that does not exist is reported as unreadable.
A whole-tree run over BASELINE exits 1; a run on named files exits 1 on any hit. Reading no UI file is reported, not
failed. Python 3.9+, standard library only.
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
C_EXT = {".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx"}  # firmware drawn with LVGL
UI_EXT = {".html", ".htm", ".css", ".scss", ".sass", ".less", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".vue", ".svelte",
          ".astro", ".erb", ".liquid", ".hbs", ".njk", ".swift", ".kt", ".java", ".dart", ".xml"} | C_EXT
SKIP_DIRS = ("node_modules/", "vendor/", "third_party/", "build/", "dist/", "out/", "coverage/", ".cache/", ".venv/",
             "Pods/", "managed_components/", ".agents/", ".claude/", ".codex/", ".github/")
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
# C and C++ get only LVGL's animation calls: the web and native patterns above match ordinary C (`motion.ax`,
# a bit-field named `animation`).
LV_ANIMATES = re.compile(r"\blv_anim_start\s*\(|\blv_anim_timeline_start\s*\(|\blv_obj_fade_(?:in|out)\s*\(|"
                         r"\blv_style_transition_dsc_init\s*\(")
# A device with no system setting reads the product's own (ACCESSIBILITY §8), named however the code names it.
REDUCED = re.compile(r"prefers-reduced-motion|useReducedMotion|accessibilityReduceMotion|isReduceMotionEnabled|"
                     r"reduceMotion|ANIMATOR_DURATION_SCALE|animatorDurationScale|areAnimatorsEnabled|motion-safe|"
                     r"motion-reduce|disableAnimations|reduced?_motion|Reduced?Motion")
# LVGL (ACCESSIBILITY §2, §5): direct style calls, read argument by argument.
LV_FOCUS_OFF = re.compile(r"\blv_obj_set_style_(?:outline|border)_(?:width|opa)\s*\(")
LV_FOCUS_STYLE = re.compile(r"\blv_obj_(?:set_style_\w+|add_style)\s*\(")
LV_TEXT_OPA = re.compile(r"\blv_(?:obj_set_style|style_set)_text_opa\s*\(")
# An encoder or keypad: LVGL 9's setter, LVGL 8's lv_indev_drv_t field, esp_lvgl_port's knob, buttons and USB keyboard.
LV_KEY_INPUT = re.compile(r"\blv_indev_set_type\s*\([^;]*?\bLV_INDEV_TYPE_(?:ENCODER|KEYPAD)\b|"
                          r"\.\s*type\s*=\s*LV_INDEV_TYPE_(?:ENCODER|KEYPAD)\b|"
                          r"\blvgl_port_add_(?:encoder|navigation_buttons|usb_hid_keyboard_input)\s*\(")
LV_GROUP_BOUND = re.compile(r"\blv_indev_set_group\s*\(")
FOCUS_STATE = re.compile(r"\bLV_STATE_FOCUS(?:ED|_KEY)\b")
OPA = {"LV_OPA_TRANSP": 0, "LV_OPA_COVER": 255, "LV_OPA_MIN": 2, "LV_OPA_MAX": 253,
       **{f"LV_OPA_{n}": n * 255 // 100 for n in range(0, 101, 10)}}


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


def call_args(text: str, open_paren: int) -> list[str]:
    """The top-level arguments of the C call whose `(` is at `open_paren`, stripped; nested parentheses and string
    literals stay inside their argument."""
    args, depth, quote, start, i = [], 0, "", open_paren + 1, open_paren + 1
    while i < len(text):
        c = text[i]
        if quote:
            if c == "\\":
                i += 1
            elif c == quote:
                quote = ""
        elif c in "\"'":
            quote = c
        elif c in "([{":
            depth += 1
        elif c in ")]}":
            if depth == 0:
                args.append(text[start:i].strip())
                return args
            depth -= 1
        elif c == "," and depth == 0:
            args.append(text[start:i].strip())
            start = i + 1
        i += 1
    return args


def opa_value(arg: str) -> int | None:
    """A literal opacity — an LV_OPA_* name or a number — or None for anything computed."""
    if arg in OPA:
        return OPA[arg]
    try:
        return int(arg.rstrip("uU"), 0)
    except ValueError:
        return None


def ui_patterns() -> tuple | None:
    """UI_PATHS from the kit's settings, or None when the repo has no kit."""
    settings = ROOT / ".agents/project.py"
    if not settings.is_file():
        return None
    sys.path.insert(0, str(settings.parent))
    import project  # noqa: E402 — the kit's settings
    return tuple(getattr(project, "UI_PATHS", ()))


def matches(path: str, patterns) -> bool:
    """A path in UI_PATHS: a folder ending in `/` (a glob one like `components/ui_*/` too), a glob, or the path."""
    def one(p: str) -> bool:
        glob = any(c in p for c in "*?[")
        if p.endswith("/"):
            return path.startswith(p) or (glob and fnmatch.fnmatch(path, p + "*"))
        return (glob and fnmatch.fnmatch(path, p)) or path == p
    return any(one(p) for p in patterns)


def sort_named(names: list[str], root: Path) -> tuple[list[str], list[str], list[str]]:
    """Named files split into those to scan, those with no UI extension, and those that cannot be read."""
    ui, other, missing = [], [], []
    for f in names:
        (missing if not (root / f).is_file() else ui if Path(f).suffix in UI_EXT else other).append(f)
    return ui, other, missing


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
    lines = text.split("\n")  # the same breaks line_of counts; splitlines also breaks on \f, \v and \x1c–\x1e
    hits: list[tuple[int, str]] = []

    def add(n: int, msg: str) -> None:
        if not (0 < n <= len(lines) and "a11y-exception" in lines[n - 1]):
            hits.append((n, msg))

    if ext in C_EXT:
        scan_lvgl(text, add)
        return hits
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


def scan_lvgl(text: str, add) -> None:
    """A10 and A11 in one C or C++ file: LVGL style calls, each read argument by argument."""
    removed, replaced = [], False
    for m in LV_FOCUS_STYLE.finditer(text):
        args = call_args(text, m.end() - 1)
        if len(args) < 3 or not FOCUS_STATE.search(args[-1]):
            continue
        value = opa_value(args[1])
        off = value is not None and (value == 0 or ("_opa" in m.group(0) and value <= OPA["LV_OPA_MIN"]))
        if LV_FOCUS_OFF.match(text, m.start()) and off:
            removed.append(line_of(text, m.start()))
        else:
            replaced = True
    if not replaced:
        for n in removed:
            add(n, "A10 the focus outline or border removed and focus styled nowhere else in this file — give "
                   "LV_STATE_FOCUSED and LV_STATE_FOCUS_KEY a replacement at 3:1 (WCAG 2.4.7, ACCESSIBILITY §5)")
    for m in LV_TEXT_OPA.finditer(text):
        args = call_args(text, m.end() - 1)
        if len(args) < 2:  # a call cut off by the end of the file
            continue
        value = opa_value(args[1])
        disabled = ("LV_STATE_DISABLED" in (args[2] if len(args) > 2 else "")
                    or bool(re.search(r"disab|_dis\b", args[0], re.I)))  # a style named for the disabled state
        if value is not None and OPA["LV_OPA_MIN"] < value < OPA["LV_OPA_MAX"] and not disabled:
            add(line_of(text, m.start()), "A11 text dimmed with text_opa — paint it a colour whose value passes "
                                          "4.5:1, and keep opacity for disabled text (WCAG 1.4.3, ACCESSIBILITY §2)")


def tree_scan(texts: list[tuple[str, str]]) -> list[str]:
    """The whole-tree rules, A9 and A12: each needs the absence of something anywhere in the UI, so they run only on a
    whole-tree pass, where the clearing line may sit in a file a change did not touch."""
    found: dict[str, str] = {}
    cleared = {"A9": False, "A12": False}
    for f, text in texts:
        animates = LV_ANIMATES if Path(f).suffix in C_EXT else ANIMATES
        for rule, pattern in (("A9", animates), ("A12", LV_KEY_INPUT)):
            m = None if rule in found else pattern.search(text)
            if m and "a11y-exception" not in text.split("\n")[line_of(text, m.start()) - 1]:
                found[rule] = f"{f}:{line_of(text, m.start())}"
        cleared["A9"] = cleared["A9"] or bool(REDUCED.search(text))
        cleared["A12"] = cleared["A12"] or bool(LV_GROUP_BOUND.search(text))
    out = []
    if "A9" in found and not cleared["A9"]:
        out.append(f"{found['A9']}: A9 the UI animates and no file handles reduced motion — follow the person's "
                   f"setting: the platform's, or the product's own where the platform has none "
                   f"(WCAG 2.3.3, ACCESSIBILITY §8)")
    if "A12" in found and not cleared["A12"]:
        out.append(f"{found['A12']}: A12 an encoder or keypad input and no lv_indev_set_group anywhere — it reaches "
                   f"no control; bind each screen's group to it (WCAG 2.1.1, ACCESSIBILITY §5)")
    return out


def scan(files: list[str], whole: bool = True) -> list[str]:
    """The hits in these files; A9 and A12 only on a whole-tree run."""
    out, texts = [], []
    for f in files:
        try:
            text = (ROOT / f).read_text(errors="replace")
        except OSError:
            continue
        out += [f"{f}:{n}: {msg}" for n, msg in sorted(scan_text(f, text))]
        texts.append((f, text))
    return out + (tree_scan(texts) if whole else [])


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
        # C and C++: only the LVGL rules; a CSS-looking comment is not read as CSS.
        ("ae.c", "/* outline: none; maximum-scale=1 */", []),
        ("af.c", "lv_obj_set_style_outline_width(btn, 0, LV_PART_MAIN | LV_STATE_FOCUS_KEY);", ["A10"]),
        ("ag.cpp", "lv_obj_set_style_border_opa(row,\n    LV_OPA_TRANSP, LV_STATE_FOCUSED);", ["A10"]),
        ("ah.c", "lv_obj_set_style_outline_width(btn, 0, LV_STATE_FOCUS_KEY);\n"
                 "lv_obj_set_style_bg_color(btn, color_focus(), LV_STATE_FOCUS_KEY);", []),
        ("ai.c", "lv_obj_set_style_border_width(card, 0, LV_PART_MAIN);", []),
        ("aj.c", "lv_obj_set_style_outline_width(btn, 0, LV_STATE_FOCUSED); /* a11y-exception: ring is a child */",
         []),
        ("ak.c", "lv_obj_set_style_text_opa(hint, LV_OPA_60, 0);\nlv_style_set_text_opa(&st_caption, 150);",
         ["A11", "A11"]),
        ("al.cpp", "lv_obj_set_style_text_opa(label, LV_OPA_COVER, 0);\n"
                   "lv_obj_set_style_text_opa(btn, LV_OPA_50, LV_PART_MAIN | LV_STATE_DISABLED);\n"
                   "lv_style_set_text_opa(&st_disabled, LV_OPA_40);\n"
                   "lv_style_set_text_opa(&style_button_dis, LV_OPA_40);\n"
                   "lv_obj_set_style_text_opa(label, (lv_opa_t)v, 0);\n"
                   "lv_obj_set_style_text_opa(label, LV_OPA_TRANSP, 0);", []),
        # A call cut off by the end of the file reads as nothing, not a crash.
        ("am.c", "/* see lv_obj_set_style_text_opa(", []),
        ("am2.c", "lv_style_set_text_opa(&s", []),
        ("am3.c", "lv_obj_set_style_outline_width(btn, 0", []),
        # A form feed is not a line break for line numbers, so the marker on the hit's line is still found.
        ("an.c", "/* \f */\nlv_obj_set_style_text_opa(l, LV_OPA_50, 0); /* a11y-exception: decorative */", []),
        ("an2.c", "/* \f */\nlv_obj_set_style_text_opa(l, LV_OPA_50, 0);", ["A11"]),
    ]
    bad = 0
    for name, text, want in cases:
        got = sorted(msg.split()[0] for _, msg in scan_text(name, text))
        if got != sorted(want):
            bad += 1
            print(f"FAIL {name}: want {want}, got {got}")
    # A9 and A12 are whole-tree: what clears them may sit in any file.
    tree = [([("r.css", ".menu { transition: opacity 200ms; }")], ["A9"]),
            ([("s0.css", ".menu { transition: none; animation: none; }")], []),
            ([("s.css", ".menu { transition: opacity 200ms; }\n@media (prefers-reduced-motion: reduce) { .menu { "
                        "transition: none; } }")], []),
            ([("anim.c", "lv_anim_start(&a);")], ["A9"]),
            ([("anim.c", "lv_anim_start(&a);"), ("settings.c", "if (settings.reduce_motion) { duration = 0; }")], []),
            ([("input.c", "lv_indev_set_type(indev, LV_INDEV_TYPE_ENCODER);")], ["A12"]),
            ([("input.c", "lv_indev_t *knob = lvgl_port_add_encoder(&cfg);")], ["A12"]),
            ([("input.c", "lv_indev_set_type(indev, LV_INDEV_TYPE_ENCODER);"),
              ("screen.c", "lv_indev_set_group(indev, group);")], []),
            ([("touch.c", "lv_indev_set_type(indev, LV_INDEV_TYPE_POINTER);")], []),
            # C and C++ take only LVGL's animation calls for A9; a web file still takes the web patterns.
            ([("imu.cpp", "float v = motion.ax;\nx.animate(1);\nstruct s { int animation: 3; };")], []),
            ([("a.ts", "el.animate(frames, 200);")], ["A9"]),
            # A12 knows LVGL 8's driver field and esp_lvgl_port's USB keyboard.
            ([("in8.c", "indev_drv.type = LV_INDEV_TYPE_ENCODER;")], ["A12"]),
            ([("in8.c", "indev_drv.type = LV_INDEV_TYPE_POINTER;")], []),
            ([("hid.c", "lv_indev_t *kb = lvgl_port_add_usb_hid_keyboard_input(&cfg);")], ["A12"]),
            ([("hid.c", "lv_indev_t *m = lvgl_port_add_usb_hid_mouse_input(&cfg);")], [])]
    for texts, want in tree:
        got = sorted(line.split()[1] for line in tree_scan(texts))
        if got != sorted(want):
            bad += 1
            print(f"FAIL {[f for f, _ in texts]}: want {want}, got {got}")
    # UI_PATHS: a folder pattern with a glob matches the files beneath it.
    paths = [("components/ui_theme/theme.cpp", ("components/ui_*/",), True),
             ("components/ui_theme/sub/x.c", ("components/ui_*/",), True),
             ("components/core/main.c", ("components/ui_*/",), False),
             ("src/app.tsx", ("src/",), True),
             ("src/app.tsx", ("src/*.tsx",), True),
             ("lib/app.tsx", ("src/",), False)]
    for path, patterns, want in paths:
        if matches(path, patterns) != want:
            bad += 1
            print(f"FAIL matches({path!r}, {patterns}): want {want}")
    # Named files: a non-UI file is skipped, a missing one cannot be read, a UI file is scanned.
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "README.md").write_text("# x")
        (Path(tmp) / "ui.cpp").write_text("")
        got = sort_named(["README.md", "ui.cpp", "gone.cpp"], Path(tmp))
        if got != (["ui.cpp"], ["README.md"], ["gone.cpp"]):
            bad += 1
            print(f"FAIL sort_named: got {got}")
    total = len(cases) + len(tree) + len(paths) + 1
    print(f"a11y_check self-test: {total - bad}/{total} passed")
    return 1 if bad else 0


def main(argv: list[str]) -> int:
    if argv[:1] == ["--test"]:
        return self_test()
    named = bool(argv)
    files, other, missing = sort_named(argv, ROOT) if named else (ui_files(), [], [])
    for f in other:
        print(f"{f}: skipped — not a UI file")
    for f in missing:
        print(f"{f}: cannot be read")
    hits = scan(files, whole=not named)
    for h in hits:
        print(h)
    limit = 0 if named else BASELINE
    read = len(files)
    print(f"A1–A12 accessibility patterns — {len(hits)} hits in {read} UI files read"
          + ("" if named else f" (baseline {BASELINE})"))
    if not read:
        why = ("none of the named files is a UI file that can be read" if named
               else "UI_PATHS in .agents/project.py matches no file" if ui_patterns() is not None
               else "no tracked file has a UI extension")
        print(f"NOTHING CHECKED — read no UI file: {why}. A pass here says nothing about the UI.")
    if len(hits) > limit:
        print("FAIL — fix each hit, or mark a sanctioned one `a11y-exception` with its reason")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
