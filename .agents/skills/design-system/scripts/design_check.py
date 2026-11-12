#!/usr/bin/env python3
"""The design-system skill's DESIGN.md check: the design brief at the repo root (`DESIGN_FILE` in .agents/project.py)
stays true to itself and to the code.

    python3 .agents/skills/design-system/scripts/design_check.py          # DESIGN.md against its floors and the code
    python3 .agents/skills/design-system/scripts/design_check.py --test   # the check's own cases

It reads two kinds of table in DESIGN.md:

  - a token table — a header row `| Token | <Theme> | <Theme> | … |`, then rows `` | `color.x` | `#hex` | `#hex` | … ``
    (one value per theme). Any table whose header starts `| Token |` names tokens: colour, type, space, radius, motion.
    The colour table may add a `Kind` column — `| Token | Kind | Light | Dark | Use |` — giving each role its kinds
    (`surface`, `text`, `non-text`, `fill`, `on-fill`, `scrim`, `exempt`; several, comma-separated), which D1 and D4 read.
  - the contrast-pairs table — a header row `| Foreground | Background | Floor | <Theme> | <Theme> |`, then rows
    `` | `color.fg` | `color.bg` | 4.5 | 16.88 | 16.75 | `` — the ratio written for each theme.

  D1 contrast pair under its floor — a pair's computed ratio, in some theme, is below its floor; or a pair is
     written with a floor under its kind's: 4.5 for a text or on-fill foreground, 3 for non-text
  D2 ratio written wrong — the ratio written in DESIGN.md differs from the computed one by more than 0.05, or names a
     colour token that is not in a token table
  D3 token missing from the token files — a token DESIGN.md names, or a colour value it gives, is not in TOKEN_FILES
     (skipped while TOKEN_FILES is empty). A name matches in any spelling: `color.text.primary`,
     `--color-text-primary`, `colorTextPrimary`, `color_text_primary`.
  D4 contrast pair missing — a pair the kinds call for has no row. A token table with a `Kind` column gives each
     colour role one or more kinds (`text, fill`): every `text` and `non-text` role needs a row on every `surface`,
     and every `on-fill` role a row on every `fill`; `scrim` and `exempt` roles are not paired. With no `Kind`
     column, the names decide: `color.text.*` (but `disabled` and `on-*`) on every `color.bg.*`.

Prints one line per hit, then a count per check; any hit exits 1. Baseline: 0.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip()
            or ".")
sys.path.insert(0, str(ROOT / ".agents"))
sys.path.insert(0, str(ROOT / ".agents/skills/accessibility/scripts"))
import project  # noqa: E402
from contrast import ratio  # noqa: E402 — one contrast formula for the whole kit

HEX = re.compile(r"^#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")


def cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def unquote(cell: str) -> str:
    return cell.strip().strip("`").strip()


FLOORS = {"text": 4.5, "on-fill": 4.5, "non-text": 3.0}
KINDS: dict[str, set] = {}  # colour role → its kinds, from a `Kind` column; filled by parse()


def parse(text: str) -> tuple[dict, list, set]:
    """(colour token → {theme: hex}, contrast rows, every token name) from DESIGN.md's tables; the kinds into KINDS."""
    KINDS.clear()
    colours: dict[str, dict[str, str]] = {}
    pairs: list[tuple[int, str, str, float, dict[str, str]]] = []
    names: set[str] = set()
    header, kind, fence = [], None, False
    for n, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith(("```", "~~~")):
            fence = not fence
            continue
        if fence or not line.startswith("|"):
            header, kind = [], None
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
        elif kind == "pairs" and row[0].startswith("`"):
            try:
                floor = float(row[2])
            except ValueError:
                continue
            written = {header[i]: c for i, c in enumerate(row[3:], 3) if i < len(header)}
            pairs.append((n, unquote(row[0]), unquote(row[1]), floor, written))
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
            got = ratio(colours[fg][theme], colours[bg][theme])
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


def squash(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def check_code(colours: dict, names: set) -> list[str]:
    files = [ROOT / f for f in project.TOKEN_FILES if (ROOT / f).is_file()]
    text = "\n".join(f.read_text(errors="replace") for f in files)
    flat, low = squash(text), text.lower()
    hits = [f"token {n} is not in {', '.join(project.TOKEN_FILES)}" for n in sorted(names) if squash(n) not in flat]
    for name, values in sorted(colours.items()):
        for theme, value in values.items():
            if value.lower() not in low:
                hits.append(f"{name} {theme} {value} is not in {', '.join(project.TOKEN_FILES)}")
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
    failed = [what for ok, what in cases if not ok]
    for what in failed:
        print(f"FAIL  {what}")
    print(f"design check self-test: {len(cases) - len(failed)}/{len(cases)} cases pass")
    return 1 if failed else 0


def main(argv: list[str]) -> int:
    if "--test" in argv:
        return self_test()
    path = ROOT / project.DESIGN_FILE
    if not path.is_file():
        print(f"design check — no {project.DESIGN_FILE}: nothing to check")
        return 0
    colours, pairs, names = parse(path.read_text())
    under, wrong = check_pairs(colours, pairs, project.DESIGN_FILE)
    report("D1", "contrast pair under its floor", under)
    report("D2", "ratio written wrong in " + project.DESIGN_FILE, wrong)
    missing = missing_pairs(colours, pairs)
    report("D4", "contrast pair missing", missing)
    if project.TOKEN_FILES:
        drift = check_code(colours, names)
        report("D3", "token missing from the token files", drift)
    else:
        drift = []
        print("D3 token missing from the token files — skipped: TOKEN_FILES is empty in .agents/project.py")
    hits = len(under) + len(wrong) + len(drift) + len(missing)
    if hits:
        print(f"    FAIL — {hits} hit(s) over the baseline of 0: fix {project.DESIGN_FILE} or the token files")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
