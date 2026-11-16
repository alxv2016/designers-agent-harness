#!/usr/bin/env python3
"""The ux-content skill's string check: the UI strings in code, against the rules a script can see, from
references/ux-content.md (cited `UX_CONTENT §n`). It finds what a pattern shows; voice, tone and whether a word helps
are the writer's and the reviewer's.

    python3 .agents/skills/ux-content/scripts/ux_lint.py            # every file UX_STRINGS names, against the baseline
    python3 .agents/skills/ux-content/scripts/ux_lint.py FILE …     # some files, every hit, no baseline
    python3 .agents/skills/ux-content/scripts/ux_lint.py --test     # the self-test

Settings: in a repo with the agent-harness kit, the dict UX_STRINGS in `.agents/project.py`, every key optional; a
single string stands for a one-item list —
  paths     the files that hold UI strings (a pattern ending in `/` is a folder, `*` `?` `[` make a glob); empty falls
            back to UI_PATHS, and both empty means none yet
  calls     regular expressions that replace DEFAULT_CALLS below. A pattern is a call, and EVERY string literal at the
            call's own level is read — each argument, both arms of a ternary, a literal in bare parentheses — so a
            call that takes a title and a message (`lv_msgbox_create(NULL, "Title", "Text", …)`) has both read; a
            literal inside a nested call, a closure or an array is not. A pattern that ends in `=` or `:` is an
            assignment instead: the literal right after it is read, or each literal of a `{…}` list of literals
  names     proper nouns, product names and acronyms that keep their capitals (never title case or all capitals)
  baseline  the number of hits accepted today; a whole-tree run over it exits 1
  case      "sentence" (the default) or "title" — a product that follows Apple's title case on iOS (UX_CONTENT §3.1)
            turns U7 off
In any other repo: every tracked file of a kind below outside vendored and generated folders (at any depth), with the
defaults.

Which strings, besides the calls and assignments: the text between tags in markup and JSX (`.html .htm .jsx .tsx
.js .vue .svelte .astro`), and Android's `<string>` and `<item>` resources in XML — inline tags such as `<xliff:g>`
and `<b>` and a CDATA section read through, a `translatable="false"` string skipped. Files read: web (those and `.ts
.mjs`), Swift, Kotlin and Java, XML, Apple `.strings` and `.xcstrings`, C and C++ (`.c .cc .cpp .cxx .h .hh .hpp
.hxx`); with UX_STRINGS paths or on the command line, also `.json .arb .yaml .yml .properties .po .resx`, where only
the calls you set apply. Files are read as UTF-8 (a BOM dropped), or UTF-16 when they start with its BOM.

Each file is read by a small lexer, so a literal is never mistaken for a comment or the reverse: `"/*"` hides
nothing; C's adjacent literals (`"Oops" "!"`) are joined, and C++ raw strings read; Swift's and Kotlin's
interpolation, quotes nested in it, triple-quoted strings and nested block comments; JavaScript's template literals
and regular-expression literals (`/'/g`); and `//` inside markup text is text, not a comment. A line that carries
`ux-exception` is skipped — write the reason beside it (an "OK" on a dialog that only informs, a product name in
capitals).

  U1  a generic button word — OK, Yes, No, Submit, Go, Confirm, Click here, Learn more, Read more   UX_CONTENT §5.2
  U2  "please"   UX_CONTENT §2.2, §7.5
  U3  an exclamation mark   UX_CONTENT §3.2
  U4  "oops", "uh-oh" or "whoops"   UX_CONTENT §5.7
  U5  "invalid" or "illegal"   UX_CONTENT §5.7
  U6  "Error" as a title or a prefix   UX_CONTENT §5.7
  U7  title case — two words both capitalised, or three or more with two capitalised after the first   UX_CONTENT §3.1
  U8  three full stops   UX_CONTENT §3.2
  U9  "e.g.", "i.e.", "etc.", "and/or" or "via"   UX_CONTENT §3.4
  U10 "successfully"   UX_CONTENT §5.9
  U11 "click here", "tap on" or "click on"   UX_CONTENT §4.3, §5.3
  U12 "the user"   UX_CONTENT §1.3
  U13 "enable", "disable" or "toggle"   UX_CONTENT §4.3
  U14 words in all capitals — two together, or one of five letters or more, counting letters only; the common
      acronyms in ACRONYMS and the project's names never count   UX_CONTENT §3.1

A string is cleaned before the rules: placeholders (`%d`, `%1$s`, `{count}`, `$name`; interpolation is dropped by
the lexer) and HTML entities become spaces, escapes are read, and `\n` splits it into lines checked one by one (an
LVGL dropdown's options). A string with no letter, or one word that looks like a key, a path or an id, is not UI text.

What it cannot see: a string built at run time, a string kept in a table no setting names, the words behind a key
(`stringResource(R.string.save)`, `lv_tr("save")`, `t("save")` — read the resource file instead), a literal inside a
nested call, the text of an `.xcstrings` key with no `"value"`, JSX text broken by an expression only partly, `//`
inside markup text that runs over several lines, and whether a word helps. A pass is a floor, never a review.

Prints one line per hit — `file:line: U<n> what — "text"` — then a count of hits, strings checked and files read. A
run that read no files, or read files but found no UI strings in them, says "nothing was checked" and exits 0. A
whole-tree run over the baseline exits 1; a run on named files exits 1 on any hit, and 2 when a named file cannot be
read. Python 3.9+, standard library only.
"""

from __future__ import annotations

import bisect
import fnmatch
import importlib.util
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip()
            or ".")

C_EXT = {".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx"}
MARKUP_EXT = {".html", ".htm", ".jsx", ".tsx", ".js", ".vue", ".svelte", ".astro"}  # text between tags is read
WEB_EXT = MARKUP_EXT | {".ts", ".mjs"}
JVM_EXT = {".kt", ".kts", ".java"}
KOTLIN_EXT = {".kt", ".kts"}
STRING_EXT = WEB_EXT | C_EXT | JVM_EXT | {".swift", ".xml", ".strings", ".xcstrings"}
DATA_EXT = {".json", ".arb", ".yaml", ".yml", ".properties", ".po", ".resx"}  # read only when named
SKIP_DIRS = ("node_modules/", "vendor/", "third_party/", "build/", "dist/", "out/", "coverage/", ".cache/", ".venv/",
             "Pods/", "managed_components/", ".agents/", ".claude/", ".codex/", ".github/")  # at any depth

# The calls and assignments whose string literals are UI text, for each platform (UX_CONTENT §5, §6.2).
DEFAULT_CALLS = (
    # Web: dialogs, toasts, and the attributes that are read or shown (JSX `={"…"}` too)
    r"(?<![\w$])alert", r"(?<![\w$])confirm", r"(?<![\w$])toast(?:\.\w+)?",
    r"(?<![\w-])aria-label\s*=", r"(?<![\w-])aria-description\s*=", r"(?<![\w-])(?:sub)?title\s*=",
    r"(?<![\w-])alt\s*=", r"(?<![\w-])placeholder\s*=", r"(?<![\w-])label\s*=", r"\.(?:textContent|innerText)\s*=",
    # iOS: SwiftUI views and modifiers, UIKit, localisation
    r"(?<![\w.])(?:Text|Button|Label|Toggle|TextField|SecureField|Section|Picker|Link|NavigationLink|Menu)",
    r"\.(?:navigationTitle|alert|confirmationDialog|accessibilityLabel|accessibilityHint|help|setTitle)",
    r"(?<![\w.])(?:UIAlertController|UIAlertAction|NSLocalizedString|LocalizedStringKey)",
    r"(?<![\w.])String(?=\s*\(\s*localized\s*:)", r"\.(?:accessibilityLabel|accessibilityHint|text)\s*=",
    r'^[ \t]*"(?:\\.|[^"\\\n])*"[ \t]*=',  # Localizable.strings: "key" = "value"; — `\s` would rescan blank runs
    r'"value"\s*:',                    # .xcstrings: a localisation's value
    # Android: Views, dialogs, toasts, notifications, Compose's Text (above), layout attributes
    r"\.(?:setText|setMessage|setHint|setContentDescription|setPositiveButton|setNegativeButton|setNeutralButton"
    r"|setContentTitle|setContentText)", r"\bToast\.makeText", r"\bSnackbar\.make",
    r"(?<![\w-])contentDescription\s*=",
    r"(?<![\w-])(?:android|app):(?:text|hint|contentDescription|title|label|summary|tooltipText)\s*=",
    # Embedded (ESP-IDF, LVGL 8 and 9): labels, a button's label, message boxes, lists, menus, options
    r"\blv_label_set_text(?:_fmt|_static)?", r"\blv_checkbox_set_text(?:_static)?",
    r"\blv_dropdown_set_text(?:_static)?", r"\blv_dropdown_set_options(?:_static)?", r"\blv_dropdown_add_option",
    r"\blv_roller_set_options", r"\blv_textarea_set_placeholder_text",
    r"\blv_msgbox_add_(?:title|text|text_fmt|footer_button)", r"\blv_msgbox_create",
    r"\blv_list_add_(?:text|button|btn)", r"\blv_list_set_button_text", r"\blv_win_add_title",
    r"\blv_tabview_add_tab", r"\blv_tabview_set_tab_text", r"\blv_menu_page_create",
    r"\blv_menu_set_page_title(?:_static)?", r"\blv_span_set_text(?:_static|_fmt)?",
    r"\blv_spangroup_set_span_text(?:_static|_fmt)?",
    # an array of button texts — a button matrix's map, LVGL 8's message box buttons: {"Yes", "No", ""}. Bounded,
    # so a long identifier stays linear.
    r"\b\w{0,40}(?:btn|button|Btn|Button)\w{0,40}\s*\[[^\]\n]{0,32}\]\s*=",
    # gettext, on any platform: the message id is the English text
    r"(?<![\w$.])_", r"\bgettext",
)

# Acronyms people read as words; never counted as all capitals (U14). A project adds its own in `names`.
ACRONYMS = {"AC", "AM", "API", "BLE", "CPU", "DC", "DNS", "FM", "GPS", "HD", "HDMI", "ID", "IP", "LED", "LEDS", "MAC",
            "NFC", "OK", "OTA", "PDF", "PIN", "PM", "QR", "RGB", "SD", "SIM", "SSID", "TV", "UI", "URL", "USB", "VPN"}

RULES = [
    ("U1", "a generic button word where the action has a name — UX_CONTENT §5.2",
     re.compile(r"^(?:OK|Ok|Yes|No|Submit|Go|Confirm|Click here|Learn more|Read more)$")),
    ("U2", "\"please\" in an instruction — UX_CONTENT §2.2, §7.5", re.compile(r"\bplease\b", re.I)),
    ("U3", "an exclamation mark — UX_CONTENT §3.2", re.compile(r"!")),
    ("U4", "\"oops\", \"uh-oh\" or \"whoops\" — UX_CONTENT §5.7", re.compile(r"\b(?:oops|uh-oh|whoops)\b", re.I)),
    ("U5", "\"invalid\" or \"illegal\" — say what is needed, UX_CONTENT §5.7",
     re.compile(r"\b(?:invalid|illegal)\b", re.I)),
    ("U6", "\"Error\" as a title or a prefix — name what failed, UX_CONTENT §5.7", re.compile(r"^(?:Error|ERROR)\b")),
    ("U8", "three full stops — \"…\", and only for more input or work under way, UX_CONTENT §3.2",
     re.compile(r"\.\.\.")),
    ("U9", "\"e.g.\", \"i.e.\", \"etc.\", \"and/or\" or \"via\" — UX_CONTENT §3.4",
     re.compile(r"\b(?:e\.g\.|i\.e\.|etc\.|and/or|via)(?=\W|$)", re.I)),
    ("U10", "\"successfully\" — UX_CONTENT §5.9", re.compile(r"\bsuccessfully\b", re.I)),
    ("U11", "\"click here\", \"tap on\" or \"click on\" — UX_CONTENT §4.3, §5.3",
     re.compile(r"\b(?:click|tap) (?:here|on)\b", re.I)),
    ("U12", "\"the user\" in the interface — \"you\", UX_CONTENT §1.3", re.compile(r"\bthe user\b", re.I)),
    ("U13", "\"enable\", \"disable\" or \"toggle\" — \"turn on\", \"turn off\", UX_CONTENT §4.3",
     re.compile(r"\b(?:enable|disable|toggle)\b", re.I)),
]
WHY = {r: w for r, w, _ in RULES}
WHY["U7"] = "title case — sentence case, UX_CONTENT §3.1"
WHY["U14"] = "all capitals — sentence case, UX_CONTENT §3.1"
ORDER = ["U%d" % n for n in range(1, 15)]

WORD = re.compile(r"[A-Za-z][A-Za-z'’-]*")
SMALL = {"a", "an", "and", "as", "at", "but", "by", "for", "from", "in", "into", "nor", "of", "on", "or", "per",
         "the", "to", "up", "via", "with"}


# --- The lexer ----------------------------------------------------------------------------------------------------
# One pass per file finds the string literals, the brackets and commas, and the comments, so neither hides the other.
# Every scan is bounded or moves forward, so a long line stays linear.

DQ_RE = re.compile(r'"(?:\\.|[^"\\\n])*"')
SQ_RE = re.compile(r"'(?:\\.|[^'\\\n])*'")
CHAR_RE = re.compile(r"'(?:\\.|[^'\\\n]){1,8}'")  # a C, Kotlin or Java character; `1'000` is not one
CPP_RAW = re.compile(r'(?:u8|u|U|L)?R"([^()\\\s"]{0,16})\(')
# Bounded: an unclosed class (`/[` repeated) would otherwise rescan the rest of the line from every slash.
REGEX_LIT = re.compile(r"/(?![*/>])(?:\\.|\[(?:\\.|[^\]\\\n]){0,200}\]|[^/\\\[\n]){1,500}/[A-Za-z]*")
STARTS = {
    "c": re.compile(r'(?<!\w)(?:u8|u|U|L)?R"|["\'(),\[\]{}]|/\*|//'),
    "jvm": re.compile(r'"""|["\'(),\[\]{}]|/\*|//'),
    "swift": re.compile(r'#{1,8}"|"|[(),\[\]{}]|/\*|//'),  # a raw string's hashes: at most 8
    "strings": re.compile(r'"|[(),\[\]{}]|/\*|//'),
    "web": re.compile(r'<!--|/\*|//|/|["\'`(),\[\]{}]'),
    "xml": re.compile(r'<!--|["\']'),
    "data": re.compile(r'"|[(),\[\]{}]'),
}
KW_BEFORE_REGEX = {"return", "typeof", "case", "else", "in", "of", "new", "delete", "void", "throw", "yield", "await",
                   "do"}
NESTED_DEPTH = 3      # strings inside interpolation inside strings
EXPR_LIMIT = 4000     # characters an interpolation may span
STOPS: dict = {}


def stops(close: str, esc: str, interp: str | None, multiline: bool):
    key = (close, esc, interp, multiline)
    if key not in STOPS:
        alts = [re.escape(close), re.escape(esc)] + ([re.escape(interp)] if interp else []) + ([] if multiline else ["\n"])
        STOPS[key] = re.compile("|".join(alts))
    return STOPS[key]


def kind_of(path: str) -> str | None:
    ext = Path(path).suffix.lower()
    if ext in C_EXT:
        return "c"
    if ext in WEB_EXT:
        return "web"
    if ext in JVM_EXT:
        return "jvm"
    if ext == ".swift":
        return "swift"
    if ext == ".strings":
        return "strings"
    if ext == ".xml":
        return "xml"
    if ext == ".xcstrings" or ext in DATA_EXT:
        return "data"
    return None


def interp_string(text: str, i: int, close: str, esc: str, interp: str | None, multiline: bool, lx, depth: int):
    """Scan a string body from `i` to its `close`; an escape is kept as written, an interpolation becomes a space.
    Returns (end, content) or None when it does not close."""
    if i >= lx.no_close.get(close, len(text) + 1):
        return None  # a search from an earlier position found no close, so none follows this one
    rx = stops(close, esc, interp, multiline)
    parts = []
    n = len(text)
    while i <= n:
        m = rx.search(text, i)
        if not m:
            lx.no_close[close] = min(i, lx.no_close.get(close, i))
            return None
        parts.append(text[i:m.start()])
        t = m.group()
        if t == close:
            return m.end(), "".join(parts)
        if t == "\n":
            return None
        if interp and t == interp:
            end = lx.expr(text, m.end(), "}" if interp.endswith("{") else ")", depth + 1)
            if end is None:
                return None
            parts.append(" ")
            i = end
            continue
        # an escape: Swift's `\(` (or `\#(`) opens an interpolation; anything else is kept for pieces() to read
        k = m.end()
        if lx.kind == "swift" and text.startswith("(", k):
            end = lx.expr(text, k + 1, ")", depth + 1)
            if end is None:
                return None
            parts.append(" ")
            i = end
            continue
        parts.append(text[m.start():k + 1])
        i = k + 1
    return None


class Lexer:
    def __init__(self, path: str):
        self.kind = kind_of(path)
        self.ext = Path(path).suffix.lower()
        self.starts = STARTS[self.kind]
        self.no_close: dict = {}  # a closing delimiter: the position after which it occurs nowhere

    def string(self, text: str, p: int, depth: int):
        """(end, type, content) for the literal at p — type "s" a string, "o" a character — or None."""
        if depth > NESTED_DEPTH:
            return None
        c = text[p]
        k = self.kind
        if k == "c":
            if c != '"' and c != "'":
                m = CPP_RAW.match(text, p)
                if not m:
                    return None
                close = ")" + m.group(1) + '"'
                e = -1 if m.end() >= self.no_close.get(close, len(text) + 1) else text.find(close, m.end())
                if e == -1:
                    self.no_close[close] = min(m.end(), self.no_close.get(close, m.end()))
                    return None
                return e + len(close), "s", text[m.end():e]
            if c == "'":
                m = CHAR_RE.match(text, p)
                return (m.end(), "o", "") if m else None
            m = DQ_RE.match(text, p)
            return (m.end(), "s", text[p + 1:m.end() - 1]) if m else None
        if k == "jvm":
            if c == "'":
                m = CHAR_RE.match(text, p)
                return (m.end(), "o", "") if m else None
            kotlin = self.ext in KOTLIN_EXT
            if text.startswith('"""', p):  # a Kotlin raw string or a Java text block
                r = interp_string(text, p + 3, '"""', "\x00" if kotlin else "\\", "${" if kotlin else None, True,
                                  self, depth)
            else:
                r = interp_string(text, p + 1, '"', "\\", "${" if kotlin else None, False, self, depth)
            return (r[0], "s", r[1]) if r else None
        if k == "swift":
            hashes = 0
            while text.startswith("#", p + hashes):
                hashes += 1
            q = p + hashes
            multi = text.startswith('"""', q)
            close = ('"""' if multi else '"') + "#" * hashes
            r = interp_string(text, q + (3 if multi else 1), close, "\\" + "#" * hashes, None, multi, self, depth)
            return (r[0], "s", r[1]) if r else None
        if k == "web":
            if c == "`":
                r = interp_string(text, p + 1, "`", "\\", "${", True, self, depth)
                return (r[0], "s", r[1]) if r else None
            m = (DQ_RE if c == '"' else SQ_RE).match(text, p)
            return (m.end(), "s", text[p + 1:m.end() - 1]) if m else None
        if k == "xml":
            m = (DQ_RE if c == '"' else SQ_RE).match(text, p)
            return (m.end(), "s", text[p + 1:m.end() - 1]) if m else None
        m = DQ_RE.match(text, p)  # strings, data
        return (m.end(), "s", text[p + 1:m.end() - 1]) if m else None

    def expr(self, text: str, i: int, closer: str, depth: int):
        """The end of an interpolation that starts at i: past its matching closer, strings inside read whole."""
        if depth > NESTED_DEPTH:
            return None
        limit = min(len(text), i + EXPR_LIMIT)
        stack = []
        pos = i
        while pos < limit:
            m = self.starts.search(text, pos, limit)
            if not m:
                return None
            p, t = m.start(), m.group()
            if t in "([{":
                stack.append(t)
                pos = p + 1
            elif t in ")]}":
                if not stack:
                    return p + 1 if t == closer else None
                stack.pop()
                pos = p + 1
            elif t in (",", "/", "//", "/*", "<!--"):
                pos = p + len(t)
            else:
                r = self.string(text, p, depth)
                if r is None:
                    return None
                pos = r[0]
        return None

    def lex(self, text: str):
        """(the text with comments and regular-expression literals blanked, the tokens). A token is (start, end,
        type, content): "s" a string, "o" a character, "b" a bracket, "p" a comma."""
        n = len(text)
        tokens: list = []
        blanks: list = []
        pos = 0
        while pos < n:
            m = self.starts.search(text, pos)
            if not m:
                break
            p, t = m.start(), m.group()
            if t in "()[]{}":
                tokens.append((p, p + 1, "b", t))
                pos = p + 1
            elif t == ",":
                tokens.append((p, p + 1, "p", t))
                pos = p + 1
            elif t == "/*":
                end = self.block_end(text, p)
                blanks.append((p, end))
                pos = end
            elif t == "//":
                if self.kind == "web" and not self.web_comment(text, p):
                    pos = p + 2
                    continue
                end = text.find("\n", p)
                end = n if end == -1 else end
                blanks.append((p, end))
                pos = end
            elif t == "<!--":
                end = text.find("-->", p + 4)
                end = n if end == -1 else end + 3
                blanks.append((p, end))
                pos = end
            elif t == "/":
                r = REGEX_LIT.match(text, p) if self.regex_allowed(text, p) else None
                if r:
                    blanks.append((p, r.end()))
                    pos = r.end()
                else:
                    pos = p + 1
            else:
                if t in "'\"" and self.kind == "xml" and not text[max(0, p - 40):p].rstrip().endswith("="):
                    pos = p + 1  # in XML, a quote opens an attribute's value, nothing else
                    continue
                if t == "'" and self.kind == "web" and p and (text[p - 1].isalnum() or text[p - 1] == "_"):
                    pos = p + 1  # an apostrophe in a word: "Don't"
                    continue
                r = self.string(text, p, 0)
                if r is None:
                    if t == "`":
                        break  # an unterminated template literal runs to the end of the file
                    pos = p + 1
                    continue
                tokens.append((p, r[0], r[1], r[2]))
                pos = r[0]
        if self.kind == "c":
            tokens = join_adjacent(text, tokens)
        if not blanks:
            return text, tokens
        out, last = [], 0
        for a, b in blanks:
            out.append(text[last:a])
            out.append(re.sub(r"[^\n]", " ", text[a:b]))
            last = b
        out.append(text[last:])
        return "".join(out), tokens

    def block_end(self, text: str, p: int) -> int:
        """Past the comment that opens at p. Swift and Kotlin nest block comments; C, Java and the web do not."""
        if self.kind == "swift" or self.ext in KOTLIN_EXT:
            depth = 0
            for m in re.finditer(r"/\*|\*/", text[p:]):
                depth += 1 if m.group() == "/*" else -1
                if depth == 0:
                    return p + m.end()
            return len(text)
        e = text.find("*/", p + 2)
        return len(text) if e == -1 else e + 2

    def web_comment(self, text: str, p: int) -> bool:
        """Whether `//` at p opens a comment: never after `:` or a word (a URL), and in markup never inside the text
        between a `>` and a `<` on the same line."""
        if p and (text[p - 1] in ":/_" or text[p - 1].isalnum()):
            return False
        if self.ext not in MARKUP_EXT:
            return True
        lo = max(0, p - 300)
        before = text[lo:p].rsplit("\n", 1)[-1]
        after = text[p:p + 300].split("\n", 1)[0]
        gt = before.rfind(">")
        if gt == -1 or "<" not in after:
            return True
        seg = before[gt + 1:]
        return bool(CODE_LIKE.search(seg) or re.search(r"[{}()=]", seg))

    def regex_allowed(self, text: str, p: int) -> bool:
        """Whether `/` at p can open a regular-expression literal: after an operator, `(`, `,`, a keyword or a line
        start — never after `<` (a closing tag) or a value."""
        lo = max(0, p - 200)
        j = p - 1
        while j >= lo and text[j] in " \t\r":
            j -= 1
        if j < 0:
            return True
        if j < lo:
            return False
        c = text[j]
        if c in "(,=:[!&|?{};+-*%~^\n":
            return True
        if c.isalnum() or c in "_$":
            k = j
            while k >= lo and (text[k].isalnum() or text[k] in "_$"):
                k -= 1
            return text[k + 1:j + 1] in KW_BEFORE_REGEX
        return False


def join_adjacent(text: str, tokens: list) -> list:
    """C and C++ join literals that sit side by side — `"Oops" "!"` is one string, "Oops!"."""
    out: list = []
    for tok in tokens:
        if out and tok[2] == "s" and out[-1][2] == "s" and not text[out[-1][1]:tok[0]].strip():
            prev = out.pop()
            tok = (prev[0], tok[1], "s", prev[3] + tok[3])
        out.append(tok)
    return out


# --- Reading the strings ------------------------------------------------------------------------------------------

SKIP_LABEL = re.compile(r"(?:comment|systemImage|systemName|image|bundle|tableName|id|key|forKey|identifier|named)"
                        r"\s*:\s*$")
STRING_OPEN = re.compile(r"<(string|item)\b([^<>]{0,500})>")
STRING_CLOSE = {"string": re.compile(r"</string\s*>"), "item": re.compile(r"</item\s*>")}
NOT_TRANSLATABLE = re.compile(r"\btranslatable\s*=\s*[\"']false[\"']")
CDATA = re.compile(r"<!\[CDATA\[(.*?)\]\]>", re.S)
XLIFF = re.compile(r"<xliff:g\b[^<>]{0,300}>[^<]{0,300}</xliff:g\s*>")
TAG = re.compile(r"<[^<>]{0,300}>")
ELEMENT_TEXT = re.compile(r">([^<>]+)<")
CODE_LIKE = re.compile(r"&&|\|\||=>|==|!=|;|\)\s*\{|\b(?:return|const|let|var|function|typeof|import|export)\b")
ENTITY = re.compile(r"&(?:#\d+|#x[0-9A-Fa-f]+|\w+);")
EXPR = re.compile(r"\{[^{}]*\}")
SPACE = re.compile(r"\s*")
COMPILED: dict = {}


def compile_calls(calls) -> tuple:
    """(the call pattern, the assignment pattern), either None when the list has none of that kind."""
    calls = tuple(calls)
    if calls not in COMPILED:
        assigns = [c for c in calls if c.endswith(("=", ":"))]
        plain = [c for c in calls if not c.endswith(("=", ":"))]
        call = re.compile(r"(?:" + "|".join(plain) + r")\s*\(", re.M) if plain else None
        assign = re.compile(r"(?:" + "|".join(assigns) + r")", re.M) if assigns else None
        COMPILED[calls] = (call, assign)
    return COMPILED[calls]


def literals(path: str, text: str, calls) -> list:
    """(position, raw text) for every UI string the file holds."""
    if kind_of(path) is None:
        return []
    lx = Lexer(path)
    code, tokens = lx.lex(text)
    call, assign = compile_calls(calls)
    starts = [t[0] for t in tokens]
    found: dict = {}

    def token_at(pos: int):
        i = bisect.bisect_left(starts, pos)
        return i if i < len(tokens) and tokens[i][0] == pos else None

    if call:
        for m in call.finditer(code):
            i = token_at(m.end() - 1)
            if i is None or tokens[i][3] != "(":
                continue  # the "(" sits inside a literal
            stack: list = []
            for start, _, typ, content in tokens[i + 1:i + 65]:  # a call's arguments: at most 64 tokens
                if typ == "b":
                    if content in ")]}":
                        if not stack:
                            break
                        stack.pop()
                    elif content == "(":
                        before = code[max(0, start - 1):start]
                        stack.append("call" if re.match(r"[\w>?!\]]", before) else "group")
                    else:
                        stack.append("block")
                elif typ == "s" and all(s == "group" for s in stack):
                    if not SKIP_LABEL.search(code[max(0, start - 40):start]):
                        found.setdefault(start, content)
    if assign:
        for m in assign.finditer(code):
            i = token_at(SPACE.match(code, m.end()).end())
            if i is None:
                continue
            if tokens[i][2] == "s":
                found.setdefault(tokens[i][0], tokens[i][3])
            elif tokens[i][3] == "{":  # a list of literals and nothing else: {"Yes", "No", ""}, or JSX {"Save"}
                got, prev_end, want = [], tokens[i][1], "s"
                for start, end, typ, content in tokens[i + 1:i + 513]:
                    if code[prev_end:start].strip():
                        break
                    if want == "s" and typ == "s":
                        got.append((start, content))
                        want = ","
                    elif typ == "p" and (want == "," or (want == "s" and got)):
                        want = "s"
                    elif content == "}" and got:
                        for s, c in got:
                            found.setdefault(s, c)
                        break
                    else:
                        break
                    prev_end = end
    if lx.ext in MARKUP_EXT:
        for m in ELEMENT_TEXT.finditer(code):
            raw = m.group(1)
            if raw.strip() and not CODE_LIKE.search(ENTITY.sub(" ", raw)):
                lead = len(raw) - len(raw.lstrip())
                found.setdefault(m.start(1) + lead, EXPR.sub(" ", raw.strip()))
    if lx.kind == "xml":
        for m in STRING_OPEN.finditer(code):
            if NOT_TRANSLATABLE.search(m.group(2)):
                continue  # a product name or a format kept as written
            c = STRING_CLOSE[m.group(1)].search(code, m.end(), m.end() + EXPR_LIMIT)
            if not c:
                continue
            inner = TAG.sub(" ", XLIFF.sub(" ", CDATA.sub(lambda d: d.group(1), code[m.end():c.start()])))
            if inner.strip():
                found.setdefault(m.end(), inner)
    return sorted(found.items())


PLACEHOLDER = re.compile(r"%(?:\d+\$)?[-+ #0]*\d*(?:\.\d+)?(?:hh|h|ll|l|L|z|j|t|q)?[diouxXeEfgGcsSpn@%]"
                         r"|\{[^{}\n]{0,40}\}|\$[A-Za-z_]\w{0,40}")
ESCAPE = re.compile(r"\\(?:x[0-9A-Fa-f]{1,2}|u\{[0-9A-Fa-f]{1,8}\}|u[0-9A-Fa-f]{4}|U[0-9A-Fa-f]{8}|[0-7]{1,3}|.)", re.S)
KEY_LIKE = re.compile(r"^[^\s]*[._/:#@][^\s]*$|^[a-z0-9]+(?:[-_][a-z0-9]+)+$")


def pieces(raw: str) -> list:
    """The readable lines of one string: placeholders, entities and escapes taken out, split at `\\n`."""
    text = PLACEHOLDER.sub(" ", raw)
    text = ENTITY.sub(" ", text)
    text = text.replace("\\n", "\n")
    text = ESCAPE.sub(lambda m: m.group(0)[1] if m.group(0)[1] in "'\"\\" else " ", text)
    out = []
    for line in text.split("\n"):
        line = " ".join(line.split())
        if not re.search(r"[A-Za-z]", line):
            continue
        if KEY_LIKE.match(line) and not line.endswith(("...", "…", "!", "?")):
            continue  # a key, a path, an id or a URL, not words
        out.append(line)
    return out


def without_names(text: str, names) -> str:
    for name in sorted(names, key=len, reverse=True):
        text = re.sub(r"(?<!\w)" + re.escape(name) + r"(?!\w)", " ", text)
    return text


def raised(word: str) -> bool:
    """A capitalised word of two letters or more that is not an acronym ("LED", "LEDs") or a hyphenated name
    ("Wi-Fi")."""
    return (len(word) > 1 and word[0].isupper() and sum(c.isupper() for c in word) < 2 and "-" not in word
            and word.lower() not in SMALL)


def title_case(text: str, names) -> bool:
    """U7: two words both capitalised, or three or more with at least two capitalised after the first."""
    words = WORD.findall(without_names(text, names))
    if len(words) < 2 or not raised(words[0]):
        return False
    up = [w for w in words[1:] if raised(w)]
    return len(up) >= 1 if len(words) == 2 else len(up) >= 2


def all_caps(text: str, names) -> bool:
    """U14: two words of two letters or more in capitals side by side, or one of five letters or more — letters
    counted, hyphens and apostrophes not; the common acronyms never count."""
    caps = []
    for w in WORD.findall(without_names(text, names)):
        letters = re.sub(r"[^A-Za-z]", "", w)
        caps.append((len(letters) >= 2 and letters.isupper() and letters not in ACRONYMS, len(letters)))
    return (any(a[0] and b[0] for a, b in zip(caps, caps[1:]))
            or any(c and n >= 5 for c, n in caps))


def check(text: str, cfg: dict) -> list:
    names = cfg.get("names", ())
    out = [rule for rule, _, rx in RULES if rx.search(text)]
    if cfg.get("case", "sentence") != "title" and title_case(text, names):
        out.append("U7")
    if all_caps(text, names):
        out.append("U14")
    return sorted(out, key=ORDER.index)


def scan(path: str, text: str, cfg: dict) -> tuple:
    """([(line, rule, string)] for every hit in one file, the number of strings checked)."""
    newlines = [m.start() for m in re.finditer("\n", text)]
    excepted = {bisect.bisect_left(newlines, m.start()) for m in re.finditer("ux-exception", text)}
    hits, count = [], 0
    for pos, raw in literals(path, text, cfg.get("calls") or DEFAULT_CALLS):
        n = bisect.bisect_left(newlines, pos)  # newlines before pos: the line is n + 1
        if n in excepted:
            continue
        for piece in pieces(raw):
            count += 1
            hits += [(n + 1, rule, piece) for rule in check(piece, cfg)]
    return hits, count


def scan_text(path: str, text: str, cfg: dict) -> list:
    return scan(path, text, cfg)[0]


def decode(data: bytes) -> str:
    """UTF-16 when the file starts with its byte-order mark (Apple `.strings` often do), else UTF-8 with any BOM."""
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16", errors="replace")
    return data.decode("utf-8-sig", errors="replace")


def summary(hits: int, strings: int, files: int, why: str, named: bool, baseline: int) -> str:
    if not files:
        return f"U1–U14 UI strings — read no files ({why}) — nothing was checked"
    if not strings:
        return f"U1–U14 UI strings — read {files} files but found no UI strings — nothing was checked"
    return (f"U1–U14 UI strings — {hits} hits in {strings} strings checked from {files} files read"
            + ("" if named else f" (baseline {baseline})"))


# --- Which files --------------------------------------------------------------------------------------------------

def as_tuple(value) -> tuple:
    """A setting as a tuple: a single string is one item, never its characters."""
    if not value:
        return ()
    return (value,) if isinstance(value, str) else tuple(value)


def load_settings():
    """(UX_STRINGS, UI_PATHS) from the kit's settings, or None when the repo has no kit."""
    settings = ROOT / ".agents/project.py"
    if not settings.is_file():
        return None
    spec = importlib.util.spec_from_file_location("_ux_project_settings", settings)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return dict(getattr(module, "UX_STRINGS", None) or {}), as_tuple(getattr(module, "UI_PATHS", ()))


def matches(path: str, patterns) -> bool:
    """A pattern ending in `/` is a folder and takes every file beneath it, globbed (`components/ui_*/`) or not."""
    def one(p: str) -> bool:
        glob = any(c in p for c in "*?[")
        if p.endswith("/"):
            return fnmatch.fnmatch(path, p + "*") if glob else path.startswith(p)
        return fnmatch.fnmatch(path, p) if glob else path == p
    return any(one(p) for p in patterns)


def skipped(path: str) -> bool:
    """A file under a vendored or generated folder, at any depth."""
    slashed = "/" + path
    return any("/" + d in slashed for d in SKIP_DIRS)


def tracked_files() -> list:
    return subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=ROOT,
                          capture_output=True, text=True).stdout.splitlines()


def select(tracked: list, settings) -> tuple:
    """(the files to read, why none when there are none)."""
    if settings is None:
        files = [f for f in tracked if not skipped(f) and Path(f).suffix.lower() in STRING_EXT]
        return files, "no tracked file holds UI strings"
    ux, ui_paths = settings
    own = as_tuple(ux.get("paths"))
    patterns = own or as_tuple(ui_paths)
    if not patterns:
        return [], "UX_STRINGS paths and UI_PATHS in .agents/project.py are empty"
    name = "UX_STRINGS paths" if own else "UI_PATHS"
    hit = [f for f in tracked if matches(f, patterns)]
    if not hit:
        return [], f"{name} matches no tracked file"
    exts = STRING_EXT | (DATA_EXT if own else set())
    files = [f for f in hit if Path(f).suffix.lower() in exts]
    return files, f"{name} matches tracked files, but none holds UI strings"


# --- The self-test ------------------------------------------------------------------------------------------------

def self_test() -> int:
    cfg = {"names": ("Bluetooth", "Wi-Fi", "Acme Cloud", "HDMI ARC")}
    cases = [
        # Each rule: a hit, then a near miss
        ("u1.tsx", "<button>OK</button>", ["U1"]),
        ("u1b.tsx", "<button>OK, got it</button>", []),
        ("u2.swift", 'Text("Please wait")', ["U2"]),
        ("u2b.swift", 'Text("Pleased to see you")', []),
        ("u3.c", 'lv_label_set_text(l, "Saved!");', ["U3"]),
        ("u3b.c", 'lv_label_set_text(l, "Saved"); if (!ok) return;', []),
        ("u4.kt", 'Text("Oops, couldn\'t load")', ["U4"]),
        ("u4b.kt", 'Text("Couldn\'t load loops")', []),
        ("u5.html", '<p class="error">Invalid email</p>', ["U5"]),
        ("u5b.html", "<p>Enter an email address like name@example.com</p>", []),
        ("u6.java", 'builder.setTitle("Error: no network");', ["U6"]),
        ("u6b.java", 'builder.setTitle("Errors are listed below");', []),
        ("u7.swift", 'Button("Save Changes") { save() }', ["U7"]),
        ("u7b.swift", 'Button("Turn on Bluetooth") { on() }', []),
        ("u8.c", 'lv_label_set_text(l, "Saving...");', ["U8"]),
        ("u8b.c", 'lv_label_set_text(l, "Saving\u2026");', []),
        ("u9.tsx", "<p>Choose a file, e.g. a photo</p>", ["U9"]),
        ("u9b.tsx", "<p>Choose a file, for example a photo</p>", []),
        ("u10.kt", 'Toast.makeText(ctx, "Photo saved successfully", Toast.LENGTH_SHORT).show()', ["U10"]),
        ("u10b.kt", 'Toast.makeText(ctx, "Photo saved", Toast.LENGTH_SHORT).show()', []),
        ("u11.html", "<a href='/p'>Click here</a>", ["U1", "U11"]),
        ("u11b.html", "<a href='/p'>Read the privacy policy</a>", []),
        ("u12.xml", '<string name="hint">The user can pick a song</string>', ["U12"]),
        ("u12b.xml", '<string name="hint">Pick a song</string>', []),
        ("u13.tsx", '<button aria-label="Toggle menu"><Icon /></button>', ["U13"]),
        ("u13b.tsx", '<button aria-label="Show menu"><Icon /></button>', []),
        ("u14.cpp", 'lv_label_set_text(title_, "RESET DEVICE");', ["U14"]),
        ("u14b.cpp", 'lv_label_set_text(title_, "Plug in the USB cable");', []),
        ("u14c.cpp", 'lv_label_set_text(title_, "Switch to HDMI ARC");', []),
        ("u14d.cpp", 'lv_label_set_text(title_, "Plug in a USB-C cable");', []),     # letters only: USBC is 4
        ("u14e.cpp", 'lv_label_set_text(title_, "Enter the USB PIN");', []),         # common acronyms
        ("u14f.cpp", 'lv_label_set_text(title_, "Wait for the GREEN LIGHT");', ["U14"]),
        # Web: JSX text across lines and around an expression, attributes, toasts, entities, code is not text
        ("w1.tsx", "<p>\n  Delete {count} Photos\n</p>", ["U7"]),
        ("w2.tsx", "<input placeholder={'Search...'} />", ["U8"]),
        ("w3.tsx", "<img alt=\"Profile Picture\" src={src} />", ["U7"]),
        ("w4.ts", "toast.success('Saved!')", ["U3"]),
        ("w5.html", "<title>Account Settings</title>", ["U7"]),
        ("w6.html", "<p>Save&nbsp;changes</p>", []),
        ("w7.tsx", "if (a > Max && b < Min) { go() }", []),
        ("w8.ts", "const t: Array<Foo> = make<Bar>(\"Save Now\")", []),
        ("w9.js", "document.title = 'Error';", ["U6"]),
        ("w10.tsx", "<a href=\"https://example.com//x\">Read the guide</a>", []),
        ("w11.tsx", "// <p>Oops!</p>\nconst a = 1", []),
        ("w12.tsx", '<p subtitle="Please Enter Your Name">x</p>', ["U2", "U7"]),
        # JS regular-expression literals do not open strings; `//` in markup text is text
        ("w13.js", "s = s.replace(/'/g, \"\");\nalert(\"Oops!\");", ["U3", "U4"]),
        ("w14.ts", "const r = /`/g;\nalert('Saved!');", ["U3"]),
        ("w15.tsx", "<p>Tap a // b, oops</p>", ["U4"]),
        ("w16.tsx", "<p>Fine</p> // alert('Oops!')", []),
        ("w17.tsx", "const n = a / b; alert('Done!'); const m = c / d;", ["U3"]),
        ("w18.tsx", "toast(`Saved ${n} files!`)", ["U3"]),
        ("w19.tsx", "<p>Don't stop</p>\nalert('Oops');", ["U4"]),
        # iOS: views, modifiers, labelled arguments skipped, UIKit, .strings, .xcstrings
        ("i1.swift", 'Label("Settings", systemImage: "gear.Shape.Fill")', []),
        ("i2.swift", '.alert("Delete Photo?", isPresented: $show) { Button("Delete", role: .destructive) {} }', ["U7"]),
        ("i3.swift", 'Text(NSLocalizedString("Create Your Account", comment: "The Main Button"))', ["U7"]),
        ("i4.swift", 'label.text = "Please try again"', ["U2"]),
        ("i5.strings", '/* "Oops" */\n"save.title" = "Oops, not saved";', ["U4"]),
        ("i6.xcstrings", '{"stringUnit": {"state": "translated", "value": "Tap on Save"}}', ["U11"]),
        ("i7.swift", 'Text("You have \\(count) new messages!")', ["U3"]),
        ("i8.swift", 'Text(String(localized: "Learn more"))', ["U1"]),
        # Swift and Kotlin: nested quotes in interpolation, triple quotes, raw strings, nested block comments
        ("i9.swift", 'Text("Hello \\(user.name ?? "Guest Person")!")', ["U3"]),
        ("i10.swift", 'Text("""\n    Please wait\n    """)', ["U2"]),
        ("i11.swift", '/* a /* b */ Text("Oops") */ Text("Fine")', []),
        ("i12.swift", 'Text(#"Say "hi"!"#)', ["U3"]),
        ("i13.swift", 'Text("Now \\(a ? "x \\(b) y" : "z") oops")', ["U4"]),  # two levels of nesting
        ("k1.kt", 'Text("${if (a) "Yes" else "No"} oops")', ["U4"]),
        ("k2.kt", 'Text("""Please wait""")', ["U2"]),
        ("k3.kt", '/* a /* b */ Text("Oops") */ Text("Fine")', []),
        ("k5.kt", 'Text("${f("a")} Oops") ; Text("Fine")', ["U4"]),
        ("k4.java", '/* a /* b */ x.setText("Oops");', ["U4"]),  # Java does not nest: the comment ends at "*/"
        # Android: Compose, resources, layout attributes, references skipped, keys not read
        ("a1.kt", 'Text(text = stringResource(R.string.save))', []),
        ("a2.xml", '<TextView android:text="@string/save" android:hint="Enter Your Name" />', ["U7"]),
        ("a3.xml", '<plurals name="n"><item quantity="one">%d photo deleted!</item></plurals>', ["U3"]),
        ("a4.xml", '<!-- <string name="x">Oops</string> -->\n<string name="y">Saved</string>', []),
        ("a5.xml", '<color name="accent">#FF00AA</color>', []),
        ("a6.kt", 'AlertDialog.Builder(ctx).setPositiveButton("Yes", null)', ["U1"]),
        ("a7.xml", '<string name="z">Don\\\'t disable this</string>', ["U13"]),
        ("a8.xml", '<string name="d">Delete <xliff:g id="n" example="3">%d</xliff:g> photos?</string>\n'
                   '<string name="b">Saved <b>now</b>!</string>', ["U3"]),
        ("a9.xml", '<string name="c"><![CDATA[Oops, <b>not</b> saved]]></string>', ["U4"]),
        ("a10.xml", '<string name="app" translatable="false">ACME CLOUD!</string>', []),
        # Embedded (ESP-IDF, LVGL 8 and 9): message boxes, lists, options, maps, formats, comments, nested calls
        ("e1.c", 'lv_obj_t *mb = lv_msgbox_create(NULL);\nlv_msgbox_add_title(mb, "Delete Recording?");\n'
                 'lv_msgbox_add_footer_button(mb, "OK");', ["U7", "U1"]),
        ("e2.c", 'lv_dropdown_set_options(dd, "Low\\nMedium\\nVERY HIGH");', ["U14"]),
        ("e3.c", 'lv_label_set_text_fmt(l, "%d%%", pct);', []),
        ("e4.c", 'lv_label_set_text_fmt(l, "Battery: %d%% Remaining", pct);', ["U7"]),
        ("e5.cpp", 'lv_list_add_button(list_, LV_SYMBOL_WIFI, "Connect To Home Network");', ["U7"]),
        ("e6.c", 'static const char *btn_map[] = {"Yes", "No", ""};', ["U1", "U1"]),
        ("e7.c", 'httpd_uri_t u = { .uri = "/*" };\nlv_label_set_text(l, "Done!");\nconst char *e = "*/";', ["U3"]),
        ("e8.c", '/* lv_label_set_text(l, "Oops!"); */ int n = 1;', []),
        ("e9.c", 'lv_label_set_text(l, on ? "Now Active!" : "Off");', ["U3", "U7"]),
        ("e10.c", 'lv_label_set_text(l, lv_tr("settings.title"));', []),
        ("e11.c", 'lv_label_set_text(l, fmt_name("Please Pick"));', []),
        ("e12.c", 'lv_label_set_text(l, LV_SYMBOL_OK " Saved!");', ["U3"]),
        ("e13.c", 'lv_label_set_text(l, "Oops"); // ux-exception: the product\'s mascot says it', []),
        ("e14.c", 'lv_label_set_text(l, "Saved\\x21 \\u00b0C");', []),
        ("e15.c", 'lv_msgbox_create(NULL, "Error", "Please retry", btns, true);', ["U6", "U2"]),
        ("e16.c", 'char c = \'"\'; lv_label_set_text(l, "Go");', ["U1"]),
        ("e17.c", 'lv_list_add_button_translation_tag(list, NULL, "Click Here");', []),
        ("e18.ino", 'lv_label_set_text(l, "Oops!");', []),  # not an ESP-IDF file: not read
        ("e19.c", 'lv_label_set_text(l,\n    "Saving...");', ["U8"]),
        ("e20.c", 'lv_label_set_text(l, "Oops" "!");', ["U3", "U4"]),            # adjacent literals joined
        ("e21.c", 'lv_label_set_text(l, "Oops"\n    /* why */ " again");', ["U4"]),
        ("e22.c", 'static const char * btns[] = {"Yes", "Close", ""};', ["U1"]),  # LVGL 8 message box buttons
        ("e23.c", 'static const char * paths[] = {"Oops", ""};', []),            # not a button array
        ("e24.cpp", 'lv_label_set_text(l, R"(Oops!)");', ["U3", "U4"]),
    ]
    bad = 0
    for name, text, want in cases:
        got = [rule for _, rule, _ in scan_text(name, text, cfg)]
        if sorted(got) != sorted(want):
            bad += 1
            print(f"FAIL {name}: want {want}, got {got}")
    line_case = scan_text("ln.c", "int a;\n\nlv_label_set_text(l,\n  \"Oops\");", cfg)
    mb = 1 << 20
    GROWTH = 8  # linear is 4, quadratic 16: room for a noisy runner on either side
    NOISE = 0.05  # seconds

    def linear(name: str, make, n: int) -> bool:
        """Scanning n repeats costs about four times n // 4, as a linear scan does; a quadratic one costs sixteen.
        A ratio, not seconds: a shared CI runner runs several times slower than a laptop, and a fixed limit in
        seconds failed there on a linear scan. Under NOISE the run is too short to measure, and passes."""
        small = timed(lambda: scan_text(name, make(n // 4), cfg))
        big = timed(lambda: scan_text(name, make(n), cfg))
        return big < NOISE or big < GROWTH * max(small, NOISE / 4)

    def output_survives_ascii() -> bool:
        with tempfile.TemporaryDirectory() as d:
            f = os.path.join(d, "a.c")
            with open(f, "w", encoding="utf-8") as fh:
                fh.write('lv_label_set_text(l, "Saving\u2026 Oops!");\n')
            env = dict(os.environ, PYTHONIOENCODING="ascii")
            r = subprocess.run([sys.executable, os.path.abspath(__file__), f], capture_output=True, text=True,
                               env=env, errors="replace")
            return r.returncode == 1 and "Traceback" not in r.stderr and "U4" in r.stdout

    checks = [
        ("line of a wrapped literal", lambda: [n for n, _, _ in line_case] == [4]),
        ("case title turns U7 off", lambda: scan_text("t.swift", 'Button("Save Changes")', {"case": "title"}) == []),
        ("own calls replace the defaults", lambda: [r for _, r, _ in scan_text(
            "k.json", '{"save": "Oops"}', {"calls": (r'"\w+"\s*:',)})] == ["U4"]),
        ("defaults read no JSON key", lambda: scan_text("k.json", '{"title": "Oops"}', {}) == []),
        ("strings counted", lambda: scan("c.c", 'lv_label_set_text(a, "Saved");\nlv_label_set_text(b, "Done");',
                                         cfg) == ([], 2)),
        ("summary: files but no strings", lambda: summary(0, 0, 434, "", False, 0)
         == "U1–U14 UI strings — read 434 files but found no UI strings — nothing was checked"),
        ("summary: strings and files", lambda: summary(2, 20, 434, "", True, 0)
         == "U1–U14 UI strings — 2 hits in 20 strings checked from 434 files read"),
        ("summary: no files", lambda: summary(0, 0, 0, "why", False, 0).endswith("(why) — nothing was checked")),
        ("decode: UTF-16 with BOM", lambda: decode('"a" = "Oops";'.encode("utf-16")) == '"a" = "Oops";'),
        ("decode: UTF-8 BOM dropped", lambda: decode(b'\xef\xbb\xbf"a" = "b";') == '"a" = "b";'),
        ("UTF-16 .strings read", lambda: [r for _, r, _ in scan_text(
            "u.strings", decode('"a" = "Oops";'.encode("utf-16")), cfg)] == ["U4"]),
        ("output survives an ASCII terminal", output_survives_ascii),
        # a long input stays linear: 1 MB of calls, 40,000 literals on one line, unclosed interpolation, maps
        ("timing: 1 MB of calls", lambda: linear("big.c", lambda k: 'lv_label_set_text(l, "Save");\n' * k, mb // 30)),
        ("timing: 40,000 literals on a line", lambda: linear(
            "big1.c", lambda k: 'lv_label_set_text(l, "Save"); ' * k, 40000)),
        ("timing: unclosed interpolation", lambda: linear("big.swift", lambda k: 'Text("' + "\\(a" * k, 333000)),
        ("timing: button maps", lambda: linear("big3.c", lambda k: "btn_map[" * k, 125000)),
        ("timing: blank lines", lambda: linear("blank.c", lambda k: "\n" * k, 200000)),
        ("timing: unclosed regex classes", lambda: linear("rx.js", lambda k: "x = /[" * k, 40000)),
        ("timing: placeholders", lambda: linear(
            "big4.c", lambda k: 'lv_label_set_text(l, "' + "{a ${b " * k + '");', 100000)),
        ("timing: long literal", lambda: linear(
            "big5.c", lambda k: 'const char *img = "' + "a" * k + '";\nlv_label_set_text(l, "Save");', 20000)),
        ("timing: open tag", lambda: linear("big.tsx", lambda k: ">" + "Word " * k, 4000)),
        ("timing: long identifier", lambda: linear("big6.c", lambda k: "btn" * k + "x[] = {1};", 7000)),
        ("timing: nested calls", lambda: linear("big2.swift", lambda k: "Text(" * k, 4000)),
        ("timing: unclosed quote", lambda: linear("big2.tsx", lambda k: "<p>Don't " + "x" * k + "</p>", 20000)),
        ("timing: unclosed templates", lambda: linear("big3.tsx", lambda k: "`${" * k, 100000)),
        ("timing: regex slashes", lambda: linear("big4.tsx", lambda k: "(/" * k, 200000)),
        ("timing: markup slashes", lambda: linear("big5.tsx", lambda k: "<p>a // b " * k, 50000)),
        ("timing: nested comments", lambda: linear("big3.swift", lambda k: "/*" * k, 200000)),
        ("timing: raw-string hashes", lambda: linear("big4.swift", lambda k: "#" * k + '"', 200000)),
        ("timing: unclosed raw strings", lambda: linear("big.cpp", lambda k: 'R"(' * k, 200000)),
        ("timing: nested interpolation", lambda: linear("big5.swift", lambda k: '"\\(' * k, 200000)),
        ("timing: XML opens", lambda: linear("big.xml", lambda k: "<string name='a'>" * k, 30000)),
        ("matches folder glob", lambda: matches("components/ui_sheet/src/a.cpp", ("components/ui_*/",))),
        ("matches folder glob miss", lambda: not matches("components/uix.cpp", ("components/ui_*/",))),
        ("select: no kit", lambda: select(["src/a.tsx", "node_modules/x/a.js", "a.png"], None)[0] == ["src/a.tsx"]),
        ("select: skipped at any depth", lambda: select(["components/x/build/a.c", "web/vendor/j.js",
                                                         "a/third_party/b.cpp", "src/a.c"], None)[0] == ["src/a.c"]),
        ("select: empty", lambda: select(["a.c"], ({}, ()))[1].endswith("are empty")),
        ("select: UI_PATHS fallback", lambda: select(["ui/a.c", "ui/a.png"], ({}, ("ui/",)))[0] == ["ui/a.c"]),
        ("select: no match", lambda: select(["a.c"], ({"paths": ("ui/",)}, ()))[1]
         == "UX_STRINGS paths matches no tracked file"),
        ("select: a path given as a string", lambda: select(["src/a.c", "s"], ({"paths": "src/"}, ()))[0]
         == ["src/a.c"]),
        ("select: own paths take data", lambda: select(["l/en.json"], ({"paths": ("l/",)}, ()))[0] == ["l/en.json"]),
        ("select: UI_PATHS takes no data", lambda: select(["l/en.json"], ({}, ("l/",)))[0] == []),
    ]
    for label, ok in checks:
        if not ok():
            bad += 1
            print(f"FAIL {label}")
    total = len(cases) + len(checks)
    print(f"ux_lint self-test: {total - bad}/{total} passed")
    return 1 if bad else 0


def timed(fn) -> float:
    start = time.perf_counter()
    fn()
    return time.perf_counter() - start


def main(argv: list) -> int:
    try:
        sys.stdout.reconfigure(errors="replace")  # a terminal that cannot show "—" or "…" gets "?"
    except (AttributeError, ValueError):
        pass
    if argv[:1] == ["--test"]:
        return self_test()
    try:
        settings = load_settings()
    except Exception as e:  # a settings file that does not import is the person's to fix
        print(f"ux-content strings — cannot read .agents/project.py: {e}")
        return 2
    ux = settings[0] if settings else {}
    cfg = {"calls": as_tuple(ux.get("calls")), "names": as_tuple(ux.get("names")),
           "case": ux.get("case", "sentence")}
    baseline = int(ux.get("baseline", 0) or 0)
    named = bool(argv)
    if named:
        files, why = argv, "none of the named files holds UI strings"
    else:
        files, why = select(tracked_files(), settings)
    hits, read, strings = [], 0, 0
    for f in files:
        if named and kind_of(f) is None:
            print(f"{f}: skipped — not a file that holds UI strings")
            continue
        try:
            text = decode((ROOT / f).read_bytes())
        except OSError as e:
            if named:
                print(f"ux-content strings — cannot read {f}: {e.strerror}")
                return 2
            continue
        read += 1
        found, count = scan(f, text, cfg)
        strings += count
        hits += [f"{f}:{n}: {rule} {WHY[rule]} — \"{s}\"" for n, rule, s in found]
    for h in hits:
        print(h)
    print(summary(len(hits), strings, read, why, named, baseline))
    if not read or not strings:
        return 0
    limit = 0 if named else baseline
    if len(hits) > limit:
        print("FAIL — fix each string, or mark a sanctioned one `ux-exception` with its reason"
              + ("" if named else f"; the baseline is {baseline}"))
        return 1
    if not named and len(hits) < baseline:
        print(f"    under the baseline: lower UX_STRINGS[\"baseline\"] to {len(hits)} in .agents/project.py")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
