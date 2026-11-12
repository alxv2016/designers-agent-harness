"""The doc scripts' settings, so this skill folder works in any repo.

In a repo with the agent-harness kit, the settings come from `.agents/project.py` (`PROJECT_NAME`, `DOC_PREFIX`,
`PROJECT_WIDE_DOCS`, `DESIGN_FILE`, `CODE_PATHS`, …). Copied on its own into another repo, the skill falls back to the
defaults below: no doc prefix, no project name, the code being everything outside `docs/` and the root's Markdown.
Override a default by creating `.agents/project.py` with just the names you need.

    python3 .agents/skills/docs-authoring-and-sync/scripts/_config.py NAME   # print one setting (doc_checks.sh uses it)
"""

from __future__ import annotations

import fnmatch
import subprocess
import sys
from pathlib import Path

ROOT = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip()
            or ".")
GUIDE = ".agents/skills/docs-authoring-and-sync/references/guidelines.md"

PROJECT_NAME = "<Project>"
DOC_PREFIX = ""
PROJECT_WIDE_DOCS = ("docs/AGENT_HARNESS.md", GUIDE)
DESIGN_FILE = "DESIGN.md"
CODE_PATHS: tuple = ()
GENERATED = ("build/", "dist/", "out/", "coverage/", ".cache/", "node_modules/", ".venv/", "__pycache__/")
HARNESS_DIRS = (".agents/", ".claude/", ".codex/", ".github/")


def code_pathspec() -> list[str]:
    """A git pathspec for the code, for `git grep`."""
    if CODE_PATHS:
        return [p if not any(c in p for c in "*?[") else f":(glob){p}" for p in CODE_PATHS]
    return [".", ":(exclude)docs", ":(exclude)*.md"] + [f":(exclude){d.rstrip('/')}" for d in HARNESS_DIRS] \
        + [f":(exclude){g.rstrip('/')}" for g in GENERATED]


def matches(path: str, patterns) -> bool:
    for p in patterns:
        if (p.endswith("/") and path.startswith(p)) or (any(c in p for c in "*?[") and fnmatch.fnmatch(path, p)) \
                or path == p:
            return True
    return False


_project = ROOT / ".agents/project.py"
if _project.is_file():
    sys.path.insert(0, str(_project.parent))
    import project as _p  # noqa: E402 — the kit's settings win over the defaults above
    for _name in ("PROJECT_NAME", "DOC_PREFIX", "PROJECT_WIDE_DOCS", "DESIGN_FILE", "CODE_PATHS", "GENERATED"):
        if hasattr(_p, _name):
            globals()[_name] = getattr(_p, _name)
    if hasattr(_p, "code_pathspec"):
        code_pathspec = _p.code_pathspec  # noqa: F811

if __name__ == "__main__":
    value = globals().get(sys.argv[1]) if len(sys.argv) > 1 else None
    print("\n".join(value) if isinstance(value, (tuple, list)) else ("" if value is None else value))
