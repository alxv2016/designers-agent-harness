#!/usr/bin/env python3
"""The design-system skill's DESIGN.md check: the design brief at the repo root (`DESIGN_FILE` in .agents/project.py,
or `DESIGN.md` in a repo without the kit — scripts/_config.py) stays true to itself and to the code.

    python3 .agents/skills/design-system/scripts/design_check.py              # DESIGN.md against its floors and code
    python3 .agents/skills/design-system/scripts/design_check.py --file F     # another brief, such as the template
    python3 .agents/skills/design-system/scripts/design_check.py --test       # the check's own cases

It reads two kinds of table in DESIGN.md:

  - a token table — a header row `| Token | <Theme> | <Theme> | … |`, then rows `` | `color.x` | `#hex` | `#hex` | … ``
    (one value per theme). Any table whose header starts `| Token |` names tokens: colour, type, space, radius, motion.
    The colour table may add a `Kind` column — `| Token | Kind | Light | Dark | Use |` — giving each role its kinds
    (`surface`, `text`, `non-text`, `fill`, `on-fill`, `scrim`, `exempt`; several, comma-separated), which D1 and D4 read.
  - the contrast-pairs table — a header row `| Foreground | Background | Floor | <Theme> | <Theme> |`, then rows
    `` | `color.fg` | `color.bg` | 4.5 | 16.88 | 16.75 | `` — the ratio written for each theme.

  D1 contrast pair under its floor — a pair's computed ratio, in some theme, is below its floor; or a pair is
     written with a floor under its kind's: 4.5 for a text or on-fill foreground, 3 for non-text; or its background is
     translucent, so it has no fixed colour to measure
  D2 ratio written wrong — the ratio written in DESIGN.md differs from the computed one by more than 0.05, or names a
     colour token that is not in a token table
  D3 token missing from the token files — a token DESIGN.md names, or a colour value it gives, is not in TOKEN_FILES
     (skipped while TOKEN_FILES is empty). A name matches in any spelling: `color.text.primary`,
     `--color-text-primary`, `colorTextPrimary`, `color_text_primary`, `kColorTextPrimary`. A colour matches only
     its exact value, as CSS writes it (`#6b7280`, any case; `#fff` or `#ffffff` for `#fff`) or as C and C++ write
     it (`0x6B7280`, any case, an integer suffix allowed, so `lv_color_hex(0x6B7280)` too) — never a longer or
     shorter number (DESIGN_BRIEF §15). Prints how many token files it read; TOKEN_FILES naming no file that
     exists is one hit.
  D4 contrast pair missing — a pair the kinds call for has no row. A token table with a `Kind` column gives each
     colour role one or more kinds (`text, fill`): every `text` and `non-text` role needs a row on every `surface`,
     and every `on-fill` role a row on every `fill`; `scrim` and `exempt` roles are not paired. With no `Kind`
     column, the names decide: `color.text.*` (but `disabled` and `on-*`) on every `color.bg.*`.
  D5 theme value missing — a colour token gives a hex value in one theme column and none in another, so a theme is
     half made (DESIGN_BRIEF §5). A table's themes are its columns that hold a colour in some row, so a `Use` or
     `Usage` column is never one
  D6 translucent surface or fill — a role of kind `surface` or `fill` has an alpha value, so its painted colour
     depends on what is under it and no pair can be checked; only `scrim` and `exempt` roles may be translucent
     (DESIGN_BRIEF §4)

Prints one line per hit, then a count per check; any hit exits 1. Baseline: 0.
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
from _config import ratio  # noqa: E402 — the accessibility skill's formula when it sits beside this one

HEX = re.compile(r"^#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")


def cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def unquote(cell: str) -> str:
    return cell.strip().strip("`").strip()


FLOORS = {"text": 4.5, "on-fill": 4.5, "non-text": 3.0}
BLANKS: list[str] = []  # D5: "line: token has no <theme> value"; filled by parse()
KINDS: dict[str, set] = {}  # colour role → its kinds, from a `Kind` column; filled by parse()


def parse(text: str) -> tuple[dict, list, set]:
    """(colour token → {theme: hex}, contrast rows, every token name) from DESIGN.md's tables; the kinds into KINDS."""
    KINDS.clear()
    colours: dict[str, dict[str, str]] = {}
    pairs: list[tuple[int, str, str, float, dict[str, str]]] = []
    names: set[str] = set()
    BLANKS.clear()
    header, kind, fence, table = [], None, False, []

    def close(rows: list) -> None:
        """D5 for one token table: its themes are the columns that hold a colour in some row."""
        themes = {t for _, _, values in rows for t in values}
        if len(themes) > 1:
            BLANKS.extend(f"{n}: {name} has no {t} value" for n, name, values in rows for t in sorted(themes - set(values)))
    for n, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith(("```", "~~~")):
            fence = not fence
            continue
        if fence or not line.startswith("|"):
            close(table)
            header, kind, table = [], None, []
            continue
        row = cells(line)
        if not header:
            header = row
            kind = "token" if row[0] == "Token" else "pairs" if row[:3] == ["Foreground", "Background", "Floor"] \
                else None
            continue
        if set("".join(row)) <= set("-: "):
            continue  # the separator row
        if kind == "token" and row[0].startswith("`"):
            name = unquote(row[0])
            names.add(name)
            if "Kind" in header and header.index("Kind") < len(row):
                KINDS[name] = {k.strip() for k in row[header.index("Kind")].split(",") if k.strip()}
            values = {header[i]: unquote(c) for i, c in enumerate(row[1:], 1)
                      if i < len(header) and HEX.match(unquote(c))}
            if values:
                colours[name] = values
                table.append((n, name, values))
        elif kind == "pairs" and row[0].startswith("`"):
            try:
                floor = float(row[2])
            except ValueError:
                continue
            written = {header[i]: c for i, c in enumerate(row[3:], 3) if i < len(header)}
            pairs.append((n, unquote(row[0]), unquote(row[1]), floor, written))
    close(table)
    return colours, pairs, names


def check_pairs(colours: dict, pairs: list, where: str) -> tuple[list[str], list[str]]:
    under, wrong = [], []
    for n, fg, bg, floor, written in pairs:
        missing = [t for t in (fg, bg) if t not in colours]
        if missing:
            wrong.append(f"{where}:{n}: {', '.join(missing)} is not in a token table")
            continue
        for theme, text in written.items():
            if theme not in colours[fg] or theme not in colours[bg]:
                wrong.append(f"{where}:{n}: no {theme} value for {fg} or {bg}")
                continue
            need = floor_for(fg)
            if floor < need and theme == next(iter(written)):
                under.append(f"{where}:{n}: {fg}'s floor is written {floor:g}; its kind needs {need:g}")
            try:
                got = ratio(colours[fg][theme], colours[bg][theme])
            except ValueError:
                under.append(f"{where}:{n}: {fg} on {bg} in {theme}: {bg} is translucent, so the pair has no fixed "
                             f"colour to measure — pair it on a solid role")
                continue
            if got < floor:
                under.append(f"{where}:{n}: {fg} on {bg} in {theme}: {got:.2f}:1, under its floor of {floor:g}:1")
            try:
                if abs(float(text) - got) > 0.05:
                    wrong.append(f"{where}:{n}: {fg} on {bg} in {theme} is written {text}, computes {got:.2f}")
            except ValueError:
                wrong.append(f"{where}:{n}: {fg} on {bg} in {theme}: '{text}' is not a ratio")
    return under, wrong


def floor_for(fg: str) -> float:
    """The lowest floor a foreground's kind allows: by its `Kind`, or by its name when no kinds are declared."""
    if KINDS:
        return max((FLOORS[k] for k in KINDS.get(fg, ()) if k in FLOORS), default=0.0)
    return 4.5 if fg.startswith("color.text.") else 0.0


def missing_pairs(colours: dict, pairs: list) -> list[str]:
    have = {(fg, bg) for _, fg, bg, _, _ in pairs}
    if KINDS:
        of = lambda kind: [t for t in colours if kind in KINDS.get(t, ())]  # noqa: E731
        wanted = [(f, b) for f in of("text") + of("non-text") for b in of("surface")] \
            + [(f, b) for f in of("on-fill") for b in of("fill")]
    else:
        texts = [t for t in colours if t.startswith("color.text.") and t != "color.text.disabled"
                 and not t.startswith("color.text.on-")]
        wanted = [(t, b) for t in texts for b in colours if b.startswith("color.bg.")]
    return [f"{f} on {b} has no row in the contrast pairs" for f, b in wanted if (f, b) not in have]


def translucent(colours: dict) -> list[str]:
    """D6: a surface or fill role with an alpha value."""
    out = []
    for name, values in sorted(colours.items()):
        if KINDS.get(name, set()) & {"surface", "fill"}:
            for theme, value in values.items():
                h = value.lstrip("#")
                if len(h) in (4, 8) and h[-2:].lower() != "ff" and not (len(h) == 4 and h[-1].lower() == "f"):
                    out.append(f"{name} in {theme} is {value}: a surface or fill is painted solid")
    return out


def squash(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def spelled(value: str) -> re.Pattern:
    """Every way a token file writes one hex colour, and only that value: `#6b7280` as CSS writes it, and
    `0x6B7280` as C and C++ write it (inside `lv_color_hex(…)` on LVGL), with an optional integer suffix. C has no
    shorthand, so `#fff` is `0xffffff` there. A longer or shorter number — `0xFF6B7280`, `0x6B72801` — is another
    value (DESIGN_BRIEF §15)."""
    digits = value.lstrip("#").lower()
    full = "".join(c * 2 for c in digits) if len(digits) in (3, 4) else digits
    css = digits if full == digits else f"(?:{digits}|{full})"
    return re.compile(rf"#{css}(?![0-9a-f])|(?<![0-9a-z_])0x{full}[ul]{{0,3}}(?![0-9a-z_])", re.IGNORECASE)


def check_code(colours: dict, names: set, files: list) -> list[str]:
    text = "\n".join((ROOT / f).read_text(errors="replace") for f in files)
    return code_hits(colours, names, text, ", ".join(files))


def code_hits(colours: dict, names: set, text: str, where: str) -> list[str]:
    flat = squash(text)
    hits = [f"token {n} is not in {where}" for n in sorted(names) if squash(n) not in flat]
    for name, values in sorted(colours.items()):
        for theme, value in values.items():
            if not spelled(value).search(text):
                hits.append(f"{name} {theme} {value} is not in {where}")
    return hits


def report(code: str, title: str, hits: list[str]) -> None:
    for h in hits:
        print(h)
    print(f"{code} {title} — {len(hits)} hits (baseline 0)")


def self_test() -> int:
    good = ("| Token | Light | Dark | Use |\n| --- | --- | --- | --- |\n"
            "| `color.text` | `#000000` | `#FFFFFF` | x |\n| `color.bg` | `#FFFFFF` | `#000000` | x |\n"
            "| `space.md` | 12 px | x |\n\n"
            "| Foreground | Background | Floor | Light | Dark |\n| --- | --- | --- | --- | --- |\n"
            "| `color.text` | `color.bg` | 4.5 | 21.00 | 21.00 |\n")
    colours, pairs, names = parse(good)
    under, wrong = check_pairs(colours, pairs, "t")
    cases = [(not under and not wrong, "a passing pair passes"), (names == {"color.text", "color.bg", "space.md"},
                                                                  "every token named")]
    bad = good.replace("21.00 | 21.00", "20.00 | 21.00").replace("`#000000` | `#FFFFFF` | x", "`#BBBBBB` | `#FFFFFF` | x")
    under, wrong = check_pairs(*parse(bad)[:2], "t")
    cases += [(len(under) == 1, "a pale pair is under its floor"), (len(wrong) == 1, "a wrong ratio is caught")]
    cases += [(squash("--color-text") == squash("colorText") == squash("color.text"), "names match in any spelling")]
    loose = good.replace("| `color.text` | `color.bg` | 4.5 |", "| `color.text` | `color.bg` | 3 |") \
        .replace("`color.text`", "`color.text.body`").replace("`color.bg`", "`color.bg.page`")
    under, _ = check_pairs(*parse(loose)[:2], "t")
    cases += [(len(under) == 1, "a text pair with a floor of 3 is caught")]
    extra = good.replace("| `space.md` |", "| `color.bg.card` | `#EEEEEE` | `#111111` | x |\n| `space.md` |") \
        .replace("`color.text`", "`color.text.body`").replace("`color.bg`", "`color.bg.page`")
    c, pr, _ = parse(extra)
    cases += [(missing_pairs(c, pr) == ["color.text.body on color.bg.card has no row in the contrast pairs"],
               "a text role with no pair on a background is caught")]
    kinded = ("| Token | Kind | Light | Dark | Use |\n| --- | --- | --- | --- | --- |\n"
              "| `color.ink` | text | `#000000` | `#FFFFFF` | x |\n| `color.line` | non-text | `#767676` | `#8A8A8A` | x |\n"
              "| `color.page` | surface | `#FFFFFF` | `#000000` | x |\n\n"
              "| Foreground | Background | Floor | Light | Dark |\n| --- | --- | --- | --- | --- |\n"
              "| `color.ink` | `color.page` | 4.5 | 21.00 | 21.00 |\n| `color.line` | `color.page` | 3 | 4.54 | 6.08 |\n")
    c, pr, _ = parse(kinded)
    under, wrong = check_pairs(c, pr, "t")
    cases += [(not under and not wrong and not missing_pairs(c, pr), "kinds: a complete, passing table passes")]
    c, pr, _ = parse(kinded.replace("| `color.line` | `color.page` | 3 | 4.54 | 6.08 |\n", ""))
    cases += [(missing_pairs(c, pr) == ["color.line on color.page has no row in the contrast pairs"],
               "kinds: a non-text role with no pair on a surface is caught")]
    c, pr, _ = parse(kinded.replace("| `color.ink` | `color.page` | 4.5 |", "| `color.ink` | `color.page` | 3 |"))
    cases += [(len(check_pairs(c, pr, "t")[0]) == 1, "kinds: a text role written with floor 3 is caught")]
    c, pr, _ = parse(kinded.replace("| `color.page` | surface | `#FFFFFF` | `#000000` |",
                                    "| `color.page` | surface | `#FFFFFF` | |"))
    cases += [(len(BLANKS) == 1 and "Dark" in BLANKS[0], "D5: a colour with no dark value is caught")]
    c, pr, _ = parse(kinded.replace("| `color.page` | surface | `#FFFFFF` |", "| `color.page` | surface | `#FFFFFF80` |"))
    cases += [(len(translucent(c)) == 1, "D6: a translucent surface is caught")]
    c, pr, _ = parse(kinded.replace("| `color.line` | non-text | `#767676` |", "| `color.line` | scrim | `#00000066` |"))
    cases += [(not translucent(c), "D6: a translucent scrim passes")]
    cases += [(all(abs(ratio(f, b) - project._wcag_ratio(f, b)) < 1e-9
                   for f, b in (("#585E69", "#F4F5F7"), ("#00000080", "#ffffff"), ("#7EA2FF", "#23304F"))),
               "the skill's own contrast formula agrees with the accessibility skill's")]
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "DESIGN.md"
        f.write_text(kinded.replace("| `color.page` | surface | `#FFFFFF` |", "| `color.page` | surface | `#FFFFFFCC` |"))
        cases += [(brief_hits(f) >= 1, "D6: a translucent surface with pairs is reported, not a crash")]
        f.write_text(good.replace("| `color.bg` | `#FFFFFF` |", "| `color.bg` | `#FFFFFFCC` |"))
        cases += [(brief_hits(f) >= 1, "D1: a translucent background is reported without kinds too")]
        f.write_text(kinded.replace("| `color.line` | non-text | `#767676` | `#8A8A8A` | x |",
                                    "| `color.line` | non-text | `#767676` | `#8A8A8A` | x |\n"
                                    "| `color.dim` | scrim | `#00000066` | `#00000099` | x |")
                     + "| `color.ink` | `color.dim` | 4.5 | 1.00 | 1.00 |\n")
        cases += [(brief_hits(f) >= 1, "D1: text written on a scrim is reported")]
        f.write_text(kinded.replace("| Token | Kind | Light | Dark | Use |", "| Token | Kind | Light | Dark | Usage |"))
        cases += [(brief_hits(f) == 0, "D5: a column named Usage is not a theme")]
        kept, project.TOKEN_FILES = project.TOKEN_FILES, ("no/such/tokens.h",)
        try:
            f.write_text(kinded)
            cases += [(brief_hits(f, code=True) == 1, "D3: TOKEN_FILES naming no file that exists is one hit")]
        finally:
            project.TOKEN_FILES = kept
    brief = {"color.text.secondary": {"Dark": "#6B7280"}}
    named = {"color.text.secondary"}
    for code, ok, what in (
            (":root { --color-text-secondary: #6b7280; }", True, "D3: a CSS custom property matches"),
            ("constexpr uint32_t kColorTextSecondary = 0x6B7280;", True, "D3: a C constant 0x6B7280 matches"),
            ("constexpr uint32_t kColorTextSecondary = 0x6b7280u;", True, "D3: a lowercase C constant with a suffix "
                                                                            "matches"),
            ("lv_color_t ColorTextSecondary() { return lv_color_hex(0x6B7280); }", True,
             "D3: lv_color_hex(0x6B7280) matches"),
            ("constexpr uint32_t kColorTextSecondary = 0x6B7281;", False, "D3: a C value one step off is missing"),
            ("constexpr uint32_t kColorTextSecondary = 0xFF6B7280;", False, "D3: an ARGB 0xFF6B7280 is another value"),
            ("constexpr uint32_t kColorTextSecondary = 0x6B72801;", False, "D3: a longer C number is another value"),
            ("--color-text-secondary: #6b728080;", False, "D3: a CSS value with alpha is another value")):
        cases += [((code_hits(brief, named, code, "t") == []) == ok, what)]
    cases += [(code_hits({"color.bg": {"Light": "#FFF"}}, {"color.bg"}, "kColorBg = 0xFFFFFF;", "t") == [],
               "D3: #FFF matches its C spelling 0xFFFFFF")]
    template = Path(__file__).resolve().parent.parent / "references" / "templates" / "DESIGN.md"
    if template.is_file():
        cases += [(brief_hits(template) == 0, "the DESIGN.md template passes the design check")]
    failed = [what for ok, what in cases if not ok]
    for what in failed:
        print(f"FAIL  {what}")
    print(f"design check self-test: {len(cases) - len(failed)}/{len(cases)} cases pass")
    return 1 if failed else 0


def brief_hits(path: Path, code: bool = False, quiet: bool = True) -> int:
    """Every D-check on one brief; the count of hits. `code` adds D3 against TOKEN_FILES."""
    say = (lambda *a: None) if quiet else report
    where = path.name if quiet else str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
    colours, pairs, names = parse(path.read_text())
    blanks = list(BLANKS)
    under, wrong = check_pairs(colours, pairs, where)
    say("D1", "contrast pair under its floor", under)
    say("D2", "ratio written wrong in " + where, wrong)
    missing = missing_pairs(colours, pairs)
    say("D4", "contrast pair missing", missing)
    say("D5", "theme value missing", [f"{where}:{b}" for b in blanks])
    clear = translucent(colours)
    say("D6", "translucent surface or fill", clear)
    drift = []
    if code and project.TOKEN_FILES:
        files = project.token_paths()
        if not quiet:
            print(f"D3 read {len(files)} token file(s)" + (f": {', '.join(files)}" if files else
                  f" — TOKEN_FILES ({', '.join(project.TOKEN_FILES)}) names no file that exists"))
        drift = check_code(colours, names, files) if files else \
            [f"TOKEN_FILES names no file that exists: {', '.join(project.TOKEN_FILES)}"]
        say("D3", "token missing from the token files", drift)
    elif code and not quiet:
        print("D3 token missing from the token files — skipped: no TOKEN_FILES"
              + (" in .agents/project.py" if project.KIT else " (set them in .agents/project.py)"))
    return len(under) + len(wrong) + len(missing) + len(blanks) + len(clear) + len(drift)


def main(argv: list[str]) -> int:
    if "--test" in argv:
        return self_test()
    given = argv[argv.index("--file") + 1] if "--file" in argv and argv.index("--file") + 1 < len(argv) else None
    path = Path(given).resolve() if given else ROOT / project.DESIGN_FILE
    if not path.is_file():
        print(f"design check — no {given or project.DESIGN_FILE}: read no brief, nothing to check")
        return 0
    print(f"design check — read {path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}")
    hits = brief_hits(path, code=not given, quiet=False)
    if hits:
        print(f"    FAIL — {hits} hit(s) over the baseline of 0: fix {path.name} or the token files")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
