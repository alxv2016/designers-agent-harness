#!/usr/bin/env python3
"""The touch-and-gesture skill's check: patterns in UI files that break touch, gestures or layout, from
references/touch.md (cited `TOUCH §n`). It finds what a pattern shows; the device walk finds the rest.

    python3 .agents/skills/touch-and-gesture/scripts/touch_check.py            # every UI file, against the baseline
    python3 .agents/skills/touch-and-gesture/scripts/touch_check.py FILE …     # some files, no baseline
    python3 .agents/skills/touch-and-gesture/scripts/touch_check.py --test     # the self-test

Which files: in a repo with the agent-harness kit, UI_PATHS from `.agents/project.py` (empty there means none yet);
in any other repo, every tracked file with a UI extension outside vendored and generated folders (`managed_components/`
among them). A line that carries `touch-exception` is skipped — write the reason beside it (a canvas, map, slider or
drag handle that takes every gesture, with its plain alternative named).

Web files (CSS, markup, scripts):
  T1  a surface that claims every axis (`touch-action: none`, `touch-none`, `touchAction = 'none'`)   TOUCH §2
  T2  a height on `100vh` (`height`, `minHeight`, `--var`, `h-screen`, `h-[100vh]`) in a file with no `dvh`, `svh` or
      `-webkit-fill-available`   TOUCH §7
  T3  a text field (input, textarea, contenteditable) that takes focus unasked (`autofocus`, `autoFocus`)   TOUCH §7
  T4  selection off for the whole page (html, body, :root, *, #root — CSS, `@apply`, or a body class)   TOUCH §5
  T5  the tap highlight removed in a file that draws no pressed style (`:active`, `active:`, `data-[pressed]:`,
      `whileTap`)   TOUCH §5

Embedded files (C and C++ on LVGL 8 or 9 — .c .cc .cpp .cxx .h .hh .hpp .hxx):
  T6  an object whose only press handler in the file is `LV_EVENT_PRESSED` — none for `RELEASED`, `PRESS_LOST`,
      `CLICKED`, `SHORT_CLICKED`, `SINGLE_CLICKED`, `VALUE_CHANGED` or `ALL` — so it acts on touch-down   TOUCH §3
  T7  `LV_EVENT_CLICKED` on an object that also handles `LV_EVENT_LONG_PRESSED` or `_REPEAT` — LVGL sends CLICKED on
      release even after a long press, so the hold does both; use `LV_EVENT_SHORT_CLICKED`   TOUCH §3, §4
  T8  scroll chaining off on both axes of one object (`LV_OBJ_FLAG_SCROLL_CHAIN`, both `_HOR` and `_VER`, or
      `lv_obj_set_scroll_chain(…, false)`) — a drag that starts on it never reaches the scroller behind   TOUCH §2
  T9  scroll momentum or elastic removed (`LV_OBJ_FLAG_SCROLL_MOMENTUM`, `LV_OBJ_FLAG_SCROLL_ELASTIC`, or their
      setters with false) — a fling that stops dead on lift, an end that stops dead   TOUCH §3, §6
  T10 `lv_obj_remove_style_all` on a button the file creates (`lv_button_create`, `lv_btn_create`) in a file where no
      style call (`lv_obj_add_style`, `lv_obj_set_style_*`, `lv_style_*`) names a pressed style (`LV_STATE_PRESSED`, a
      `…Pressed()` selector, a `&…pressed` style) — the theme's pressed state is gone and nothing replaces it
      TOUCH §5

A flag turned off is read from `lv_obj_remove_flag`, LVGL 8's `lv_obj_clear_flag`, and `lv_obj_set_flag` or LVGL
9.0–9.1's `lv_obj_update_flag` with false. An event code is read as every `LV_EVENT_…` token in the argument, so a
cast or `| LV_EVENT_PREPROCESS` does not hide it.

What it cannot see: how a drag feels, whether a gesture claims the right axis, whether a sheet scrolls before it
drags, whether the keyboard covers a field, a `.focus()` call in a script, how often the touch controller is read,
whether every screen works by encoder and buttons — the device walk (TOUCH §9) finds those. T2, T5, T6, T7 and T10
look across one file, so a reset, a fallback, a handler or a style in another file is not seen, and Tailwind's base
styles already remove the tap highlight project-wide. T6, T7, T8 and T10 match an object by the text of its expression
(`btn`, `ui->row[i]`), so the same object under two names is two objects; what a handler for `LV_EVENT_ALL` does is
not read, so T6 lets it stand as a release handler; T10 reads buttons only — a plain `lv_obj` made tappable never had
the theme's pressed style to lose. iOS and Android code is not read. Comments (`/* */`, `<!-- -->`, `//`) are skipped
— in C and C++ a comment opener inside a string or character literal is not one; in web files strings are scanned
like code. T3
reads a tag whose name holds input, textarea, textfield, textinput or searchfield, or one marked contenteditable — a
wrapper named otherwise is not seen. A named file that cannot be read exits 2. A pass is a floor, never a review.

Prints one line per hit — `file:line: T<n> what — fix` — then a count with how many web and C/C++ files it read; a run
that read none says so plainly. A whole-tree run over BASELINE exits 1; a run on named files exits 1 on any hit.
Python 3.9+, standard library only.
"""

from __future__ import annotations

import fnmatch
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip()
            or ".")

# Hits sanctioned today, each with its reason. A new hit on a line you touched is yours to fix.
BASELINE = 0
WEB_EXT = {".html", ".htm", ".css", ".scss", ".sass", ".less", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".vue", ".svelte",
           ".astro", ".erb", ".liquid", ".hbs", ".njk"}
C_EXT = {".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx"}
UI_EXT = WEB_EXT | C_EXT
SKIP_DIRS = ("node_modules/", "vendor/", "third_party/", "build/", "dist/", "out/", "coverage/", ".cache/", ".venv/",
             "Pods/", "managed_components/", ".agents/", ".claude/", ".codex/", ".github/")

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
# In C and C++ a string or character literal is matched before a comment can start inside it, so `"/*"` (an ESP-IDF
# HTTP wildcard URI) blanks nothing; an unterminated block comment runs to the end of the file.
C_COMMENT = re.compile(r"\"(?:\\.|[^\"\\\n])*\"|'(?:\\.|[^'\\\n]){1,8}'|/\*.*?(?:\*/|\Z)|//[^\n]*", re.S)

# LVGL (C and C++). A call is found by name and its arguments split at top-level commas, so a lambda or a nested
# call in an argument stays whole.
LV_CALL = re.compile(r"\b(lv_obj_add_event_cb|lv_obj_remove_flag|lv_obj_clear_flag|lv_obj_set_flag|lv_obj_update_flag"
                     r"|lv_obj_set_scroll_chain(?:_hor|_ver)?|lv_obj_set_scroll_momentum|lv_obj_set_scroll_elastic"
                     r"|lv_obj_remove_style_all)\s*\(")
FLAG_OFF = {"lv_obj_remove_flag", "lv_obj_clear_flag"}  # lv_obj_clear_flag is LVGL 8's name
FLAG_SET = {"lv_obj_set_flag", "lv_obj_update_flag"}    # (obj, flag, bool); lv_obj_update_flag is LVGL 9.0–9.1's name
FALSE = re.compile(r"^(?:false|0)$")
CHAIN_BOTH = re.compile(r"\bLV_OBJ_FLAG_SCROLL_CHAIN\b(?!_)")
EVENT_CODE = re.compile(r"\bLV_EVENT_\w+")  # every code in the argument, so a cast or `| LV_EVENT_PREPROCESS` is read
# A handler that ends a press, or acts on release: beside one of these, LV_EVENT_PRESSED is feedback or a drag's start.
# LV_EVENT_ALL counts: its handler may switch on any code, and the check cannot see which.
RELEASE_EVENTS = {"LV_EVENT_RELEASED", "LV_EVENT_PRESS_LOST", "LV_EVENT_CLICKED", "LV_EVENT_SHORT_CLICKED",
                  "LV_EVENT_SINGLE_CLICKED", "LV_EVENT_VALUE_CHANGED", "LV_EVENT_ALL"}
LONG_EVENTS = {"LV_EVENT_LONG_PRESSED", "LV_EVENT_LONG_PRESSED_REPEAT"}
BUTTON_CREATE = re.compile(r"\blv_(?:button|btn)_create\s*\(")  # lv_btn_create is LVGL 8's name
LHS_CHAR = re.compile(r"[\w.\[\]>-]")
# A pressed style is LV_STATE_PRESSED, a project's selector helper (`Pressed()`) or a style named for it
# (`&st_pressed`), inside a call that adds or sets a style.
STYLE_CALL = re.compile(r"\b(?:lv_obj_add_style|lv_obj_replace_style|lv_obj_set_style_\w+|lv_style_\w+)\s*\(")
PRESSED_STYLE = re.compile(r"\bLV_STATE_PRESSED\b|[Pp]ressed\w*\s*\(\s*\)|&\s*\w*[Pp]ressed\w*")

def ui_patterns() -> tuple | None:
    """UI_PATHS from the kit's settings, or None when the repo has no kit."""
    settings = ROOT / ".agents/project.py"
    if not settings.is_file():
        return None
    sys.path.insert(0, str(settings.parent))
    import project  # noqa: E402 — the kit's settings
    return tuple(getattr(project, "UI_PATHS", ()))


def matches(path: str, patterns) -> bool:
    """A pattern ending in `/` is a folder and takes every file beneath it, globbed (`components/ui_*/`) or not."""
    def one(p: str) -> bool:
        glob = any(c in p for c in "*?[")
        if p.endswith("/"):
            return fnmatch.fnmatch(path, p + "*") if glob else path.startswith(p)
        return fnmatch.fnmatch(path, p) if glob else path == p
    return any(one(p) for p in patterns)


def tracked_files() -> list[str]:
    return subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=ROOT,
                          capture_output=True, text=True).stdout.splitlines()


def in_scope(tracked: list[str], patterns) -> list[str]:
    """The tracked files UI_PATHS names, or with no kit every file outside vendored and generated folders."""
    if patterns is not None:
        return [f for f in tracked if matches(f, patterns)]
    return [f for f in tracked if not f.startswith(SKIP_DIRS) and "/node_modules/" not in f]


def ui_files() -> list[str]:
    return [f for f in in_scope(tracked_files(), ui_patterns()) if Path(f).suffix in UI_EXT and (ROOT / f).is_file()]


def none_read_reason(tracked: list[str], patterns) -> str:
    """Why a whole-tree run read no UI file."""
    if patterns == ():
        return "UI_PATHS in .agents/project.py is empty"
    if patterns and not in_scope(tracked, patterns):
        return "UI_PATHS matches no tracked file"
    if patterns:
        return "UI_PATHS matches tracked files, but none has a UI extension"
    return "no tracked file has a UI extension"


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


def call_args(text: str, open_paren: int) -> list[str]:
    """The arguments of the call whose `(` is at `open_paren`, split at its top-level commas; brackets, braces, string
    and character literals are kept whole."""
    args: list[str] = []
    depth, i, start = 0, open_paren + 1, open_paren + 1
    while i < len(text):
        c = text[i]
        if c in "\"'":
            j = i + 1
            while j < len(text) and text[j] != c:
                j += 2 if text[j] == "\\" else 1
            i = j
        elif c in "([{":
            depth += 1
        elif c in ")]}":
            if depth == 0:
                args.append(text[start:i])
                break
            depth -= 1
        elif c == "," and depth == 0:
            args.append(text[start:i])
            start = i + 1
        i += 1
    return [re.sub(r"\s+", "", a) for a in args]


def scan_text(name: str, text: str) -> list[tuple[int, str]]:
    """Every hit in one file's text: (line, message). Comments are read as blanks, so a note naming a pattern never
    counts; a `touch-exception` marker in a comment still does. C and C++ files get the LVGL rules, every other file
    the web rules."""
    lines = text.split("\n")  # the same breaks line_of counts; splitlines() also breaks on \f and \r and shifts them
    is_c = Path(name).suffix in C_EXT
    blank = lambda m: re.sub(r"[^\n]", " ", m.group())  # noqa: E731
    if is_c:
        code = C_COMMENT.sub(lambda m: blank(m) if m.group().startswith("/") else m.group(), text)
    else:
        code = COMMENT.sub(blank, text)
    hits: list[tuple[int, str]] = []

    def add(pos: int, msg: str) -> None:
        n = line_of(text, pos)
        if not (0 < n <= len(lines) and "touch-exception" in lines[n - 1]):
            hits.append((n, msg))

    if is_c:
        scan_lvgl(code, add)
    else:
        scan_web(code, add)
    return sorted(hits)


def scan_lvgl(code: str, add) -> None:
    """T6–T10: the LVGL patterns in one C or C++ file, comments already blanked."""
    events: dict[str, list[tuple[int, set]]] = {}   # object expression → (position, event codes) per handler
    chain_off: dict[str, list[tuple[int, str]]] = {}  # object expression → (position, axis) per chain turned off
    unstyled: list[tuple[int, str]] = []             # (position, object) per lv_obj_remove_style_all
    buttons = {b for b in (assigned_to(code, m.start()) for m in BUTTON_CREATE.finditer(code)) if b}
    for m in LV_CALL.finditer(code):
        fn, pos = m.group(1), m.start()
        args = call_args(code, m.end() - 1)
        if not args:
            continue
        obj = args[0]
        flags = args[1] if len(args) > 1 else ""
        off = fn in FLAG_OFF or (fn in FLAG_SET and len(args) > 2 and FALSE.match(args[2]))
        if fn == "lv_obj_add_event_cb" and len(args) > 2:
            events.setdefault(obj, []).append((pos, set(EVENT_CODE.findall(args[2]))))
        elif fn == "lv_obj_remove_style_all":
            unstyled.append((pos, obj))
        elif fn.startswith("lv_obj_set_scroll_chain") and len(args) > 1 and FALSE.match(args[1]):
            axis = {"lv_obj_set_scroll_chain": "both", "lv_obj_set_scroll_chain_hor": "hor"}.get(fn, "ver")
            chain_off.setdefault(obj, []).append((pos, axis))
        elif fn in ("lv_obj_set_scroll_momentum", "lv_obj_set_scroll_elastic") and len(args) > 1 \
                and FALSE.match(args[1]):
            add(pos, T9)
        if off:
            if CHAIN_BOTH.search(flags) or ("LV_OBJ_FLAG_SCROLL_CHAIN_HOR" in flags
                                            and "LV_OBJ_FLAG_SCROLL_CHAIN_VER" in flags):
                chain_off.setdefault(obj, []).append((pos, "both"))
            elif "LV_OBJ_FLAG_SCROLL_CHAIN_HOR" in flags:
                chain_off.setdefault(obj, []).append((pos, "hor"))
            elif "LV_OBJ_FLAG_SCROLL_CHAIN_VER" in flags:
                chain_off.setdefault(obj, []).append((pos, "ver"))
            if "LV_OBJ_FLAG_SCROLL_MOMENTUM" in flags or "LV_OBJ_FLAG_SCROLL_ELASTIC" in flags:
                add(pos, T9)
    for obj, regs in events.items():
        codes = set().union(*(c for _, c in regs))
        for pos, c in regs:
            if "LV_EVENT_PRESSED" in c and not codes & RELEASE_EVENTS:
                add(pos, T6)
            if "LV_EVENT_CLICKED" in c and codes & LONG_EVENTS:
                add(pos, T7)
    for obj, offs in chain_off.items():
        axes = {a for _, a in offs}
        if "both" in axes or {"hor", "ver"} <= axes:
            add(max(p for p, _ in offs), T8)
    if unstyled and not any(PRESSED_STYLE.search(",".join(call_args(code, m.end() - 1)))
                            for m in STYLE_CALL.finditer(code)):
        for pos, obj in unstyled:
            if obj in buttons:
                add(pos, T10)


def assigned_to(code: str, pos: int) -> str:
    """The expression a call at `pos` is assigned to (`btn` in `lv_obj_t *btn = lv_button_create(…)`), read back from
    the call so the scan is linear; empty when the call is not assigned."""
    i = pos - 1
    while i >= 0 and code[i] in " \t\r\n":
        i -= 1
    if i < 0 or code[i] != "=" or (i > 0 and code[i - 1] in "=!<>+-*/%&|^"):
        return ""
    i -= 1
    while i >= 0 and code[i] in " \t\r\n":
        i -= 1
    end = i + 1
    while i >= 0 and LHS_CHAR.match(code[i]):
        i -= 1
    return re.sub(r"\s+", "", code[i + 1:end])


T6 = ("T6 the object's only press handler is LV_EVENT_PRESSED, so it acts on touch-down — act on LV_EVENT_CLICKED "
      "(SHORT_CLICKED beside a long press); a press that starts a drag also handles RELEASED and PRESS_LOST (TOUCH §3)")
T7 = ("T7 LV_EVENT_CLICKED beside a long press fires on release after the hold too — act on LV_EVENT_SHORT_CLICKED "
      "(TOUCH §3, §4)")
T8 = ("T8 scroll chaining off on both axes: a drag that starts here never reaches the scroller behind — turn off only "
      "the axis it uses (_HOR or _VER); only a slider, arc, canvas, map or drag handle takes both, marked (TOUCH §2)")
T9 = ("T9 scroll momentum or elastic removed: the list stops dead on lift or at its end — keep LVGL's own; tune "
      "lv_indev_set_scroll_throw on the input device instead (TOUCH §3, §6)")
T10 = ("T10 a button stripped of the theme's styles, and this file styles no LV_STATE_PRESSED — draw a pressed style "
       "from a DESIGN.md token, or keep the theme's (TOUCH §5)")


def scan_web(code: str, add) -> None:
    """T1–T5: the web patterns in one file, comments already blanked."""
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
        # LVGL, C and C++
        ("p.c", "lv_obj_add_event_cb(btn, on_go, LV_EVENT_PRESSED, NULL);", ["T6"]),
        ("p2.c", "lv_obj_add_event_cb(btn, on_go, LV_EVENT_CLICKED, NULL);", []),
        ("p3.cpp", "lv_obj_add_event_cb(knob, DragCb, LV_EVENT_PRESSED, this);\n"
                   "lv_obj_add_event_cb(knob, DragCb, LV_EVENT_PRESS_LOST, this);", []),
        ("p4.cpp", "lv_obj_add_event_cb(row,\n    [](lv_event_t *e) { go(e, 1); },\n    LV_EVENT_PRESSED, nullptr);", ["T6"]),
        ("p5.c", "lv_obj_add_event_cb(a, on_go, LV_EVENT_PRESSED, NULL);\nlv_obj_add_event_cb(b, up, LV_EVENT_RELEASED, NULL);",
         ["T6"]),
        ("p6.c", "lv_obj_add_event_cb(btn, tick, LV_EVENT_PRESSED, NULL); // touch-exception: haptic tick only", []),
        ("q.c", "lv_obj_add_event_cb(row, open, LV_EVENT_CLICKED, NULL);\nlv_obj_add_event_cb(row, menu, LV_EVENT_LONG_PRESSED, NULL);",
         ["T7"]),
        ("q2.c", "lv_obj_add_event_cb(row, open, LV_EVENT_SHORT_CLICKED, NULL);\n"
                 "lv_obj_add_event_cb(row, menu, LV_EVENT_LONG_PRESSED, NULL);", []),
        ("q3.c", "lv_obj_add_event_cb(row, open, LV_EVENT_CLICKED, NULL);\nlv_obj_add_event_cb(list, menu, LV_EVENT_LONG_PRESSED, NULL);",
         []),
        ("r.c", "lv_obj_remove_flag(card, LV_OBJ_FLAG_SCROLL_CHAIN);", ["T8"]),
        ("r2.cpp", "lv_obj_set_scroll_chain_hor(strip_, false);\nlv_obj_set_scroll_chain_ver(strip_, false);", ["T8"]),
        ("r3.c", "lv_obj_remove_flag(carousel, LV_OBJ_FLAG_SCROLL_CHAIN_HOR);", []),
        ("r4.c", "lv_obj_set_scroll_chain(map, false); /* touch-exception: map pans both axes; zoom buttons */", []),
        ("r5.c", "lv_obj_clear_flag(card, LV_OBJ_FLAG_SCROLL_CHAIN_HOR | LV_OBJ_FLAG_SCROLL_CHAIN_VER);", ["T8"]),
        ("r6.c", "lv_obj_add_flag(card, LV_OBJ_FLAG_SCROLL_CHAIN);", []),
        ("s.c", "lv_obj_remove_flag(list, LV_OBJ_FLAG_SCROLL_MOMENTUM);", ["T9"]),
        ("s2.cpp", "lv_obj_set_scroll_elastic(list_, false);", ["T9"]),
        ("s3.c", "lv_obj_add_flag(list, LV_OBJ_FLAG_SCROLL_MOMENTUM | LV_OBJ_FLAG_SCROLL_ELASTIC);", []),
        ("s4.c", "lv_obj_set_flag(list, LV_OBJ_FLAG_SCROLL_ELASTIC, false);", ["T9"]),
        ("s5.c", "lv_obj_remove_flag(list, LV_OBJ_FLAG_SCROLLABLE);", []),
        ("p7.cpp", "lv_obj_add_event_cb(btn_, HapticCb, LV_EVENT_PRESSED, this);\n"
                   "lv_obj_add_event_cb(btn_, OpenCb, LV_EVENT_CLICKED, this);", []),
        ("p8.c", "lv_obj_add_event_cb(scrim, close_menu, LV_EVENT_PRESSED, NULL);\n"
                 "lv_obj_add_event_cb(menu, pick, LV_EVENT_CLICKED, NULL);", ["T6"]),
        ("t.c", "lv_obj_t *btn = lv_button_create(scr);\nlv_obj_remove_style_all(btn);", ["T10"]),
        ("t2.c", "lv_obj_t *btn = lv_button_create(scr);\nlv_obj_remove_style_all(btn);\n"
                 "lv_obj_set_style_bg_color(btn, lv_color_hex(0x202020), LV_STATE_PRESSED);", []),
        ("t3.c", "lv_obj_t *card = lv_obj_create(scr);\nlv_obj_remove_style_all(card);", []),
        ("t4.c", "ui->go = lv_btn_create(scr);\nlv_obj_remove_style_all(ui->go);", ["T10"]),
        ("t6.cpp", "row_ = lv_button_create(list_);\nlv_obj_remove_style_all(row_);\n"
                   "lv_obj_add_style(row_, theme::StyleRowPressed(), theme::Pressed());", []),
        ("t5.c", "/* lv_obj_add_event_cb(btn, go, LV_EVENT_PRESSED, NULL); */\nint x;", []),
        ("u.css", ".a { content: 'lv_obj_add_event_cb(btn, go, LV_EVENT_PRESSED, NULL)'; }", []),
        ("u2.c", 'const char *s = "<input autofocus>"; /* touch-action: none */', []),
        # event codes read as tokens: casts, `| LV_EVENT_PREPROCESS`, LV_EVENT_ALL
        ("v.cpp", "lv_obj_add_event_cb(kb_, KeyCb, LV_EVENT_PRESSED, this);\nlv_obj_add_event_cb(kb_, ValCb,\n"
                  "    static_cast<lv_event_code_t>(LV_EVENT_VALUE_CHANGED | LV_EVENT_PREPROCESS), this);", []),
        ("v2.c", "lv_obj_add_event_cb(b, go, (lv_event_code_t)(LV_EVENT_PRESSED | LV_EVENT_PREPROCESS), NULL);", ["T6"]),
        ("v3.c", "lv_obj_add_event_cb(b, go, (lv_event_code_t)LV_EVENT_PRESSED, NULL);", ["T6"]),
        ("v4.c", "lv_obj_add_event_cb(r, open, (lv_event_code_t)LV_EVENT_CLICKED, NULL);\n"
                 "lv_obj_add_event_cb(r, menu, LV_EVENT_LONG_PRESSED, NULL);", ["T7"]),
        ("v5.c", "lv_obj_add_event_cb(b, tick, LV_EVENT_PRESSED, NULL);\nlv_obj_add_event_cb(b, all_cb, LV_EVENT_ALL, NULL);",
         []),
        # T10 is cleared only by a pressed style inside a style call
        ("w.c", "lv_obj_t *btn = lv_button_create(scr);\nlv_obj_remove_style_all(btn);\n"
                "lv_obj_add_event_cb(btn, &PressedCb, LV_EVENT_CLICKED, NULL);", ["T10"]),
        ("w2.c", "lv_obj_t *btn = lv_button_create(scr);\nlv_obj_remove_style_all(btn);\n"
                 "if (lv_obj_has_state(btn, LV_STATE_PRESSED)) go();", ["T10"]),
        ("w3.c", "lv_obj_t *btn = lv_button_create(scr);\nlv_obj_remove_style_all(btn);\nif (a && is_pressed) go();",
         ["T10"]),
        ("w4.c", "lv_obj_t *btn = lv_button_create(scr);\nlv_obj_remove_style_all(btn);\n"
                 "lv_obj_add_style(btn, &st_pressed, LV_PART_MAIN);", []),
        ("w5.c", "bool same = a == lv_button_create(scr);\nlv_obj_remove_style_all(same);", []),
        # LVGL 9.0–9.1's lv_obj_update_flag
        ("x.c", "lv_obj_update_flag(list, LV_OBJ_FLAG_SCROLL_MOMENTUM, false);", ["T9"]),
        ("x2.c", "lv_obj_update_flag(card, LV_OBJ_FLAG_SCROLL_CHAIN, false);", ["T8"]),
        ("x3.c", "lv_obj_update_flag(list, LV_OBJ_FLAG_SCROLL_ELASTIC, true);", []),
        # line numbers across a form feed; strings that hold a comment opener; C extensions
        ("y.c", "int a;\f\nlv_obj_remove_flag(l, LV_OBJ_FLAG_SCROLL_MOMENTUM); // touch-exception: one-shot pager", []),
        ("y2.c", "httpd_uri_t u = { .uri = \"/*\" };\nlv_obj_remove_flag(l, LV_OBJ_FLAG_SCROLL_MOMENTUM);\n"
                 "const char *e = \"*/\";", ["T9"]),
        ("y3.c", "char c = '\"'; /* lv_obj_remove_flag(l, LV_OBJ_FLAG_SCROLL_MOMENTUM); */ int n = 1'000;", []),
        ("z.hxx", "lv_obj_remove_flag(l, LV_OBJ_FLAG_SCROLL_ELASTIC);", ["T9"]),
        ("z2.hxx", ".a { touch-action: none; }", []),
        ("z3.ino", "lv_obj_set_scroll_momentum(list, false);", []),  # not an ESP-IDF file: not read
    ]
    bad = 0
    for name, text, want in cases:
        got = sorted(msg.split()[0] for _, msg in scan_text(name, text))
        if got != sorted(want):
            bad += 1
            print(f"FAIL {name}: want {want}, got {got}")
    checks = [
        # a long line before a button call stays linear (a backtracking match took 37 s on 50,000 characters)
        ("timing", lambda: timed(lambda: scan_text("big.c", 'const char *img = "' + "a" * 20000
                                                    + '";\nlv_obj_t *b = lv_button_create(s);')) < 1.0),
        ("matches folder glob", lambda: matches("components/ui_sheet/src/a.cpp", ("components/ui_*/",))),
        ("matches folder glob miss", lambda: not matches("components/uix.cpp", ("components/ui_*/",))),
        ("matches plain folder", lambda: matches("main/ui/a.c", ("main/ui/",))),
        ("reason: empty", lambda: none_read_reason(["a.c"], ()) == "UI_PATHS in .agents/project.py is empty"),
        ("reason: no match", lambda: none_read_reason(["a.c"], ("ui/",)) == "UI_PATHS matches no tracked file"),
        ("reason: no UI ext", lambda: "none has a UI extension" in none_read_reason(["ui/a.md"], ("ui/",))),
        ("reason: no kit", lambda: none_read_reason([], None) == "no tracked file has a UI extension"),
    ]
    for label, ok in checks:
        if not ok():
            bad += 1
            print(f"FAIL {label}")
    total = len(cases) + len(checks)
    print(f"touch_check self-test: {total - bad}/{total} passed")
    return 1 if bad else 0


def timed(fn) -> float:
    start = time.perf_counter()
    fn()
    return time.perf_counter() - start


def main(argv: list[str]) -> int:
    if argv[:1] == ["--test"]:
        return self_test()
    named = bool(argv)
    files = argv if named else ui_files()
    hits, read = [], []
    for f in files:
        if named and Path(f).suffix not in UI_EXT:
            print(f"{f}: skipped — not a UI file")
            continue
        try:
            text = (ROOT / f).read_text(errors="replace")
        except OSError as e:
            if named:
                print(f"touch check — cannot read {f}: {e.strerror}")
                return 2
            continue
        read.append(f)
        hits += [f"{f}:{n}: {msg}" for n, msg in scan_text(f, text)]
    for h in hits:
        print(h)
    limit = 0 if named else BASELINE
    if not read:
        why = "none of the named files is a UI file that can be read" if named else \
            none_read_reason(tracked_files(), ui_patterns())
        print(f"T1–T10 touch patterns — read no UI files ({why}); nothing was checked")
        return 0
    c_files = sum(Path(f).suffix in C_EXT for f in read)
    print(f"T1–T10 touch patterns — {len(hits)} hits in {len(read)} UI files read ({len(read) - c_files} web, "
          f"{c_files} C/C++)" + ("" if named else f" (baseline {BASELINE})"))
    if len(hits) > limit:
        print("FAIL — fix each hit, or mark a sanctioned one `touch-exception` with its reason")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
