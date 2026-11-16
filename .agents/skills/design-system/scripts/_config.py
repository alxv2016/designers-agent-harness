"""The design scripts' settings, so this skill folder works in any repo.

In a repo with the agent-harness kit, the settings come from `.agents/project.py` (`DESIGN_FILE`, `TOKEN_FILES`,
`UI_PATHS`). Copied on its own into another repo, the skill falls back to the defaults below: the brief at
`DESIGN.md`, no token files, and every tracked UI file outside vendored and generated folders. Override a default by
creating `.agents/project.py` with just the names you need.

The contrast formula is the accessibility skill's (`contrast.py`) when that skill sits beside this one, so the whole
kit computes one ratio; without it, the same WCAG 2 formula below.

    python3 .agents/skills/design-system/scripts/_config.py NAME   # print one setting
"""

from __future__ import annotations

import fnmatch
import subprocess
import sys
from pathlib import Path

ROOT = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip()
            or ".")
HERE = Path(__file__).resolve().parent

DESIGN_FILE = "DESIGN.md"
TOKEN_FILES: tuple = ()
UI_PATHS = None  # None: every tracked UI file; a tuple (the kit's, possibly empty): only those paths
KIT = False
SKIP_DIRS = ("node_modules/", "vendor/", "third_party/", "build/", "dist/", "out/", "coverage/", ".cache/", ".venv/",
             "Pods/", "managed_components/", ".agents/", ".claude/", ".codex/", ".github/")
VENDORED = ("/node_modules/", "/managed_components/")  # the npm and ESP-IDF component managers' downloads

_project = ROOT / ".agents/project.py"
if _project.is_file():
    sys.path.insert(0, str(_project.parent))
    import project as _p  # noqa: E402 — the kit's settings win over the defaults above
    KIT = True
    for _name in ("DESIGN_FILE", "TOKEN_FILES", "UI_PATHS"):
        if hasattr(_p, _name):
            globals()[_name] = getattr(_p, _name)


def matches(path: str, patterns) -> bool:
    """A folder with `/`, a glob, or an exact file — the kit's pattern rules. A folder with a glob in it
    (`components/ui_*/`) matches every file beneath the folders it names."""
    def one(p: str) -> bool:
        glob = any(c in p for c in "*?[")
        if p.endswith("/"):
            return fnmatch.fnmatch(path, p + "*") if glob else path.startswith(p)
        return fnmatch.fnmatch(path, p) if glob else path == p
    return any(one(p) for p in patterns)


def is_ui(path: str) -> bool:
    if UI_PATHS is not None:
        return matches(path, UI_PATHS)
    return not path.startswith(SKIP_DIRS) and not any(v in path for v in VENDORED)


def tracked() -> list[str]:
    return subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=ROOT,
                          capture_output=True, text=True).stdout.splitlines()


def token_paths() -> list[str]:
    """The files TOKEN_FILES names, each pattern resolved the way `matches` reads it: an exact file, a folder or a
    glob."""
    found = [f for f in TOKEN_FILES if (ROOT / f).is_file()]
    return sorted(set(found) | {f for f in tracked() if matches(f, TOKEN_FILES) and (ROOT / f).is_file()})


def _wcag_ratio(fg_hex: str, bg_hex: str) -> float:
    """WCAG 2's contrast ratio, the foreground composited over an opaque background."""
    def parse(h: str):
        h = h.strip().lstrip("#")
        h = "".join(c * 2 for c in h) if len(h) in (3, 4) else h
        if len(h) not in (6, 8):
            raise ValueError(f"not a hex colour: {h!r}")
        rgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
        return rgb, (int(h[6:8], 16) / 255 if len(h) == 8 else 1.0)

    def lum(rgb):
        lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
        return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]
    bg, bga = parse(bg_hex)
    if bga < 1:
        raise ValueError(f"the background must be opaque: {bg_hex!r}")
    fg, a = parse(fg_hex)
    fg = [fg[i] * a + bg[i] * (1 - a) for i in range(3)]
    l1, l2 = sorted((lum(fg), lum(bg)), reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)


_a11y = HERE.parent.parent / "accessibility" / "scripts"
if (_a11y / "contrast.py").is_file():
    sys.path.insert(0, str(_a11y))
    from contrast import ratio  # noqa: E402,F401 — one contrast formula for the whole kit
    SHARED_RATIO = True
else:
    ratio = _wcag_ratio
    SHARED_RATIO = False

if __name__ == "__main__":
    value = globals().get(sys.argv[1]) if len(sys.argv) > 1 else None
    print("\n".join(value) if isinstance(value, (tuple, list)) else ("" if value is None else value))
