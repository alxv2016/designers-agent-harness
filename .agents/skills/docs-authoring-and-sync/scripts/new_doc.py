#!/usr/bin/env python3
"""Creates a new doc in docs/ from the template for its type (GUIDELINES §2, §3.1, §10), and lists it in README.md's
Documentation section (GUIDELINES §7) as one line: `--summary`, or the purpose's first sentence.

    python3 .agents/skills/docs-authoring-and-sync/scripts/new_doc.py --type system --topic DATA_MODEL \\
        --purpose "What the app stores, where, and what clearing it loses."
    python3 .agents/skills/docs-authoring-and-sync/scripts/new_doc.py --list
    python3 .agents/skills/docs-authoring-and-sync/scripts/new_doc.py --test

Types — each opens with what GUIDELINES §2 says its readers come for:
  rules         Rules and reference — Rules (Do / Never), task lookup, reference, traps, exceptions
  interface     Interface — critical constraints, reference with sources, traps, open items
  system        System explanation — the shape, rules, how it works, decisions, traps, open items
  config        Configuration — the settings that matter and why, coupled settings, pinned dependencies
  notes         Working notes — open items grouped by what unblocks them
  requirements  Requirements — status banner, requirements, conflicts, what to test first

The file is `docs/<PREFIX>_<TOPIC>.md` (no prefix when DOC_PREFIX is empty), titled `# <Project> — <Topic>` once
PROJECT_NAME is set, else `# <Topic>`. It refuses to overwrite a doc. The new doc's `<…>` placeholders are for the
writer to fill in from the code and the person — never left in a committed doc. Exit 0 created, 1 refused, 2 usage.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _config as cfg  # noqa: E402 — .agents/project.py when present, else the skill's defaults

TEMPLATES = Path(__file__).resolve().parent.parent / "references" / "templates"
TYPES = {"rules": "Rules and reference", "interface": "Interface", "system": "System explanation",
         "config": "Configuration", "notes": "Working notes", "requirements": "Requirements"}


def title_case(topic: str) -> str:
    return " ".join(w.capitalize() if not w.isupper() or len(w) > 3 else w for w in topic.split("_"))


def doc_path(root: Path, topic: str) -> Path:
    name = f"{cfg.DOC_PREFIX}_{topic}" if cfg.DOC_PREFIX else topic
    return root / "docs" / f"{name}.md"


def heading(topic_title: str) -> str:
    named = cfg.PROJECT_NAME and not cfg.PROJECT_NAME.startswith("<")
    return f"{cfg.PROJECT_NAME} — {topic_title}" if named else topic_title


def one_line(text: str) -> str:
    """A table cell: the first sentence, newlines collapsed, `|` escaped."""
    flat = " ".join(text.split())
    first = re.match(r"(.+?[.!?])(\s|$)", flat)
    return (first.group(1) if first else flat).replace("|", "\\|")


def list_in_readme(root: Path, rel: str, cite: str, summary: str) -> str:
    """Add a row to README.md's Documentation table, or the section itself when there is none."""
    readme = root / "README.md"
    text = readme.read_text() if readme.is_file() else ""
    row = f"| [{cite}]({rel}) | {one_line(summary)} |"
    if f"]({rel})" in text:
        return "already listed in README.md"
    m = re.search(r"^## Documentation\s*$", text, re.M)
    if m:
        lines = text[m.end():].split("\n")
        start = next((i for i, l in enumerate(lines) if l.startswith("|")), None)
        if start is not None:
            end = start
            while end + 1 < len(lines) and lines[end + 1].startswith("|"):
                end += 1
            lines.insert(end + 1, row)
            readme.write_text(text[:m.end()] + "\n".join(lines))
            return "added to README.md's Documentation table"
        readme.write_text(text[:m.end()] + "\n\n| Doc | What it holds |\n| --- | --- |\n" + row + "\n"
                          + text[m.end():].lstrip("\n"))
        return "added a table to README.md's Documentation section"
    readme.write_text(text.rstrip("\n") + "\n\n## Documentation\n\n| Doc | What it holds |\n| --- | --- |\n"
                      + row + "\n")
    return "added a Documentation section to README.md"


def create(root: Path, kind: str, topic: str, title: str | None, purpose: str, summary: str = "") -> tuple[int, str]:
    if not re.fullmatch(r"[A-Z][A-Z0-9_]*", topic):
        return 2, f"--topic is upper snake case, like DATA_MODEL (GUIDELINES §3.1): {topic!r}"
    path = doc_path(root, topic)
    if path.exists():
        return 1, f"{path.relative_to(root)} exists — edit it, or pick another topic"
    topic_title = title or title_case(topic)
    body = (TEMPLATES / f"{kind}.md").read_text()
    body = body.replace("{title}", heading(topic_title)).replace("{purpose}", purpose.strip() or
                                                                 "`<What this covers and who needs it, in 1–4 lines.>`")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)
    rel = path.relative_to(root).as_posix()
    listed = list_in_readme(root, rel, topic, summary.strip() or purpose.strip() or f"`<what {topic_title} holds>`")
    return 0, (f"created {rel} ({TYPES[kind]}) — {listed}.\n"
               "next: fill every `<…>` from the code and the person, drop the blocks that stay empty (GUIDELINES "
               "§3.3), then run the doc checks (docs-authoring-and-sync → Checks).")


def self_test() -> int:
    bad = 0
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "README.md").write_text("# X\n\n## Documentation\n\n| Doc | What it holds |\n| --- | --- |\n"
                                        "| [A](docs/A.md) | a |\n\n## License\n")
        saved = (cfg.DOC_PREFIX, cfg.PROJECT_NAME)
        cfg.DOC_PREFIX, cfg.PROJECT_NAME = "ACME", "Acme"
        code, _ = create(root, "system", "DATA_MODEL", None, "What the app stores.")
        doc = (root / "docs/ACME_DATA_MODEL.md").read_text() if code == 0 else ""
        readme = (root / "README.md").read_text()
        checks = [
            (code == 0, "a new doc is created"),
            (doc.startswith("# Acme — Data Model\n"), "its title is the project's"),
            ("What the app stores." in doc and "## 4. Decisions" in doc, "the template is filled in"),
            ("| [DATA_MODEL](docs/ACME_DATA_MODEL.md) | What the app stores. |\n\n## License" in readme,
             "it is listed in README's table, before the next section"),
            (create(root, "system", "DATA_MODEL", None, "x")[0] == 1, "an existing doc is never overwritten"),
            (create(root, "notes", "OPEN_ITEMS", None, "Line one, a | pipe.\nLine two.")[0] == 0
             and "| [OPEN_ITEMS](docs/ACME_OPEN_ITEMS.md) | Line one, a \\| pipe. |\n"
             in (root / "README.md").read_text(),
             "a multi-line purpose becomes one README cell, its first sentence, with `|` escaped"),
            (create(root, "config", "BUILD", None, "Long purpose. More.", "Build settings.")[0] == 0
             and "| [BUILD](docs/ACME_BUILD.md) | Build settings. |" in (root / "README.md").read_text(),
             "--summary sets the README description"),
            (create(root, "rules", "data-model", None, "x")[0] == 2, "a topic not in upper snake case is refused"),
            (all((TEMPLATES / f"{t}.md").is_file() for t in TYPES), "every type has its template"),
        ]
        cfg.DOC_PREFIX, cfg.PROJECT_NAME = saved
    for ok, what in checks:
        if not ok:
            bad += 1
            print(f"FAIL  {what}")
    print(f"new_doc self-test: {len(checks) - bad}/{len(checks)} cases pass")
    return 1 if bad else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--type", choices=sorted(TYPES))
    parser.add_argument("--topic", help="upper snake case: DATA_MODEL, NAVIGATION, DESIGN_SYSTEM_USAGE")
    parser.add_argument("--title", help="the topic in title case, when the default from --topic is wrong")
    parser.add_argument("--purpose", default="", help="1–4 lines: what the doc covers and who needs it")
    parser.add_argument("--summary", default="", help="one line for README's Documentation table; the purpose's first "
                        "sentence by default")
    parser.add_argument("--list", action="store_true", help="the types and what each opens with")
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()
    if args.test:
        return self_test()
    if args.list:
        for t, what in TYPES.items():
            print(f"{t:13} {what}")
        return 0
    if not args.type or not args.topic:
        parser.error("--type and --topic are needed (or --list)")
    code, message = create(cfg.ROOT, args.type, args.topic, args.title, args.purpose, args.summary)
    print(message, file=sys.stderr if code else sys.stdout)
    return code


if __name__ == "__main__":
    sys.exit(main())
