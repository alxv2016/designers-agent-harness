#!/usr/bin/env python3
"""The design-system skill's token check: a colour written as a literal in a UI file instead of taken from a design
token. It reads UI_PATHS and TOKEN_FILES from .agents/project.py (in a repo without the kit: every tracked UI file,
and no token files until one is named there — scripts/_config.py) and scans every UI file that is not a token file.

    python3 .agents/skills/design-system/scripts/token_check.py            # every UI file, against the baseline
    python3 .agents/skills/design-system/scripts/token_check.py FILE …     # some files, no baseline
    python3 .agents/skills/design-system/scripts/token_check.py --test     # the check's own cases

What it finds, by language (DESIGN_BRIEF §15):

  - Web, iOS, Android and the rest: hex colours (`#1a73e8`, `#fff`), `rgb()`, `rgba()`, `hsl()` and `hsla()` calls,
    and `0xFF1A73E8`-style colour integers.
  - C and C++ (`.c`, `.cc`, `.cpp`, `.cxx`, `.h`, `.hh`, `.hpp`, `.hxx`; LVGL on an ESP-IDF device), with
    comments blanked first: a number given to LVGL's colour constructors (`lv_color_hex(0x1A73E8)`,
    `lv_color_hex3(0xF00)`, `lv_color_make(26, 115, 232)`, `lv_color32_make(…)`, `LV_COLOR_MAKE(…)`), LVGL's built-in
    palette (`lv_palette_main(…)`, `_lighten`, `_darken`), a bare `0xRRGGBB` or `0xAARRGGBB` passed to a call whose
    name says colour (`SetTextColor(0x1A73E8)`), and a label recolour (`"a #ff0000 red# word"`) on a
    `lv_label_set_text…` line or in a file that calls `lv_label_set_recolor(…, true)`. A bare `0x…` anywhere else — an
    address, a mask, a register value — and a `#123456` in other text are not colours and never a hit.

A line that carries `token-exception` is skipped: it is a sanctioned exception, registered with its reason in
DESIGN.md's exceptions. Prints one line per hit, then a count and how many files it read; a whole-tree run over
BASELINE exits 1. Python 3.9+, standard library only.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip()
            or ".")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _config as project  # noqa: E402 — .agents/project.py when present, else the skill's defaults

# Hits sanctioned today, each with its reason. A new hit on a line you touched is yours to fix.
BASELINE = 0
C_FAMILY = {".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx"}
TEXT = {".css", ".scss", ".sass", ".less", ".html", ".htm", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".vue", ".svelte",
        ".astro", ".swift", ".kt", ".java", ".dart", ".xml", ".json", ".py", ".rb", ".erb", ".liquid", ".hbs"} | C_FAMILY
LITERAL = re.compile(r"(?<![\w&/])#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3,4})\b(?![-\w])"
                     r"|\b(?:rgba?|hsla?)\(\s*\d"
                     r"|\b0x(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6})\b")
# In C and C++ a `0x…` is as often an address, a mask or a register as a colour, so only a value in a colour's
# place is one: LVGL's constructors and palette, a colour-named call's argument.
C_LITERAL = re.compile(r"\b(?:lv_color_hex3?|lv_color(?:32)?_make|LV_COLOR_MAKE)\s*\(\s*(?:0[xX][0-9a-fA-F]+|\d)"
                       r"|\blv_palette_(?:main|lighten|darken)\s*\("
                       r"|\b\w*(?i:colou?r)\w*\s*\((?:[^()]|\([^()]*\))*?"
                       r"(?<![\w.])0[xX](?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6})(?![\w.])")
# LVGL's label recolour, `"a #ff0000 red# word"`: a `#RRGGBB ` and its closing `#` inside one string, counted on a
# label-text call's line, or anywhere in a file that turns recolour on — so `"Order #123456 failed"` is not one.
RECOLOUR = re.compile(r"\"[^\"\n]*#[0-9a-fA-F]{6} [^\"#\n]*#")
LABEL_TEXT = re.compile(r"\blv_label_set_text(?:_fmt|_static)?\s*\(")
RECOLOUR_ON = re.compile(r"\blv_label_set_recolor\s*\([^;]*?\b(?:true|1)\s*\)")


def ui_files() -> list[str]:
    return [f for f in ui_candidates() if not project.matches(f, project.TOKEN_FILES)]


def ui_candidates() -> list[str]:
    """Every UI file the check could read, the token files among them."""
    return [f for f in project.tracked() if project.is_ui(f) and Path(f).suffix in TEXT and (ROOT / f).is_file()]


def blank_comments(text: str) -> str:
    """C and C++ text with every comment turned to spaces, line breaks kept, so a hit keeps its line number and a
    value quoted in a comment is not one. Strings and character literals are skipped whole, so `"/*"` or `"//"` in a
    string opens no comment; a `'` between digits is C++14's digit separator, not a character literal."""
    out, i, n = [], 0, len(text)
    while i < n:
        c, nxt = text[i], text[i + 1] if i + 1 < n else ""
        if c == "/" and nxt == "/":
            end = text.find("\n", i)
            end = n if end < 0 else end
            out.append(" " * (end - i))
            i = end
        elif c == "/" and nxt == "*":
            end = text.find("*/", i + 2)
            end = n if end < 0 else end + 2
            out.append(re.sub(r"[^\r\n]", " ", text[i:end]))
            i = end
        elif c in "\"'" and not (c == "'" and i and text[i - 1].isalnum()):
            j = i + 1
            while j < n and text[j] != c and text[j] != "\n":
                j += 2 if text[j] == "\\" else 1
            j = min(j + 1, n)
            out.append(text[i:j])
            i = j
        else:
            out.append(c)
            i += 1
    return "".join(out)


def line_hits(name: str, text: str) -> list[str]:
    """The colour literals in one file's text, by its language."""
    original = text.splitlines()
    if Path(name).suffix not in C_FAMILY:
        return [f"{name}:{n}: {line.strip()[:120]}" for n, line in enumerate(original, 1)
                if "token-exception" not in line and LITERAL.search(line)]
    code = blank_comments(text)
    recolour_on = bool(RECOLOUR_ON.search(code))
    hits = []
    for n, (line, kept) in enumerate(zip(original, code.splitlines()), 1):
        if "token-exception" in line:
            continue
        if C_LITERAL.search(kept) or (RECOLOUR.search(kept) and (recolour_on or LABEL_TEXT.search(kept))):
            hits.append(f"{name}:{n}: {line.strip()[:120]}")
    return hits


def scan(files: list[str]) -> tuple[list[str], int]:
    """(hits, how many files were read)."""
    hits, read = [], 0
    for f in files:
        try:
            text = (ROOT / f).read_text(errors="replace")
        except OSError:
            continue
        read += 1
        hits += line_hits(f, text)
    return hits, read


def self_test() -> int:
    cases = [
        ("a.css", "color: #1a73e8;", True), ("a.css", "background: rgba(0, 0, 0, .5);", True),
        ("a.css", "color: var(--color-text-secondary);", False), ("a.kt", "val c = Color(0xFF1A73E8)", True),
        ("a.tsx", "<a href='#top'>", False),
        ("ui.cpp", "lv_obj_set_style_bg_color(obj, lv_color_hex(0x1A73E8), 0);", True),
        ("ui.cpp", "lv_obj_set_style_bg_color(obj, lv_color_hex3(0xF00), 0);", True),
        ("ui.c", "lv_color_t c = lv_color_make(0x1A, 0x73, 0xE8);", True),
        ("ui.c", "lv_color32_t c = lv_color32_make(26, 115, 232, 255);", True),
        ("ui.h", "static const lv_color_t kRed = LV_COLOR_MAKE(255, 0, 0);", True),
        ("ui.cc", "lv_style_set_text_color(&s, lv_palette_main(LV_PALETTE_RED));", True),
        ("ui.hpp", "label.SetTextColor(0x1A73E8);", True),
        ("ui.cpp", "SET_COLOUR(screen, 0xFF1A73E8);", True),
        ("ui.cpp", 'lv_label_set_text(label, "#ff0000 Error#");', True),
        ("ui.cpp", 'lv_label_set_recolor(label, true);\nstatic const char *kMsg = "a #ff0000 red# word";', True),
        ("ui.cpp", 'printf("Order #123456 failed");', False),
        ("ui.cpp", 'lv_label_set_text(label, "Order #123456 failed");', False),
        ("ui.cpp", 'static const char *kMsg = "Order #123456 and #7";', False),
        ("ui.cpp", "// lv_color_hex(0x1A73E8) was the old accent", False),
        ("ui.cpp", "/* SetTextColor(0x1A73E8);\n   lv_palette_main(LV_PALETTE_RED) */\nint x = 0;", False),
        ("ui.cpp", 'puts("/*"); lv_obj_set_style_bg_color(obj, lv_color_hex(0x1A73E8), 0); // "*/"', True),
        ("ui.cpp", 'puts("//"); lv_color_t c = lv_color_hex(0x1A73E8);', True),
        ("ui.cpp", "uint32_t n = 1'000'000; lv_color_t c = lv_color_hex(0x1A73E8);", True),
        ("ui.hxx", "label.SetTextColor(0x1A73E8);", True),
        ("ui.cpp", "lv_obj_set_style_bg_color(obj, lv_color_hex(0xFF0000), 0);  // token-exception: test pattern",
         False),
        ("ui.cpp", "lv_obj_set_style_text_color(label, ColorTextSecondary(), LV_PART_MAIN);", False),
        ("ui.cpp", "lv_obj_set_style_bg_color(obj, lv_color_hex(kColorBgCanvas), 0);", False),
        ("ui.c", "lv_color_t c = lv_color_make(r, g, b);", False),
        ("ui.h", "#define LCD_FRAMEBUFFER_BASE 0x3C000000", False),
        ("ui.c", "write_reg(dev, 0x302060, 1);", False),
        ("ui.c", "uint32_t rgb = value & 0xFFFFFF;", False),
        ("ui.c", "panel_set_color_mode(dev, 0x55);", False),
        ("ui.c", "if (has_color(x)) base = 0x302060;", False),
        ("ui.h", "#include \"lvgl.h\"", False),
        ("ui.cpp", "lv_obj_set_style_bg_opa(obj, LV_OPA_COVER, 0);", False),
    ]
    failed = [f"{name}: {line!r} should {'hit' if hit else 'not hit'}" for name, line, hit in cases
              if bool(line_hits(name, line)) != hit]
    numbered = line_hits("ui.c", "/* a\n   b */\nlv_color_t c = lv_color_hex(0x123456);")
    if not (len(numbered) == 1 and numbered[0].split(":")[1] == "3"):
        failed.append(f"a hit after a two-line comment keeps its line number: {numbered}")
    globbed = ("components/ui_*/",)
    if not (project.matches("components/ui_theme/include/tokens.h", globbed)
            and not project.matches("components/net/wifi.c", globbed)):
        failed.append("a folder pattern with a glob matches the files beneath it, and only those")
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "screen.cpp"
        f.write_text("lv_obj_set_style_bg_color(obj, lv_color_hex(0x1A73E8), 0);\n")
        hits, read = scan([str(f), str(Path(d) / "missing.cpp")])
    if not (len(hits) == 1 and read == 1):
        failed.append(f"a C++ file is read and a missing one is not counted: {len(hits)} hits in {read} files")
    total = len(cases) + 3
    for what in failed:
        print(f"FAIL  {what}")
    print(f"token check self-test: {total - len(failed)}/{total} cases pass")
    return 1 if failed else 0


def main(argv: list[str]) -> int:
    if "--test" in argv:
        return self_test()
    if not project.TOKEN_FILES:
        print("token check — read no files: no TOKEN_FILES in .agents/project.py, so nothing to check against")
        return 0
    whole = not argv
    files = ui_files() if whole else argv
    hits, read = scan(files)
    if not read:
        if not whole:
            why = "none of the files named exists"
        elif ui_candidates():
            why = "the only UI files UI_PATHS matches are token files, which the check skips"
        else:
            why = "UI_PATHS in .agents/project.py matches no tracked file with a UI suffix"
        print(f"token check — read no UI files: {why}")
        return 0
    print("\n".join(hits))
    print(f"T1 colour literal outside the tokens — {len(hits)} hits in {read} UI file(s)"
          + (f" (baseline {BASELINE})" if whole else ""))
    if whole and len(hits) > BASELINE:
        print(f"    FAIL — over the baseline of {BASELINE}: take the colour from a token, or register an exception")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
