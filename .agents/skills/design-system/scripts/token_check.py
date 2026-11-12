#!/usr/bin/env python3
"""The design-system skill's token check: a colour written as a literal in a UI file instead of taken from a design
token. It reads UI_PATHS and TOKEN_FILES from .agents/project.py and scans every UI file that is not a token file.

    python3 .agents/skills/design-system/scripts/token_check.py            # every UI file, against the baseline
    python3 .agents/skills/design-system/scripts/token_check.py FILE …     # some files, no baseline

It finds hex colours (`#1a73e8`, `#fff`), `rgb()`, `rgba()`, `hsl()` and `hsla()` calls, and `0xFF1A73E8`-style
colour integers. A line that carries `token-exception` is skipped: it is a sanctioned exception, registered with its
reason in DESIGN.md's Exceptions (DESIGN §10). Prints one line per hit, then a count; a
whole-tree run over BASELINE exits 1.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip()
            or ".")
sys.path.insert(0, str(ROOT / ".agents"))
import project  # noqa: E402

# Hits sanctioned today, each with its reason. A new hit on a line you touched is yours to fix.
BASELINE = 0
TEXT = {".css", ".scss", ".sass", ".less", ".html", ".htm", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".vue", ".svelte",
        ".astro", ".swift", ".kt", ".java", ".dart", ".xml", ".json", ".py", ".rb", ".erb", ".liquid", ".hbs"}
LITERAL = re.compile(r"(?<![\w&/])#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3,4})\b(?![-\w])"
                     r"|\b(?:rgba?|hsla?)\(\s*\d"
                     r"|\b0x(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6})\b")


def ui_files() -> list[str]:
    out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=ROOT,
                         capture_output=True, text=True).stdout.splitlines()
    return [f for f in out if project.matches(f, project.UI_PATHS) and not project.matches(f, project.TOKEN_FILES)
            and Path(f).suffix in TEXT and (ROOT / f).is_file()]


def scan(files: list[str]) -> list[str]:
    hits = []
    for f in files:
        try:
            lines = (ROOT / f).read_text(errors="replace").splitlines()
        except OSError:
            continue
        for n, line in enumerate(lines, 1):
            if "token-exception" in line:
                continue
            if LITERAL.search(line):
                hits.append(f"{f}:{n}: {line.strip()[:120]}")
    return hits


def main(argv: list[str]) -> int:
    if not project.TOKEN_FILES:
        print("token check — TOKEN_FILES is empty in .agents/project.py: nothing to check against")
        return 0
    whole = not argv
    hits = scan(ui_files() if whole else argv)
    print("\n".join(hits))
    print(f"T1 colour literal outside the tokens — {len(hits)} hits" + (f" (baseline {BASELINE})" if whole else ""))
    if whole and len(hits) > BASELINE:
        print(f"    FAIL — over the baseline of {BASELINE}: take the colour from a token, or register an exception")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
