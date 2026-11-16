#!/usr/bin/env python3
"""S4 of the docs-authoring-and-sync checks: every `##` is in its doc's contents table, every `#anchor` link in the
docs, README and the kit resolves, and every `<DOC> §n` cited in them and in the code names a real heading.

    python3 .agents/skills/docs-authoring-and-sync/scripts/check_anchors.py

A doc is cited by its file name without the project's doc prefix: `docs/<PREFIX>_DATA_MODEL.md` is cited
`DATA_MODEL §2.3`. Rules kept in the kit count as docs too: `.agents/HARNESS.md` is `HARNESS`, a skill's reference
is cited by its title in capitals (`# Documentation Guidelines` → `DOCUMENTATION_GUIDELINES`), and the design brief by
its name (`DESIGN.md` → `DESIGN`). `GUIDELINES` is short for `DOCUMENTATION_GUIDELINES`.

In the code and the kit's scripts (comments, docstrings, messages) it also fails a `§` with no doc name before it —
a named citation, a list after one (`DESIGN §6, §9`, `§6 / §7`, `§§4-5`), or a name ending the line before — and a
line-number reference (`file.ext:N`, `#LN`, `file.ext line N`, `see line N`) (GUIDELINES §4.8). Examples in backticks
are skipped. Inside a Markdown doc, a bare `§n` is that doc's own section. Anchors follow GitHub's slugs (GUIDELINES §3.5): lowercase, spaces to `-`,
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
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _config as project  # noqa: E402 — .agents/project.py when present, else the skill's defaults

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
    if re.match(r'\.agents/skills/[^/]+/references/', path):
        # A rule kept in a skill is cited by its title: `# Documentation Guidelines` → DOCUMENTATION_GUIDELINES.
        with open(path, encoding='utf-8') as fh:
            title = fh.readline().lstrip('#').strip().split(' — ')[-1]
        return re.sub(r'[^A-Za-z0-9]+', '_', title).strip('_').upper()
    base = os.path.basename(path)[:-3]
    prefix = project.DOC_PREFIX + '_' if project.DOC_PREFIX else None
    return base[len(prefix):] if prefix and base.startswith(prefix) else base


LINE_REF = re.compile(r'#L\d+\b|\b[\w./-]+\.(?:py|js|jsx|ts|tsx|mjs|swift|kt|java|css|scss|go|rs|rb|dart|c|cc|cpp|h|sh'
                      r'|md|json|ya?ml|toml):\d+\b|\b[\w./-]+\.\w+ lines? \d+\b|\bsee lines? \d+\b')
SECTION = re.compile('§\\s?\\d')
# What may sit between a named citation and the next in a list: `, §4`, `–§6`, ` / §7`, `§§4-5`, `; see also §2`.
CONTINUES = re.compile('^(?:[\\s,;/–—\\-()§\\d.]|and|or|see|also)*$')


def comment_files():
    """The code and the kit's own scripts — where a citation sits in a comment, not in a doc's prose (GUIDELINES §4.8)."""
    code = subprocess.run(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '--', *project.code_pathspec()],
                          capture_output=True, text=True).stdout.splitlines()
    kit = glob.glob('.agents/**/*.py', recursive=True) + glob.glob('.agents/**/*.sh', recursive=True) \
        + glob.glob('.agents/githooks/*') + glob.glob('.github/**/*.yml', recursive=True)
    return sorted({f for f in code + kit if os.path.isfile(f) and not f.endswith('.md') and '__pycache__' not in f})


def comment_citations(cite) -> list[str]:
    """A `§n` with no doc name before it, and a line-number reference, in the code and the kit's scripts. A name on the
    line before counts, for a citation wrapped across lines (GUIDELINES §4.8)."""
    hits = []
    for f in comment_files():
        try:
            lines = open(f, encoding='utf-8').read().splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        for i, raw in enumerate(lines):
            text = re.sub(r'`[^`]*`', lambda m: ' ' * len(m.group()), raw)  # an example in backticks is not a citation
            text = text.replace(chr(167) * 2, chr(167))  # a range sign, `DESIGN §§4-5`, reads as one
            for m in LINE_REF.finditer(text):
                hits.append(f'{f}:{i + 1}: a line-number reference ({m.group(0)}) — cite the file and symbol instead')
            if '§' not in text:
                continue
            spans = [m.span() for m in cite.finditer(text)]
            prev = lines[i - 1] if i else ''
            for m in SECTION.finditer(text):
                if any(s <= m.start() < e for s, e in spans):
                    continue  # part of a named citation
                ends = [e for s, e in spans if e <= m.start()]
                if ends and CONTINUES.match(text[max(ends):m.start()]):
                    continue  # a list after a named citation: `DESIGN §2, §4`
                if not text[:m.start()].strip(' #/*"\'-`(') and cite.search(prev.rstrip() + ' ' + chr(167) + '1'):
                    continue  # wrapped: the name ends the line before
                hits.append(f'{f}:{i + 1}: a § citation with no doc name — cite it as `DOC §n`')
    return hits


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

    hits += comment_citations(cite)

    print('\n'.join(hits))
    print(f'S4 contents rows, anchors and § citations — {len(hits)} hits (baseline {BASELINE})')
    if len(hits) > BASELINE:
        print(f'    FAIL — over the baseline of {BASELINE}: fix the link, the citation or the heading')
        raise SystemExit(1)


if __name__ == '__main__':
    main()
