#!/usr/bin/env python3
"""S4 of the docs-authoring-and-sync checks: every `##` is in its doc's contents table, every `#anchor` link in the
docs, README and the kit resolves, and every `<DOC> §n` cited in them and in the code names a real heading.

    python3 .agents/skills/docs-authoring-and-sync/scripts/check_anchors.py

A doc is cited by its file name without the project's doc prefix (`docs/<PREFIX>_DATA_MODEL.md` → `DATA_MODEL
§2.3`). Rules kept in the kit count as docs too: `.agents/HARNESS.md` is `HARNESS`, and a skill's references are cited
by the skill's name in capitals (`.agents/skills/accessibility/references/*.md` → `ACCESSIBILITY`), and the design brief
by its name (`DESIGN.md` → `DESIGN`). `GUIDELINES` is
short for `DOCUMENTATION_GUIDELINES`. Anchors follow GitHub's slugs (GUIDELINES §3.5): lowercase, spaces to `-`,
punctuation but `-` and `_` dropped, so an em dash leaves `--`.

Prints one line per hit, then a count. Baseline: 0.
"""
import glob
import os
import re
import subprocess
import sys

ROOT = subprocess.run(['git', 'rev-parse', '--show-toplevel'], capture_output=True, text=True).stdout.strip() or '.'
os.chdir(ROOT)
sys.path.insert(0, '.agents')
import project  # noqa: E402

BASELINE = 0
ALIASES = {'GUIDELINES': 'DOCUMENTATION_GUIDELINES'}


def slug(heading):
    heading = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', heading).replace('`', '').replace('*', '')
    return re.sub(r'[^\w\- ]', '', heading.strip().lower()).replace(' ', '-')


def lines_outside_fences(path):
    """(line number, line) for every line outside a code fence; a fence closes only on its own marker."""
    fence = None
    with open(path, encoding='utf-8') as fh:
        for n, line in enumerate(fh, 1):
            m = re.match(r' *(`{3,}|~{3,})', line)
            if m:
                if fence is None:
                    fence = m.group(1)
                elif m.group(1).startswith(fence) and not line.strip()[len(m.group(1)):].strip():
                    fence = None
                continue
            if fence is None:
                yield n, line


def heading_anchors(path):
    found, seen = set(), {}
    for _, line in lines_outside_fences(path):
        m = re.match(r'#{1,6} (.*)', line)
        if m:
            s = slug(m.group(1))
            k = seen.get(s, 0)
            seen[s] = k + 1
            found.add(s if k == 0 else f'{s}-{k}')
    return found


def doc_name(path):
    if path == '.agents/HARNESS.md':
        return 'HARNESS'
    if path == project.DESIGN_FILE:
        return os.path.basename(path)[:-3].upper()
    m = re.match(r'\.agents/skills/([^/]+)/references/', path)
    if m:
        return m.group(1).upper().replace('-', '_')
    base = os.path.basename(path)[:-3]
    prefix = project.DOC_PREFIX + '_' if project.DOC_PREFIX else None
    return base[len(prefix):] if prefix and base.startswith(prefix) else base


def main():
    DOCS = sorted(glob.glob('docs/*.md')) + [f for f in ('.agents/HARNESS.md', project.DESIGN_FILE) if os.path.isfile(f)] \
        + sorted(glob.glob('.agents/skills/*/references/*.md'))

    hits = []
    anchors, nums = {}, {}
    for f in DOCS:
        n, h2, rows, toc = set(), [], [], False
        for _, line in lines_outside_fences(f):
            if line.startswith('| § | Section | Look here for |'):
                toc = True
                continue
            if toc and not line.startswith('|'):
                toc = False
            if toc:
                rows += re.findall(r'\]\(#([^)]+)\)', line)[:1]
            m = re.match(r'(#{1,4}) (.*)', line)
            if not m:
                continue
            if m.group(1) == '##':
                h2.append(slug(m.group(2)))
            num = re.match(r'(\d+(?:\.\d+)*[a-z]?)\.? ', m.group(2))
            if num and len(m.group(1)) > 1:
                n.add(num.group(1))
        anchors[os.path.normpath(f)] = heading_anchors(f)
        name = doc_name(f)
        nums[name] = nums.get(name, set()) | n
        for s in h2:
            if rows and s not in rows:
                hits.append(f'{f}: ## #{s} is not in the contents table')

    names = '|'.join(sorted(list(nums) + list(ALIASES), key=len, reverse=True))
    cite = re.compile(r'(?:' + (re.escape(project.DOC_PREFIX) + '_|' if project.DOC_PREFIX else '') + r'\b)(' + names
                      + r')(?:\.md)?\]?(?:\([^)]*\))?\)?,? §(\d+(?:\.\d+)*[a-z]?)')
    link = re.compile(r'\]\(([\w./-]*\.md)?#([^)\s]+)\)')

    # Markdown is read outside its fences; code is grepped whole — a citation in a code comment counts.
    markdown = DOCS + [f for f in ('README.md', 'AGENTS.md', 'CONTRIBUTING.md') if os.path.isfile(f)] \
        + sorted(set(glob.glob('.agents/**/*.md', recursive=True)) - set(DOCS))
    sources = [(f, n, line) for f in markdown for n, line in lines_outside_fences(f)]
    code = subprocess.run(['git', 'grep', '--untracked', '-nIE', '§[0-9]', '--', *project.code_pathspec()],
                          capture_output=True, text=True).stdout
    for line in code.splitlines():
        parts = line.split(':', 2)
        if len(parts) == 3:
            sources.append((parts[0], parts[1], parts[2]))

    for f, ln, text in sources:
        text = re.sub(r'`[^`]*`', '', text) if f.endswith('.md') else text  # an example in backticks is not a citation
        for d, n in cite.findall(text):
            if d in ALIASES:
                d = ALIASES[d]
            if d in nums and n.rstrip('.') not in nums[d]:
                hits.append(f'{f}:{ln}: {d} §{n} names no heading')
        for t, a in (link.findall(text) if f.endswith('.md') else []):
            tgt = os.path.normpath(os.path.join(os.path.dirname(f), t)) if t else os.path.normpath(f)
            if tgt not in anchors and os.path.isfile(tgt):
                anchors[tgt] = heading_anchors(tgt)
            if tgt in anchors and a not in anchors[tgt]:
                hits.append(f'{f}:{ln}: #{a} does not resolve in {tgt}')

    print('\n'.join(hits))
    print(f'S4 contents rows, anchors and § citations — {len(hits)} hits (baseline {BASELINE})')
    if len(hits) > BASELINE:
        print(f'    FAIL — over the baseline of {BASELINE}: fix the link, the citation or the heading')
        raise SystemExit(1)


if __name__ == '__main__':
    main()
