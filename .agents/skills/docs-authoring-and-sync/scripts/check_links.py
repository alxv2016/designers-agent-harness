#!/usr/bin/env python3
"""S15 of the docs-authoring-and-sync checks: every relative link in the repo's Markdown — the kit (`.agents/`),
`docs/`, AGENTS.md, DESIGN.md and README.md — points at a file that exists, and its `#anchor`, if any, at a real heading.

    python3 .agents/skills/docs-authoring-and-sync/scripts/check_links.py            # every Markdown file
    python3 .agents/skills/docs-authoring-and-sync/scripts/check_links.py FILE.md …  # some files

A link inside a code fence or inside backticks is an example, not a link. Prints one line per broken link, then a
count. Baseline: 0.
"""
import glob
import os
import re
import subprocess
import sys

ROOT = subprocess.run(['git', 'rev-parse', '--show-toplevel'], capture_output=True, text=True).stdout.strip() or '.'
os.chdir(ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_anchors import heading_anchors, lines_outside_fences  # noqa: E402

_anchors = {}


def anchors(path):
    if path not in _anchors:
        _anchors[path] = heading_anchors(path)
    return _anchors[path]


files = sys.argv[1:] or sorted(set(glob.glob('.agents/**/*.md', recursive=True) + glob.glob('docs/**/*.md',
                                   recursive=True) + [f for f in ('AGENTS.md', 'README.md', 'CLAUDE.md',
                                                                  'CONTRIBUTING.md', 'DESIGN.md') if os.path.isfile(f)]))
hits = []
for f in files:
    for n, line in lines_outside_fences(f):
        for target in re.findall(r'\]\(([^)\s]+)\)', re.sub(r'`[^`]*`', '', line)):
            if re.match(r'[a-z]+:', target):
                continue
            path, _, frag = target.partition('#')
            full = os.path.normpath(os.path.join(os.path.dirname(f), path)) if path else f
            if not os.path.exists(full):
                hits.append(f'{f}:{n}: {path} does not exist')
            elif frag and full.endswith('.md') and frag not in anchors(full):
                hits.append(f'{f}:{n}: #{frag} does not resolve in {full}')

print('\n'.join(hits))
print(f'S15 links — {len(hits)} hits in {len(files)} files (baseline 0)')
if hits:
    print('    FAIL — over the baseline of 0: fix the link or the heading')
    raise SystemExit(1)
