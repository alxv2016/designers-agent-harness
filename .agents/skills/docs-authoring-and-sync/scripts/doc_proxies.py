#!/usr/bin/env python3
"""The doc-reviewer judge's measured proxies, on what the change wrote in the docs: what a reviewer otherwise judges
by eye, as numbers with a range. A proxy outside its range caps its quality dimension at 2; it never fails a run.

    python3 .agents/skills/docs-authoring-and-sync/scripts/doc_proxies.py          # the change: its sections and lines
    python3 .agents/skills/docs-authoring-and-sync/scripts/doc_proxies.py --all    # every doc whole: the audit
    python3 .agents/skills/docs-authoring-and-sync/scripts/doc_proxies.py FILE …   # these docs, whole
    python3 .agents/skills/docs-authoring-and-sync/scripts/doc_proxies.py --self-test

A review scores the change, an audit the product: bare, only the changed docs are read, and in each only what the
diff against HEAD touched — the paragraphs and bullets on a changed line, the sections that hold one (a new doc: all
of it); a sentence the change never touched never caps its review. Measures, by dimension (the keys of
.agents/evals/weights.json):
  plain         the mean sentence length, at most 25 words, and the longest, at most 50 — [J] plain-language limits
                (GOV.UK's 25 words a sentence); code, tables and headings are not prose and are left out
  answer-first  the share of sections (## and ###) whose first line is the answer — a rule or what the section holds,
                not a preamble ("This section…", "The following…", a line ending in a colon, a table or a list
                first); at least 0.9 (GUIDELINES §3.6, a heuristic)
  accuracy      history words — used to, was, were, former, formerly, originally, until recently, closed on — none
                (GUIDELINES §4.3: the current state, not history)
  concise       sentences of 12 words or more found word for word in another doc: one home per rule, none
                (GUIDELINES §5)
Docs are docs/*.md, DESIGN.md, README.md, AGENTS.md, .agents/HARNESS.md and the skills' references/*.md. Writes
.cache/harness/proxies/doc-reviewer.json — {"judge", "at", "scope": "change" | "product" | "files", "metrics":
[{"dimension", "name", "value", "range": [lo, hi], "ok", "where", "offenders"?, "base"?, "base_offenders"?}]} — and
prints a summary. In the change's scope each metric carries its `base`: its value over the lines of HEAD's doc the
change replaced (null: none there). The sentences, sections and history words out of range are `offenders`, keyed by
their normalised words, and `base_offenders` are HEAD's whole doc's — so verify.py caps only what the change made
worse, and a sentence re-wrapped or moved is carried debt (.agents/HARNESS.md §12.5). Python 3.9+, standard library
only.
"""

from __future__ import annotations

import argparse
import glob
import json
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip()
            or ".")
PROXIES = ROOT / ".cache/harness/proxies"
DOC_GLOBS = ("docs/*.md", "DESIGN.md", "README.md", "AGENTS.md", ".agents/HARNESS.md", ".agents/skills/*/references/*.md")
MEAN_WORDS, LONGEST_WORDS, ANSWER_FIRST, ONE_HOME_WORDS = 25, 50, 0.9, 12
HISTORY = re.compile(r"\b(?:used to|was|were|former|formerly|originally|until recently|closed on)\b", re.I)
PREAMBLE = re.compile(r"^(?:this (?:section|doc|document|page|chapter|part)\b|in this (?:section|doc|document)\b|here (?:we|you)\b"
                      r"|below\b|the following\b|we\b|let's\b|let us\b|overview\b|introduction\b|as (?:mentioned|noted|described)\b"
                      r"|note that\b|before (?:we|you)\b)", re.I)


def all_docs() -> list:
    found = set()
    for pattern in DOC_GLOBS:
        found.update(str(Path(p).relative_to(ROOT)) for p in glob.glob(str(ROOT / pattern)))
    return sorted(found)


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, errors="replace").stdout


def changed_docs() -> list:
    changed = set(git("diff", "--name-only", "HEAD").split()) | set(git("ls-files", "--others", "--exclude-standard")
                                                                    .split())
    return [d for d in all_docs() if d in changed]


def changed_lines(path: str) -> set | None:
    """The doc's lines the change wrote, numbered in the new file; None when the doc is new (all of it)."""
    if git("ls-files", "--", path).strip() == "":
        return None
    lines: set = set()
    for m in re.finditer(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", git("diff", "-U0", "HEAD", "--", path), re.M):
        start, count = int(m.group(1)), int(m.group(2) if m.group(2) is not None else 1)
        lines.update(range(start, start + count))
    return lines


# --- Reading a doc as prose ---------------------------------------------------------------------------------------------

INLINE = [(re.compile(r"`[^`]*`"), "code"), (re.compile(r"!\[[^\]]*\]\([^)]*\)"), " "),
          (re.compile(r"\[([^\]]*)\]\([^)]*\)"), r"\1"), (re.compile(r"\*\*|__|(?<!\w)[*_](?!\s)|(?<!\s)[*_](?!\w)"), ""),
          (re.compile(r"<[^>]+>"), " ")]


def plain_text(s: str) -> str:
    for rx, rep in INLINE:
        s = rx.sub(rep, s)
    return " ".join(s.split())


def blocks(text: str) -> list:
    """[(line, kind, text, last line)]: each prose unit — a paragraph or a bullet, joined across its lines — and each
    heading (kind "h2"/"h3"/…), table, fence and other line kind, in order."""
    out, lines = [], text.split("\n")
    i, n = 0, len(lines)
    if lines and lines[0].strip() == "---":  # front matter
        i = next((k + 1 for k in range(1, n) if lines[k].strip() == "---"), 0)
    unit, start = [], 0

    def flush():
        nonlocal unit
        if unit:
            out.append((start, "prose", " ".join(unit), start + len(unit) - 1))
            unit = []

    while i < n:
        raw = lines[i]
        s = raw.strip()
        if s.startswith(("```", "~~~")):
            flush()
            fence, k = s[:3], i + 1
            while k < n and not lines[k].strip().startswith(fence):
                k += 1
            out.append((i + 1, "fence", "", min(k + 1, n)))
            i = k + 1
            continue
        if not s or s.startswith("<!--"):
            flush()
        elif s.startswith("#"):
            flush()
            level = len(s) - len(s.lstrip("#"))
            out.append((i + 1, f"h{level}", s.lstrip("#").strip(), i + 1))
        elif s.startswith("|"):
            flush()
            if out and out[-1][1] == "table" and out[-1][3] == i:
                out[-1] = out[-1][:3] + (i + 1,)
            else:
                out.append((i + 1, "table", "", i + 1))
        elif s.startswith(">"):
            flush()
            out.append((i + 1, "quote", s.lstrip("> "), i + 1))
        elif re.match(r"^(?:[-*+]|\d+[.)])\s", s):
            flush()
            unit, start = [re.sub(r"^(?:[-*+]|\d+[.)])\s+", "", s)], i + 1  # a list item is prose
        else:
            if not unit:
                start = i + 1
            unit.append(s)
        i += 1
    flush()
    return out


def sentences(prose: str) -> list:
    text = plain_text(prose)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"(“])|(?<=:)\s+(?=[A-Z])|\s+—\s+(?=[A-Z])", text)
    return [p.strip() for p in parts if re.search(r"[A-Za-z]", p)]


def words(sentence: str) -> int:
    return len(re.findall(r"[A-Za-z0-9][\w'’.%-]*", sentence))


def normal(sentence: str) -> str:
    return re.sub(r"[^\w ]", "", sentence.lower()).strip()


# --- The proxies --------------------------------------------------------------------------------------------------------

def metric(dimension: str, name: str, value: float, lo: float, hi: float, where: str,
           offenders: dict | None = None) -> dict:
    """A metric; `offenders`, {place: how bad}, names what is out of range by a key an edit elsewhere keeps — the
    normalised sentence, the section's heading — so verify.py can tell carried debt from new."""
    out = {"dimension": dimension, "name": name, "value": value, "range": [lo, hi], "ok": lo <= value <= hi,
           "where": where}
    if offenders is not None:
        out["offenders"] = offenders
    return out


def opens_with_answer(first: tuple | None) -> bool:
    if first is None:
        return True  # an empty section is another check's
    line, kind, text = first[:3]
    if kind != "prose":
        return False  # a table, a fence or a quote first: the answer is not the first line
    t = plain_text(text)
    return not PREAMBLE.match(t) and not t.rstrip().endswith(":")


def touched(first: int, last: int, lines: set | None) -> bool:
    return lines is None or any(first <= n <= last for n in lines)


def section_spans(bl: list) -> list:
    """[(index of the ## or ### heading, its line, the last line before the next heading)] — a section's own text,
    its subsections left to themselves."""
    heads = [(k, b[0]) for k, b in enumerate(bl) if re.fullmatch(r"h[1-6]", b[1])]
    out = []
    for j, (k, line) in enumerate(heads):
        if bl[k][1] in ("h2", "h3"):
            out.append((k, line, heads[j + 1][1] - 1 if j + 1 < len(heads) else bl[-1][3]))
    return out


def measure_doc(doc: str, text: str, homes: dict, lines: set | None = None) -> list:
    """The doc's metrics; with `lines`, only from the prose on those lines and the sections that hold one."""
    bl = blocks(text)
    seen: dict = {}

    def nth(kind: str, key: str) -> str:
        """A place's key with its occurrence in the whole doc — counted over lines the change never touched too, as
        HEAD's whole doc counts them — so a second copy the change adds is a new place."""
        seen[(kind, key)] = seen.get((kind, key), 0) + 1
        return key if seen[(kind, key)] == 1 else f"{key} #{seen[(kind, key)]}"

    sents = []
    for line, kind, t, last in bl:
        if kind == "prose":
            for s in sentences(t):
                place = nth("sentence", normal(s)[:200])
                if touched(line, last, lines):
                    sents.append((line, s, place))
    out = []
    if sents:
        lengths = [words(s) for _, s, _ in sents]
        mean = sum(lengths) / len(lengths)
        k = max(range(len(lengths)), key=lengths.__getitem__)
        out.append(metric("plain", f"mean sentence length (words) {doc}", round(mean, 1), 0, MEAN_WORDS,
                          f"{doc}: {len(sents)} sentences"))
        out.append(metric("plain", f"longest sentence (words) {doc}", lengths[k], 0, LONGEST_WORDS,
                          f"{doc}:{sents[k][0]} \"{sents[k][1][:90]}…\"",
                          {p: n for (_, _, p), n in zip(sents, lengths) if n > LONGEST_WORDS}))
    # Answer first: each ## and ### section's first content — with `lines`, each section the change wrote in.
    sections, misses, missed = 0, [], {}
    for idx, line, end in section_spans(bl):
        t = bl[idx][2]
        place = nth("section", f"§{t}")
        if not touched(line, end, lines):
            continue
        sections += 1
        first = bl[idx + 1] if idx + 1 < len(bl) else None
        if first is not None and first[1].startswith("h"):
            first = None  # a heading straight away: an empty section, or one that holds only its subsections
        if not opens_with_answer(first):
            misses.append(f"{doc}:{line} §{t[:40]}")
            missed[place] = 1
    if lines is not None and not sents and not sections:
        return out  # the change wrote no prose and no section here: a table, a fence, a heading's level
    if sections:
        share = (sections - len(misses)) / sections
        out.append(metric("answer-first", f"sections that open with the answer {doc}", round(share, 3), ANSWER_FIRST, 1,
                          f"{len(misses)} of {sections}: " + ("; ".join(misses[:3]) or "every section"), missed))
    # History words, in prose only — each kept with the sentence it stands in.
    hist, used = [], {}
    for line, kind, t, last in bl:
        if kind == "prose":
            quoted = re.sub(r"(?<![*\w])\*[^*\s][^*]*\*(?!\*)|\"[^\"]*\"|“[^”]*”", " ", t)  # a word named, not used
            for s in sentences(quoted):
                for m in HISTORY.finditer(s):
                    place = nth("history", f"{m.group(0).lower()}: {normal(s)[:160]}")
                    if touched(line, last, lines):
                        hist.append(f"{doc}:{line} \"{m.group(0)}\"")
                        used[place] = 1
    out.append(metric("accuracy", f"history words {doc}", len(hist), 0, 0, "; ".join(hist[:4]) or f"{doc}: none",
                      used))
    # One home: a long sentence word for word in another doc.
    dupes, shared = [], {}
    for line, s, place in sents:
        if words(s) >= ONE_HOME_WORDS:
            others = [d for d in homes.get(normal(s), ()) if d != doc]
            if others:
                dupes.append(f"{doc}:{line} also in {others[0]}: \"{s[:70]}…\"")
                shared[place] = 1
    out.append(metric("concise", f"sentences found word for word in another doc {doc}", len(dupes), 0, 0,
                      "; ".join(dupes[:3]) or f"{doc}: none", shared))
    return out


# --- The base: what the change's lines held at HEAD, so verify.py caps only what the change made -------------------

def at_head(path: str) -> str | None:
    """The file as HEAD holds it; None when HEAD does not have it."""
    proc = subprocess.run(["git", "show", f"HEAD:{path}"], cwd=ROOT, capture_output=True, text=True, errors="replace")
    return proc.stdout if proc.returncode == 0 else None


def old_lines(path: str) -> set:
    """The lines of HEAD's version the change replaced, and for a pure insertion the line it follows."""
    lines: set = set()
    for m in re.finditer(r"^@@ -(\d+)(?:,(\d+))? \+\d+(?:,\d+)? @@", git("diff", "-U0", "HEAD", "--", path), re.M):
        start, count = int(m.group(1)), int(m.group(2) if m.group(2) is not None else 1)
        lines.update(range(start, start + count) if count else {start} if start else set())
    return lines


def with_base(metrics: list, scoped: list, whole: list) -> list:
    """Each metric with `base` — its value over the lines the change replaced (null: no such metric there) — and, where
    it names offenders, `base_offenders` from HEAD's whole doc: a sentence moved or re-wrapped is carried, not new."""
    by_scoped = {m["name"]: m for m in scoped}
    by_whole = {m["name"]: m for m in whole}
    for m in metrics:
        b = by_scoped.get(m["name"])
        m["base"] = b["value"] if b else None
        if "offenders" in m:
            m["base_offenders"] = (by_whole.get(m["name"]) or {}).get("offenders", {})
    return metrics


def homes_at_head(docs: list) -> dict:
    """homes_of over HEAD's docs."""
    homes: dict = {}
    for d in docs:
        text = at_head(d)
        for _, kind, t, _ in blocks(text or ""):
            if kind == "prose":
                for s in sentences(t):
                    if words(s) >= ONE_HOME_WORDS:
                        homes.setdefault(normal(s), set()).add(d)
    return homes


def homes_of(docs: list) -> dict:
    """normalised long sentence -> the docs that hold it."""
    homes: dict = {}
    for d in docs:
        try:
            text = (ROOT / d).read_text(errors="replace")
        except OSError:
            continue
        for _, kind, t, _ in blocks(text):
            if kind == "prose":
                for s in sentences(t):
                    if words(s) >= ONE_HOME_WORDS:
                        homes.setdefault(normal(s), set()).add(d)
    return homes


def write(judge: str, metrics: list, scope: str, in_scope: list | None = None, what: str = "") -> Path:
    """The results; `in_scope` names what was measured — empty, the change is out of this judge's scope."""
    PROXIES.mkdir(parents=True, exist_ok=True)
    path = PROXIES / f"{judge}.json"
    at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    path.write_text(json.dumps({"judge": judge, "at": at, "scope": scope, "scope_what": what,
                                "in_scope": in_scope or [], "metrics": metrics}, indent=1, ensure_ascii=False) + "\n")
    return path


def self_test() -> int:
    failures = []

    def check(ok: bool, what: str):
        if not ok:
            failures.append(what)

    doc = """---
name: x
---
# Title

## 1. Rules

**Take every colour from a token.** A literal drifts from the theme.

- **Name the thing.** Say `color.text` and not the grey text colour, which is what this list item says in a long way.

## 2. How it works

This section explains how it works.

## 3. Values

| a | b |
| --- | --- |

## 4. History

The value was 15 px until recently.

```c
was = 1;  // not prose
```
"""
    shared = "Every screen takes its colours from the tokens that DESIGN.md names in its front matter."
    homes = {normal(shared): {"docs/A.md", "docs/B.md"}}
    ms = measure_doc("docs/A.md", doc + "\n" + shared + "\n", homes)
    by = {m["name"].rsplit(" ", 1)[0]: m for m in ms}
    af = by.get("sections that open with the answer")
    check(af is not None and af["value"] == 0.5, f"2 of 4 sections open with the answer: {af and af['value']}")
    check(af is not None and "\u00a72. How it works" in af["where"] and "\u00a73. Values" in af["where"], "the preamble and the "
          "table-first sections are named")
    hist = by.get("history words")
    check(hist is not None and hist["value"] == 2, f"'was' and 'until recently' in prose, none in code: {hist}")
    dup = by.get("sentences found word for word in another doc")
    check(dup is not None and dup["value"] == 1 and "docs/B.md" in dup["where"], f"the shared sentence: {dup}")
    check(sentences("One. Two words here. Three: Four.") == ["One.", "Two words here.", "Three:", "Four."],
          f"sentences split: {sentences('One. Two words here. Three: Four.')}")
    check(words(plain_text("Take `x` from [the token](a.md), 16 px.")) == 7, "inline code is a word, a link its text")
    longest = by.get("longest sentence (words)")
    check(longest is not None and longest["value"] >= 15, "the long bullet is the longest sentence")
    check(not opens_with_answer((1, "prose", "The following lists the rules:")), "a colon-ended lead is a preamble")
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "d.md"
        p.write_text(doc)
        check(blocks(p.read_text())[0][1] == "h1", "front matter is skipped")
    # The change's scope: a long sentence in a section the change never touched caps nothing.
    long = "## 5. Long\n\n" + " ".join(["word"] * 60) + ".\n"
    text = doc + long
    at = text.split("\n").index("The value was 15 px until recently.") + 1
    ms = {m["name"].rsplit(" ", 1)[0]: m for m in measure_doc("docs/A.md", text, {}, {at})}
    check(ms.get("longest sentence (words)", {}).get("value") == 7, f"only the changed line's sentence is measured: "
          f"{ms.get('longest sentence (words)')}")
    check(ms.get("sections that open with the answer", {}).get("value") == 1.0, "only the changed section is read "
          f"for answer-first: {ms.get('sections that open with the answer')}")
    check(ms.get("history words", {}).get("value") == 2, "history words on the changed line count")
    whole = {m["name"].rsplit(" ", 1)[0]: m for m in measure_doc("docs/A.md", text, {})}
    check(whole["longest sentence (words)"]["value"] == 60, "the audit reads the whole doc, the long sentence in it")
    table = text.split("\n").index("| a | b |") + 1
    names = [m["name"].rsplit(" ", 1)[0] for m in measure_doc("docs/A.md", text, {}, {table})]
    check(names == ["sections that open with the answer", "history words",
                    "sentences found word for word in another doc"], f"a table row changed reads its section, no prose "
          f"sentence: {names}")
    check(measure_doc("docs/A.md", text, {}, set()) == [], "a doc the change wrote nothing in measures nothing")
    # The base: a long sentence re-wrapped is the same offender; one the change wrote is new.
    long_line = next(k for k, ln in enumerate(text.split("\n"), 1) if ln.startswith("word word"))
    wrapped = text.replace(" ".join(["word"] * 60), " ".join(["word"] * 30) + "\n" + " ".join(["word"] * 30))
    now = {m["name"]: m for m in measure_doc("docs/A.md", wrapped, {}, {long_line, long_line + 1})}
    head = measure_doc("docs/A.md", text, {}, {long_line})
    based = {m["name"]: m for m in with_base(list(now.values()), head, measure_doc("docs/A.md", text, {}))}
    lng = based.get("longest sentence (words) docs/A.md", {})
    check(lng.get("base") == 60 and lng.get("offenders") and lng["offenders"].keys() <= lng["base_offenders"].keys(),
          f"a re-wrapped long sentence is the one at the base: {lng}")
    fresh = with_base(measure_doc("docs/B.md", long, {}), [], [])
    lng = next((m for m in fresh if m["name"].startswith("longest")), {})
    check(lng.get("base") is None and lng.get("base_offenders") == {}, f"a new doc's metrics have no base: {lng}")
    hist = by.get("history words") or {}
    check(any(k.startswith("was: the value was 15 px") for k in hist.get("offenders", {})), "a history word is kept "
          f"with its sentence: {hist.get('offenders')}")
    twice = "## 1. A\n\nThis section is one.\n\n## 1. A\n\nThis section is two.\n"
    af = next(m for m in measure_doc("docs/C.md", twice, {}) if m["name"].startswith("sections that open"))
    sign = "§"  # spelled as an escape, so the citation check does not read the fixture as a bare citation
    check(sorted(af["offenders"]) == [f"{sign}1. A", f"{sign}1. A #2"],
          f"the same heading twice is two places: {af['offenders']}")
    # HEAD holds a long sentence once; the change adds it again elsewhere: the copy is a new place, though only its
    # lines are measured and the first copy is untouched.
    copied = text + "\n## 6. Again\n\n" + " ".join(["word"] * 60) + ".\n"
    added = {len(text.split("\n")) + 3}
    lng = next(m for m in measure_doc("docs/A.md", copied, {}, added) if m["name"].startswith("longest"))
    head_lng = next(m for m in measure_doc("docs/A.md", text, {}) if m["name"].startswith("longest"))
    fresh = set(lng["offenders"]) - set(head_lng["offenders"])
    check(len(fresh) == 1 and next(iter(fresh)).endswith(" #2"), f"a second copy of an untouched long sentence is "
          f"new: {sorted(lng['offenders'])} against {sorted(head_lng['offenders'])}")
    for f in failures:
        print(f"FAIL  {f}")
    total = 20
    print(f"doc_proxies self-test: {total - len(failures)} of {total} checks pass")
    return 1 if failures else 0


def main(argv: list) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("files", nargs="*", help="docs to measure (default: those changed against HEAD)")
    parser.add_argument("--all", action="store_true", help="every doc")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    docs = all_docs()
    scope = "files" if args.files else "product" if args.all else "change"
    targets = args.files or (docs if args.all else changed_docs())
    homes = homes_of(sorted(set(docs) | set(targets)))
    base_homes = homes_at_head(docs) if scope == "change" and targets else {}
    metrics, measured = [], []
    for d in targets:
        try:
            lines = changed_lines(d) if scope == "change" else None
            found = measure_doc(d, (ROOT / d).read_text(errors="replace"), homes, lines)
        except OSError as e:
            print(f"doc proxies: cannot read {d}: {e.strerror}")
            continue
        if scope == "change":  # the base: HEAD's doc, over the lines the change replaced and whole
            head = at_head(d)
            found = with_base(found, measure_doc(d, head, base_homes, old_lines(d)) if head is not None else [],
                              measure_doc(d, head, base_homes) if head is not None else [])
        metrics += found
        measured += [d] if found else []
    path = write("doc-reviewer", metrics, scope, measured, "the prose and sections the change wrote in the docs")
    outside = [m for m in metrics if not m["ok"]]
    print(f"doc-reviewer ({scope}{': the changed sections and lines' if scope == 'change' else ''}): {len(targets)} "
          f"docs, {len(metrics)} metrics, {len(outside)} outside their range — {path.relative_to(ROOT)}"
          + ("" if targets else " (no changed doc; --all measures every doc)"))
    dims: dict = {}
    for m in metrics:
        dims.setdefault(m["dimension"], [0, 0])
        dims[m["dimension"]][0] += 1
        dims[m["dimension"]][1] += 0 if m["ok"] else 1
    for dim, (n, bad) in sorted(dims.items()):
        print(f"  {dim:<13} {n:>3} measured  {bad:>3} outside")
    for m in outside[:12]:
        lo, hi = m["range"]
        print(f"  OUT {m['dimension']}: {m['name']} = {m['value']:g} (range {lo:g}–{hi:g}) — {m['where'][:150]}")
    if len(outside) > 12:
        print(f"  … {len(outside) - 12} more in {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
