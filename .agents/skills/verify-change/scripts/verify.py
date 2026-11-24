#!/usr/bin/env python3
"""The verify-change loop's fixed part: picks the checks and the judges a change needs from the files it touches, runs
the checks in parallel, keeps the task's state, records the judges' verdicts and the person's approvals, counts failed
attempts, stops at the retry limit, and refuses a hand-over while anything is open (.agents/HARNESS.md §4–§5;
docs/AGENT_HARNESS.md §10).

    verify.py start "<task>"          # a new task: state reset, the last one kept in history/
    verify.py run [--only docs,harness,design,<the project's checks>]
    verify.py review <judge> pass|blocking [--note TEXT] [--score dim=0-4|na,... | --scores-file F | --out-of-scope]
                      [--no-proxy]   # --out-of-scope: refused unless the judge's proxy shows its scope empty
                      # with a score, --note gives a reason per dimension: "dim: why; dim: why"; the judge's proxy
                      # runs first on the change, and caps only from what the change made worse than at the base
                      [--nit "path:line[-line] TEXT" …]   # approve with nits: each nit with its lines
    verify.py nits-fixed <judge>      # a pass re-stamped when every hunk since lies within a few lines of a nit
    verify.py delta <judge>           # the diff since the judge's snapshot, with its verdict, note and nits
    verify.py ask <judge>             # before briefing a judge: its files kept as it reads them, for its review
    verify.py selfcheck               # the fast checks on the changed files, before asking the judges
    verify.py proxies [--judge J] [--all]   # run the measured proxies on the change (--all: the product), print caps
    verify.py accept <judge> "<the person's words>"   # they accept a quality score below the bar
    verify.py taste "<the person's words>" --judge J --dimension D [--anchor FILE] [--good|--poor]
    verify.py rate <file> --judge J --dimension D --score 0-4 [--note TEXT]   # the person's own score
    verify.py weight --judge J --dimension D --set N [--words TEXT]           # the person sets a weight
    verify.py audit <judge> [--scores-file F] [--note TEXT] [--no-proxy]   # the whole product, in scores.jsonl
    verify.py approve <file> --kind ux|mock|motion|copy|built|kit [--note TEXT]   # the person's yes, naming the file
    verify.py decision "<what the person decided>"   # settled for this task: the judges read it in `status`
    verify.py target --where "<where it ran>" --build "<which build>" [--health-exit N] [--note TEXT]   # every run
    verify.py signoff "<what the person judged on the target>"   # their yes on the target, in their words
    verify.py finding "<what was seen or learned>" --route test|rubric|guard|skill|doc|open-item|none [--for-run N]
                      [--source person|agent] [--about AREA] [--judge AGENT --caught yes|no] [--edit PATH]
    verify.py decline <file> "<what the person said>" --kind ux|option|mock|motion|copy|built|kit --about AREA
                      --route ROUTE [--judge AGENT] [--edit PATH]   # the person's no, routed like a lesson
    verify.py dispute <judge> "<what the judge flagged that was not a problem>" [--source agent|person] [--about AREA]
                      [--edit PATH]
    verify.py kitdiff <file>          # the whole diff of the skills and agents, new files too, for a kit yes
    verify.py status | finish | calibration | doctor
    verify.py unverified [--hook]     # the tree changed since the last run? --hook: the agents' Stop hook

Run it with python3 from the repo root. The project's checks, judges and gates come from .agents/project.py.

State is .cache/harness/task.json (git-ignored). `finding`, `decline`, `dispute` and `approve` also append to
.agents/evals/judgements.jsonl (committed), which `calibration` reads — never put a token, a key, a password or a
person's data in their text. `finish` refuses a lesson whose route's edit is not in the change — made after it was
recorded, or named with --edit — and a rubric lesson that added no learned item to that agent's rubric.
The quality layer keeps its weights in .agents/evals/weights.json, the scores, ratings and taste in
.agents/evals/scores.jsonl and the anchors in .agents/evals/anchors/ (committed; .agents/HARNESS.md §12). Every write
to task.json, weights.json, scores.jsonl and judgements.jsonl goes to a temp file, os.replace'd over, under an
fcntl.flock kept in .cache/harness/locks/. The guard asks the person before the commands that record their words —
approve, decline, signoff, accept, taste, weight, rate.

Exit status: 0 pass, 1 a check failed or `finish` found something open, 2 usage, 3 the retry limit is reached — stop
and ask the person.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import importlib.util
import io
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import tokenize
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

try:
    import fcntl  # the writes' lock; absent on Windows, where the writes are still atomic
except ImportError:  # pragma: no cover
    fcntl = None

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / ".agents"))
import project  # noqa: E402 — the project's facts: .agents/project.py

STATE = ROOT / ".cache/harness"
TASK = STATE / "task.json"
JUDGEMENTS = ROOT / ".agents/evals/judgements.jsonl"
# The quality layer (.agents/HARNESS.md §12): weights per judge and dimension, the scores and the person's taste,
# the anchors, and each judge's measured proxies.
EVALS = ".agents/evals/"
WEIGHTS = ROOT / EVALS / "weights.json"
SCORES = ROOT / EVALS / "scores.jsonl"
ANCHORS = ROOT / EVALS / "anchors"
PROXY_DIR = STATE / "proxies"
QUALITY_BAR = getattr(project, "QUALITY_BAR", 75)
PROXIES = getattr(project, "PROXIES", {})
SCORE_MAX = 4         # each dimension 0–4 against its anchors
PROXY_CAP = 2         # a measured proxy out of its range caps its dimension here
WEIGHT_MIN, WEIGHT_MAX = 5, 40
MISS_RAISE = 0.2      # a taste miss raises its dimension's weight by 20 %
OUT_OF_SCOPE = "out of scope"  # a review whose judge's measured scope the change never touches: no score, no bar
NA_FLOOR = 0.6        # at least 60 % of a judge's weight scored, or the review's score is refused
SCOPE_CHANGE, SCOPE_PRODUCT = "change", "product"  # a review measures the change; an audit the whole product
PROXY_PRODUCT_FLAG = "--all"  # every proxy script's switch from the change to the whole product
MAX_FAILURES = 3
SKILLS = ".agents/skills"
DOC_SCRIPTS = f"{SKILLS}/docs-authoring-and-sync/scripts"
TOKEN_CHECK = f"{SKILLS}/design-system/scripts/token_check.py"
DESIGN_CHECK = f"{SKILLS}/design-system/scripts/design_check.py"
A11Y_SKILL = f"{SKILLS}/accessibility/"
A11Y_SCRIPTS = f"{A11Y_SKILL}scripts"
HARNESS_TESTS = (".agents/hooks/guard.py", ".agents/hooks/untrusted.py", ".agents/skills/verify-change/scripts/verify.py")
ROUTES = ["test", "rubric", "guard", "skill", "doc", "open-item", "none"]
# What a lesson is about, so calibration can show an area that keeps coming back (AGENT_HARNESS §9.4).
AREAS = ("flow", "states", "structure", "words", "layout", "type", "colour", "components", "motion", "gesture",
         "accessibility", "code", "docs", "harness")
REPEAT_AT = 3  # lessons in one area before calibration asks for a check, a principle or a skill's Never
RUBRICS = ROOT / ".agents/rubrics"
LEARNED_ROW = re.compile(r"^\|\s*(L\d+)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*$")
KINDS_BEFORE = ("ux", "mock", "motion", "copy")  # a draft, approved before the build; `ux` is the UX brief
KINDS_AFTER = ("built", "kit")            # the built thing beside its draft; a change to a skill or an agent —
                                          # approved after, and held against the files as they were at the yes
KIND_NAMES = {"ux": "UX brief", "mock": "mock", "motion": "motion study", "copy": "copy",
              "built": "built screen beside its mock", "kit": "change to a skill or an agent"}
# The person's word that waives a gate: no visible change waives every gate but the kit's; a design they gave waives
# the draft.
NO_VISIBLE_CHANGE = "no visible change"
DESIGN_GIVEN = "design given"

# --- Which files call for which check and which judge (.agents/HARNESS.md §4) -----------------------------------
HARNESS = (".agents/hooks/", ".agents/githooks/", ".agents/project.py", ".agents/skills/verify-change/",
           ".claude/settings.json", ".codex/", ".github/")


def is_kit_or_doc(f: str) -> bool:
    """The docs and the kit — not the judgements log, which a yes or a lesson appends to after a review: it is data
    the rubrics check reads, and a line in it leaves the doc-reviewer's pass standing."""
    return f != JUDGEMENTS.relative_to(ROOT).as_posix() and (project.is_doc(f) or f.startswith(".agents/"))


def is_design(f: str) -> bool:
    """The design brief, the token files and the UI: what the design check and the ui-designer cover."""
    return f == project.DESIGN_FILE or project.matches(f, project.UI_PATHS + project.TOKEN_FILES)


def load_weights() -> dict:
    """Each judge's quality dimensions with their labels and weights, and the history of every change to them."""
    try:
        data = json.loads(WEIGHTS.read_text())
    except (OSError, ValueError):
        data = {}
    data.setdefault("judges", {})
    data.setdefault("history", [])
    return data


JUDGES = {
    # Docs describe the code, and the kit is kept true like a doc: both call for the doc-reviewer.
    "doc-reviewer": lambda f: is_kit_or_doc(f) or project.is_code(f),
    "code-reviewer": lambda f: project.is_code(f),
    "ui-designer": lambda f: is_design(f),
    **{name: (lambda f, p=paths: project.matches(f, p)) for name, paths in project.JUDGES.items()},
}
# A judge with quality dimensions and no paths — the ux-designer, the ux-content-writer — is asked, never named by
# `run`; `review` records it, and `finish` holds its score to the bar once it has reviewed in this task.
JUDGES.update({name: (lambda f: False) for name in load_weights()["judges"] if name not in JUDGES})


def judge_ready(name: str) -> bool:
    return (ROOT / ".agents/agents" / f"{name}.md").is_file()


def rubric_owners() -> list[str]:
    """Every agent a lesson can teach: the judges in the plan, and every agent with a rubric file — the ux-designer's
    learned items live in a rubric though it is asked only on request."""
    return sorted(set(JUDGES) | {p.stem for p in RUBRICS.glob("*.md")})


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout


def changed_files() -> list[str]:
    files = git("diff", "--name-only", "HEAD").splitlines() + git("ls-files", "--others", "--exclude-standard") \
        .splitlines()
    return sorted(set(files))


def watched(files: list[str]) -> list[str]:
    """The changed files a fingerprint covers: all but the evals, which the loop itself writes — a finding, a scored
    review or the person's taste never makes the last run or a judge's pass stale."""
    return [f for f in files if not f.startswith(EVALS)]


def content_hash(paths, salt: str = "", root: Path | None = None) -> str:
    """The paths' content under `root` (the repo, or a judge's snapshot), each with its name."""
    h = hashlib.sha256(salt.encode())
    for f in paths:
        p = (root or ROOT) / f
        h.update(f.encode() + b"\0" + (p.read_bytes() if p.is_file() else b"(deleted)") + b"\0")
    return h.hexdigest()[:16]


def judge_files(judge: str, files: list[str] | None = None) -> list[str]:
    """The changed files a judge reads."""
    return [f for f in watched(files if files is not None else changed_files()) if JUDGES[judge](f)]


def judge_fingerprint(judge: str, files: list[str] | None = None) -> str:
    """The content of the changed files a judge reads, so a change elsewhere leaves its review standing."""
    return content_hash(judge_files(judge, files), judge)


# --- What a verdict rests on: normalised content, snapshots, nits and deltas (.agents/HARNESS.md §13) -------------

C_SOURCES = (".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx")
NIT_SLACK = 3      # a hunk within this many lines of a nit is that nit's fix
NIT_SPAN = 10      # the most lines one nit covers
LINE_LIMIT = 120   # the longest code line `selfcheck` lets through
SNAPSHOTS = STATE / "snapshots"
RAW_STRING = re.compile(r"(?:^|\W)(?:u8|u|U|L)?R$")  # C++'s R"delim( … )delim", seen from its opening quote


def read_text(p: Path) -> str | None:
    return p.read_bytes().decode("utf-8", "replace") if p.is_file() else None


def kind_of(path: str, text: str) -> str:
    """How a file is normalised — c, py, sh, md or raw — by its extension, else by its shebang."""
    for kind, ext in (("c", C_SOURCES), ("py", (".py",)), ("sh", (".sh", ".bash")), ("md", (".md",))):
        if path.endswith(ext):
            return kind
    first = text.split("\n", 1)[0]
    if first.startswith("#!"):
        return "py" if "python" in first else "sh" if re.search(r"\b(?:ba|z|da|k)?sh\b", first) else "raw"
    return "raw"


def is_word(ch: str) -> bool:
    return ch.isalnum() or ch in "_$"


def c_units(text: str) -> list[tuple[int, int, str]]:
    """C and C++ as statements: comments dropped, a run of whitespace one space — and none between a word and a sign
    — a unit ending at `;`, `{`, `}` or a preprocessor line's end. Literals are kept as written, and a directive keeps
    every space (`#define F (x)` is not `#define F(x)`)."""
    out: list = []
    buf: list = []
    span = [0, 0]
    i, n, line = 0, len(text), 1
    directive, line_start, space = False, True, False

    def put(s: str) -> None:
        nonlocal space
        if not buf:
            span[0] = line
        elif space and (directive or is_word(buf[-1][-1]) == is_word(s[0])):
            buf.append(" ")
        space = False
        buf.append(s)
        span[1] = line

    def cut() -> None:
        nonlocal space
        if buf:
            out.append((span[0], span[1], "".join(buf)))
            buf.clear()
        space = False

    while i < n:
        c = text[i]
        if c == "\n":
            if directive and not (text[i - 1:i] == "\\" or text[i - 2:i] == "\\\r"):
                cut()
                directive = False
            space, line_start, line, i = True, True, line + 1, i + 1
            continue
        if c in " \t\r\f\v":
            space, i = True, i + 1
            continue
        if text.startswith("//", i):  # a backslash before its newline splices the next line into it
            j = text.find("\n", i)
            while j > 0 and (text[j - 1] == "\\" or text[j - 2:j] == "\\\r"):
                line += 1
                j = text.find("\n", j + 1)
            space, i = True, n if j < 0 else j
            continue
        if text.startswith("/*", i):
            j = text.find("*/", i + 2)
            j = n if j < 0 else j + 2
            line += text.count("\n", i, j)
            line_start = line_start and "\n" not in text[i:j]
            space, i = True, j
            continue
        if line_start and c == "#":
            cut()
            directive = True
        line_start = False
        if c == '"' and RAW_STRING.search(text[max(0, i - 3):i]):
            opened = text.find("(", i)
            close = text.find(")" + text[i + 1:opened] + '"', opened) if opened >= 0 else -1
            j = n if close < 0 else close + opened - i + 1
            put(text[i:j])
            line += text.count("\n", i, j)
            span[1], i = line, j
            continue
        if c in "\"'" and not (c == "'" and i and text[i - 1].isdigit()):  # 1'000 is a digit separator
            j = i + 1
            while j < n and text[j] not in (c, "\n"):
                j += 2 if text[j] == "\\" else 1
            j = j + 1 if j < n and text[j] == c else j
            put(text[i:j])
            line += text.count("\n", i, j)  # a backslash-newline inside the literal
            span[1], i = line, j
            continue
        put(c)
        i += 1
        if c in ";{}" and not directive:
            cut()
    cut()
    return out


def py_units(text: str) -> list[tuple[int, int, str]]:
    """Python as logical lines, from its own tokenizer: comments and the breaks inside brackets dropped, tokens one
    space apart, each line led by its indent depth — strings kept as written. Source it cannot read is taken raw."""
    out, cur, first, last, depth = [], [], 0, 0, 0
    try:
        for t in tokenize.generate_tokens(io.StringIO(text).readline):
            if t.type in (tokenize.COMMENT, tokenize.NL, tokenize.ENCODING, tokenize.ENDMARKER):
                continue
            if t.type in (tokenize.INDENT, tokenize.DEDENT):
                depth += 1 if t.type == tokenize.INDENT else -1
                continue
            if t.type == tokenize.NEWLINE:
                if cur:
                    out.append((first, last, f"{depth}|" + " ".join(cur)))
                cur = []
                continue
            if not cur:
                first = t.start[0]
            cur.append(t.string)
            last = t.end[0]
    except (tokenize.TokenError, SyntaxError, ValueError):
        return raw_units(text)
    if cur:
        out.append((first, last, f"{depth}|" + " ".join(cur)))
    return out


HEREDOC = re.compile(r"(?<!<)<<(-?)\s*(['\"]?)([A-Za-z_]\w*)\2")


def sh_units(text: str) -> list[tuple[int, int, str]]:
    """Shell as lines: a comment — `#` where a word starts, outside quotes — dropped, a run of spaces outside quotes
    one space, a blank line dropped. Line breaks are kept, since they end commands; a here-document is kept as
    written."""
    out, quote, heredoc = [], None, None
    for ln, raw in enumerate(text.split("\n"), 1):
        if heredoc:
            body = raw.lstrip("\t") if heredoc[0] else raw
            out.append((ln, ln, raw))
            heredoc = None if body == heredoc[1] else heredoc
            continue
        res, opened, space, word_start, i = [], quote is not None, False, True, 0
        while i < len(raw):
            c = raw[i]
            if quote:
                if quote == '"' and c == "\\":
                    res.append(raw[i:i + 2])
                    i += 2
                    continue
                res.append(c)
                quote = None if c == quote else quote
                i += 1
                continue
            if c in " \t":
                space, word_start, i = True, True, i + 1
                continue
            if c == "#" and word_start:
                break
            if space and res:
                res.append(" ")
            space = False
            if c == "\\":
                res.append(raw[i:i + 2])
                i += 2
                word_start = False
                continue
            quote = c if c in "'\"" else None
            res.append(c)
            word_start = c in ";|&()<>"
            i += 1
        line = "".join(res)
        line = line if opened else line.lstrip()
        line = line if quote else line.rstrip()
        if line:
            out.append((ln, ln, line))
            m = None if quote else HEREDOC.search(line)
            heredoc = (m.group(1) == "-", m.group(3)) if m else None
    return out


MD_BREAK = re.compile(r"\s*(?:[-*+]\s|\d+[.)]\s|#{1,6}(?:\s|$)|\||>|<|```|~~~)")


def md_units(text: str) -> list[tuple[int, int, str]]:
    """Markdown as blocks: a paragraph or a list item, its lines joined and its whitespace collapsed, so prose
    re-wrapped with the same words is the same; a heading, a table row, a quote or a list marker starts a new block, a
    blank line ends one. Front matter, fenced code — closed only by a fence of its own character at least as long — and
    indented code outside a list are kept line by line, as written."""
    out, cur, first, last, fence, in_list = [], [], 0, 0, None, False
    lines = text.split("\n")
    front = lines[0].strip() == "---" if lines else False

    def cut() -> None:
        if cur:
            out.append((first, last, " ".join(cur)))
            cur.clear()

    for ln, raw in enumerate(lines, 1):
        s = raw.strip()
        if front:
            out.append((ln, ln, raw.rstrip()))
            front = not (ln > 1 and s == "---")
            continue
        if fence:
            out.append((ln, ln, raw.rstrip()))
            fence = None if s.startswith(fence) and not s.strip(fence[0]) else fence
            continue
        opened = re.match(r"(`{3,}|~{3,})", s)
        if opened:
            cut()
            out.append((ln, ln, s))
            fence = opened.group(1)
            continue
        if not s:
            cut()
            continue
        if not cur and not in_list and re.match(r"(?: {4}|\t)", raw):  # an indented code block: as written
            out.append((ln, ln, raw.rstrip()))
            continue
        if not cur and raw[:1] not in (" ", "\t"):
            in_list = bool(re.match(r"(?:[-*+]|\d+[.)])\s", s))
        if MD_BREAK.match(raw):
            cut()
        if not cur:
            first = ln
        cur.append(" ".join(s.split()))
        last = ln
        if s.startswith(("#", "|")):
            cut()
    cut()
    return out


def raw_units(text: str) -> list[tuple[int, int, str]]:
    """Any other file as lines, trailing whitespace and blank lines dropped."""
    return [(ln, ln, s.rstrip()) for ln, s in enumerate(text.split("\n"), 1) if s.strip()]


UNITS = {"c": c_units, "py": py_units, "sh": sh_units, "md": md_units, "raw": raw_units}


def file_units(path: str, text: str | None) -> list[tuple[int, int, str]]:
    """A file's normalised units — (first line, last line, text) — or none for a file that is not there. A `#!` first
    line is a unit of its own in Python and shell, whose readers take it for a comment: it names the interpreter."""
    if text is None:
        return []
    kind = kind_of(path, text)
    units = UNITS[kind](text)
    if kind in ("py", "sh") and text.startswith("#!"):
        units = [(1, 1, text.split("\n", 1)[0].rstrip())] + [u for u in units if u[0] != 1 or u[1] != 1]
    return units


def normal_hash(paths, salt: str = "", root: Path | None = None) -> str:
    """content_hash of the files once normalised: a comment or whitespace edit leaves it as it was."""
    h = hashlib.sha256(salt.encode())
    for f in paths:
        text = read_text((root or ROOT) / f)
        body = "(deleted)" if text is None else "\x1e".join(u[2] for u in file_units(f, text))
        h.update(f.encode() + b"\0" + body.encode() + b"\0")
    return h.hexdigest()[:16]


def stamp(judge: str, files: list[str] | None = None) -> dict:
    """What a review keeps of the judge's files: the raw fingerprint, and the normalised one."""
    jf = judge_files(judge, files)
    return {"fingerprint": content_hash(jf, judge), "normal": normal_hash(jf, judge)}


def review_stands(judge: str, r: dict, files: list[str] | None = None) -> str | None:
    """'exact' when the judge's files are as it judged them; 'normalised' when only comments and whitespace changed
    since; None when they changed and the review is stale. A review kept before the normalised stamp compares raw."""
    if judge not in JUDGES or r.get("fingerprint") == judge_fingerprint(judge, files):
        return "exact"
    if r.get("normal") and r["normal"] == normal_hash(judge_files(judge, files), judge):
        return "normalised"
    return None


def snapshot_dir(task: dict, judge: str) -> Path:
    return SNAPSHOTS / (re.sub(r"[^0-9A-Za-z]+", "", task.get("started") or "") or "untimed") / judge


def asked_dir(task: dict, judge: str) -> Path:
    """Where `ask` keeps the judge's files as they were when it was asked, until its review takes them."""
    return snapshot_dir(task, judge).with_name(f"{judge}.asked")


def take_asked(task: dict, judge: str) -> dict | None:
    """The review's stamp from the files as they were when `ask` was run — taken when the judge was asked after its
    last review — with that snapshot moved into place, so an edit made while it read is in the next `delta`. None
    when it was not asked since; the review then snapshots the tree as it is."""
    asked, prev = (task.get("asked") or {}).get(judge), task["reviews"].get(judge)
    src = asked_dir(task, judge)
    if not asked or (prev and asked < prev["at"]) or not (src / "manifest.json").is_file():
        return None
    files = list(json.loads((src / "manifest.json").read_text())["files"])
    d = snapshot_dir(task, judge)
    shutil.rmtree(d, ignore_errors=True)
    shutil.move(str(src), str(d))
    del task["asked"][judge]
    return {"fingerprint": content_hash(files, judge, d / "files"), "normal": normal_hash(files, judge, d / "files"),
            "read_at": asked}


def save_snapshot(task: dict, judge: str, files: list[str], d: Path | None = None) -> None:
    """A copy of the files the judge read, as it read them — what `delta` and `nits-fixed` diff the tree against."""
    d = d or snapshot_dir(task, judge)
    shutil.rmtree(d, ignore_errors=True)
    kept = {}
    for f in files:
        src = ROOT / f
        kept[f] = file_hash(src)
        if src.is_file():
            (d / "files" / f).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, d / "files" / f)
    write_atomic(d / "manifest.json", json.dumps({"at": now(), "files": kept}, indent=1))


def load_snapshot(task: dict, judge: str) -> dict | None:
    try:
        data = json.loads((snapshot_dir(task, judge) / "manifest.json").read_text())
    except (OSError, ValueError):
        return None
    return data if isinstance(data.get("files"), dict) else None


def snapshot_text(task: dict, judge: str, f: str) -> str | None:
    return read_text(snapshot_dir(task, judge) / "files" / f)


NIT = re.compile(r"(?P<path>[^:\s]+):(?P<a>\d+)(?:-(?P<b>\d+))?(?:\s+(?P<text>.+))?", re.S)


def parse_nits(specs: list[str] | None, files: list[str]) -> list[dict]:
    """`path:line[-line] words` → {"path", "from", "to", "text"}, each on a file the judge read in the change."""
    out = []
    for spec in specs or ():
        m = NIT.fullmatch(spec.strip())
        if not m:
            raise ValueError(f"--nit takes path:line or path:line-line, then its words: {spec!r}")
        a, b = int(m["a"]), int(m["b"] or m["a"])
        if not 1 <= a <= b:
            raise ValueError(f"--nit's lines run from 1, first to last: {spec!r}")
        if b - a + 1 > NIT_SPAN:
            raise ValueError(f"a nit covers at most {NIT_SPAN} lines — polish on more is a finding to review: {spec!r}")
        if m["path"] not in files:
            raise ValueError(f"{m['path']} is not a file this judge read in the change — one of "
                             f"{', '.join(files[:4]) or 'none'}{' …' if len(files) > 4 else ''}")
        out.append({"path": m["path"], "from": a, "to": b, "text": (m["text"] or "").strip()})
    return out


def nit_name(n: dict) -> str:
    return f"{n['path']}:{n['from']}" + (f"-{n['to']}" if n["to"] != n["from"] else "") \
        + (f" {n['text']}" if n.get("text") else "")


def unit_span(units: list, a: int, b: int) -> tuple[int, int, bool]:
    """The lines units[a:b] cover, and whether they are real; for an empty slice, the line it follows."""
    if a < b:
        return units[a][0], units[b - 1][1], True
    at = units[a - 1][1] if a else 0
    return at, at, False


def narrow_span(old: str, new: str, o: tuple, n: tuple) -> tuple[tuple, tuple]:
    """A replaced unit's two spans, the same length, trimmed to the lines that differ as written — a one-word fix in a
    six-line paragraph is one line, not six. The lines kept are those between the common first and last lines,
    compared stripped. When no line differs as written, both spans stay whole."""
    ol, nl = old.split("\n")[o[0] - 1:o[1]], new.split("\n")[n[0] - 1:n[1]]
    p = 0
    while p < len(ol) and ol[p].strip() == nl[p].strip():
        p += 1
    if p == len(ol):
        return o, n
    s = 0
    while ol[-1 - s].strip() == nl[-1 - s].strip():
        s += 1
    return (o[0] + p, o[1] - s, True), (n[0] + p, n[1] - s, True)


def unit_hunks(path: str, old: str | None, new: str | None) -> list[dict]:
    """The hunks between two versions of a file once normalised — what a comment or whitespace edit never makes. Each
    is {"path", "old": (a, b, real), "new": (c, d, real)}, in each version's own lines. A hunk that replaces units one
    for one, each as many lines long as before, is narrowed to the lines that differ as written (narrow_span); any
    other — a unit split, joined or read anew, as an unclosed comment or fence makes — keeps its whole span."""
    ou, nu = file_units(path, old), file_units(path, new)
    sm = difflib.SequenceMatcher(None, [u[2] for u in ou], [u[2] for u in nu], autojunk=False)
    out = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        o, n = unit_span(ou, i1, i2), unit_span(nu, j1, j2)
        if tag == "replace" and [u[1] - u[0] for u in ou[i1:i2]] == [u[1] - u[0] for u in nu[j1:j2]] \
                and o[1] - o[0] == n[1] - n[0]:
            o, n = narrow_span(old, new, o, n)
        out.append({"path": path, "old": o, "new": n})
    return out


def span_len(s: tuple) -> int:
    return s[1] - s[0] + 1 if s[2] else 0


def near_nit(h: dict, nits: list[dict]) -> dict | None:
    """The nit a hunk fixes: it lies within NIT_SLACK lines of the nit, in the lines the judge read, and neither side
    of it is longer than the nit's own lines plus NIT_SLACK — a hundred lines inserted after a nit are not its fix."""
    a, b, _ = h["old"]
    return next((n for n in nits if n["path"] == h["path"] and n["from"] - NIT_SLACK <= a
                 and b <= n["to"] + NIT_SLACK
                 and max(span_len(h["old"]), span_len(h.get("new", (0, 0, False))))
                 <= n["to"] - n["from"] + 1 + NIT_SLACK), None)


def delta_since(task: dict, judge: str, snap: dict, files: list[str]) -> list[tuple[str, str | None, str | None]]:
    """(path, as the judge read it, as it is now) for each of its files that differs from its snapshot."""
    out = []
    for f in sorted(set(files) | set(snap["files"])):
        old = snapshot_text(task, judge, f) if f in snap["files"] else None
        new = read_text(ROOT / f) if f in files else None
        if old != new:
            out.append((f, old, new))
    return out


def carry_line(h: dict) -> str:
    """A carry-forward in a review's history, in words."""
    if h.get("kind") == "nits-fixed":
        return (f"its pass re-stamped at {h['at']}: {h['hunks']} hunk(s) since its review, each within {NIT_SLACK} "
                f"lines of a nit it raised")
    if h.get("kind") == "acceptance":
        return (f"the person's acceptance at {h['quality']}/100 ({h['from']}) holds — this review scored "
                f"{h['now']}, the same or higher: \"{h['words']}\"")
    return str(h)


def tree_fingerprint() -> str:
    """HEAD and every changed file's content but the evals' — the same whether a file is staged, unstaged or
    untracked."""
    return content_hash(watched(changed_files()), git("rev-parse", "HEAD"))


def deployed_fingerprint() -> str:
    """HEAD and the changed files that reach the target — everything but docs and the harness; a doc edit leaves a
    sign-off standing."""
    return content_hash([f for f in changed_files() if not is_kit_or_doc(f) and not f.startswith(HARNESS)],
                        git("rev-parse", "HEAD"))


def gated_fingerprint(files: list[str] | None = None, kind: str | None = None) -> str:
    """The content of the changed files the gates cover — of those that ask for `kind`, when given: what a `built` or
    a `kit` yes saw."""
    paths = tuple(p for _, ps, kinds in project.GATES for p in ps if kind is None or kind in kinds)
    return content_hash([f for f in (files if files is not None else changed_files()) if project.matches(f, paths)])


def file_hash(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16] if path.is_file() else None


def gated_contents(files: list[str] | None = None) -> dict:
    """Each changed file a gate covers, with its content hash — what the gated files held at a start or a run, so a
    change left uncommitted by an earlier task is not taken for this task's build."""
    paths = tuple(p for _, ps, _ in project.GATES for p in ps)
    return {f: file_hash(ROOT / f) for f in (files if files is not None else changed_files())
            if project.matches(f, paths)}


def first_build(task: dict, paths) -> str | None:
    """When the first run built a change in these paths: the first run whose gated files differ from what they held
    when the task started. A task or run recorded before `gated` was kept falls back to the first run that touched
    them."""
    start = task.get("gated_at_start")
    for r in task["runs"]:
        if start is None or "gated" not in r:
            if any(project.matches(f, paths) for f in r["files"]):
                return r["at"]
            continue
        held = {f: h for f, h in r["gated"].items() if project.matches(f, paths)}
        if held != {f: h for f, h in start.items() if project.matches(f, paths)}:
            return r["at"]
    return None


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


# --- Writes: atomic, under a lock — two agents recording at once never tear a file or lose a row ------------------

LOCKS = STATE / "locks"
_HELD: dict[str, int] = {}  # the locks this process holds, so a nested take of the same one does not wait on itself


@contextmanager
def locked(path: Path):
    """An exclusive fcntl.flock for one file's writers, its lock file in .cache/harness/locks/ (git-ignored), so the
    committed folders hold no lock files. Re-entrant within a process; on a platform with no fcntl, no lock."""
    key = str(path.resolve())
    if key in _HELD or fcntl is None:
        _HELD[key] = _HELD.get(key, 0) + 1
        try:
            yield
        finally:
            _HELD[key] -= 1
            if not _HELD[key]:
                del _HELD[key]
        return
    LOCKS.mkdir(parents=True, exist_ok=True)
    name = f"{path.name}.{hashlib.sha256(key.encode()).hexdigest()[:8]}.lock"
    with open(LOCKS / name, "a") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        _HELD[key] = 1
        try:
            yield
        finally:
            del _HELD[key]
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def write_atomic(path: Path, text: str) -> None:
    """Write a temp file beside `path` and os.replace it over, under the file's lock: a reader sees the old file or
    the new one, never half of either. The file keeps its mode."""
    with locked(path):
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(text)
                f.flush()
                os.fsync(f.fileno())
            if path.is_file():
                shutil.copymode(path, tmp)
            else:
                os.chmod(tmp, 0o644)
            os.replace(tmp, path)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)


def append_line(path: Path, line: str) -> None:
    """One JSON line added to a log, the whole file rewritten atomically under its lock."""
    with locked(path):
        old = path.read_text(encoding="utf-8") if path.is_file() else ""
        write_atomic(path, old + ("" if not old or old.endswith("\n") else "\n") + line + "\n")


def load() -> dict:
    try:
        return json.loads(TASK.read_text())
    except (OSError, ValueError):
        return {}


def save(task: dict) -> None:
    write_atomic(TASK, json.dumps(task, indent=2))


@contextmanager
def task_update(name: str = "(unnamed)"):
    """The task read, changed and saved under its lock — a review recorded while a run is under way is kept."""
    with locked(TASK):
        task = load() or new_task(name)
        yield task
        save(task)


def new_task(name: str) -> dict:
    return {"task": name, "started": now(), "commit": git("rev-parse", "--short", "HEAD").strip(), "failures": 0,
            "runs": [], "reviews": {}, "approvals": [], "decisions": [], "target": None, "target_log": [],
            "signoffs": [], "findings": [], "gated_at_start": gated_contents()}


# --- The checks --------------------------------------------------------------------------------------------------

def sh(cmd: list[str], log: Path) -> tuple[int, str]:
    try:
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    except FileNotFoundError:
        out = f"{cmd[0]}: not found — install it, or take the check out of .agents/project.py"
        log.write_text(out)
        return 127, out
    out = proc.stdout + proc.stderr
    log.write_text(out)
    return proc.returncode, out


def tail(out: str, n: int = 12) -> list[str]:
    return [line for line in out.splitlines() if line.strip()][-n:]


def failing(out: str) -> list[str]:
    """A check script's FAIL lines with the line before each — the check that went over its baseline."""
    lines = out.splitlines()
    return [f"{lines[i - 1].strip()[:90]} — {line.strip()}" if i else line.strip()
            for i, line in enumerate(lines) if "FAIL" in line][:12]


def scripts_check(name: str, scripts: list[list[str]], run_dir: Path, what: str) -> dict:
    results = [sh(cmd, run_dir / f"{name}.{i}.log") for i, cmd in enumerate(scripts)]
    ok = all(code == 0 for code, _ in results)
    return {"ok": ok, "detail": f"{what} {'at baseline' if ok else 'over a baseline'}",
            "tail": [] if ok else [line for code, out in results if code != 0 for line in failing(out) or tail(out, 4)]}


SCOPES = ("portable", "project")  # a skill's or agent's metadata.scope (AGENT_HARNESS §7.3)
LINK = re.compile(r"\]\(([^)\s]+)\)")


FM_KEY = re.compile(r"([A-Za-z_][\w-]*):(?:[ \t]+(.*?))?[ \t]*")


def frontmatter(text: str) -> tuple[str | None, str | None]:
    """(the frontmatter's body, why it cannot be read) — (None, None) for a file with none. CRLF line ends are read as
    LF, so a file saved on Windows is checked like any other."""
    text = text.replace("\r\n", "\n")
    if not text.startswith("---\n"):
        return None, None
    m = re.match(r"---\n(?:(.*?)\n)?---[ \t]*(?:\n|$)", text, re.S)
    if not m:
        return None, "its frontmatter is never closed by a `---` line"
    return m.group(1) or "", None


def top_keys(body: str) -> list[list]:
    """[key or None, value, [(line, child line)], line] for each top-level line of a frontmatter body; an indented line
    belongs to the key above it — a folded block's text, a mapping's children — and so does an unindented `- ` item,
    YAML's sequence under a key (`allowed-tools:` then `- Bash`). Lines are the file's own."""
    out: list = []
    for n, line in enumerate(body.split("\n"), 2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line[0] in " \t" or re.match(r"-(?:\s|$)", line):
            if out:
                out[-1][2].append((n, line))
            continue
        m = FM_KEY.fullmatch(line)
        out.append([m.group(1), m.group(2) or "", [], n] if m else [None, line, [], n])
    return out


def meta_value(text: str, name: str) -> str | None:
    """A top-level key's value in the frontmatter, else the value of that key under `metadata:` — read by structure,
    so words inside a folded `description: >-` block are never taken for a key."""
    body, _ = frontmatter(text)
    for key, value, children, _ in top_keys(body) if body is not None else []:
        if key == name:
            return value.strip()
        if key == "metadata":
            for _, line in children:
                m = re.fullmatch(r"[ \t]+([\w-]+):(?:[ \t]+(.*?))?[ \t]*", line)
                if m and m.group(1) == name:
                    return (m.group(2) or "").strip()
    return None


def frontmatter_problems(text: str) -> list[str]:
    """Why a frontmatter would not parse as YAML, in the shapes that broke one here: a block never closed, a line that
    is no `key: value`, a plain (unquoted) value holding `: ` — YAML reads a nested mapping and refuses it — or ` #`,
    which YAML drops as a comment, on its line or a continuation line; an open quote; a bad block indicator."""
    body, problem = frontmatter(text)
    if problem:
        return [problem]
    out = []
    for key, value, children, n in top_keys(body) if body is not None else []:
        if key is None:
            out.append(f"frontmatter line {n} is not `key: value`: {value[:60]!r}")
            continue
        v = value.strip()
        if not v or v[0] in "[{&*!":
            continue
        if v[0] in "|>":
            if not re.fullmatch(r"[|>](?:[-+]?[1-9]?|[1-9][-+])", v):
                out.append(f"frontmatter line {n}: `{key}:` has a bad block indicator {v!r} — `>-` folds it")
            continue
        if v[0] in "'\"":
            closed = len(v) > 1 and v.endswith(v[0]) or any(c.rstrip().endswith(v[0]) for _, c in children)
            if not closed:
                out.append(f"frontmatter line {n}: `{key}:` opens a {v[0]} quote it never closes")
            continue
        for ln, part in [(n, v)] + [(c, t.strip()) for c, t in children]:
            if ": " in part or part.endswith(":"):
                out.append(f"frontmatter line {ln}: `{key}:`'s plain value holds `: `, which YAML reads as a nested "
                           "mapping and refuses — fold it (`>-`, the text indented two spaces) or quote it")
                break
            if " #" in part:
                out.append(f"frontmatter line {ln}: `{key}:`'s plain value holds ` #`, which YAML drops as a "
                           "comment — fold it (`>-`) or quote it")
                break
    return out


def scope_of(text: str) -> str | None:
    """`metadata: scope:` (or a top-level `scope:`) from a SKILL.md's or an agent's frontmatter."""
    v = meta_value(text, "scope")
    m = re.match(r"\S+", v or "")
    return m.group(0).strip("'\"") if m else None


def requires_of(text: str) -> list[str]:
    """`metadata: requires: [a, b]` from an agent's frontmatter — the skills a portable agent needs."""
    r = re.fullmatch(r"\[([^\]]*)\]", meta_value(text, "requires") or "")
    return [s.strip().strip("'\"") for s in r.group(1).split(",") if s.strip()] if r else []


def scope_problems() -> list[str]:
    """Every skill and agent carries its scope; a portable skill links nothing outside its own folder; a portable
    agent names the skills it needs, and each is present and portable."""
    problems = []
    files = sorted(ROOT.glob(f"{SKILLS}/*/SKILL.md")) + sorted(ROOT.glob(".agents/agents/*.md"))
    scopes = {f.parent.name: scope_of(f.read_text(errors="replace")) for f in ROOT.glob(f"{SKILLS}/*/SKILL.md")}
    for f in files:
        rel = f.relative_to(ROOT).as_posix()
        text = f.read_text(errors="replace")
        problems += [f"{rel}: {p}" for p in frontmatter_problems(text)]  # a runtime that cannot parse it drops it
        scope = scope_of(text)
        if scope not in SCOPES:
            problems.append(f"{rel}: metadata.scope is {scope or 'missing'} — one of {', '.join(SCOPES)}")
            continue
        if scope == "portable" and f.name != "SKILL.md":
            needs = requires_of(text)
            if not needs:
                problems.append(f"{rel}: a portable agent names the skills it needs in metadata.requires")
            for skill in needs:
                if scopes.get(skill) != "portable":
                    problems.append(f"{rel}: requires {skill}, which is "
                                    f"{'missing' if skill not in scopes else 'not portable'}")
            for target in LINK.findall(re.sub(r"`[^`]*`", "", text)):
                if not re.match(r"[a-z]+:|#", target):
                    problems.append(f"{rel}: a portable agent links to a file ({target}) — name it in backticks")
        if scope == "portable" and f.name == "SKILL.md":
            folder = f.parent.resolve()
            for doc in [f] + sorted(f.parent.glob("references/**/*.md")):
                text = re.sub(r"```.*?```", "", doc.read_text(errors="replace"), flags=re.S)
                for target in LINK.findall(re.sub(r"`[^`]*`", "", text)):
                    if re.match(r"[a-z]+:|#", target):
                        continue
                    dest = (doc.parent / target.split("#")[0]).resolve()
                    if folder not in dest.parents and dest != folder:
                        problems.append(f"{doc.relative_to(ROOT).as_posix()}: a portable skill links out of its "
                                        f"folder ({target}) — name the file in backticks instead")
    return problems


def check_scope(run_dir: Path) -> dict:
    """The scope labels on every skill and agent, and portable skills' links."""
    problems = scope_problems()
    (run_dir / "scope.log").write_text("\n".join(problems) + "\n")
    return {"ok": not problems, "detail": f"{len(problems)} scope problem(s) in the skills and agents",
            "tail": problems[:12]}


def check_docs(run_dir: Path) -> dict:
    """Every doc and kit-link check, each exiting 1 over its baseline."""
    return scripts_check("docs", [["bash", f"{DOC_SCRIPTS}/doc_checks.sh"],
                                  [sys.executable, f"{DOC_SCRIPTS}/check_anchors.py"],
                                  [sys.executable, f"{DOC_SCRIPTS}/check_links.py"],
                                  [sys.executable, f"{DOC_SCRIPTS}/new_doc.py", "--test"]], run_dir,
                         "doc lint, anchors, links, the scaffolder's self-test")


def check_harness(run_dir: Path) -> dict:
    """The guard's and the flag's self-tests, and the pre-commit hook on the index."""
    results = [sh([sys.executable, s, "--test"], run_dir / f"harness.{Path(s).stem}.log") for s in HARNESS_TESTS]
    hook = sh([sys.executable, ".agents/githooks/pre-commit"], run_dir / "harness.pre-commit.log")
    ok = all(code == 0 for code, _ in results) and hook[0] == 0
    detail = "; ".join(tail(out, 1)[0] if out.strip() else "no output" for _, out in results)
    detail += f"; pre-commit on the index: exit {hook[0]}"
    return {"ok": ok, "detail": detail, "tail": [] if ok else [ln for _, out in results + [hook] for ln in tail(out, 6)]}


def check_design(run_dir: Path) -> dict:
    """DESIGN.md against its contrast floors and the token files; then no colour literal in a UI file."""
    results = [sh([sys.executable, DESIGN_CHECK], run_dir / "design.brief.log"),
               sh([sys.executable, DESIGN_CHECK, "--test"], run_dir / "design.selftest.log"),
               sh([sys.executable, TOKEN_CHECK, "--test"], run_dir / "design.tokens.selftest.log")]
    ui = sh([sys.executable, TOKEN_CHECK], run_dir / "design.tokens.log") if project.TOKEN_FILES else None
    results += [ui] if ui else []
    ok = all(code == 0 for code, _ in results)
    return {"ok": ok, "detail": ui_detail(f"{project.DESIGN_FILE}, the tokens", ok, ui and ui[1]),
            "tail": [] if ok else [line for code, out in results if code != 0 for line in tail(out, 16)]}


def project_check(name: str):
    spec = project.CHECKS[name]

    def run(run_dir: Path) -> dict:
        code, out = sh(list(spec["run"]), run_dir / f"{name}.log")
        return {"ok": code == 0, "detail": f"`{' '.join(spec['run'])}` exit {code}",
                "tail": [] if code == 0 else tail(out)}
    return run


READ_NOTHING = re.compile(r"NOTHING CHECKED|nothing was checked|read no (?:UI )?files?", re.I)


def ui_detail(what: str, ok: bool, out: str | None) -> str:
    """A UI check's line in the run: a pass over no files says so, rather than "at baseline" — the paths may name
    nothing the check reads (a firmware project's UI_PATHS before its C/C++ folders are listed)."""
    said = next((ln.strip() for ln in (out or "").splitlines() if READ_NOTHING.search(ln)), None)
    if ok and said:
        return f"{what}: self-tests pass, but the UI run read no file — {said}"
    return f"{what} and the UI {'at baseline' if ok else 'over a baseline'}"


def check_a11y(run_dir: Path) -> dict:
    """The accessibility scripts' self-tests; then the UI files against the accessibility patterns."""
    results = [sh([sys.executable, f"{A11Y_SCRIPTS}/contrast.py", "--test"], run_dir / "a11y.contrast.log"),
               sh([sys.executable, f"{A11Y_SCRIPTS}/a11y_check.py", "--test"], run_dir / "a11y.selftest.log")]
    ui = sh([sys.executable, f"{A11Y_SCRIPTS}/a11y_check.py"], run_dir / "a11y.ui.log") if project.UI_PATHS else None
    results += [ui] if ui else []
    ok = all(code == 0 for code, _ in results)
    return {"ok": ok, "detail": ui_detail("the accessibility scripts", ok, ui and ui[1]),
            "tail": [] if ok else [line for code, out in results if code != 0 for line in tail(out, 16)]}


MOTION_SKILL = f"{SKILLS}/motion/"
MOTION_CHECK = f"{MOTION_SKILL}scripts/motion_check.py"


def check_motion(run_dir: Path) -> dict:
    """The motion check's self-test; then the UI files against the motion patterns."""
    results = [sh([sys.executable, MOTION_CHECK, "--test"], run_dir / "motion.selftest.log")]
    ui = sh([sys.executable, MOTION_CHECK], run_dir / "motion.ui.log") if project.UI_PATHS else None
    results += [ui] if ui else []
    ok = all(code == 0 for code, _ in results)
    return {"ok": ok, "detail": ui_detail("the motion check", ok, ui and ui[1]),
            "tail": [] if ok else [line for code, out in results if code != 0 for line in tail(out, 16)]}


TOUCH_SKILL = f"{SKILLS}/touch-and-gesture/"
TOUCH_CHECK = f"{TOUCH_SKILL}scripts/touch_check.py"


def check_touch(run_dir: Path) -> dict:
    """The touch check's self-test; then the UI files against the touch patterns."""
    results = [sh([sys.executable, TOUCH_CHECK, "--test"], run_dir / "touch.selftest.log")]
    ui = sh([sys.executable, TOUCH_CHECK], run_dir / "touch.ui.log") if project.UI_PATHS else None
    results += [ui] if ui else []
    ok = all(code == 0 for code, _ in results)
    return {"ok": ok, "detail": ui_detail("the touch check", ok, ui and ui[1]),
            "tail": [] if ok else [line for code, out in results if code != 0 for line in tail(out, 16)]}


LAYOUT_SKILL = f"{SKILLS}/layout/"
LAYOUT_CHECK = f"{LAYOUT_SKILL}scripts/layout_check.py"


def check_layout(run_dir: Path) -> dict:
    """The layout check's self-test; then the UI files against the layout patterns."""
    results = [sh([sys.executable, LAYOUT_CHECK, "--test"], run_dir / "layout.selftest.log")]
    ui = sh([sys.executable, LAYOUT_CHECK], run_dir / "layout.ui.log") if project.UI_PATHS else None
    results += [ui] if ui else []
    ok = all(code == 0 for code, _ in results)
    return {"ok": ok, "detail": ui_detail("the layout check", ok, ui and ui[1]),
            "tail": [] if ok else [line for code, out in results if code != 0 for line in tail(out, 16)]}


TYPE_SKILL = f"{SKILLS}/typography/"
TYPE_CHECK = f"{TYPE_SKILL}scripts/typography_check.py"


def check_typography(run_dir: Path) -> dict:
    """The typography check's self-test; then the UI files against the typography patterns."""
    results = [sh([sys.executable, TYPE_CHECK, "--test"], run_dir / "typography.selftest.log")]
    ui = sh([sys.executable, TYPE_CHECK], run_dir / "typography.ui.log") if project.UI_PATHS else None
    results += [ui] if ui else []
    ok = all(code == 0 for code, _ in results)
    return {"ok": ok, "detail": ui_detail("the typography check", ok, ui and ui[1]),
            "tail": [] if ok else [line for code, out in results if code != 0 for line in tail(out, 16)]}


STORY_SKILL = f"{SKILLS}/storybook/"
STORY_CHECK = f"{STORY_SKILL}scripts/story_check.py"


def check_storybook(run_dir: Path) -> dict:
    """The story check's self-test; then the story files under UI_PATHS against the story layout."""
    results = [sh([sys.executable, STORY_CHECK, "--test"], run_dir / "storybook.selftest.log")]
    ui = sh([sys.executable, STORY_CHECK], run_dir / "storybook.ui.log") if project.UI_PATHS else None
    results += [ui] if ui else []
    ok = all(code == 0 for code, _ in results)
    return {"ok": ok, "detail": ui_detail("the story check", ok, ui and ui[1]),
            "tail": [] if ok else [line for code, out in results if code != 0 for line in tail(out, 16)]}


EINK_SKILL = f"{SKILLS}/e-ink/"
EINK_CHECK = f"{EINK_SKILL}scripts/e_ink_check.py"
EINK_PATHS = tuple(getattr(project, "EINK_PATHS", ()))


def check_eink(run_dir: Path) -> dict:
    """The e-ink check's self-test; then the e-paper UI files (EINK_PATHS) against its patterns."""
    results = [sh([sys.executable, EINK_CHECK, "--test"], run_dir / "e-ink.selftest.log")]
    ui = sh([sys.executable, EINK_CHECK], run_dir / "e-ink.ui.log") if EINK_PATHS else None
    results += [ui] if ui else []
    ok = all(code == 0 for code, _ in results)
    return {"ok": ok, "detail": f"the e-ink check {'clean' if ok else 'failing'}"
                                + ("" if EINK_PATHS else " — self-test only; EINK_PATHS is empty"),
            "tail": [] if ok else [line for code, out in results if code != 0 for line in tail(out, 16)]}


PW_SKILL = f"{SKILLS}/playwright/"
PW_CHECK = f"{PW_SKILL}scripts/e2e_check.py"
PW_FILES = re.compile(r"(?:^|/)(?:e2e|tests?)/|\.(?:spec|test)\.[cm]?[jt]sx?$|(?:^|/)playwright\.config\.[cm]?[jt]s$")


def check_playwright(run_dir: Path) -> dict:
    """The e2e check's self-test; then every file that imports @playwright/test, and the Playwright config."""
    results = [sh([sys.executable, PW_CHECK, "--test"], run_dir / "playwright.selftest.log"),
               sh([sys.executable, PW_CHECK], run_dir / "playwright.files.log")]
    ok = all(code == 0 for code, _ in results)
    summary = next((line for line in results[1][1].splitlines() if line.startswith("PW1")), "")
    return {"ok": ok, "detail": f"the e2e check {'clean' if ok else 'failing'}: {summary}",
            "tail": [] if ok else [line for code, out in results if code != 0 for line in tail(out, 16)]}


ESP_SKILL = f"{SKILLS}/esp-idf-setup/"
ESP_SCRIPT = f"{ESP_SKILL}scripts/esp_idf.py"
ESP_PATHS = ("main/", "components/", "CMakeLists.txt")


def check_esp_idf(run_dir: Path) -> dict:
    """The esp-idf-setup script's self-test; then the app's layering, E1–E5, when the repo is an ESP-IDF app."""
    results = [sh([sys.executable, ESP_SCRIPT, "--test"], run_dir / "esp-idf.selftest.log"),
               sh([sys.executable, ESP_SCRIPT, "check"], run_dir / "esp-idf.layering.log")]
    ok = all(code == 0 for code, _ in results)
    return {"ok": ok, "detail": f"the esp-idf-setup script and the app's layering {'clean' if ok else 'failing'}",
            "tail": [] if ok else [line for code, out in results if code != 0 for line in tail(out, 16)]}


UX_SKILL = f"{SKILLS}/ux-content/"
UX_LINT = f"{UX_SKILL}scripts/ux_lint.py"


def ux_paths() -> tuple:
    """The files the string check reads: UX_STRINGS' paths, else UI_PATHS."""
    return tuple((getattr(project, "UX_STRINGS", None) or {}).get("paths") or ()) or tuple(project.UI_PATHS)


def check_ux(run_dir: Path) -> dict:
    """The string check's self-test; then the UI strings against the rules a script can see (UX_CONTENT §1–§6)."""
    results = [sh([sys.executable, UX_LINT, "--test"], run_dir / "ux.selftest.log")]
    ui = sh([sys.executable, UX_LINT], run_dir / "ux.strings.log") if ux_paths() else None
    results += [ui] if ui else []
    ok = all(code == 0 for code, _ in results)
    return {"ok": ok, "detail": ui_detail("the string check", ok, ui and ui[1]),
            "tail": [] if ok else [line for code, out in results if code != 0 for line in tail(out, 16)]}


SECRETS_SKILL = f"{SKILLS}/secrets-handling/"
SECRET_SCAN = f"{SECRETS_SKILL}scripts/secret_scan.py"


def check_secrets(run_dir: Path) -> dict:
    """The secret scan's self-test when its skill changes; then the change itself, for key-shaped strings — counted
    by file and line, never printed (SECRETS §11). The pre-commit hook refuses the same at the commit."""
    results = [sh([sys.executable, SECRET_SCAN, "--test"], run_dir / "secrets.selftest.log")] \
        if any(f.startswith(SECRETS_SKILL) for f in changed_files()) else []
    results.append(sh([sys.executable, SECRET_SCAN], run_dir / "secrets.scan.log"))
    ok = all(code == 0 for code, _ in results)
    return {"ok": ok, "detail": "no key-shaped string in the change" if ok else "a key-shaped string in the change",
            "tail": [] if ok else [line for code, out in results if code != 0 for line in tail(out, 16)]}


WEB_SKILL = f"{SKILLS}/react-vite-setup/"
WEB_SCRIPT = f"{WEB_SKILL}scripts/react_vite.py"
WEB_PATHS = ("src/",)


def is_react_vite_app() -> bool:
    """A package.json that depends on react, beside a vite.config — the repo the layering rules W1–W5 are for."""
    pkg = ROOT / "package.json"
    if not pkg.is_file() or not any((ROOT / f"vite.config.{e}").is_file() for e in ("ts", "mts", "js", "mjs")):
        return False
    try:
        data = json.loads(pkg.read_text())
    except ValueError:
        return False
    return isinstance(data, dict) and "react" in {**data.get("dependencies", {}), **data.get("devDependencies", {})}


def check_react_vite(run_dir: Path) -> dict:
    """The react-vite-setup script's self-test; then the app's layering, W1–W5, when the repo is a React and Vite
    app."""
    results = [sh([sys.executable, WEB_SCRIPT, "--test"], run_dir / "react-vite.selftest.log"),
               sh([sys.executable, WEB_SCRIPT, "check"], run_dir / "react-vite.layering.log")]
    ok = all(code == 0 for code, _ in results)
    return {"ok": ok, "detail": f"the react-vite-setup script and the app's layering {'clean' if ok else 'failing'}",
            "tail": [] if ok else [line for code, out in results if code != 0 for line in tail(out, 16)]}


def is_test_file(f: str) -> bool:
    return bool(re.search(r"(^|/)(tests?|e2e|__tests__)/|\.(test|spec)\.[^/]+$|_test\.[^/]+$|(^|/)test_[^/]+$", f))


def is_doc_file(f: str) -> bool:
    return (f.startswith("docs/") or ("/" not in f and f.endswith(".md")) or f == ".agents/HARNESS.md"
            or bool(re.match(r"\.agents/skills/[^/]+/references/", f)))


# Where each route's edit lands (AGENT_HARNESS §9.2): a lesson recorded with a route and no such file in the change
# was written down and changed nothing.
ROUTE_PATHS = {
    "test": lambda f: is_test_file(f) or f == ".agents/project.py" or f.startswith(".agents/hooks/")
    or bool(re.match(r"\.agents/skills/[^/]+/scripts/", f)) or project.matches(f, [p for s in project.CHECKS.values()
                                                                                   for p in s.get("when", ())]),
    "guard": lambda f: f == ".agents/project.py" or f.startswith(".agents/hooks/"),
    "skill": lambda f: bool(re.match(r"\.agents/skills/[^/]+/SKILL\.md$|\.agents/agents/[^/]+\.md$", f)),
    "doc": is_doc_file,
    "open-item": is_doc_file,
    "rubric": lambda f: f.startswith(".agents/rubrics/") or f.endswith("/references/rubric.md"),
}
ROUTE_WHERE = {"test": "test, check or self-test file", "guard": "guard rule or guard case (.agents/project.py, "
               ".agents/hooks/)", "skill": "skill's SKILL.md or agent's file", "doc": "doc (docs/, a root Markdown file, a skill's "
               "references/, HARNESS.md)", "open-item": "doc's open items", "rubric": "rubric"}


def count_new_rows(diff: str) -> int:
    """Learned items a diff adds: `+| L<n> | …` lines (a whole file's lines, for a file git does not track yet)."""
    return sum(1 for line in diff.splitlines() if line.startswith("+") and LEARNED_ROW.match(line[1:]))


def new_learned_rows(agent: str) -> int:
    rel = f".agents/rubrics/{agent}.md"
    if not (ROOT / rel).is_file():
        return 0
    tracked = git("ls-files", "--", rel).strip()
    diff = git("diff", "HEAD", "--", rel) if tracked else \
        "\n".join("+" + line for line in (ROOT / rel).read_text().splitlines())
    return count_new_rows(diff)


def lesson_snapshot(route: str, agent: str | None) -> dict:
    """What a lesson's route could change, as it stood when the lesson was recorded — so `finish` asks for an edit made
    after it, not one an unrelated change happened to make (kept in the task, never in the log)."""
    if route == "rubric" and agent:
        return {"rows_at": new_learned_rows(agent),
                "seen": {f".agents/rubrics/{agent}.md": file_hash(ROOT / f".agents/rubrics/{agent}.md")}}
    if route == "none":
        return {}
    return {"seen": {f: file_hash(ROOT / f) for f in changed_files() if ROUTE_PATHS[route](f)}}


def lesson_problems(task: dict, files: list[str], new_rows=new_learned_rows,
                    hash_of=lambda f: file_hash(ROOT / f)) -> list[str]:
    """Each lesson recorded this task — a finding, a false alarm, a no — has the edit its route names in the change,
    made after the lesson was recorded; one routed to an agent's rubric adds a learned item to that agent's file."""
    problems = []
    # Named with --edit: that file, in the change and on the route. Otherwise a file on the route that changed after
    # the lesson was recorded.
    edited = lambda x, ok: (x["edit"] in files and ok(x["edit"])) if x.get("edit") else \
        any(ok(f) and hash_of(f) != x.get("seen", {}).get(f) for f in files)
    lessons = [x for x in task.get("findings", []) + task.get("declines", []) if x.get("route", "none") != "none"]
    learned: dict[str, list] = {}
    for x in lessons:
        route, agent = x["route"], x.get("judge")
        if route == "rubric" and agent:
            if x["kind"] == "false-alarm":
                if not edited(x, lambda f, a=agent: f == f".agents/rubrics/{a}.md"):
                    problems.append(f"the false alarm \"{x['text'][:70]}\" is recorded and {agent}'s rubric "
                                    f"(.agents/rubrics/{agent}.md) did not change since — tighten the item it misread")
            elif x.get("edit") and x["edit"] != f".agents/rubrics/{agent}.md":
                problems.append(f"the lesson \"{x['text'][:70]}\" names {x['edit']} as its edit, which is not "
                                f"{agent}'s rubric (.agents/rubrics/{agent}.md)")
            else:
                learned.setdefault(agent, []).append(0 if x.get("edit") else x.get("rows_at", 0))
            continue
        if not edited(x, ROUTE_PATHS[route]):
            problems.append(f"the lesson \"{x['text'][:70]}\" is routed to {route} and no {ROUTE_WHERE[route]} "
                            "changed after it was recorded — make the edit the route names, or record it again with "
                            "the right route")
    for agent, marks in sorted(learned.items()):
        n, have = len(marks), new_rows(agent) - min(marks)
        if have < n:
            problems.append(f"{n} lesson(s) routed to {agent}'s rubric and {have} new learned item(s) in "
                            f".agents/rubrics/{agent}.md — add an L-item for each (AGENT_HARNESS §9.3)")
    return problems


def rubric_problems(name: str, text: str, today: str | None = None) -> list[str]:
    """A rubric's Learned table, as AGENT_HARNESS §9.3 has it: `| L<n> | YYYY-MM-DD | from the person | looks for |`,
    numbers rising and never reused, every cell filled, no date ahead of today."""
    today = today or datetime.now().date().isoformat()
    problems, seen, last, inside = [], set(), 0, False
    for i, line in enumerate(text.splitlines(), 1):
        if line.startswith("## "):
            inside = line.strip() == "## Learned"
            continue
        if not inside or not line.startswith("|") or re.match(r"^\|\s*(Item|-+)\s*\|", line):
            continue
        m = LEARNED_ROW.match(line)
        if not m:
            problems.append(f"{name}:{i}: a Learned row is not "
                            "`| L<n> | YYYY-MM-DD | <from the person> | <looks for> |`")
            continue
        item, since, heard, looks = m.groups()
        n = int(item[1:])
        if item in seen:
            problems.append(f"{name}:{i}: {item} is used twice — the next free number, never reused")
        elif n <= last:
            problems.append(f"{name}:{i}: {item} comes after L{last} — numbers rise; a retired item leaves its gap")
        seen.add(item)
        last = max(last, n)
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", since) or since > today:
            problems.append(f"{name}:{i}: {item}'s date \"{since}\" is not a real day up to today (YYYY-MM-DD)")
        if not heard or not looks:
            problems.append(f"{name}:{i}: {item} needs what the person saw and what in a diff predicts it")
    return problems


def judgement_problems(lines: list[str]) -> list[str]:
    """Each line of the judgements log parses and carries the fields calibration reads."""
    problems = []
    kinds = {"finding", "false-alarm", "decline", "approval"}
    for i, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except ValueError:
            problems.append(f"judgements.jsonl:{i}: not JSON")
            continue
        if r.get("kind") not in kinds:
            problems.append(f"judgements.jsonl:{i}: kind {r.get('kind')!r} is none of {sorted(kinds)}")
        if r.get("route") not in ROUTES:
            problems.append(f"judgements.jsonl:{i}: route {r.get('route')!r} is none of {ROUTES}")
        if r.get("about") not in (None,) + AREAS:
            problems.append(f"judgements.jsonl:{i}: about {r.get('about')!r} is none of {list(AREAS)}")
        if r.get("kind") in ("decline", "approval") and r.get("draft") not in KINDS_BEFORE + KINDS_AFTER + ("option",):
            problems.append(f"judgements.jsonl:{i}: a {r['kind']} names no kind of draft")
    return problems


def check_rubrics(run_dir: Path) -> dict:
    """The rubrics' Learned tables and the judgements log are written as calibration and the judges read them."""
    problems = []
    for p in sorted(RUBRICS.glob("*.md")):
        problems += rubric_problems(p.relative_to(ROOT).as_posix(), p.read_text(errors="replace"))
    if JUDGEMENTS.is_file():
        problems += judgement_problems(JUDGEMENTS.read_text().splitlines())
    (run_dir / "rubrics.log").write_text("\n".join(problems) + "\n")
    return {"ok": not problems, "detail": f"{len(problems)} problem(s) in the rubrics' learned items and the "
                                          "judgements log", "tail": problems[:16]}


BUILTIN = {"docs": check_docs, "harness": check_harness, "design": check_design, "a11y": check_a11y,
           "motion": check_motion, "touch": check_touch, "layout": check_layout,
           "typography": check_typography, "storybook": check_storybook, "playwright": check_playwright,
           "rubrics": check_rubrics, "e-ink": check_eink, "ux": check_ux,
           "esp-idf": check_esp_idf, "react-vite": check_react_vite, "secrets": check_secrets, "scope": check_scope}
CHECKS = {**BUILTIN, **{name: project_check(name) for name in project.CHECKS}}
WAIT = {name for name, spec in project.CHECKS.items() if spec.get("wait")}
# The checks whose failure counts toward MAX_FAILURES: the project's build and tests ("counts": True in
# .agents/project.py). A lint, a doc or a self-test failure is fixed and run again without spending an attempt.
COUNTED = {name for name, spec in project.CHECKS.items() if spec.get("counts")}


def plan(files: list[str], only: set[str] | None) -> list[str]:
    """The checks the touched files call for, or exactly `--only`'s."""
    if only:
        return [c for c in CHECKS if c in only]
    wants = {
        "docs": any(is_kit_or_doc(f) or project.is_code(f) for f in files),
        "harness": any(f.startswith(HARNESS) for f in files),
        "design": (ROOT / DESIGN_CHECK).is_file()
        and any(is_design(f) or f.startswith(f"{SKILLS}/design-system/") for f in files),
        "a11y": (ROOT / A11Y_SCRIPTS / "a11y_check.py").is_file()
        and any(f.startswith(A11Y_SKILL) or project.matches(f, project.UI_PATHS) for f in files),
        "motion": (ROOT / MOTION_CHECK).is_file()
        and any(f.startswith(MOTION_SKILL) or project.matches(f, project.UI_PATHS) for f in files),
        "touch": (ROOT / TOUCH_CHECK).is_file()
        and any(f.startswith(TOUCH_SKILL) or project.matches(f, project.UI_PATHS) for f in files),
        "layout": (ROOT / LAYOUT_CHECK).is_file()
        and any(f.startswith(LAYOUT_SKILL) or project.matches(f, project.UI_PATHS) for f in files),
        "typography": (ROOT / TYPE_CHECK).is_file()
        and any(f.startswith(TYPE_SKILL) or project.matches(f, project.UI_PATHS) for f in files),
        "storybook": (ROOT / STORY_CHECK).is_file()
        and any(f.startswith(STORY_SKILL) or project.matches(f, project.UI_PATHS) for f in files),
        "rubrics": any(f.startswith((".agents/rubrics/", ".agents/evals/", f"{SKILLS}/verify-change/")) for f in files),
        "e-ink": (ROOT / EINK_CHECK).is_file()
        and any(f.startswith(EINK_SKILL) or project.matches(f, EINK_PATHS) for f in files),
        "playwright": (ROOT / PW_CHECK).is_file()
        and any(f.startswith(PW_SKILL) or (not f.startswith(".agents/") and PW_FILES.search(f)) for f in files),
        # the app's paths only in an ESP-IDF app: a web app's `components/` is not one
        "esp-idf": (ROOT / ESP_SCRIPT).is_file()
        and any(f.startswith(ESP_SKILL) or ((ROOT / "main/app_features.def").is_file()
                                            and project.matches(f, ESP_PATHS)) for f in files),
        # the app's paths only in a React and Vite app: another project's `src/` is not one
        "react-vite": (ROOT / WEB_SCRIPT).is_file()
        and any(f.startswith(WEB_SKILL) or (project.matches(f, WEB_PATHS) and is_react_vite_app()) for f in files),
        "ux": (ROOT / UX_LINT).is_file()
        and any(f.startswith(UX_SKILL) or project.matches(f, ux_paths()) for f in files),
        "secrets": (ROOT / SECRET_SCAN).is_file() and bool(files),  # every change: cheap, and before the commit
        "scope": any(f.startswith((f"{SKILLS}/", ".agents/agents/")) for f in files),
        **{name: any(project.matches(f, spec["when"]) for f in files) for name, spec in project.CHECKS.items()},
    }
    return [c for c in CHECKS if wants[c]]


def debug_hits() -> list[str]:
    if not project.DEBUG_MARKERS:
        return []
    return git("grep", "-nE", project.DEBUG_MARKERS, "--", *project.code_pathspec()).splitlines()


def broken_invariants() -> list[str]:
    out = []
    for path, pattern, why in project.INVARIANTS:
        p = ROOT / path
        if not p.is_file() or not re.search(pattern, p.read_text(errors="replace"), re.M):
            out.append(f"{path} lacks /{pattern}/ — {why}")
    return out


# --- The commands ------------------------------------------------------------------------------------------------

def cmd_start(args: argparse.Namespace) -> int:
    with locked(TASK):
        old = load()
        if old.get("runs"):
            write_atomic(STATE / "history" / f"{old['started'].replace(':', '')}.json", json.dumps(old, indent=2))
        shutil.rmtree(SNAPSHOTS, ignore_errors=True)  # the last task's judges' snapshots: no delta reaches back
        save(new_task(args.task))
    print(f"task started: {args.task} — the retry limit is {MAX_FAILURES}")
    gated = [what for what, paths, kinds in project.GATES if paths and set(kinds) & set(KINDS_BEFORE)]
    if gated:
        print(f"a visible change ({', '.join(gated)}) starts with a draft and the person's yes on it — "
              "verify.py approve <file> --kind ux|mock|motion|copy, before the first edit")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    task = load() or new_task("(unnamed)")
    files = changed_files()
    only = set(args.only.split(",")) if args.only else None
    checks = plan(files, only)
    n = len(task["runs"]) + 1
    run_dir = STATE / "runs" / str(n)
    run_dir.mkdir(parents=True, exist_ok=True)
    print(f"run {n} — {len(files)} changed file(s); checks: {', '.join(checks) or 'none'}")
    t0 = time.time()
    first = [c for c in checks if c not in WAIT]
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {c: pool.submit(CHECKS[c], run_dir) for c in first}
        results = {c: f.result() for c, f in futures.items()}
    for c in checks:
        if c in WAIT:
            results[c] = CHECKS[c](run_dir)
    for c in checks:
        r = results[c]
        print(f"  {c:9} {'PASS' if r['ok'] else 'FAIL'}  {r['detail']}")
        for line in r["tail"]:
            print(f"            | {line}")
    hits = debug_hits()
    if hits:
        print(f"  debug     ON    a debug marker in the tree ({len(hits)} line(s)) — remove it before finish")
    ok = all(r["ok"] for r in results.values())
    counted = any(not results[c]["ok"] for c in COUNTED if c in results)
    # Read again under the lock: a review or a finding recorded while the checks ran is kept.
    with task_update(task["task"]) as task:
        task["failures"] = 0 if ok else task["failures"] + 1 if counted else task["failures"]
        task["runs"].append({"n": n, "at": now(), "ok": ok,
                             "checks": {c: {k: v for k, v in r.items() if k != "tail"} for c, r in results.items()},
                             "files": files, "gated": gated_contents(files), "fingerprint": tree_fingerprint(),
                             "debug": bool(hits), "partial": bool(only),
                             "seconds": round(time.time() - t0)})
    print(f"run {n}: {'PASS' if ok else 'FAIL'} in {time.time() - t0:.0f} s — logs in {run_dir.relative_to(ROOT)}")
    if not ok and not counted:
        print(f"failed, not counted — only {', '.join(sorted(COUNTED)) or 'no check'} count toward the retry limit "
              "(\"counts\": True in .agents/project.py); fix and run again")
        return 1
    if not ok:
        return stop_or_retry(task)
    judges = [j for j, wants in JUDGES.items() if judge_ready(j) and any(wants(f) for f in files)]
    if judges:
        print(f"next: the judges — {', '.join(judges)} (ask them in parallel: `verify.py ask <judge>` for each before "
              "briefing it, then record each with `verify.py review`)")
    return 0


def stop_or_retry(task: dict) -> int:
    if task["failures"] >= MAX_FAILURES:
        print(f"STOP: {task['failures']} failed attempts in a row — the retry limit. Ask the person; do not try "
              "again on your own.")
        print("first record the approach that failed and why: verify.py finding \"<approach, why it failed>\" "
              "--source agent --route doc|skill|open-item (verify-change → Recording what was learned)")
        return 3
    print(f"attempt {task['failures']} of {MAX_FAILURES} failed — fix and run again")
    return 1


def cmd_review(args: argparse.Namespace) -> int:
    dims = load_weights()["judges"].get(args.judge, {})
    scored = None
    files = changed_files()
    try:
        nits = parse_nits(args.nit, judge_files(args.judge, files))
    except ValueError as e:
        print(f"review: {e}", file=sys.stderr)
        return 2
    if args.out_of_scope:
        return review_out_of_scope(args, dims, files, nits)
    if args.score or args.scores_file:
        if not dims:
            print(f"review: {args.judge} has no quality dimensions in {WEIGHTS.relative_to(ROOT)}", file=sys.stderr)
            return 2
        try:
            raw, reasons = read_scores(args.score, args.scores_file, args.note, dims)
        except ValueError as e:
            print(f"review: {e}", file=sys.stderr)
            return 2
        # A review scores the change: the proxy measures the change's scope, run now so its results are this tree's.
        if proxy_built(args.judge) and not args.no_proxy:
            print(f"proxy ({SCOPE_CHANGE}): {run_proxy(args.judge)}")
        scored = scorecard(args.judge, raw, reasons, dims, SCOPE_CHANGE)
    with task_update() as task:  # a blocking verdict is fixed and asked again; it does not count toward the limit
        taken = take_asked(task, args.judge)  # the files as they were when the judge was asked, if it was
        review = {"verdict": args.verdict, "note": args.note, **(taken or stamp(args.judge, files)), "at": now(),
                  "nits": nits, "history": [], **(scored or {})}
        carried = accepted(task, args.judge, review) if scored and scored["quality"] is not None \
            and scored["quality"] < QUALITY_BAR else None
        if carried:  # a carry-forward, kept in the review's history so status and finish show it
            review["history"].append({"kind": "acceptance", "at": review["at"], "from": carried["review_at"],
                                      "quality": carried["quality"], "now": scored["quality"],
                                      "words": carried["words"]})
        task["reviews"][args.judge] = review
        if not taken:
            save_snapshot(task, args.judge, judge_files(args.judge, files))
    print(f"review recorded: {args.judge} {args.verdict}" + (f" with {len(nits)} nit(s)" if nits else "")
          + (f" — on its files as they were when asked, {taken['read_at']}" if taken else ""))
    if scored:
        log_score({"kind": "review", "judge": args.judge, "verdict": args.verdict, **scored})
        print_scorecard(args.judge, scored, dims, gate=not carried)
        if carried:
            print(f"the person's acceptance at {carried['quality']}/100 carries to this review — its score "
                  f"{scored['quality']} is the same or higher: \"{carried['words']}\"")
    elif dims:
        print(f"no quality score — finish holds {args.judge} to the bar ({QUALITY_BAR}): record its Score block with "
              "--score dim=n,... and a reason per dimension in --note, or --scores-file")
    if args.verdict == "blocking":
        print(f"each item {args.judge} raised that you fix is a catch: verify.py finding \"<what>\" --source agent "
              f"--route <route> --judge {args.judge} --caught yes; one that was not a problem: verify.py dispute")
        return 1
    return 0


def review_out_of_scope(args: argparse.Namespace, dims: dict, files: list[str], nits: list[dict]) -> int:
    """The verdict of a judge whose measured scope the change never touches, with no score — verify.py checks that
    the scope is empty, so the claim is never only the agent's word."""
    if args.score or args.scores_file or not dims:
        print("review: --out-of-scope takes no score, and is for a judge with quality dimensions", file=sys.stderr)
        return 2
    if proxy_built(args.judge) and not args.no_proxy:
        print(f"proxy ({SCOPE_CHANGE}): {run_proxy(args.judge)}")
    ok, said = out_of_scope_check(args.judge)
    print(said)
    if not ok:
        print(f"review refused: {args.judge} is not out of scope — record its score: verify.py review {args.judge} "
              f"{args.verdict} --score dim=n,... --note \"dim: why; …\"", file=sys.stderr)
        return 1
    with task_update() as task:
        taken = take_asked(task, args.judge)
        task["reviews"][args.judge] = {"verdict": args.verdict, "note": args.note, "quality": None,
                                       "out_of_scope": True, "scope": said, "scope_fingerprint": tree_fingerprint(),
                                       **(taken or stamp(args.judge, files)), "at": now(), "nits": nits,
                                       "history": []}
        if not taken:
            save_snapshot(task, args.judge, judge_files(args.judge, files))
    print(f"review recorded: {args.judge} {args.verdict} — {OUT_OF_SCOPE}, not held to the bar; finish still needs "
          "its verdict")
    return 1 if args.verdict == "blocking" else 0


def cmd_ask(args: argparse.Namespace) -> int:
    """The judge is being asked: its files kept as they are now, and the time, so its review rests on what it read —
    an edit made while it reads shows in the next `delta` (.agents/HARNESS.md §13)."""
    with task_update() as task:
        files = judge_files(args.judge)
        save_snapshot(task, args.judge, files, asked_dir(task, args.judge))
        task.setdefault("asked", {})[args.judge] = now()
    print(f"asked: {args.judge} — its {len(files)} file(s) kept as it reads them; brief it now, and record its verdict "
          f"with verify.py review {args.judge} …")
    return 0


def cmd_nits_fixed(args: argparse.Namespace) -> int:
    """A pass re-stamped on the tree when every hunk since the judge's snapshot — normalised, so a comment or
    whitespace edit is none — lies within NIT_SLACK lines of a nit it raised. A blocking verdict is never cleared here:
    only a new pass clears it (.agents/HARNESS.md §13)."""
    task, judge = load(), args.judge
    r = (task.get("reviews") or {}).get(judge)
    if not r:
        print(f"nits-fixed: no review from {judge} this task", file=sys.stderr)
        return 1
    if r["verdict"] != "pass":
        print(f"nits-fixed: {judge} said blocking — that stays in force until it records a new pass; fix it, then "
              f"give it the delta: verify.py delta {judge}", file=sys.stderr)
        return 1
    files = changed_files()
    if review_stands(judge, r, files):
        print(f"nits-fixed: {judge}'s review already stands on this tree — nothing to re-stamp")
        return 0
    snap = load_snapshot(task, judge)
    if snap is None:
        print(f"nits-fixed: no snapshot of what {judge} read — ask it for a full review", file=sys.stderr)
        return 1
    jf = judge_files(judge, files)
    moved = sorted(set(jf) ^ set(snap["files"]))
    hunks = [h for f, old, new in delta_since(task, judge, snap, jf) for h in unit_hunks(f, old, new)]
    away = [h for h in hunks if not near_nit(h, r.get("nits") or [])]
    if moved or away or not r.get("nits"):
        why = (f"files added to or gone from what it read: {', '.join(moved[:4])}" if moved
               else "the review raised no nits" if not r.get("nits")
               else f"{len(away)} hunk(s) by no nit — more than {NIT_SLACK} lines from every nit, or longer than "
                    f"its lines plus {NIT_SLACK} — first at {away[0]['path']}:{away[0]['old'][0]}")
        print(f"nits-fixed refused: {why}. Re-review the delta: verify.py delta {judge}, then verify.py review "
              f"{judge} …", file=sys.stderr)
        return 1
    with task_update() as fresh:
        rr = fresh["reviews"].get(judge)
        if not rr or rr.get("at") != r["at"]:
            print(f"nits-fixed: {judge} reviewed again meanwhile — nothing re-stamped", file=sys.stderr)
            return 1
        rr.setdefault("history", []).append({"kind": "nits-fixed", "at": now(), "hunks": len(hunks),
                                             "from": rr.get("fingerprint")})
        rr.update(stamp(judge, files))
    print(f"nits-fixed: {judge}'s pass re-stamped — {len(hunks)} hunk(s), each within {NIT_SLACK} lines of a nit "
          "it raised")
    return 0


def mark_hunk(lines: list[str], hunks: list[dict], nits: list[dict], path: str) -> str:
    """A unified diff hunk's tag: comments or whitespace only, or changed — and the nit it lies by."""
    old_n = new_n = 0
    head = re.match(r"@@ -(\d+)(?:,\d+)? \+(\d+)", lines[0])
    if head:
        old_n, new_n = int(head.group(1)), int(head.group(2))
    olds, news = set(), set()
    for ln in lines[1:]:
        if ln.startswith("-"):
            olds.add(old_n)
            old_n += 1
        elif ln.startswith("+"):
            news.add(new_n)
            new_n += 1
        else:
            old_n, new_n = old_n + 1, new_n + 1
    hit = [h for h in hunks if (h["old"][2] and olds & set(range(h["old"][0], h["old"][1] + 1)))
           or (h["new"][2] and news & set(range(h["new"][0], h["new"][1] + 1)))]
    if not hit:
        return "[comments or whitespace only]"
    nit = next((n for n in (near_nit(h, nits) for h in hit) if n), None)
    return "[changed]" + (f" [by the nit {nit_name(nit)}]" if nit and all(near_nit(h, nits) for h in hit) else "")


def cmd_delta(args: argparse.Namespace) -> int:
    """The brief for a re-review of only what changed: the judge's last verdict, note and nits, then the unified diff
    between what it read and the tree, each hunk marked (.agents/HARNESS.md §13)."""
    task, judge = load(), args.judge
    r = (task.get("reviews") or {}).get(judge)
    if not r:
        print(f"delta: no review from {judge} this task — ask it for a full review", file=sys.stderr)
        return 1
    quality = f", quality {r['quality']}/100" if r.get("quality") is not None else ""
    print(f"{judge}'s last verdict: {r['verdict']}{quality}, at {r['at']}")
    if r.get("note"):
        print(f"its note: {r['note']}")
    for n in r.get("nits") or []:
        print(f"its nit: {nit_name(n)}")
    for h in r.get("history") or []:
        print(f"carried forward: {carry_line(h)}")
    snap = load_snapshot(task, judge)
    if snap is None:
        print(f"no snapshot of what {judge} read — ask it for a full review", file=sys.stderr)
        return 1
    changed = delta_since(task, judge, snap, judge_files(judge))
    substantive = 0
    for f, old, new in changed:
        hunks = unit_hunks(f, old, new)
        substantive += len(hunks)
        diff = list(difflib.unified_diff((old or "").splitlines(), (new or "").splitlines(),
                                         f"a/{f} (as {judge} read it)" if old is not None else "/dev/null",
                                         f"b/{f}" if new is not None else "/dev/null", lineterm=""))
        starts = [i for i, ln in enumerate(diff) if ln.startswith("@@")] + [len(diff)]
        print("\n".join(diff[:starts[0]]))
        for a, b in zip(starts, starts[1:]):
            print(f"{diff[a]}  {mark_hunk(diff[a:b], hunks, r.get('nits') or [], f)}")
            print("\n".join(diff[a + 1:b]))
    if not changed:
        print(f"nothing changed in {judge}'s files since it read them")
    elif not substantive:
        print("every hunk is comments or whitespace — the review stands on this tree")
    else:
        print(f"brief: re-review this delta and what it touches; the earlier passes stand for the rest — say so. "
              f"Record the verdict: verify.py review {judge} pass|blocking …")
    return 0


def changed_lines_of(path: str) -> set[int] | None:
    """The lines the change wrote in a file, against HEAD; None for a file git does not track (every line)."""
    if not git("ls-files", "--", path).strip():
        return None
    lines: set[int] = set()
    for m in re.finditer(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", git("diff", "-U0", "HEAD", "--", path), re.M):
        start, count = int(m.group(1)), int(m.group(2) if m.group(2) is not None else 1)
        lines.update(range(start, start + count))
    return lines


def long_lines(files: list[str]) -> list[str]:
    """The changed lines of the changed C, C++, Python and shell files longer than LINE_LIMIT."""
    out = []
    skip = tuple(getattr(project, "GENERATED", ())) + tuple(getattr(project, "MANAGED", ())) \
        + tuple(getattr(project, "VENDORED", ()))
    for f in files:
        text = read_text(ROOT / f)
        if text is None or project.matches(f, skip) or kind_of(f, text) not in ("c", "py", "sh"):
            continue
        wrote = changed_lines_of(f)
        for n, line in enumerate(text.split("\n"), 1):
            if (wrote is None or n in wrote) and len(line) > LINE_LIMIT:
                out.append(f"{f}:{n} is {len(line)} characters — over {LINE_LIMIT}")
    return out


def cmd_selfcheck(_: argparse.Namespace) -> int:
    """The fast, deterministic proxies on the changed files only — what a judge would otherwise flag as a nit — run by
    the builder before it asks the judges (.agents/HARNESS.md §13)."""
    t0, files, flagged = time.time(), changed_files(), []
    log_dir = STATE / "selfcheck"
    log_dir.mkdir(parents=True, exist_ok=True)
    docs = [f for f in files if f.endswith(".md") and is_kit_or_doc(f)]
    ui = [f for f in files if project.matches(f, ux_paths())]
    for judge, wanted, what in (("doc-reviewer", docs, "doc"), ("ux-content-writer", ui, "UI")):
        if not wanted:
            continue
        if not proxy_built(judge):
            print(f"{what} files changed, but {judge}'s proxy is not built (PROXIES in .agents/project.py)")
            continue
        print(f"{judge}'s proxy on {len(wanted)} changed {what} file(s): {run_proxy(judge)}")
        caps, carried = split_metrics(proxy_data(judge), judge)
        flagged += [f"{judge} {d}: {r}" for d, rs in caps.items() for r in rs]
        if carried:
            print(f"  {sum(map(len, carried.values()))} metric(s) of carried debt — out of range at the base too")
    if ui and not proxy_built("ux-content-writer") and (ROOT / UX_LINT).is_file():
        code, out = sh([sys.executable, UX_LINT, *ui], log_dir / "ux.log")
        flagged += [] if code == 0 else [ln.strip() for ln in out.splitlines() if re.search(r"\bU\d+\b", ln)][:20]
    flagged += long_lines(files)
    anchors = ROOT / DOC_SCRIPTS / "check_anchors.py"
    if anchors.is_file() and files:
        code, out = sh([sys.executable, str(anchors)], log_dir / "anchors.log")
        flagged += [] if code == 0 else failing(out) or tail(out, 4)
    for line in flagged:
        print(f"  nit: {line}")
    print(f"selfcheck: {len(flagged)} thing(s) a judge would flag, on {len(files)} changed file(s), in "
          f"{time.time() - t0:.1f} s" + ("" if flagged else " — ask the judges"))
    return 1 if flagged else 0


def cmd_approve(args: argparse.Namespace) -> int:
    """The person's yes to a draft — a mock, a motion study, the copy — or to the built thing beside it, recorded
    with the file's hash, so a file changed after the yes is not the one approved (.agents/HARNESS.md §9). Only the
    person's own words name the file; a request, a silence or a judge's pass is not a yes."""
    path = Path(args.file).expanduser()
    digest = file_hash(path)
    if digest is None:
        print(f"approve: no file at {path}", file=sys.stderr)
        return 2
    no = next((d for d in load().get("declines", []) if d["sha"] == digest), None)
    if no:
        print(f"approve: the person said no to {path.name} as it is — \"{no['text']}\"; draw the next draft and show "
              "them that", file=sys.stderr)
        return 1
    with task_update() as task:
        task["approvals"].append({"kind": args.kind, "file": str(path.resolve()), "sha": digest, "note": args.note,
                                  "at": now(), "code": gated_fingerprint(kind=args.kind)})
    # Logged too, so calibration can set the person's yeses against their noes per kind of draft
    log_judgement({"kind": "approval", "draft": args.kind, "file": path.name, "source": "person", "route": "none"})
    print(f"approval recorded: {args.kind} {path.name} ({digest})")
    return 0


def cmd_kitdiff(args: argparse.Namespace) -> int:
    """The whole diff of the paths a `kit` gate covers — changes to tracked files and every new file in full — for
    the person to read before their `kit` yes; `git diff` alone leaves new files out (AGENT_HARNESS §11.3)."""
    paths = [p for _, ps, kinds in project.GATES if "kit" in kinds for p in ps]
    if not paths:
        print("kitdiff: no gate asks for a kit yes (.agents/project.py → GATES)", file=sys.stderr)
        return 2
    new = [f for f in git("ls-files", "--others", "--exclude-standard", "--", *paths).splitlines() if f]
    text = git("diff", "HEAD", "--", *paths)
    for f in new:  # git exits 1 when the files differ; its output is the diff
        text += subprocess.run(["git", "diff", "--no-index", "--", "/dev/null", f], cwd=ROOT, capture_output=True,
                               text=True).stdout
    out = Path(args.out).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text)
    changed = len(re.findall(r"^diff --git ", text, re.M))
    print(f"kit diff: {changed} file(s), {len(new)} new, in {out}" + (" — new: " + ", ".join(new) if new else ""))
    return 0


def cmd_decline(args: argparse.Namespace) -> int:
    """The person's no to a draft — a UX brief, an option, a mock, a motion study, the copy, the built screen — in
    their words, with the file's hash, so the same file cannot be approved later, and routed like any lesson, so the
    next draft and the next task avoid it (AGENT_HARNESS §9.2)."""
    path = Path(args.file).expanduser()
    digest = file_hash(path)
    if digest is None:
        print(f"decline: no file at {path}", file=sys.stderr)
        return 2
    if args.route == "rubric" and not args.judge:
        print("decline: a rubric lesson names the agent whose rubric learns it — --judge ui-designer, ux-designer, …",
              file=sys.stderr)
        return 2
    entry = {"kind": "decline", "draft": args.kind, "file": path.name, "sha": digest, "source": "person",
             "text": args.text, "about": args.about, "route": args.route, "judge": args.judge, "caught": None,
             "edit": args.edit}
    with task_update() as task:
        task.setdefault("declines", []).append({**entry, **lesson_snapshot(args.route, args.judge)})
    log_judgement(entry)
    print(f"no recorded: {args.kind} {path.name} ({args.about}) → route: {args.route}"
          + (f" ({args.judge}'s rubric)" if args.judge else "")
          + " — make the edit the route names in this change, then draw the next draft, n + 1")
    return 0


def cmd_decision(args: argparse.Namespace) -> int:
    """The person's word on something a judge might flag — settled for this task. A rule meant to last goes into the
    doc that owns it as well."""
    with task_update() as task:
        task["decisions"].append({"text": args.text, "at": now()})
    print(f"decision recorded: {args.text} — the judges read it in `verify.py status`; a rule meant to last goes in "
          "its doc too")
    return 0


def cmd_target(args: argparse.Namespace) -> int:
    with task_update() as task:
        task["target"] = {"where": args.where, "build": args.build, "health_exit": args.health_exit,
                          "note": args.note, "at": now(), "deployed": deployed_fingerprint()}
        # Every run on the target, with how many findings and decisions were recorded by then — finish reads it
        # (unrecorded_redeploys).
        task.setdefault("target_log", []).append({"at": task["target"]["at"], "deployed": task["target"]["deployed"],
                                                  "findings": len(task.get("findings", [])),
                                                  "decisions": len(task.get("decisions", []))})
    print(f"target recorded: {args.build} on {args.where}"
          + (f", health check exit {args.health_exit}" if args.health_exit is not None else "")
          + f" — run {len(task['target_log'])} on the target this task")
    return 0


def unrecorded_redeploys(target_log: list[dict], covered: frozenset = frozenset()) -> list[str]:
    """The code ran on the target again, changed, with nothing recorded between. A change after the person looked at
    the target almost always follows something they pointed out; that report is a lesson — a finding, with --judge
    when a judge reviewed that part — or, for a change they asked for, their decision (verify-change → Recording what
    was learned). Unrecorded, calibration shows every judge perfect and no rubric learns. A lesson recorded late names
    the run that shipped its change (`finding --for-run N`), and `covered` holds those runs: it closes that gap."""
    gaps = []
    for n, (a, b) in enumerate(zip(target_log, target_log[1:]), start=1):
        if n + 1 in covered:
            continue
        if b["deployed"] != a["deployed"] and b["findings"] == a["findings"] and b["decisions"] == a["decisions"]:
            gaps.append(f"target run {n} → {n + 1} ({a['at']} → {b['at']}): the code changed with no finding or "
                        "decision recorded between — if the person pointed out a problem on the target, ask them "
                        "whether to record it as an eval and record it (verify.py finding \"<what they saw>\" --route "
                        "<route>, with --judge <judge> --caught no when a judge reviewed that part); a change they "
                        "asked for is their decision (verify.py decision); the agent's own fix is a finding "
                        f"--source agent; recorded after the run, name it: --for-run {n + 1}")
    return gaps


def cmd_signoff(args: argparse.Namespace) -> int:
    """The person's yes on the target, after it ran there (.agents/HARNESS.md §9). It holds for the code as deployed —
    a code change after it needs the target and their look again."""
    task = load() or new_task("(unnamed)")
    target = task.get("target")
    if not target:
        print("signoff: nothing ran on the target this task — run it there, record it with verify.py target, then "
              "show the person", file=sys.stderr)
        return 1
    if target["deployed"] != deployed_fingerprint():
        print("signoff: the code changed since it ran on the target — run it again, record it with verify.py "
              "target, and show the person again", file=sys.stderr)
        return 1
    with task_update() as task:
        task["signoffs"].append({"text": args.text, "at": now(), "deployed": target["deployed"]})
    print(f"sign-off recorded: {args.text} — the person's yes on the target, for the code as it ran at {target['at']}")
    return 0


def signoff_state(s: dict) -> str:
    return "" if s["deployed"] == deployed_fingerprint() else " — the code changed since"


def log_judgement(entry: dict) -> None:
    entry = {"date": datetime.now().date().isoformat(), "task": load().get("task", "(unnamed)"),
             "commit": git("rev-parse", "--short", "HEAD").strip(), **entry}
    append_line(JUDGEMENTS, json.dumps(entry))


def cmd_finding(args: argparse.Namespace) -> int:
    if args.judge and args.caught is None:
        print("--judge needs --caught yes|no", file=sys.stderr)
        return 2
    if args.route == "rubric" and not args.judge:
        print("finding: a rubric lesson names the agent whose rubric learns it — --judge <agent> --caught yes|no",
              file=sys.stderr)
        return 2
    task = load() or new_task("(unnamed)")
    runs = len(task.get("target_log", []))
    if args.for_run is not None and not 2 <= args.for_run <= runs:
        print(f"--for-run names a run on the target after the first: 2 to {runs} this task", file=sys.stderr)
        return 2
    entry = {"kind": "finding", "source": args.source, "text": args.text, "about": args.about, "route": args.route,
             "judge": args.judge, "caught": args.caught == "yes" if args.judge else None, "edit": args.edit}
    if args.for_run is not None:
        entry["for_run"] = args.for_run  # recorded late: the run on the target that shipped this lesson's change
    with task_update() as fresh:
        fresh["findings"].append({**entry, **lesson_snapshot(args.route, args.judge)})
    log_judgement(entry)
    print(f"finding recorded ({args.source}) → route: {args.route} — make the edit the route names in this change "
          "(verify-change → Recording what was learned)")
    return 0


def cmd_dispute(args: argparse.Namespace) -> int:
    entry = {"kind": "false-alarm", "source": args.source, "text": args.text, "about": args.about, "route": "rubric",
             "judge": args.judge, "caught": None, "edit": args.edit}
    with task_update() as task:
        task["findings"].append({**entry, **lesson_snapshot("rubric", args.judge)})
    log_judgement(entry)
    print(f"false alarm recorded against {args.judge} → route: rubric — tighten the item it misread")
    return 0


# --- Quality: scores, proxies, taste and weights (.agents/HARNESS.md §12) ----------------------------------------

def save_weights(data: dict) -> None:
    write_atomic(WEIGHTS, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def weights_of(dims: dict) -> dict:
    return {d: v["weight"] for d, v in dims.items()}


def score_rows() -> list[dict]:
    try:
        return [json.loads(line) for line in SCORES.read_text().splitlines() if line.strip()]
    except (OSError, ValueError):
        return []


def log_score(entry: dict) -> None:
    entry = {"date": datetime.now().date().isoformat(), "at": now(), "task": load().get("task", "(unnamed)"),
             "commit": git("rev-parse", "--short", "HEAD").strip(), **entry}
    append_line(SCORES, json.dumps(entry, ensure_ascii=False))


def parse_score_arg(text: str) -> dict:
    """`hierarchy=3,spacing=2,consistency=na` → {dimension: 0–4 or None}."""
    out = {}
    for part in filter(None, (p.strip() for p in (text or "").split(","))):
        if "=" not in part:
            raise ValueError(f"--score takes dim=n pairs: {part!r}")
        d, v = (s.strip() for s in part.split("=", 1))
        out[d] = None if v.lower() in ("na", "n/a") else int(v) if v.isdigit() else v
    return out


def parse_reasons(note: str, dims) -> dict:
    """A reason per dimension from a note written `dim: why; dim: why` (or one per line)."""
    out = {}
    for part in re.split(r";|\n", note or ""):
        m = re.match(r"\s*([\w-]+)\s*:\s*(.+)", part)
        if m and m.group(1) in dims:
            out[m.group(1)] = m.group(2).strip()
    return out


def read_scores(score_arg: str | None, scores_file: str | None, note: str | None, dims: dict) -> tuple[dict, dict]:
    """Every dimension of the judge scored 0–4 (or `na`, left out of the weighting), each with its reason."""
    raw, reasons = {}, {}
    if scores_file:
        try:
            data = json.loads(Path(scores_file).expanduser().read_text())
        except (OSError, ValueError) as e:
            raise ValueError(f"cannot read {scores_file}: {e}")
        data = data.get("scores", data) if isinstance(data, dict) else {}
        for d, v in data.items():
            if isinstance(v, dict):
                raw[d] = v.get("score")
                if v.get("reason"):
                    reasons[d] = str(v["reason"])
            else:
                raw[d] = v
        raw = {d: None if isinstance(v, str) and v.lower() in ("na", "n/a") else v for d, v in raw.items()}
    raw.update(parse_score_arg(score_arg))
    reasons.update(parse_reasons(note, dims))
    unknown = sorted(set(raw) - set(dims))
    if unknown:
        raise ValueError(f"no such dimension {unknown} — one of {', '.join(dims)}")
    missing = [d for d in dims if d not in raw]
    if missing:
        raise ValueError(f"every dimension is scored (0–4, or na): missing {', '.join(missing)}")
    bad = [d for d, v in raw.items() if v is not None and (not isinstance(v, int) or not 0 <= v <= SCORE_MAX)]
    if bad:
        raise ValueError(f"a score is 0–{SCORE_MAX} or na: {', '.join(f'{d}={raw[d]}' for d in bad)}")
    unreasoned = [d for d in dims if not reasons.get(d)]
    if unreasoned:
        raise ValueError(f"a reason per dimension, with its evidence — --note \"dim: why; dim: why\" or the file's "
                         f"\"reason\": missing {', '.join(unreasoned)}")
    total = sum(v.get("weight", 0) for v in dims.values())
    share = sum(v.get("weight", 0) for d, v in dims.items() if raw[d] is not None) / total if total else 1
    if share < NA_FLOOR:
        raise ValueError(f"only {share:.0%} of the weight is scored — at least {NA_FLOOR:.0%} must be, or the score "
                         f"says little: score more dimensions than {', '.join(d for d in dims if raw[d] is not None)}"
                         " (na only where a dimension cannot apply), or leave the score out of this review")
    return raw, reasons


def weighted(scores: dict, weights: dict) -> int | None:
    """The quality score 0–100: each dimension's 0–4 times its weight, over the weights of the dimensions scored."""
    used = {d: w for d, w in weights.items() if scores.get(d) is not None}
    total = sum(used.values())
    if not total:
        return None
    return round(100 * sum(w * scores[d] / SCORE_MAX for d, w in used.items()) / total)


def apply_caps(scores: dict, caps: dict) -> dict:
    """A dimension with a measured proxy out of its range scores at most PROXY_CAP."""
    return {d: min(s, PROXY_CAP) if s is not None and caps.get(d) else s for d, s in scores.items()}


def proxy_built(judge: str, cmd=None) -> bool:
    """Whether the judge's proxy command is filled in: not empty, no `<…>` placeholder, its script present."""
    cmd = list(PROXIES.get(judge) or () if cmd is None else cmd)
    if not cmd or any(str(a).startswith("<") for a in cmd):
        return False
    scripts = [a for a in cmd[1:] if str(a).endswith((".py", ".sh")) and not str(a).startswith("-")]
    return all((ROOT / a).is_file() for a in scripts)


def number(v) -> float | None:
    """A finite number, or None — a bool, a string, null or NaN is not one."""
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    return float(v) if math.isfinite(v) else None


def distance(value, rng) -> float | None:
    """How far a value lies outside its [lo, hi] range, 0 inside it; None when the value or the range is not numbers."""
    if not isinstance(rng, (list, tuple)) or len(rng) != 2:
        return None
    lo, hi, v = number(rng[0]), number(rng[1]), number(value)
    if None in (lo, hi, v):
        return None
    return max(lo - v, v - hi, 0.0)


def badness(v) -> float | None:
    return number(v)


def regression(m: dict) -> str | None:
    """Why a metric out of its range caps a review — it is new since the base, worse than there, or at a new place —
    or None when it is carried debt: out of range at the base already, no worse and nowhere new (SonarQube's Clean as
    You Code; .agents/HARNESS.md §12.5). The proxy writes `base`, the value at the base for the same scope (null: no
    such metric there), and may write `offenders` and `base_offenders`, {place: how bad}, which then decide alone. A
    metric with neither, or with anything that cannot be compared, caps — the check fails closed."""
    if m.get("ok") is not False:
        return None
    off, base_off = m.get("offenders"), m.get("base_offenders")
    if isinstance(off, dict) and isinstance(base_off, dict):
        if not off:
            return "out of range, but it names no place"
        if any(badness(v) is None for v in list(off.values()) + list(base_off.values())):
            return "not comparable: a place's measure is not a number"
        fresh = [k for k, v in off.items() if k not in base_off or badness(v) > badness(base_off[k])]
        if not fresh:
            return None
        return f"new or worse at {str(fresh[0])[:80]}" + (f" (+{len(fresh) - 1} more)" if len(fresh) > 1 else "")
    if "base" not in m:
        return "no base value to compare"
    if m["base"] is None:
        return "new since the base"
    now, was = distance(m.get("value"), m.get("range")), distance(m["base"], m.get("range"))
    if now is None or was is None:
        return "not comparable: the value, the base or the range is not numbers"
    if now > was + 1e-9:
        return f"worse than the base's {m['base']}"
    return None


def split_metrics(data: dict, judge: str) -> tuple[dict, dict]:
    """({dimension: [what caps it]}, {dimension: [the carried debt]}) from a proxy's JSON. In the change's scope a
    metric out of range caps only when `regression` says so; in the product's (an audit), every one caps."""
    caps: dict[str, list] = {}
    carried: dict[str, list] = {}
    if not isinstance(data, dict) or data.get("judge") not in (None, judge):
        return caps, carried
    change = data.get("scope", SCOPE_CHANGE) == SCOPE_CHANGE
    for m in data.get("metrics") or []:
        if not (isinstance(m, dict) and m.get("ok") is False and m.get("dimension")):
            continue
        said = (f"{m.get('name', '?')} {m.get('value', '?')} outside {m.get('range', '?')}"
                + (f" at {m['where']}" if m.get("where") else ""))
        why = regression(m) if change else None
        if not change or why:
            caps.setdefault(m["dimension"], []).append(said + (f" — {why}" if why else ""))
        else:
            carried.setdefault(m["dimension"], []).append(said + f" — carried: {m.get('base', 'here')} at the base")
    return caps, carried


def caps_from(data: dict, judge: str) -> dict:
    """{dimension: [the metric out of range, …]} from a proxy's JSON — those that cap (split_metrics)."""
    return split_metrics(data, judge)[0]


def epoch(at: str | None) -> float | None:
    """A proxy's `at` as seconds: ISO 8601, `Z` or an offset for UTC, none for local time."""
    if not at:
        return None
    try:
        t = datetime.fromisoformat(str(at).replace("Z", "+00:00"))
    except ValueError:
        return None
    return t.timestamp() if t.tzinfo else t.astimezone().timestamp()


def newest_change(files: list[str] | None = None) -> tuple[float, str | None]:
    """The newest modification time among the changed files a fingerprint watches, and which file it is."""
    best, name = 0.0, None
    for f in watched(files if files is not None else changed_files()):
        p = ROOT / f
        if p.is_file() and p.stat().st_mtime > best:
            best, name = p.stat().st_mtime, f
    return best, name


def proxy_last_run(judge: str) -> dict:
    try:
        return json.loads((PROXY_DIR / f"{judge}.run.json").read_text())
    except (OSError, ValueError):
        return {}


def proxy_state(judge: str, scope: str, files: list[str] | None = None) -> tuple[dict, str | None, str | None, dict]:
    """(caps, when the results were measured, why they were set aside, the carried debt). Results are used only when
    they measure the wanted scope, the last run that wrote them passed, and they are newer than every changed file;
    otherwise a warning, and no cap from them."""
    try:
        data = json.loads((PROXY_DIR / f"{judge}.json").read_text())
    except (OSError, ValueError):
        return {}, None, None, {}
    if not isinstance(data, dict):
        return {}, None, "the results file is not a proxy's JSON", {}
    at, run = data.get("at"), proxy_last_run(judge)
    if run.get("exit") not in (None, 0):
        return {}, at, f"the last proxy run failed (exit {run['exit']} at {run.get('at')}) — no cap applied from it", {}
    got = data.get("scope", SCOPE_CHANGE)
    if got != scope:
        return {}, at, (f"the results measure the {got}, not the {scope} — no cap applied from them; run "
                        f"`verify.py proxies --judge {judge}{' --all' if scope == SCOPE_PRODUCT else ''}`"), {}
    newest, name = newest_change(files)
    when = epoch(at)
    if when is None or newest >= when + 1:  # `at` is kept to the second
        return {}, at, (f"stale: measured at {at}, before {name} changed — no cap applied from them; run "
                        f"`verify.py proxies --judge {judge}` again"), {}
    caps, carried = split_metrics(data, judge)
    return caps, at, None, carried


def proxy_caps(judge: str, scope: str = SCOPE_CHANGE) -> tuple[dict, str | None]:
    """The caps from the judge's last proxy run, and when it ran; none when it has not run or is set aside."""
    caps, at, _, _ = proxy_state(judge, scope)
    return caps, at


def run_proxy(judge: str, product: bool = False) -> str:
    """Run the judge's proxy on the change, or with `product` on the whole product; it writes
    .cache/harness/proxies/<judge>.json, and its exit is kept beside it so a failed run's results are never used."""
    if not proxy_built(judge):
        return "not built yet (PROXIES in .agents/project.py)"
    PROXY_DIR.mkdir(parents=True, exist_ok=True)
    cmd = [str(a) for a in PROXIES[judge]] + ([PROXY_PRODUCT_FLAG] if product else [])
    code, out = sh(cmd, PROXY_DIR / f"{judge}.log")
    for j in (j for j, c in PROXIES.items() if tuple(c) == tuple(PROXIES[judge])):  # one script, several judges' JSON
        write_atomic(PROXY_DIR / f"{j}.run.json", json.dumps({"exit": code, "at": now(), "cmd": cmd}))
    return f"exit {code}" + ("" if code == 0 else f" — {'; '.join(tail(out, 3))}")


def scorecard(judge: str, raw: dict, reasons: dict, dims: dict, scope: str = SCOPE_CHANGE) -> dict:
    caps, at, why, carried = proxy_state(judge, scope)
    if why:
        print(f"proxy for {judge} set aside: {why}")
    caps = {d: c for d, c in caps.items() if d in dims}
    scores = apply_caps(raw, caps)
    return {"scores": scores, "raw": raw, "reasons": reasons, "caps": caps, "proxy_at": at, "proxy_scope": scope,
            "proxy_set_aside": why, "weights": weights_of(dims), "quality": weighted(scores, weights_of(dims)),
            "carried": {d: c for d, c in carried.items() if d in dims}}


def brief(reasons: list[str], most: int = 1) -> str:
    """The first metrics out of range, and how many more; the proxy's JSON holds them all."""
    more = len(reasons) - most
    return "; ".join(r[:140] for r in reasons[:most]) + (f"; +{more} more" if more > 0 else "")


def print_scorecard(judge: str, card: dict, dims: dict, gate: bool = True) -> None:
    for d, meta in dims.items():
        s = card["scores"].get(d)
        cap = f" — capped at {PROXY_CAP}: {brief(card['caps'][d])}" if card["caps"].get(d) else ""
        print(f"  {d:13} {'n/a' if s is None else f'{s}/{SCORE_MAX}'}  weight {meta['weight']:>4}  "
              f"{card['reasons'].get(d, '')[:70]}{cap}")
    for d, debt in (card.get("carried") or {}).items():
        print(f"  {d}: {len(debt)} metric(s) of carried debt, not capped — {brief(debt)}")
    q = card["quality"]
    print(f"quality: {q}/100 — the bar is {QUALITY_BAR}" + ("" if q is None or q >= QUALITY_BAR else " — BELOW"))
    if q is not None and q < QUALITY_BAR:
        low = sorted((d for d, s in card["scores"].items() if s is not None and s <= 2),
                     key=lambda d: -dims[d]["weight"])
        for d in low:
            print(f"  raise: {dims[d]['label']} ({card['scores'][d]}/{SCORE_MAX}, weight {dims[d]['weight']}) — "
                  "the judge says what would lift it")
        if gate:
            print(f"below the bar, finish waits — raise it, or the person accepts it: verify.py accept {judge} "
                  "\"<their words>\"")


def renormalise(weights: dict, dim: str, value: float) -> dict:
    """Set one dimension's weight and scale the others to keep the sum at 100, each held between WEIGHT_MIN and
    WEIGHT_MAX; rounded to a tenth, the rounding put on the largest of the others."""
    others = [d for d in weights if d != dim]
    value = min(max(value, WEIGHT_MIN, 100 - len(others) * WEIGHT_MAX), WEIGHT_MAX, 100 - len(others) * WEIGHT_MIN)
    out, free, remaining = {dim: value}, list(others), 100 - value
    while free:
        total = sum(weights[d] for d in free)
        share = {d: remaining * (weights[d] / total if total else 1 / len(free)) for d in free}
        pinned = {d: min(max(s, WEIGHT_MIN), WEIGHT_MAX) for d, s in share.items() if not WEIGHT_MIN <= s <= WEIGHT_MAX}
        if not pinned:
            out.update(share)
            break
        out.update(pinned)
        remaining -= sum(pinned.values())
        free = [d for d in free if d not in pinned]
    out = {d: round(out[d], 1) for d in weights}
    drift = round(100 - sum(out.values()), 1)
    if drift and others:
        top = max(others, key=lambda d: out[d])
        out[top] = round(out[top] + drift, 1)
    return {d: int(v) if float(v).is_integer() else v for d, v in out.items()}


def last_judge_score(rows: list[dict], judge: str, dim: str) -> int | None:
    """The judge's latest score on a dimension, from a review or an audit."""
    for r in reversed(rows):
        if r.get("kind") in ("review", "audit") and r.get("judge") == judge \
                and (r.get("scores") or {}).get(dim) is not None:
            return r["scores"][dim]
    return None


def is_miss(verdict: str, judge_score: int | None) -> bool:
    """The person found poor what the judge scored 3 or 4."""
    return verdict == "poor" and judge_score is not None and judge_score >= 3


def taste_misses(rows: list[dict], judge: str, dim: str) -> int:
    return sum(1 for r in rows if r.get("kind") == "taste" and r.get("judge") == judge and r.get("dimension") == dim
               and r.get("miss"))


def change_weight(data: dict, judge: str, dim: str, value: float, why: str, words: str) -> tuple[float, dict]:
    """Set a weight, renormalise the judge's others, and log the change with the person's words."""
    dims = data["judges"][judge]
    before = dims[dim]["weight"]
    new = renormalise(weights_of(dims), dim, value)
    for d, w in new.items():
        dims[d]["weight"] = w
    data["history"].append({"at": now(), "judge": judge, "dimension": dim, "from": before, "to": new[dim],
                            "why": why, "words": words, "weights": new})
    return before, new


def next_item(text: str, prefix: str) -> int:
    """The next free number for a rubric's `L<n>` or `T<n>` rows — never reused."""
    return max([int(n) for n in re.findall(rf"^\|\s*{prefix}(\d+)\s*\|", text, re.M)] or [0]) + 1


TASTE_HEAD = ("## Taste\n\nThe person's aesthetic feedback, one row per `verify.py taste`: what they said, the quality "
              "dimension and the anchor it added (.agents/HARNESS.md §12). The judge reads every row before it scores "
              "that dimension; a dimension missed twice is promoted to a learned item in the Learned table.\n\n"
              "| Item | Since | From the person | Dimension | Anchor |\n| --- | --- | --- | --- | --- |\n")


def table_cell(text: str) -> str:
    return " ".join(str(text).split()).replace("|", "\\|")


def add_section_row(text: str, heading: str, head: str, row: str) -> str:
    """Add a row to the table under `heading` — after its last row — or the section with its table at the end."""
    lines = text.rstrip("\n").split("\n")
    if heading not in lines:
        return text.rstrip("\n") + "\n\n" + head + row + "\n"
    start = lines.index(heading)
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    rows = [i for i in range(start, end) if lines[i].startswith("|")]
    if rows:
        lines.insert(rows[-1] + 1, row)
    else:
        table = head.split("\n\n")[-1].rstrip("\n").split("\n")
        lines[end:end] = [""] + table + [row] if lines[end - 1].strip() else table + [row]
    return "\n".join(lines) + "\n"


def link_from(src: Path, dest: Path) -> str:
    return os.path.relpath(dest, src.parent).replace(os.sep, "/")


def cmd_taste(args: argparse.Namespace) -> int:
    """The person's aesthetic view on one dimension: a new anchor of good or poor, a row in the judge's Taste table,
    a miss when the judge had scored it 3 or 4 — which raises that dimension's weight — and, on the second miss, the
    prompt to promote it to a learned floor item."""
    data = load_weights()
    dims = data["judges"].get(args.judge, {})
    if args.dimension not in dims:
        print(f"taste: {args.judge} has no dimension {args.dimension!r} — one of {', '.join(dims) or 'none'}",
              file=sys.stderr)
        return 2
    verdict = "good" if args.good else "poor"
    rows = score_rows()
    judge_score = last_judge_score(rows, args.judge, args.dimension)
    miss = is_miss(verdict, judge_score)
    date = datetime.now().date().isoformat()
    anchor_md = ANCHORS / args.judge / f"{args.dimension}.md"
    anchor = anchor_md
    if args.anchor:
        src = Path(args.anchor).expanduser()
        if not src.is_file():
            print(f"taste: no file at {src}", file=sys.stderr)
            return 2
        slug = re.sub(r"[^a-z0-9]+", "-", src.stem.lower()).strip("-") or "anchor"
        anchor = ANCHORS / "img" / f"{date}-{args.judge}-{args.dimension}-{slug}{src.suffix.lower()}"
        anchor.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, anchor)
        if anchor.stat().st_size > 300_000:
            print(f"note: {anchor.name} is {anchor.stat().st_size // 1000} kB — the anchors are committed; keep it "
                  "small (a crop, or fewer pixels)")
    rubric = ROOT / ".agents/rubrics" / f"{args.judge}.md"
    rubric_text = rubric.read_text() if rubric.is_file() else f"# Rubric — {args.judge}\n"
    item = f"T{next_item(rubric_text, 'T')}"
    said = f"{verdict}" + (f"; a miss — the judge had scored it {judge_score}" if miss else "")
    # The anchors file: the person's words as the newest example of good or poor.
    anchor_md.parent.mkdir(parents=True, exist_ok=True)
    md = anchor_md.read_text() if anchor_md.is_file() else f"# {args.judge} — {dims[args.dimension]['label']}\n"
    pic = f" — [{anchor.name}]({link_from(anchor_md, anchor)})" if anchor != anchor_md else ""
    entry = f"- **{date}, {verdict}** ({item}) — \"{' '.join(args.words.split())}\"{pic}"
    md = md.rstrip("\n") + ("\n" if "\n## From the person\n" in md else "\n\n## From the person\n\n") + entry + "\n"
    write_atomic(anchor_md, md)
    # The judge's Taste table, which it reads in every review.
    path = anchor.relative_to(ROOT).as_posix()
    row = (f"| {item} | {date} | \"{table_cell(args.words)}\" ({said}) | `{args.dimension}` | "
           f"[{path}]({link_from(rubric, anchor)}) |")
    rubric.parent.mkdir(parents=True, exist_ok=True)
    with locked(rubric):
        rubric_text = add_section_row(rubric.read_text() if rubric.is_file() else rubric_text, "## Taste", TASTE_HEAD,
                                      row)
        write_atomic(rubric, rubric_text)
    count = taste_misses(rows, args.judge, args.dimension) + miss
    prompt = miss and count >= 2 and not learned_for(rubric_text, args.dimension) \
        and not promoted_before(rows, args.judge, args.dimension)
    log_score({"kind": "taste", "judge": args.judge, "dimension": args.dimension, "verdict": verdict,
               "words": args.words, "anchor": path, "item": item, "judge_score": judge_score, "miss": miss,
               "promote_prompted": bool(prompt)})
    print(f"taste recorded: {args.judge} {args.dimension} {verdict} → {item} in {rubric.relative_to(ROOT)}, anchor "
          f"{path}")
    if miss:
        with locked(WEIGHTS):  # read again under the lock: another change to the weights since is kept
            data = load_weights()
            before, new = change_weight(data, args.judge, args.dimension,
                                        data["judges"][args.judge][args.dimension]["weight"] * (1 + MISS_RAISE),
                                        "taste miss", args.words)
            save_weights(data)
        print(f"a miss: the judge had scored {args.dimension} {judge_score}/{SCORE_MAX} — its weight {before} → "
              f"{new[args.dimension]}; now " + ", ".join(f"{d} {w}" for d, w in new.items()))
    elif verdict == "poor":
        print("not a miss — " + ("the judge has not scored this dimension yet" if judge_score is None
                                 else f"the judge had scored it {judge_score}"))
    if prompt:
        print_promote(rubric, rubric_text, args.judge, args.dimension, count)
    return 0


def print_promote(rubric: Path, text: str, judge: str, dim: str, count: int) -> None:
    learned = f"L{next_item(text, 'L')}"
    ids = ", ".join(taste_items(text, dim))
    print(f"PROMOTE: the person has flagged {dim} {count} times on a score of 3 or more — a lesson that keeps recurring "
          f"should block, not only lower the score. Write {learned} in the Learned table of {rubric.relative_to(ROOT)}"
          f" — From the person: \"promoted from taste rows {ids} on `{dim}`\"; Looks for: what in a diff predicts it —"
          f" show it to the person, and record their yes: verify.py decision \"promote taste on {judge} {dim} to "
          f"{learned}: <their words>\". This prompt prints once for {dim}; once {learned} names those rows, never.")


def table_rows(text: str, heading: str) -> list[list[str]]:
    """The cells of each body row of the table under `heading`."""
    lines = text.split("\n")
    if heading not in lines:
        return []
    start = lines.index(heading)
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    rows = [ln for ln in lines[start:end] if ln.startswith("|") and not re.match(r"^\|\s*(?:Item\b|-{3})", ln)]
    return [[c.strip() for c in re.split(r"(?<!\\)\|", ln)[1:-1]] for ln in rows]


def taste_items(text: str, dim: str) -> list[str]:
    """The Taste table's `T<n>` rows on a dimension."""
    return [r[0] for r in table_rows(text, "## Taste") if len(r) > 3 and r[3].strip("` ") == dim]


def learned_for(text: str, dim: str) -> str | None:
    """The Learned item a dimension's taste was promoted to: a Taste row on it that says `promoted to L<n>`, or a
    Learned row that names the dimension in backticks or one of its Taste rows."""
    tastes = [r for r in table_rows(text, "## Taste") if len(r) > 3 and r[3].strip("` ") == dim]
    for r in tastes:
        if m := re.search(r"promoted to (L\d+)", r[2]):
            return m.group(1)
    ids = {r[0] for r in tastes}
    for r in table_rows(text, "## Learned"):
        named = set(re.findall(r"\bT\d+\b", " ".join(r[1:])))
        if f"`{dim}`" in " ".join(r[1:]) or named & ids:
            return r[0]
    return None


def promoted_before(rows: list[dict], judge: str, dim: str) -> bool:
    """The promotion prompt has printed once for this dimension already."""
    return any(r.get("kind") == "taste" and r.get("judge") == judge and r.get("dimension") == dim
               and r.get("promote_prompted") for r in rows)


def cmd_rate(args: argparse.Namespace) -> int:
    """The person's own 0–4 score of a file on one dimension; calibration compares it with the judge's."""
    dims = load_weights()["judges"].get(args.judge, {})
    if args.dimension not in dims:
        print(f"rate: {args.judge} has no dimension {args.dimension!r} — one of {', '.join(dims) or 'none'}",
              file=sys.stderr)
        return 2
    path = Path(args.file).expanduser()
    digest = file_hash(path)
    if digest is None:
        print(f"rate: no file at {path}", file=sys.stderr)
        return 2
    try:
        name = path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        name = path.name
    judge_score = last_judge_score(score_rows(), args.judge, args.dimension)
    log_score({"kind": "person", "judge": args.judge, "dimension": args.dimension, "score": args.score,
               "file": name, "sha": digest, "note": args.note, "judge_score": judge_score})
    print(f"rating recorded: the person scores {name} {args.score}/{SCORE_MAX} on {args.dimension}"
          + ("" if judge_score is None else f"; the judge's last score {judge_score} (gap {judge_score - args.score:+d})"))
    return 0


def cmd_weight(args: argparse.Namespace) -> int:
    """The person sets a dimension's weight; the others are scaled to keep 100."""
    data = load_weights()
    dims = data["judges"].get(args.judge, {})
    if args.dimension not in dims:
        print(f"weight: {args.judge} has no dimension {args.dimension!r} — one of {', '.join(dims) or 'none'}",
              file=sys.stderr)
        return 2
    if not WEIGHT_MIN <= args.set <= WEIGHT_MAX:
        print(f"weight: a weight is {WEIGHT_MIN}–{WEIGHT_MAX}", file=sys.stderr)
        return 2
    with locked(WEIGHTS):  # read again under the lock: a change to the weights since is kept
        data = load_weights()
        before, new = change_weight(data, args.judge, args.dimension, args.set, "set by the person",
                                    args.words or "set by the person")
        save_weights(data)
    print(f"weight set: {args.judge} {args.dimension} {before} → {new[args.dimension]}; now "
          + ", ".join(f"{d} {w}" for d, w in new.items()))
    return 0


def cmd_accept(args: argparse.Namespace) -> int:
    """The person accepts a judge's quality score below the bar, by name; it holds for that review only."""
    with task_update() as task:
        r = task["reviews"].get(args.judge)
        if r and r.get("quality") is not None:
            task.setdefault("acceptances", []).append({"judge": args.judge, "words": args.words, "at": now(),
                                                       "quality": r["quality"], "review_at": r["at"]})
    if not r or r.get("quality") is None:
        print(f"accept: no scored review from {args.judge} this task — verify.py review {args.judge} … --score",
              file=sys.stderr)
        return 1
    print(f"accepted by the person: {args.judge} at {r['quality']}/100 (bar {QUALITY_BAR}) — {args.words}")
    return 0


def accepted(task: dict, judge: str, review: dict) -> dict | None:
    """The person's acceptance that covers this review: one given on it, or on an earlier review of the same judge
    whose score was no higher — a later review at the same score or above keeps it; a lower one needs a new one."""
    q = review.get("quality")
    for a in reversed(task.get("acceptances", [])):
        if a["judge"] != judge:
            continue
        if a["review_at"] == review["at"]:
            return a
        if q is not None and a.get("quality") is not None and q >= a["quality"] and a["review_at"] <= review["at"]:
            return a
    return None


def review_line(judge: str, r: dict, standing: str | None = "exact") -> str:
    """A review's line in the Verified block: its verdict, and its quality score — or that it was out of scope; its
    nits, its carried debt, and whether it stands only because the edits since were comments or whitespace."""
    tail_ = (f" — {len(r['nits'])} nit(s)" if r.get("nits") else "") \
        + (f" — {sum(map(len, r['carried'].values()))} metric(s) of carried debt, not capped" if r.get("carried")
           else "") \
        + (" — stands: only comments or whitespace changed in its files since" if standing == "normalised" else "")
    if r.get("out_of_scope"):
        return (f"- Review: {judge} {r['verdict']} — {OUT_OF_SCOPE} — not held to the bar ({r.get('scope', '')})"
                + (f" — {r['note']}" if r.get("note") else "") + tail_)
    quality = f" — quality {r['quality']}/100 (bar {QUALITY_BAR})" if r.get("quality") is not None else ""
    note = r.get("note") if r.get("quality") is None else None  # a scored note is the reasons, in the card
    return f"- Review: {judge} {r['verdict']}{quality}" + (f" — {note}" if note else "") + tail_


def proxy_data(judge: str) -> dict:
    try:
        data = json.loads((PROXY_DIR / f"{judge}.json").read_text())
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def out_of_scope_check(judge: str) -> tuple[bool, str]:
    """Whether the change touches none of the judge's measured scope — the scope its proxy measures in change mode:
    for the ui-designer and ux-designer the screens whose sources changed, for the doc-reviewer the doc lines, for the
    code-reviewer the changed functions, for the ux-content-writer the changed strings. Only a proxy that ran on this
    tree, passed, and names what it measured (`in_scope`) can show the scope empty."""
    if not proxy_built(judge):
        return False, f"{judge} has no built proxy to show its scope empty (PROXIES in .agents/project.py) — score it"
    _, at, why, _ = proxy_state(judge, SCOPE_CHANGE)
    if why or at is None:
        return False, f"its scope cannot be shown empty: {why or 'the proxy wrote no results'}"
    data = proxy_data(judge)
    if not isinstance(data.get("in_scope"), list):
        return False, "its proxy does not say what it measured (no in_scope) — score it"
    what = data.get("scope_what") or "its measured scope"
    found = data["in_scope"]
    if found:
        more = f", +{len(found) - 3} more" if len(found) > 3 else ""
        return False, (f"scope: {what} — {len(found)} in scope: {', '.join(map(str, found[:3]))}{more}; the change "
                       f"reaches {judge}'s scope, so it is scored and held to the bar")
    return True, f"scope: {what} — empty"


def quality_problems(task: dict, judge: str) -> list[str]:
    """A judge with quality dimensions: a score recorded with its pass, at or above the bar, or accepted."""
    if judge not in load_weights()["judges"]:
        return []
    r = task["reviews"].get(judge)
    if not r or r["verdict"] != "pass":
        return []
    if r.get("out_of_scope"):  # verify.py checked the claim; it holds for the tree it checked
        if r.get("scope_fingerprint") != tree_fingerprint():
            return [f"the tree changed since {judge}'s out-of-scope check — review it again, with a score if the "
                    "change now reaches its scope"]
        return []
    if r.get("quality") is None:
        return [f"no quality score from {judge} — record its Score block: verify.py review {judge} pass --score "
                "dim=n,... --note \"dim: why; …\" (or --scores-file)"]
    if r["quality"] < QUALITY_BAR and not accepted(task, judge, r):
        low = ", ".join(d for d, s in r["scores"].items() if s is not None and s <= 2) or "none at 2 or under"
        return [f"{judge}'s quality score {r['quality']} is below the bar {QUALITY_BAR} (low: {low}) — raise it, or "
                f"the person accepts it: verify.py accept {judge} \"<their words>\""]
    return []


def print_proxy(judge: str, scope: str) -> None:
    """What the judge's last proxy results cap, or why they are set aside."""
    caps, at, why, carried = proxy_state(judge, scope)
    if why:
        print(f"  set aside — {why}")
        return
    if at is None:
        print("  no results — every dimension scored on the judge's reading alone")
        return
    print(f"  results for the {scope} at {at}")
    for d, reasons in caps.items():
        print(f"  {d}: capped at {PROXY_CAP} — {brief(reasons, 3)}")
    for d, debt in carried.items():
        print(f"  {d}: {len(debt)} metric(s) of carried debt, out of range at the base too — not capped: "
              f"{brief(debt, 2)}")
    if not caps:
        print("  nothing capped — " + ("what is out of range was so at the base" if carried
                                       else "every metric in range"))


def cmd_proxies(args: argparse.Namespace) -> int:
    """Run the measured proxies — for one judge, or every judge with dimensions — on the change, or with --all on the
    whole product, and print what each caps."""
    judges = [args.judge] if args.judge else list(load_weights()["judges"])
    scope = SCOPE_PRODUCT if args.all else SCOPE_CHANGE
    for j in judges:
        print(f"{j} ({scope}): {run_proxy(j, product=args.all)}")
        print_proxy(j, scope)
    return 0


def cmd_audit(args: argparse.Namespace) -> int:
    """The whole product scored by one judge — every screen, component or doc, not only a change — its proxy run on
    the whole product, the score kept in scores.jsonl so the trend shows and old debt surfaces."""
    dims = load_weights()["judges"].get(args.judge, {})
    if not dims:
        print(f"audit: {args.judge} has no quality dimensions", file=sys.stderr)
        return 2
    if args.scores_file:
        try:  # refused before the proxy's run, which can take a while
            raw, reasons = read_scores(None, args.scores_file, args.note, dims)
        except ValueError as e:
            print(f"audit: {e}", file=sys.stderr)
            return 2
    if not args.no_proxy:
        print(f"proxy ({SCOPE_PRODUCT}): {run_proxy(args.judge, product=True)}")
    print_proxy(args.judge, SCOPE_PRODUCT)
    if not args.scores_file:
        print(f"no scores recorded — the judge audits the whole product against its anchors, then: verify.py audit "
              f"{args.judge} --scores-file <file>")
        return 0
    card = scorecard(args.judge, raw, reasons, dims, SCOPE_PRODUCT)
    log_score({"kind": "audit", "judge": args.judge, "note": args.note, **card})
    print_scorecard(args.judge, card, dims, gate=False)
    trend = [r["quality"] for r in score_rows() if r.get("kind") == "audit" and r.get("judge") == args.judge]
    print(f"audits of {args.judge}: " + " → ".join(str(q) for q in trend[-8:]))
    return 0


def approval_state(a: dict) -> str:
    current = file_hash(Path(a["file"]))
    return "" if current == a["sha"] else " — the file changed since the yes" if current else " — the file is gone"


def gate_problems(task: dict, files: list[str]) -> list[str]:
    """What the approval gates still need: a yes of each kind, on a file unchanged since, a draft's given before the
    first run that built the change — or the person's recorded word that waives it."""
    problems = []
    words = [d["text"].lower() for d in task.get("decisions", [])]
    no_visible = any(w.startswith(NO_VISIBLE_CHANGE) for w in words)
    design_given = any(w.startswith(DESIGN_GIVEN) for w in words)
    touched = False
    for what, paths, kinds in project.GATES:
        if not paths or not any(project.matches(f, paths) for f in files):
            continue
        if no_visible and "kit" not in kinds:  # nothing visible waives a look, never the person's yes on the kit
            continue
        touched = True
        first = first_build(task, paths)
        for kind in kinds:
            if kind in KINDS_BEFORE and design_given:
                continue
            yes = [a for a in task.get("approvals", []) if a["kind"] == kind]
            if not yes and kind == "kit":
                problems.append(f"{what} changed with no yes from the person on the change — write its whole diff, "
                                "new files included (verify.py kitdiff <scratch>/kit.diff), show them, and record "
                                "their yes: verify.py approve <that file> --kind kit; a request or a tool's own "
                                "approval of an edit is not their yes (AGENTS.md rule 9)")
                continue
            if not yes:
                problems.append(f"{what} changed with no yes from the person on its {KIND_NAMES[kind]} — verify.py approve "
                                f"<file> --kind {kind}, or their word: verify.py decision \"{NO_VISIBLE_CHANGE}: "
                                f"<why>\" (or \"{DESIGN_GIVEN}: <where>\" for a design they handed over)")
                continue
            a = yes[-1]
            name = Path(a["file"]).name
            if approval_state(a):
                problems.append(f"the approved {kind} {name}{approval_state(a)} — show the person the new file")
            elif kind in KINDS_AFTER and a.get("code") != gated_fingerprint(files, kind):
                problems.append(f"{what} changed after the person's yes on {name} — show them the "
                                f"{'diff' if kind == 'kit' else 'built thing'} again")
            elif kind in KINDS_BEFORE and first and a["at"] > first:
                problems.append(f"the yes on the {kind} {name} came after the first run that built it — the draft is "
                                "approved before the build (.agents/HARNESS.md §9)")
    target = task.get("target")
    if touched and target:
        if target["deployed"] != deployed_fingerprint():
            problems.append("the code changed since it ran on the target — run it there again and record it with "
                            "verify.py target")
        elif not any(s["deployed"] == target["deployed"] for s in task.get("signoffs", [])):
            problems.append("no sign-off from the person on the target for the code as it ran — show them, then "
                            "verify.py signoff \"<what they judged>\" in their words")
    return problems


def cmd_status(_: argparse.Namespace) -> int:
    task = load()
    if not task:
        print("no task — verify.py start \"<task>\"")
        return 0
    last = task["runs"][-1] if task["runs"] else None
    print(f"task: {task['task']} (since {task['started']}, base {task['commit']})")
    print(f"failures in a row: {task['failures']} of {MAX_FAILURES}")
    if last:
        stale = " — the tree changed since" if last["fingerprint"] != tree_fingerprint() else ""
        print(f"last run: {last['n']} {'PASS' if last['ok'] else 'FAIL'} at {last['at']}{stale}")
    files = changed_files()
    for judge, r in task["reviews"].items():
        standing = review_stands(judge, r, files)
        stale = {"exact": "", "normalised": " — stands: only comments or whitespace changed in its files since"} \
            .get(standing, f" — its files changed since (verify.py delta {judge})")
        quality = f", quality {r['quality']}/100 (bar {QUALITY_BAR})" if r.get("quality") is not None else \
            f", {OUT_OF_SCOPE} — not held to the bar" if r.get("out_of_scope") else ""
        print(f"review: {judge} {r['verdict']}{quality}" + (f" — {r['note']}" if r.get("note") else "") + stale)
        for n in r.get("nits") or []:
            print(f"  nit: {nit_name(n)}")
        for h in r.get("history") or []:
            print(f"  carried forward: {carry_line(h)}")
    for a in task.get("acceptances", []):
        print(f"accepted below the bar by the person: {a['judge']} at {a['quality']}/100 — {a['words']}")
    for a in task.get("approvals", []):
        print(f"approved by the person: {a['kind']} {Path(a['file']).name} at {a['at']}{approval_state(a)}")
    for d in task.get("decisions", []):
        print(f"decision (the person's, settled — a judge does not block on it): {d['text']}")
    if task.get("target"):
        t = task["target"]
        print(f"target: {t['build']} on {t['where']} at {t['at']}"
              + (f", health check exit {t['health_exit']}" if t.get("health_exit") is not None else ""))
    for s in task.get("signoffs", []):
        print(f"signed off on the target by the person at {s['at']}: {s['text']}{signoff_state(s)}")
    for d in task.get("declines", []):
        print(f"the person said no: {d['draft']} {d['file']} — \"{d['text']}\" → {d['route']}")
    for f in task["findings"]:
        print(f"finding ({f['kind']}, {f.get('source', 'person')}): {f['text']} → {f['route']}")
    print(f"debug marker in the tree: {'yes' if debug_hits() else 'no'}")
    return 0


def cmd_finish(_: argparse.Namespace) -> int:
    """The hand-over gate (.agents/HARNESS.md §5): everything the change needs, then the Verified block's draft."""
    task = load()
    if not task.get("runs"):
        print("finish: no run yet — verify.py run")
        return 1
    files = changed_files()
    last = task["runs"][-1]
    open_items = []
    if not last["ok"]:
        open_items.append(f"the last run ({last['n']}) failed")
    if last["fingerprint"] != tree_fingerprint():
        open_items.append("the tree changed after the last run — run again")
    if last.get("partial"):  # a run with --only, whoever made it, never stands for the change's checks
        open_items.append(f"the last run ({last['n']}) checked only {', '.join(last['checks']) or 'nothing'} — run "
                          "every check the change needs: verify.py run")
    if debug_hits():
        open_items.append(f"a debug marker is in the tree — /{project.DEBUG_MARKERS}/ (.agents/project.py)")
    open_items += broken_invariants()
    open_items += gate_problems(task, files)
    open_items += lesson_problems(task, files)
    covered = frozenset(f["for_run"] for f in task.get("findings", []) if f.get("for_run"))
    open_items += unrecorded_redeploys(task.get("target_log", []), covered)
    for judge, wants in JUDGES.items():
        if judge_ready(judge) and any(wants(f) for f in files):
            r = task["reviews"].get(judge)
            if not r:
                open_items.append(f"no review recorded from {judge}")
            elif r["verdict"] != "pass":
                open_items.append(f"{judge} said blocking — in force until it records a new pass")
            elif not review_stands(judge, r, files):
                open_items.append(f"{judge} reviewed an older version of its files — give it only what changed: "
                                  f"verify.py delta {judge}" + (f", or verify.py nits-fixed {judge} if the edits "
                                                                "fixed its nits" if r.get("nits") else ""))
    # The quality layer: every judge the files call for, and any judge asked this task, at or above the bar.
    for judge in JUDGES:
        if (judge_ready(judge) and any(JUDGES[judge](f) for f in files)) or judge in task["reviews"]:
            open_items += quality_problems(task, judge)
    checks = last["checks"]
    target = task.get("target")
    print("## Verified")
    print(f"- Base: {task['commit']} + working tree, {len(files)} changed file(s)")
    for name, r in checks.items():
        print(f"- {name.capitalize()}: {'PASS' if r['ok'] else 'FAIL'} — {r['detail']}")
    if not checks:
        print("- Checks: none ran — no file a check covers changed")
    for judge, r in task["reviews"].items():
        print(review_line(judge, r, review_stands(judge, r, files)))
        for h in r.get("history") or []:
            print(f"- Carried forward: {judge} — {carry_line(h)}")
    for a in task.get("acceptances", []):
        print(f"- Accepted below the bar by the person: {a['judge']} at {a['quality']}/100 — {a['words']}")
    for a in task.get("approvals", []):
        print(f"- Approved by the person: {a['kind']} {Path(a['file']).name}{approval_state(a)}")
    for d in task.get("decisions", []):
        print(f"- Decided by the person: {d['text']}")
    if target:
        print(f"- Target: {target['build']} on {target['where']}, {target['at']}"
              + (f"; health check exit {target['health_exit']}" if target.get("health_exit") is not None else "")
              + " — <what was read: screenshots, logs, errors>")
    else:
        print(f"- Target ({project.TARGET}): not run — <why: nothing it shows changed, not asked, not available>")
    for s in task.get("signoffs", []):
        print(f"- Signed off on the target by the person: {s['text']}{signoff_state(s)}")
    print("- Screens: <view> → [<screenshot>](<path>), checked: <what> (or \"no screen changed\")")
    print("- Not done: <step and why>")
    print("- Left running: <dev server, simulator, deploy — or nothing>")
    print("## Judge on the target")
    print("- <what only the person can judge: the look, the feel, motion and timing, the words>")
    for d in task.get("declines", []):
        print(f"- The person said no: {d['draft']} {d['file']} — \"{d['text']}\"")
    routed = [f for f in task["findings"] + task.get("declines", []) if f["route"] != "none"]
    if routed:
        print("## Lessons routed (verify-change → Recording what was learned)")
        for f in routed:
            print(f"- {f['text']} → {f['route']}" + (f" ({f['judge']})" if f.get("judge") else "")
                  + (f" [{f['about']}]" if f.get("about") else ""))
    if open_items:
        print("## Open — not ready to hand over")
        for item in open_items:
            print(f"- {item}")
        return 1
    return 0


def cmd_unverified(args: argparse.Namespace) -> int:
    """Whether the tree changed since the last `run`. As a Stop hook (--hook): the first time an agent stops on a tree
    no run has seen, it is asked once to run the checks or say why not; then it may stop."""
    task, files = load(), changed_files()
    last = task["runs"][-1] if task.get("runs") else None
    fp = tree_fingerprint()
    unverified = bool(files) and (last is None or last["fingerprint"] != fp)
    if not args.hook:
        print("unverified: the tree changed since the last run — verify.py run" if unverified
              else "verified: the last run saw this tree" if files else "clean: nothing changed")
        return 1 if unverified else 0
    try:
        event = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        event = {}
    nudged = STATE / "nudged"
    if not unverified or event.get("stop_hook_active") or (nudged.is_file() and nudged.read_text() == fp):
        return 0
    STATE.mkdir(parents=True, exist_ok=True)
    nudged.write_text(fp)
    reason = (f"Harness: {len(files)} changed file(s) that no `verify.py run` has seen. Run "
              "`python3 .agents/skills/verify-change/scripts/verify.py run` before handing over, or tell the person "
              "why not (a draft, a question to them, work in progress). This reminder comes once per tree.")
    print(json.dumps({"decision": "block", "reason": reason}))
    return 0


def cmd_calibration(_: argparse.Namespace) -> int:
    """How often each judge caught what the person found, missed it, or raised a false alarm — every judge, so one
    that has never been tested shows as 0 / 0 / 0 rather than as missing."""
    try:
        rows = [json.loads(line) for line in JUDGEMENTS.read_text().splitlines() if line.strip()]
    except OSError:
        rows = []
    print(f"{len(rows)} judgement(s) in {JUDGEMENTS.relative_to(ROOT)}"
          + ("" if rows else " — verify.py finding / dispute add them"))
    print(f"  {'judge':26} {'caught':>6} {'missed':>6} {'false alarms':>12}")
    # Every judge in the kit, every agent with a rubric, and any the log names — one no longer here keeps its record.
    for j in sorted(set(rubric_owners()) | {r["judge"] for r in rows if r.get("judge")}):
        mine = [r for r in rows if r.get("judge") == j]
        caught = sum(1 for r in mine if r["kind"] == "finding" and r["caught"])
        missed = sum(1 for r in mine if r["kind"] == "finding" and r["caught"] is False)
        alarms = sum(1 for r in mine if r["kind"] == "false-alarm")
        print(f"  {j:26} {caught:>6} {missed:>6} {alarms:>12}")
    by_person = [r for r in rows if r["kind"] == "finding" and r.get("source", "person") == "person"]
    print(f"  only the person could see: {sum(1 for r in by_person if not r.get('judge'))}")
    print(f"  lessons the agent recorded: {sum(1 for r in rows if r['kind'] == 'finding' and r.get('source') == 'agent')}")
    routes: dict[str, int] = {}
    for r in rows:
        if r["kind"] != "approval":
            routes[r["route"]] = routes.get(r["route"], 0) + 1
    print("  by route: " + (", ".join(f"{k} {v}" for k, v in sorted(routes.items())) or "none yet"))
    print("  the person's word on drafts:")
    stats = draft_stats(rows)
    if not stats:
        print("    none yet — verify.py approve and decline add them")
    for kind, s in stats.items():
        print(f"    {KIND_NAMES.get(kind, kind):14} {s['yes']} yes, {s['no']} no — {s['first']} of {s['drafts']} "
              "approved without a no first")
    areas, untagged = area_counts(rows)
    print("  lessons by area: " + (", ".join(f"{a} {n}" for a, n in areas.items()) or "none tagged yet")
          + (f"; {untagged} untagged" if untagged else ""))
    for area, n in areas.items():
        if n >= REPEAT_AT:
            print(f"  repeats: {area} has {n} lessons — turn what they share into a check, a principle in the design "
                  "brief (with the person's yes on a specimen) or a skill's Never (AGENT_HARNESS §9.2)")
    quality_calibration()
    return 0


def draft_stats(rows: list[dict]) -> dict:
    """Per kind of draft: the person's yeses and noes, and how many tasks' drafts of that kind got a yes with no
    no before it."""
    out: dict[str, dict] = {}
    by_task: dict[tuple, list] = {}
    for r in rows:
        if r.get("kind") in ("approval", "decline") and r.get("draft"):
            s = out.setdefault(r["draft"], {"yes": 0, "no": 0, "first": 0, "drafts": 0})
            s["yes" if r["kind"] == "approval" else "no"] += 1
            by_task.setdefault((r.get("task"), r["draft"]), []).append(r["kind"])
    for (_, kind), events in by_task.items():
        if "approval" in events:
            out[kind]["drafts"] += 1
            out[kind]["first"] += events.index("approval") == 0
    return out


def area_counts(rows: list[dict]) -> tuple[dict, int]:
    """Lessons — findings, false alarms, noes — per area, most first, and how many carry no area."""
    counts: dict[str, int] = {}
    untagged = 0
    for r in rows:
        if r.get("kind") == "approval":
            continue
        if r.get("about"):
            counts[r["about"]] = counts.get(r["about"], 0) + 1
        else:
            untagged += 1
    return dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))), untagged


def calibration_rows(rows: list[dict], judge: str, dim: str) -> dict:
    """One dimension's record: the judge's last score, the person's ratings and the mean gap (judge minus person,
    each rating paired with the judge's last score before it), and the taste misses."""
    rated = [r for r in rows if r.get("kind") == "person" and r.get("judge") == judge and r.get("dimension") == dim]
    gaps = [r["judge_score"] - r["score"] for r in rated if r.get("judge_score") is not None]
    tastes = [r for r in rows if r.get("kind") == "taste" and r.get("judge") == judge and r.get("dimension") == dim]
    return {"last": last_judge_score(rows, judge, dim), "ratings": len(rated),
            "gap": round(sum(gaps) / len(gaps), 2) if gaps else None,
            "misses": sum(1 for r in tastes if r.get("miss")), "tastes": len(tastes)}


def quality_calibration() -> None:
    """Per judge and dimension: the weight, the judge's last score, how far it sits from the person's, the misses on
    taste; then every weight change with the person's words."""
    data, rows = load_weights(), score_rows()
    print(f"quality: {sum(1 for r in rows if r.get('kind') in ('review', 'audit'))} score(s), "
          f"{sum(1 for r in rows if r.get('kind') == 'person')} rating(s) and "
          f"{sum(1 for r in rows if r.get('kind') == 'taste')} taste record(s) in {SCORES.relative_to(ROOT)}; "
          f"the bar is {QUALITY_BAR}")
    for judge, dims in data["judges"].items():
        print(f"  {judge}")
        print(f"    {'dimension':13} {'weight':>6} {'last':>4} {'rated':>5} {'gap':>5} {'taste misses':>12}")
        for d, meta in dims.items():
            c = calibration_rows(rows, judge, d)
            gap = "—" if c["gap"] is None else f"{c['gap']:+}"
            last = "—" if c["last"] is None else c["last"]
            print(f"    {d:13} {meta['weight']:>6} {last:>4} {c['ratings']:>5} {gap:>5} "
                  f"{c['misses']:>5} of {c['tastes']:<4}")
    history = data["history"]
    print(f"  weight changes: {len(history)}" + ("" if history else " — taste misses and the person's settings add them"))
    for h in history:
        print(f"    {h['at'][:10]} {h['judge']} {h['dimension']} {h['from']} → {h['to']} ({h['why']}): "
              f"\"{h['words'][:70]}\"")


def check_sandboxes(check) -> None:
    """Claude Code denies reading the guard's secret paths and the project's secret files, and Codex's sandbox allows
    exactly the project's hosts."""
    spec = importlib.util.spec_from_file_location("guard", ROOT / ".agents/hooks/guard.py")
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    try:
        claude = json.loads((ROOT / ".claude/settings.json").read_text())
    except (OSError, ValueError):
        claude = {}
    denies = " ".join(claude.get("permissions", {}).get("deny", []))
    missing = [s for s in list(guard.SECRET_PATHS) + list(project.SECRET_FILES) if s not in denies]
    check(not missing, "Claude Code denies reading the guard's secret paths and the project's secret files",
          f"Claude Code's Read denies miss {missing} — add Read(<path>/**) or Read(**/<name>) to .claude/settings.json")
    try:
        import tomllib  # Python 3.11+
        codex = tomllib.loads((ROOT / ".codex/config.toml").read_text())
    except ImportError:
        check(True, "Codex's sandbox not compared — reading TOML needs Python 3.11", "")
        return
    except (OSError, ValueError):
        codex = {}
    proxy = codex.get("features", {}).get("network_proxy", {})
    allowed = {d[3:] if d.startswith("**.") else d for d, v in proxy.get("domains", {}).items() if v == "allow"}
    check(codex.get("sandbox_mode") == "workspace-write" and proxy.get("enabled") is True
          and allowed == set(project.ALLOWED_HOSTS),
          "Codex's sandbox is workspace-write and its proxy allows the project's hosts",
          f"Codex's sandbox or proxy domains differ from ALLOWED_HOSTS {sorted(project.ALLOWED_HOSTS)} "
          "(.codex/config.toml against .agents/project.py)")


def weights_problems(data: dict) -> list[str]:
    """Each judge's weights sum to 100, each within bounds, and each dimension has its anchors file."""
    problems = []
    for judge, dims in data["judges"].items():
        total = sum(v["weight"] for v in dims.values())
        if abs(total - 100) > 0.05:
            problems.append(f"{judge}'s weights sum to {total}, not 100 ({WEIGHTS.relative_to(ROOT)})")
        for d, v in dims.items():
            if not WEIGHT_MIN <= v["weight"] <= WEIGHT_MAX:
                problems.append(f"{judge} {d}: weight {v['weight']} outside {WEIGHT_MIN}–{WEIGHT_MAX}")
            if not (ANCHORS / judge / f"{d}.md").is_file():
                problems.append(f"{judge} {d}: no anchors at {(ANCHORS / judge / f'{d}.md').relative_to(ROOT)}")
    return problems


def cmd_doctor(_: argparse.Namespace) -> int:
    problems = 0

    def check(ok: bool, good: str, bad: str) -> None:
        nonlocal problems
        problems += not ok
        print(f"  {'ok ' if ok else 'BAD'} {good if ok else bad}")

    def note(text: str) -> None:
        print(f"  --  {text}")

    hooks = git("config", "--get", "core.hooksPath").strip()
    check(hooks == ".agents/githooks", "git runs .agents/githooks",
          "git hooks not wired — the person runs: git config core.hooksPath .agents/githooks")
    check(os.access(ROOT / ".agents/githooks/pre-commit", os.X_OK), "pre-commit is executable",
          "pre-commit is not executable — chmod +x .agents/githooks/pre-commit")
    for adapter in (".claude/settings.json", ".codex/hooks.json"):
        p = ROOT / adapter
        text = p.read_text() if p.is_file() else ""
        for hook in ("guard.py", "untrusted.py"):
            check(hook in text, f"{adapter} runs {hook}", f"{adapter} does not run .agents/hooks/{hook}")
        check("unverified --hook" in text, f"{adapter} runs verify.py unverified --hook when the agent stops",
              f"{adapter} has no Stop hook running verify.py unverified --hook")
    for link in ("skills", "agents"):
        p = ROOT / ".claude" / link
        check(p.is_symlink() and p.resolve() == (ROOT / ".agents" / link).resolve(),
              f".claude/{link} links to .agents/{link}",
              f".claude/{link} is not a link to ../.agents/{link} — on Windows, set git's core.symlinks=true and "
              "check out again")
    missing = [p.stem for p in (ROOT / ".agents/agents").glob("*.md")
               if not (ROOT / ".codex/agents" / f"{p.stem}.toml").is_file()]
    check(not missing, "every agent has its Codex definition in .codex/agents/",
          f"no .codex/agents/<name>.toml for {missing}")
    for j in (j for j in JUDGES if not judge_ready(j)):
        note(f"judge {j} has no agent file yet — it joins the plan once .agents/agents/{j}.md exists")
    for script in HARNESS_TESTS:
        code = subprocess.run([sys.executable, script, "--test"], cwd=ROOT, capture_output=True).returncode
        check(code == 0, f"{script} self-test passes", f"{script} self-test fails — python3 {script} --test")
    check_sandboxes(check)
    ignored = subprocess.run(["git", "check-ignore", "-q", ".cache/harness/task.json"], cwd=ROOT).returncode == 0
    check(ignored, ".cache/harness/ is git-ignored", ".cache/harness/ is not git-ignored — add .cache/ to .gitignore")
    for name, spec in project.CHECKS.items():
        prog = spec["run"][0]
        check(shutil.which(prog) is not None or (ROOT / prog).is_file(), f"check {name}: {prog} is installed",
              f"check {name}: {prog} is not on PATH")
    if project.PROJECT_NAME.startswith("<") or project.TARGET.startswith("<"):
        note("PROJECT_NAME or TARGET in .agents/project.py is still a placeholder — run the bootstrap prompt "
             "(docs/AGENT_HARNESS.md §17)")
    if not project.CHECKS:
        note("no project checks yet — add the build, tests and lint to CHECKS in .agents/project.py")
    check((ROOT / project.DESIGN_FILE).is_file(), f"{project.DESIGN_FILE} is the design brief",
          f"no {project.DESIGN_FILE} — the ui-designer and design-system skills read it first; start from the "
          "template's demo")
    for problem in weights_problems(load_weights()):
        check(False, "", problem)
    if not weights_problems(load_weights()):
        check(True, f"{WEIGHTS.relative_to(ROOT)}: each judge's weights sum to 100, each {WEIGHT_MIN}–{WEIGHT_MAX}, "
              "every dimension with its anchors", "")
    for j in load_weights()["judges"]:
        if not proxy_built(j):
            note(f"proxy for {j} not built yet — PROXIES in .agents/project.py; its dimensions are scored on reading "
                 "alone")
    if not project.UI_PATHS:
        note("no UI_PATHS yet — the screen gate is off until they are filled in")
    if not project.TOKEN_FILES:
        note(f"no TOKEN_FILES yet — {project.DESIGN_FILE}'s tokens are not checked against code")
    print("doctor: OK" if not problems else f"doctor: {problems} problem(s)")
    return 1 if problems else 0


def self_test() -> int:
    """The gate's own cases: which run first built a gated change (first_build)."""
    def run(at, gated, files=("DESIGN.md",)):
        return {"at": at, "files": list(files), "gated": gated}
    cases = [
        ("a change left by an earlier task, edited after the yes",
         {"gated_at_start": {"DESIGN.md": "a"}, "runs": [run("1", {"DESIGN.md": "a"}), run("3", {"DESIGN.md": "b"})]},
         "3"),
        ("a clean start, built at run 1", {"gated_at_start": {}, "runs": [run("1", {"DESIGN.md": "b"})]}, "1"),
        ("never changed in this task", {"gated_at_start": {"DESIGN.md": "a"}, "runs": [run("1", {"DESIGN.md": "a"})]},
         None),
        ("reverted to HEAD is a change", {"gated_at_start": {"DESIGN.md": "a"}, "runs": [run("1", {})]}, "1"),
        ("a task recorded before gated_at_start", {"runs": [{"at": "1", "files": ["DESIGN.md"]}]}, "1"),
        ("a run recorded before gated", {"gated_at_start": {"DESIGN.md": "a"},
                                         "runs": [{"at": "1", "files": ["DESIGN.md"]}, run("2", {"DESIGN.md": "a"})]},
         "1"),
        ("other paths ignored", {"gated_at_start": {}, "runs": [run("1", {"src/x.css": "z"}, ("src/x.css",))]}, None),
    ]
    bad = 0
    for name, task, want in cases:
        got = first_build(task, ("DESIGN.md",))
        if got != want:
            bad += 1
            print(f"FAIL {name}: want {want}, got {got}")
    scopes = [
        ("a metadata scope", "---\nname: x\ndescription: y\nmetadata:\n  scope: portable\n---\n# X\n", "portable"),
        ("a top-level scope", "---\nname: x\nscope: project\n---\n", "project"),
        ("no scope", "---\nname: x\ndescription: scope: in prose\n---\n", None),
        ("no frontmatter", "# X\nscope: kit\n", None),
    ]
    for name, text, want in scopes:
        got = scope_of(text)
        if got != want:
            bad += 1
            print(f"FAIL scope, {name}: want {want}, got {got}")
    needs = requires_of("---\nname: a\nmetadata:\n  scope: portable\n  requires: [ui-designer, 'motion']\n---\n")
    if needs != ["ui-designer", "motion"]:
        bad += 1
        print(f"FAIL requires: want ['ui-designer', 'motion'], got {needs}")
    dep = lambda d, n, k, at="t": {"at": at, "deployed": d, "findings": n, "decisions": k}
    redeploys = [
        ("one run on the target", [dep("a", 0, 0)], 0),
        ("the same code run twice", [dep("a", 0, 0), dep("a", 0, 0)], 0),
        ("changed code, nothing recorded", [dep("a", 0, 0), dep("b", 0, 0)], 1),
        ("changed code, a finding between", [dep("a", 0, 0), dep("b", 1, 0)], 0),
        ("changed code, a decision between", [dep("a", 2, 1), dep("b", 2, 2)], 0),
        ("three runs, the second gap unrecorded", [dep("a", 0, 0), dep("b", 1, 0), dep("c", 1, 0)], 1),
        ("three runs, both gaps unrecorded", [dep("a", 0, 0), dep("b", 0, 0), dep("c", 0, 0)], 2),
    ]
    for name, log, want in redeploys:
        got = len(unrecorded_redeploys(log))
        if got != want:
            bad += 1
            print(f"FAIL redeploys, {name}: {got} gap(s), want {want}")
    late = [
        ("a late lesson names the run that shipped it", [dep("a", 0, 0), dep("b", 0, 0)], frozenset({2}), 0),
        ("a late lesson for another run leaves the gap", [dep("a", 0, 0), dep("b", 0, 0)], frozenset({3}), 1),
        ("one late lesson closes one gap of two", [dep("a", 0, 0), dep("b", 0, 0), dep("c", 0, 0)], frozenset({3}), 1),
    ]
    for name, log, covered, want in late:
        got = len(unrecorded_redeploys(log, covered))
        if got != want:
            bad += 1
            print(f"FAIL redeploys, {name}: {got} gap(s), want {want}")
    redeploys = redeploys + [(n, l, w) for n, l, _, w in late]
    # Lessons: each route's edit in the change, a rubric lesson's learned item, the rubrics and the log well formed
    lesson = lambda route, kind="finding", judge=None: {"kind": kind, "text": "t", "route": route, "judge": judge}
    rows_for = lambda n: (lambda agent: n)
    lessons = [
        ("a doc lesson with a doc changed", {"findings": [lesson("doc")]}, ["docs/X.md"], rows_for(0), 0),
        ("a doc lesson with no doc changed", {"findings": [lesson("doc")]}, ["src/a.ts"], rows_for(0), 1),
        ("a skill lesson needs a SKILL.md", {"findings": [lesson("skill")]}, [".agents/skills/x/scripts/a.py"],
         rows_for(0), 1),
        ("a skill lesson lands in an agent's file", {"findings": [lesson("skill")]}, [".agents/agents/x.md"],
         rows_for(0), 0),
        ("a test lesson with a test", {"findings": [lesson("test")]}, ["e2e/home.spec.ts"], rows_for(0), 0),
        ("a guard lesson with project.py", {"findings": [lesson("guard")]}, [".agents/project.py"], rows_for(0), 0),
        ("none needs nothing", {"findings": [lesson("none")]}, [], rows_for(0), 0),
        ("a no to the ui-designer's rubric with its item", {"declines": [lesson("rubric", "decline", "ui-designer")]},
         [".agents/rubrics/ui-designer.md"], rows_for(1), 0),
        ("a no to the rubric with no item added", {"declines": [lesson("rubric", "decline", "ui-designer")]},
         [".agents/rubrics/ui-designer.md"], rows_for(0), 1),
        ("two rubric lessons and one item", {"findings": [lesson("rubric", judge="ux-designer")],
                                             "declines": [lesson("rubric", "decline", "ux-designer")]},
         [".agents/rubrics/ux-designer.md"], rows_for(1), 1),
        ("a false alarm needs its rubric changed", {"findings": [lesson("rubric", "false-alarm", "code-reviewer")]},
         ["docs/X.md"], rows_for(0), 1),
        ("a doc changed only before the lesson", {"findings": [{**lesson("doc"), "seen": {"docs/X.md": "h1"}}]},
         ["docs/X.md"], rows_for(0), 1),
        ("a doc changed again after the lesson", {"findings": [{**lesson("doc"), "seen": {"docs/X.md": "h0"}}]},
         ["docs/X.md"], rows_for(0), 0),
        ("a learned item there before the lesson", {"declines": [{**lesson("rubric", "decline", "ui-designer"),
                                                                  "rows_at": 1}]},
         [".agents/rubrics/ui-designer.md"], rows_for(1), 1),
        ("an edit made first and named", {"findings": [{**lesson("doc"), "seen": {"docs/X.md": "h1"},
                                                         "edit": "docs/X.md"}]}, ["docs/X.md"], rows_for(0), 0),
        ("a named edit not in the change", {"findings": [{**lesson("doc"), "edit": "docs/Y.md"}]}, ["docs/X.md"],
         rows_for(0), 1),
        ("a named edit off the route", {"findings": [{**lesson("skill"), "edit": "docs/X.md"}]}, ["docs/X.md"],
         rows_for(0), 1),
        ("a learned item added first and named",
         {"declines": [{**lesson("rubric", "decline", "ui-designer"), "rows_at": 1,
                        "edit": ".agents/rubrics/ui-designer.md"}]},
         [".agents/rubrics/ui-designer.md"], rows_for(1), 0),
    ]
    for name, task, files, rows, want in lessons:
        got = len(lesson_problems(task, files, rows, hash_of=lambda f: "h1"))
        if got != want:
            bad += 1
            print(f"FAIL lessons, {name}: {got} problem(s), want {want}")
    head = "# R\n\n## Learned\n\n| Item | Since | From the person | Looks for |\n| --- | --- | --- | --- |\n"
    rubrics = [
        ("a well-formed table", head + "| L1 | 2026-11-19 | a | b |\n| L3 | 2026-11-20 | c | d |\n", 0),
        ("an empty table", head, 0),
        ("a reused number", head + "| L1 | 2026-11-19 | a | b |\n| L1 | 2026-11-20 | c | d |\n", 1),
        ("a number out of order", head + "| L2 | 2026-11-19 | a | b |\n| L1 | 2026-11-20 | c | d |\n", 1),
        ("a date ahead of today", head + "| L1 | 2099-01-01 | a | b |\n", 1),
        ("an empty cell", head + "| L1 | 2026-11-19 |  | b |\n", 1),
        ("a row that is not an item", head + "| X1 | 2026-11-19 | a | b |\n", 1),
        ("rows outside Learned are not read", "## Items\n\n| R1 | x | y | z |\n" + head, 0),
    ]
    for name, text, want in rubrics:
        got = len(rubric_problems("r.md", text, today="2026-11-21"))
        if got != want:
            bad += 1
            print(f"FAIL rubrics, {name}: {got} problem(s), want {want}")
    if is_kit_or_doc(".agents/evals/judgements.jsonl") or not is_kit_or_doc(".agents/rubrics/ui-designer.md"):
        bad += 1
        print("FAIL judges, the judgements log is no file of the doc-reviewer's; a rubric is")
    if count_new_rows("+| L4 | 2026-11-21 | a | b |\n | L3 | 2026-11-20 | c | d |\n+unrelated\n") != 1:
        bad += 1
        print("FAIL rubrics, new rows counted from a diff")
    log = ['{"kind": "finding", "route": "doc", "about": "layout"}', '{"kind": "decline", "route": "rubric", '
           '"about": "flow", "draft": "ux"}', '{"kind": "approval", "route": "none", "draft": "mock"}', "not json",
           '{"kind": "finding", "route": "docs"}', '{"kind": "finding", "route": "doc", "about": "vibes"}',
           '{"kind": "decline", "route": "none"}']
    if len(judgement_problems(log)) != 4:
        bad += 1
        print(f"FAIL judgements, 4 bad lines: {judgement_problems(log)}")
    stats = draft_stats([{"kind": "decline", "draft": "mock", "task": "a"}, {"kind": "approval", "draft": "mock",
                         "task": "a"}, {"kind": "approval", "draft": "mock", "task": "b"},
                         {"kind": "finding", "task": "b"}])
    if stats != {"mock": {"yes": 2, "no": 1, "first": 1, "drafts": 2}}:
        bad += 1
        print(f"FAIL calibration, draft stats: {stats}")
    areas = area_counts([{"kind": "finding", "about": "layout"}, {"kind": "decline", "about": "layout"},
                         {"kind": "approval", "about": None}, {"kind": "false-alarm"}])
    if areas != ({"layout": 2}, 1):
        bad += 1
        print(f"FAIL calibration, areas: {areas}")
    quality = quality_self_test() + cli_self_test()
    bad += sum(1 for _, ok in quality if not ok)
    for name, ok in quality:
        if not ok:
            print(f"FAIL quality, {name}")
    cases = cases + scopes + redeploys + lessons + rubrics + [("requires", "", ""), ("new rows", "", ""),
                                                               ("log", "", ""),
                                                               ("judgements", "", ""), ("draft stats", "", ""),
                                                               ("areas", "", "")] + quality
    print(f"verify self-test: {len(cases) - bad}/{len(cases)} cases pass")
    return 1 if bad else 0


def quality_self_test() -> list[tuple[str, bool]]:
    """The quality layer's cases: the weighting, the caps, the scores' parsing, a taste miss, the weights kept at 100
    within bounds, the Taste table, the promote count and the bar (.agents/HARNESS.md §12)."""
    out = []

    def case(name: str, ok: bool) -> None:
        out.append((name, bool(ok)))

    def bounded(w: dict) -> bool:
        return abs(sum(w.values()) - 100) < 0.05 and all(WEIGHT_MIN <= v <= WEIGHT_MAX for v in w.values())

    ui = {"hierarchy": 20, "spacing": 20, "consistency": 15, "balance": 15, "state": 15, "medium": 15}
    w = renormalise(ui, "spacing", 20 * (1 + MISS_RAISE))
    case("a miss raises 20 to 24 and keeps 100", w["spacing"] == 24 and bounded(w) and w["hierarchy"] < 20)
    case("a raise stops at the ceiling", renormalise(ui, "spacing", 55)["spacing"] == WEIGHT_MAX)
    case("a setting under the floor is held at it", renormalise(ui, "spacing", 1)["spacing"] == WEIGHT_MIN)
    tight = {"a": 30, "b": 30, "c": 30, "d": 5, "e": 5}
    w = renormalise(tight, "a", 36)
    case("the others never fall under the floor", bounded(w) and w["d"] == WEIGHT_MIN and w["a"] == 36)
    w = renormalise({"a": 40, "b": 40, "c": 10, "d": 10}, "c", 5)
    case("the others never rise over the ceiling", bounded(w) and w["a"] == WEIGHT_MAX)
    case("all 4s score 100", weighted({"a": 4, "b": 4}, {"a": 60, "b": 40}) == 100)
    case("weights tilt the score", weighted({"a": 4, "b": 0}, {"a": 75, "b": 25}) == 75)
    case("n/a is left out of the weighting", weighted({"a": 4, "b": None}, {"a": 50, "b": 50}) == 100)
    case("nothing scored has no score", weighted({"a": None}, {"a": 100}) is None)
    case("a proxy out of range caps at 2", apply_caps({"a": 4, "b": 3, "c": None}, {"a": ["x"], "c": ["y"]})
         == {"a": 2, "b": 3, "c": None})
    proxy = {"judge": "ui-designer", "at": "t", "metrics": [
        {"dimension": "spacing", "name": "pair:group", "value": 0.8, "range": [0, 0.5], "ok": False, "where": "home"},
        {"dimension": "hierarchy", "name": "sizes", "value": 3, "range": [0, 3], "ok": True, "where": "home"}]}
    caps = caps_from(proxy, "ui-designer")
    case("caps come from the metrics out of range", list(caps) == ["spacing"] and "home" in caps["spacing"][0])
    case("another judge's proxy caps nothing", caps_from(proxy, "code-reviewer") == {})
    case("a placeholder proxy is not built", not proxy_built("x", ("<part B: the screens' proxy>",)))
    case("a proxy whose script is missing is not built", not proxy_built("x", ("python3", "no/such/proxy.py")))
    case("no proxy is not built", not proxy_built("x", ()))
    dims = {"a": {}, "b": {}}

    def raises(fn) -> bool:
        try:
            fn()
        except ValueError:
            return True
        return False
    case("every dimension is scored", raises(lambda: read_scores("a=3", None, "a: x", dims)))
    case("a score is 0–4", raises(lambda: read_scores("a=5,b=1", None, "a: x; b: y", dims)))
    case("an unknown dimension is refused", raises(lambda: read_scores("a=1,b=1,z=1", None, "a: x; b: y", dims)))
    case("each dimension needs its reason", raises(lambda: read_scores("a=1,b=1", None, "a: x", dims)))
    case("scores and reasons parse", read_scores("a=3, b=na", None, "a: the pairs glue; b: one screen", dims)
         == ({"a": 3, "b": None}, {"a": "the pairs glue", "b": "one screen"}))
    case("a miss: poor on a 3", is_miss("poor", 3))
    case("not a miss: poor on a 2", not is_miss("poor", 2))
    case("not a miss: good on a 4", not is_miss("good", 4))
    case("not a miss: never scored", not is_miss("poor", None))
    rows = [{"kind": "review", "judge": "j", "scores": {"a": 4}}, {"kind": "audit", "judge": "j", "scores": {"a": 2}},
            {"kind": "taste", "judge": "j", "dimension": "a", "miss": True},
            {"kind": "taste", "judge": "j", "dimension": "a", "miss": False},
            {"kind": "taste", "judge": "j", "dimension": "b", "miss": True},
            {"kind": "person", "judge": "j", "dimension": "a", "score": 1, "judge_score": 4},
            {"kind": "person", "judge": "j", "dimension": "a", "score": 2, "judge_score": 2}]
    case("the judge's last score is the latest review or audit", last_judge_score(rows, "j", "a") == 2)
    case("misses are counted per dimension", taste_misses(rows, "j", "a") == 1)
    rows.append({"kind": "taste", "judge": "j", "dimension": "a", "miss": True})
    case("the second miss on a dimension is counted", taste_misses(rows, "j", "a") == 2)
    c = calibration_rows(rows, "j", "a")
    case("calibration: the mean gap, judge minus person", c["gap"] == 1.5 and c["ratings"] == 2 and c["misses"] == 2)
    plain = "# Rubric — j\n\n## Learned\n\n| Item | Since |\n| --- | --- |\n| L1 | d |\n| L4 | d |\n"
    once = add_section_row(plain, "## Taste", TASTE_HEAD, "| T1 | d | w | `a` | p |")
    case("the first taste adds the Taste table", once.count("## Taste") == 1 and once.rstrip().endswith("| p |")
         and "| L4 | d |" in once)
    twice = add_section_row(once + "\n## Other\n\ntext\n", "## Taste", TASTE_HEAD, "| T2 | d | w | `b` | p |")
    case("the next taste goes under the last row, not past the section",
         twice.index("| T2 |") < twice.index("## Other") and twice.index("| T1 |") < twice.index("| T2 |"))
    case("the next T and L numbers are free ones", next_item(twice, "T") == 3 and next_item(plain, "L") == 5)
    case("a word with a pipe stays in its cell", table_cell("a | b\nc") == "a \\| b c")
    task = {"reviews": {"ui-designer": {"verdict": "pass", "quality": 70, "scores": {"hierarchy": 2}, "at": "t1"}},
            "acceptances": []}
    has_dims = "ui-designer" in load_weights()["judges"]
    case("below the bar is open", not has_dims or len(quality_problems(task, "ui-designer")) == 1)
    task["acceptances"].append({"judge": "ui-designer", "review_at": "t1", "quality": 70, "words": "ok"})
    case("the person's acceptance closes it", quality_problems(task, "ui-designer") == [])
    task["reviews"]["ui-designer"]["at"] = "t2"
    case("an acceptance carries to a later review at the same score", quality_problems(task, "ui-designer") == [])
    task["reviews"]["ui-designer"]["quality"] = 72
    case("an acceptance carries to a later review scored higher", quality_problems(task, "ui-designer") == [])
    task["reviews"]["ui-designer"]["quality"] = 65
    case("a later review scored lower needs a new acceptance",
         not has_dims or len(quality_problems(task, "ui-designer")) == 1)
    task["reviews"]["ui-designer"]["at"] = "t0"
    task["reviews"]["ui-designer"]["quality"] = 70
    case("an acceptance never reaches back to an earlier review",
         not has_dims or len(quality_problems(task, "ui-designer")) == 1)
    task["reviews"]["ui-designer"]["quality"] = QUALITY_BAR
    case("at the bar passes", quality_problems(task, "ui-designer") == [])
    del task["reviews"]["ui-designer"]["quality"]
    case("a pass with no score is open", not has_dims or len(quality_problems(task, "ui-designer")) == 1)
    case("the starting weights sum to 100 within bounds", not [p for p in weights_problems(load_weights())
                                                               if "anchors" not in p])
    heavy = {"a": {"weight": 60}, "b": {"weight": 40}}
    case("60 % of the weight scored is enough", read_scores("a=3,b=na", None, "a: x; b: y", heavy)[0]["a"] == 3)
    case("under 60 % of the weight scored is refused", raises(lambda: read_scores("a=na,b=3", None, "a: x; b: y",
                                                                                 heavy)))
    rubric = ("# R\n\n## Learned\n\n| Item | Since | From the person | Looks for |\n| --- | --- | --- | --- |\n"
              "| L4 | d | promoted from taste rows T2 and T3 | x |\n\n" + TASTE_HEAD
              + "| T1 | d | \"w\" (poor) | `hierarchy` | p |\n| T2 | d | \"w\" (poor) | `spacing` | p |\n"
              "| T3 | d | \"w\" (poor; a miss) | `spacing` | p |\n| T5 | d | \"w\" (poor; promoted to L9) | `medium` | p |\n")
    case("a Learned row naming a dimension's Taste rows is its item", learned_for(rubric, "spacing") == "L4")
    case("a Taste row that says it was promoted names the item", learned_for(rubric, "medium") == "L9")
    case("a dimension never promoted has no item", learned_for(rubric, "hierarchy") is None)
    case("the Taste rows on a dimension", taste_items(rubric, "spacing") == ["T2", "T3"])
    once = [{"kind": "taste", "judge": "j", "dimension": "a", "miss": True, "promote_prompted": True}]
    case("the promotion prompt prints once per dimension", promoted_before(once, "j", "a")
         and not promoted_before(once, "j", "b"))
    out += proxy_self_test()
    out += write_self_test()
    out += out_of_scope_self_test()
    out += clean_as_you_code_self_test()
    out += normalise_self_test()
    out += frontmatter_self_test()
    return out


def frontmatter_self_test() -> list[tuple[str, bool]]:
    """A skill's or agent's frontmatter that YAML would refuse fails the scope check; a folded description passes, and
    its words are never read as a key."""
    folded = ("---\nname: x\ndescription: >-\n  Use when: the build fails. scope: project, requires: [y]\n"
              "  Its # is text.\nmetadata:\n  scope: portable\n  requires: [a, b]\n---\n# X\n")
    bad = lambda value: f"---\nname: x\ndescription: {value}\nmetadata:\n  scope: portable\n---\n"  # noqa: E731
    return [
        ("frontmatter: a plain description holding `: ` fails",
         len(frontmatter_problems(bad("Use when: it fails"))) == 1),
        ("frontmatter: a plain description holding ` #` fails", "comment" in " ".join(frontmatter_problems(
            bad("Runs step #1 and # 2")))),
        ("frontmatter: a plain value ending in `:` fails", len(frontmatter_problems(bad("Use when:"))) == 1),
        ("frontmatter: `: ` on a plain value's continuation line fails",
         len(frontmatter_problems(bad("Runs the loop\n  then: the gate"))) == 1),
        ("frontmatter: a block never closed fails", "never closed" in " ".join(frontmatter_problems(
            "---\nname: x\nmetadata:\n  scope: portable\n# X\n"))),
        ("frontmatter: an open quote fails", len(frontmatter_problems(bad('"Use when: it fails'))) == 1),
        ("frontmatter: a line that is no key fails", len(frontmatter_problems("---\nname: x\njust words\n---\n")) == 1),
        ("frontmatter: a quoted value and a plain one without `: ` pass",
         frontmatter_problems(bad('"Use when: it fails"')) == [] and frontmatter_problems(bad("Runs the loop")) == []),
        ("frontmatter: a folded description passes", frontmatter_problems(folded) == []),
        ("frontmatter: a CRLF file is read, not taken for one with none",
         len(frontmatter_problems(bad("Use when: it fails").replace("\n", "\r\n"))) == 1
         and scope_of(folded.replace("\n", "\r\n")) == "portable"),
        ("frontmatter: an unindented sequence under a key passes",
         frontmatter_problems("---\nname: x\nallowed-tools:\n- Bash\n- Read\nmetadata:\n  scope: project\n---\n")
         == []),
        ("frontmatter: scope and requires read past a folded description's words",
         scope_of(folded) == "portable" and requires_of(folded) == ["a", "b"]),
    ]


def clean_as_you_code_self_test() -> list[tuple[str, bool]]:
    """A metric out of range caps a review only when the change made it: new, worse or somewhere new; one out of range
    at the base already is carried debt; an audit caps from every one (.agents/HARNESS.md §12.5)."""
    def m(value, base="absent", rng=(0, 50), **extra) -> dict:
        out = {"dimension": "plain", "name": "n", "value": value, "range": list(rng), "ok": rng[0] <= value <= rng[1],
               **extra}
        if base != "absent":
            out["base"] = base
        return out
    data = lambda *ms, scope=SCOPE_CHANGE: {"judge": "j", "scope": scope, "metrics": list(ms)}  # noqa: E731
    return [
        ("clean as you code: a metric in range caps nothing", regression(m(10, None)) is None),
        ("clean as you code: no base value caps, as before", regression(m(60)) == "no base value to compare"),
        ("clean as you code: a metric new since the base caps", "new" in (regression(m(60, None)) or "")),
        ("clean as you code: the same value as at the base is carried", regression(m(60, 60)) is None),
        ("clean as you code: better than the base, still out, is carried", regression(m(55, 70)) is None),
        ("clean as you code: worse than the base caps", "worse" in (regression(m(70, 60)) or "")),
        ("clean as you code: in range at the base, out now, caps", "worse" in (regression(m(60, 40)) or "")),
        ("clean as you code: a range's low side counts as far", "worse" in (regression(m(0.5, 0.8, (0.9, 1))) or "")),
        ("clean as you code: the same places as at the base are carried",
         regression(m(1, 1, (0, 0), offenders={"a": 1}, base_offenders={"a": 1, "b": 1})) is None),
        ("clean as you code: a new place caps",
         "new or worse at b" in (regression(m(1, 1, (0, 0), offenders={"b": 1}, base_offenders={"a": 1})) or "")),
        ("clean as you code: a place made worse caps",
         regression(m(70, 70, offenders={"f": 70}, base_offenders={"f": 65})) is not None),
        ("clean as you code: places decide over the value",
         regression(m(80, 60, offenders={"f": 80}, base_offenders={"f": 80})) is None),
        ("clean as you code: carried debt is split from the caps",
         split_metrics(data(m(60, 60), m(70, None)), "j") == (
             {"plain": ["n 70 outside [0, 50] — new since the base"]},
             {"plain": ["n 60 outside [0, 50] — carried: 60 at the base"]})),
        ("clean as you code: an audit caps from every metric",
         list(split_metrics(data(m(60, 60), scope=SCOPE_PRODUCT), "j")[0]) == ["plain"]),
        ("clean as you code: a value that is not a number caps, not comparable",
         "not comparable" in (regression(dict(m(60, 60), value="sixty")) or "")),
        ("clean as you code: a range with a null bound, or none, caps",
         "not comparable" in (regression(dict(m(60, 60), range=[0, None])) or "")
         and "not comparable" in (regression({k: v for k, v in m(60, 60).items() if k != "range"}) or "")),
        ("clean as you code: a null value or base value that is not a number caps",
         "not comparable" in (regression(dict(m(60, 60), value=None)) or "")
         and "not comparable" in (regression(m(60, "60")) or "")),
        ("clean as you code: out of range with no place named caps",
         regression(m(1, 1, (0, 0), offenders={}, base_offenders={"a": 1})) is not None),
        ("clean as you code: a refactor that adds no hit is uncapped",
         apply_caps({"plain": 4}, caps_from(data(m(60, 60), m(1, 1, (0, 0))), "j")) == {"plain": 4}),
    ]


def normalise_self_test() -> list[tuple[str, bool]]:
    """What a review survives: comment and whitespace edits in C, C++, Python and shell, prose re-wrapped in Markdown
    with the same words — never a change inside a literal, a word, or whitespace that means something."""
    def same(path: str, a: str, b: str) -> bool:
        return [u[2] for u in file_units(path, a)] == [u[2] for u in file_units(path, b)]
    c = 'int f(int x) {\n    return x + 1;  // one more\n}\nconst char *s = "a // b";\n'
    py = 'def f(x):\n    # one more\n    return g(x,\n             1)\ns = "a # b"\n'
    sh = '#!/bin/sh\n# say it\necho  "a # b"   # done\nn=${#x}\ncat <<EOF\n# kept\nEOF\n'
    md = "# Title\n\nOne two three\nfour five.\n\n- a\n- b\n\n```\n  x  = 1\n```\n"
    out = [
        ("normalise: a C comment edit is no change", same("a.c", c, c.replace("one more", "add one"))),
        ("normalise: C indentation and spacing are no change",
         same("a.cpp", c, c.replace("    return x + 1;", "  return x+1;").replace("{\n", "{ "))),
        ("normalise: a C block comment over lines is no change", same("a.h", c, "/* a\n b */\n" + c)),
        ("normalise: `//` inside a C string is kept", not same("a.c", c, c.replace("a // b", "a // c"))),
        ("normalise: a C token change is a change", not same("a.c", c, c.replace("x + 1", "x + 2"))),
        ("normalise: `a - -b` is not `a--b`", not same("a.c", "y = a - -b;", "y = a--b;")),
        ("normalise: a directive keeps its spaces", not same("a.h", "#define F(x) x\n", "#define F (x) x\n")),
        ("normalise: a directive's end is kept", not same("a.h", "#define A 1\nint x;\n", "#define A 1 int x;\n")),
        ("normalise: a C++ raw string is kept as written",
         not same("a.cpp", 'auto s = R"(a  // b)";\n', 'auto s = R"(a // b)";\n')),
        ("normalise: a Python comment edit is no change", same("a.py", py, py.replace("one more", "add one"))),
        ("normalise: Python re-wrapped inside brackets is no change",
         same("a.py", py, py.replace("g(x,\n             1)", "g(x, 1)"))),
        ("normalise: Python indentation that moves a line is a change",
         not same("a.py", "if a:\n    b()\nc()\n", "if a:\n    b()\n    c()\n")),
        ("normalise: `#` inside a Python string is kept", not same("a.py", py, py.replace("a # b", "a # c"))),
        ("normalise: a shell comment edit is no change",
         same("x.sh", sh, sh.replace("# say it", "# say").replace("# done", ""))),
        ("normalise: `#` in shell quotes, ${#x} and a here-document are kept",
         not same("x.sh", sh, sh.replace("a # b", "a")) and not same("x.sh", sh, sh.replace("${#x}", "${x}"))
         and not same("x.sh", sh, sh.replace("# kept", "# gone"))),
        ("normalise: a shebang names the kind", kind_of(".agents/githooks/pre-commit", "#!/usr/bin/env python3\n")
         == "py" and kind_of("hook", "#!/bin/bash\n") == "sh" and kind_of("a.txt", "x") == "raw"),
        ("normalise: Markdown re-wrapped with the same words is no change",
         same("a.md", md, md.replace("three\nfour", "three four").replace("One two", "One\ntwo"))),
        ("normalise: a word changed in Markdown is a change", not same("a.md", md, md.replace("four", "for"))),
        ("normalise: a Markdown list run into a paragraph is a change", not same("a.md", md, md.replace("- a\n- b",
                                                                                                   "- a - b"))),
        ("normalise: whitespace in a Markdown fence is kept", not same("a.md", md, md.replace("  x  = 1", "x = 1"))),
        ("normalise: a `//` comment ending in a backslash swallows the next line",
         not same("a.c", "int x; // note\nint y = f();\n", "int x; // note \\\nint y = f();\n")),
        ("normalise: so does a directive's trailing `//` comment",
         not same("a.h", "#define A 1 // n\nint y;\n", "#define A 1 // n \\\nint y;\n")),
        ("normalise: lines spliced into a comment or a literal still count",
         c_units("int x; // a \\\nb\nint y;\n")[-1][0] == 3 and c_units('s = "a\\\nb";\nint y;\n')[-1][0] == 3),
        ("normalise: a Python shebang is kept", not same("t.py", "#!/usr/bin/env python3\nx = 1\n",
                                                          "#!/usr/bin/env python2\nx = 1\n")),
        ("normalise: a shell shebang and its flags are kept",
         not same("x.sh", "#!/bin/sh -e\necho a\n", "#!/bin/sh\necho a\n")
         and not same("hook", "#!/bin/bash\necho a\n", "#!/bin/zsh\necho a\n")),
        ("normalise: a four-backtick fence holds a triple-backtick line, whitespace kept",
         not same("a.md", "````\n```\n  a  b\n````\n", "````\n```\na b\n````\n")),
        ("normalise: indented code keeps its whitespace; a list's indented paragraph does not",
         not same("a.md", "Para.\n\n    x  =  1\n", "Para.\n\n    x = 1\n")
         and same("a.md", "- a\n\n    b  c\n", "- a\n\n    b c\n")),
    ]
    hunks = unit_hunks("a.c", c, c.replace("x + 1", "x + 2").replace("one more", "plus one"))
    out.append(("delta: a code edit and a comment edit are one hunk, at its line",
                [(h["old"][:2], h["new"][:2]) for h in hunks] == [((2, 2), (2, 2))]))
    nits = [{"path": "a.c", "from": 5, "to": 5, "text": ""}]
    out.append(("nits: a hunk within the slack of a nit is its fix, one farther is not",
                near_nit({"path": "a.c", "old": (2, 2, True)}, nits) is not None
                and near_nit({"path": "a.c", "old": (1, 1, True)}, nits) is None
                and near_nit({"path": "b.c", "old": (5, 5, True)}, nits) is None))
    at = "a.c" + ":3"  # a nit's place, kept apart so the source holds no file:line reference
    try:
        parse_nits([f"{at} too long"], ["b.c"])
        refused = False
    except ValueError:
        refused = True
    out.append(("nits: a nit on a file the judge never read is refused", refused))
    out.append(("nits: a nit's lines and words parse", parse_nits([f"{at}-4 name it"], ["a.c"])
                == [{"path": "a.c", "from": 3, "to": 4, "text": "name it"}]))
    try:
        parse_nits([f"{at}-99999 all of it"], ["a.c"])
        wide = False
    except ValueError:
        wide = True
    out.append((f"nits: a nit over more than {NIT_SPAN} lines is refused", wide))
    one = [{"path": "a.c", "from": 5, "to": 5, "text": ""}]
    out.append(("nits: a hundred lines inserted after a nit are not its fix; two are",
                near_nit({"path": "a.c", "old": (5, 5, False), "new": (6, 105, True)}, one) is None
                and near_nit({"path": "a.c", "old": (5, 5, False), "new": (6, 7, True)}, one) is not None
                and near_nit({"path": "a.c", "old": (5, 5, True), "new": (5, 30, True)}, one) is None))
    para = "Title.\n\n" + "\n".join(f"line {i} of the paragraph" for i in range(3, 9)) + "\n"
    word = unit_hunks("a.md", para, para.replace("line 5 of the", "line 5 of a"))
    md_nit = [{"path": "a.md", "from": 5, "to": 5, "text": ""}]
    out.append(("nits: a one-word fix in a long Markdown paragraph is a one-line hunk, the nit's fix",
                [(h["old"][:2], h["new"][:2]) for h in word] == [((5, 5), (5, 5))]
                and all(near_nit(h, md_nit) for h in word)))
    rewrap = para.replace("line 5 of the", "line 5 of a").replace(" paragraph\nline", " paragraph line")
    out.append(("nits: a word fix that also re-wraps the paragraph stays wide, and is no nit's fix",
                not all(near_nit(h, md_nit) for h in unit_hunks("a.md", para, rewrap))))
    code = "int a;\n" + "".join(f"int v{i};\n" for i in range(2, 12))
    opened = unit_hunks("a.c", code, code.replace("int a;\n", "int a; /*\n") + "*/\n")
    out.append(("nits: an unclosed comment that hides the rest of a file is no one-line nit fix",
                not all(near_nit(h, [{"path": "a.c", "from": 1, "to": 1, "text": ""}]) for h in opened)))
    return out


def out_of_scope_self_test() -> list[tuple[str, bool]]:
    """--out-of-scope: accepted only when a fresh, passing proxy run shows the judge's scope empty; then finish holds
    the verdict and not the bar, until the tree changes."""
    global PROXY_DIR, ROOT, PROXIES
    out = []
    saved = PROXY_DIR, ROOT, PROXIES
    with tempfile.TemporaryDirectory() as tmp:
        PROXY_DIR, ROOT, PROXIES = Path(tmp) / "proxies", Path(tmp) / "repo", {"j": ("python3", "p.py")}
        PROXY_DIR.mkdir()
        ROOT.mkdir()
        try:
            subprocess.run(["git", "init", "-q"], cwd=ROOT, check=True)  # a.md: a changed file, for staleness
            (ROOT / "p.py").write_text("")
            (ROOT / "a.md").write_text("x")
            os.utime(ROOT / "a.md", (1_000_000, 1_000_000))
            os.utime(ROOT / "p.py", (1_000_000, 1_000_000))

            def check(in_scope, at: str = "2001-01-01T00:00:00Z") -> tuple[bool, str]:
                data = {"judge": "j", "at": at, "scope": SCOPE_CHANGE, "scope_what": "the screens", "metrics": []}
                if in_scope is not None:
                    data["in_scope"] = in_scope
                (PROXY_DIR / "j.json").write_text(json.dumps(data))
                (PROXY_DIR / "j.run.json").write_text(json.dumps({"exit": 0, "at": at}))
                return out_of_scope_check("j")
            ok, said = check([])
            out.append(("out of scope: an empty measured scope is accepted, and says so", ok and "empty" in said))
            ok, said = check(["kit", "home"])
            out.append(("out of scope: a scope with screens in it is refused", not ok and "2 in scope" in said))
            out.append(("out of scope: a proxy that names no scope is refused", not check(None)[0]))
            out.append(("out of scope: a stale proxy is refused", not check([], "1970-01-01T00:00:00Z")[0]))
            PROXIES = {}
            out.append(("out of scope: a judge with no proxy is refused", not out_of_scope_check("j")[0]))
        finally:
            PROXY_DIR, ROOT, PROXIES = saved
    review = {"verdict": "pass", "out_of_scope": True, "quality": None, "scope": "scope: the screens — empty",
              "scope_fingerprint": tree_fingerprint(), "at": "t"}
    task = {"reviews": {"ui-designer": review}, "acceptances": []}
    out.append(("finish: an out-of-scope pass is not held to the bar", quality_problems(task, "ui-designer") == []))
    out.append(("finish: it says so in the Verified block", "out of scope — not held to the bar"
                in review_line("ui-designer", review)))
    review["scope_fingerprint"] = "another tree"
    out.append(("finish: a tree changed since the check needs the review again",
                len(quality_problems(task, "ui-designer")) == 1))
    del review["out_of_scope"]
    out.append(("finish: an in-scope pass with no score is still held", len(quality_problems(task, "ui-designer")) == 1))
    return out


def proxy_self_test() -> list[tuple[str, bool]]:
    """A proxy's results are used only for their scope, from a run that passed, newer than every changed file."""
    global PROXY_DIR, ROOT
    out = []
    saved = PROXY_DIR, ROOT
    with tempfile.TemporaryDirectory() as tmp:
        PROXY_DIR, ROOT = Path(tmp), Path(tmp)
        try:
            (ROOT / "a.md").write_text("x")
            os.utime(ROOT / "a.md", (1_000_000, 1_000_000))
            metric = {"dimension": "plain", "name": "n", "value": 60, "range": [0, 50], "ok": False, "where": "a.md"}

            def results(at: str, scope: str = SCOPE_CHANGE, exit_code: int = 0) -> tuple:
                (PROXY_DIR / "j.json").write_text(json.dumps({"judge": "j", "at": at, "scope": scope,
                                                              "metrics": [metric]}))
                (PROXY_DIR / "j.run.json").write_text(json.dumps({"exit": exit_code, "at": at}))
                return proxy_state("j", SCOPE_CHANGE, ["a.md"])
            fresh = results("2001-01-01T00:00:00Z")
            out.append(("fresh results of the change cap", list(fresh[0]) == ["plain"] and fresh[2] is None))
            stale = results("1970-01-01T00:00:00Z")
            out.append(("results older than a changed file are set aside", stale[0] == {} and "stale" in stale[2]))
            other = results("2001-01-01T00:00:00Z", SCOPE_PRODUCT)
            out.append(("the product's results cap no review", other[0] == {} and "product" in other[2]))
            failed = results("2001-01-01T00:00:00Z", exit_code=1)
            out.append(("a failed run's results are set aside", failed[0] == {} and "failed" in failed[2]))
        finally:
            PROXY_DIR, ROOT = saved
    out.append(("a proxy's `at` reads with Z or local", epoch("1970-01-01T00:00:10Z") == 10
                and epoch("not a time") is None))
    return out


def write_self_test() -> list[tuple[str, bool]]:
    """The writes: atomic, a log appended whole, a lock taken again in one process without waiting on itself."""
    out = []
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "x.jsonl"
        append_line(p, '{"a": 1}')
        with locked(p):  # re-entrant: the append inside takes the same lock
            append_line(p, '{"a": 2}')
        out.append(("a log appended under its lock keeps every row", p.read_text() == '{"a": 1}\n{"a": 2}\n'))
        write_atomic(p, "new\n")
        left = [f for f in os.listdir(tmp) if f != "x.jsonl"]
        out.append(("an atomic write leaves no temp file", p.read_text() == "new\n" and not left))
    return out


def cli_self_test() -> list[tuple[str, bool]]:
    """End to end, in a temp copy of the kit: a review scored above the bar, the person's taste on a dimension it
    scored 3 (a miss that raises its weight), their weight set by hand, a review below the bar that `finish` holds,
    and their acceptance that lets it through."""
    out = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        me = root / ".agents/skills/verify-change/scripts/verify.py"
        me.parent.mkdir(parents=True)
        shutil.copyfile(Path(__file__), me)
        shutil.copyfile(ROOT / ".agents/project.py", root / ".agents/project.py")
        (root / EVALS).mkdir(parents=True)
        shutil.copyfile(WEIGHTS, root / EVALS / "weights.json")
        (root / ".agents/rubrics").mkdir()
        (root / ".agents/rubrics/ui-designer.md").write_text("# Rubric — ui-designer\n\n## Learned\n\n"
                                                             "| Item | Since | From the person | Looks for |\n"
                                                             "| --- | --- | --- | --- |\n")
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)

        def cli(*args: str) -> tuple[int, str]:
            p = subprocess.run([sys.executable, str(me), *args], cwd=root, capture_output=True, text=True)
            return p.returncode, p.stdout + p.stderr

        dims = list(load_weights()["judges"]["ui-designer"])
        note = "; ".join(f"{d}: seen" for d in dims)
        weights = lambda: json.loads((root / EVALS / "weights.json").read_text())["judges"]["ui-designer"]  # noqa
        cli("start", "e2e")
        cli("run", "--only", "none")
        code, said = cli("review", "ui-designer", "pass", "--out-of-scope")
        out.append(("cli: --out-of-scope is refused when no proxy can show the scope empty", code == 1
                    and "review refused" in said))
        code, said = cli("review", "ui-designer", "pass", "--score", ",".join(f"{d}=3" for d in dims), "--note", note)
        out.append(("cli: a review scored 3 on every dimension passes the bar", code == 0 and "quality: 75/100" in said))
        before = weights()["spacing"]["weight"]
        code, said = cli("taste", "too tight", "--judge", "ui-designer", "--dimension", "spacing")
        after = weights()["spacing"]["weight"]
        out.append(("cli: taste on a 3 is a miss that raises the weight", code == 0 and "a miss" in said
                    and after > before))
        code, _ = cli("weight", "--judge", "ui-designer", "--dimension", "spacing", "--set", "30", "--words", "e2e")
        w = weights()
        out.append(("cli: the person's weight is set and the rest keep 100", code == 0 and w["spacing"]["weight"] == 30
                    and abs(sum(v["weight"] for v in w.values()) - 100) < 0.05))
        cli("review", "ui-designer", "pass", "--score", ",".join(f"{d}=1" for d in dims), "--note", note)
        code, said = cli("finish")
        out.append(("cli: finish holds a score below the bar", code == 1 and "is below the bar" in said))
        code, _ = cli("accept", "ui-designer", "fine for this change")
        _, said = cli("finish")
        out.append(("cli: the person's acceptance lets it through", code == 0 and "is below the bar" not in said
                    and "Accepted below the bar by the person" in said))
        rows = [json.loads(ln) for ln in (root / EVALS / "scores.jsonl").read_text().splitlines()]
        out.append(("cli: every score and the taste are logged", [r["kind"] for r in rows] == ["review", "taste",
                                                                                                "review"]))
        code, said = cli("review", "ui-designer", "pass", "--score", ",".join(f"{d}=1" for d in dims), "--note", note)
        _, done = cli("finish")
        out.append(("cli: an acceptance carries to a later review at the same score, in its history",
                    code == 0 and "acceptance at" in said and "is below the bar" not in done
                    and "Carried forward: ui-designer" in done))
        out += review_cli_self_test(root, cli)
    return out


def review_cli_self_test(root: Path, cli) -> list[tuple[str, bool]]:
    """End to end: a pass with a nit, kept across a comment and whitespace edit, made stale by a code edit, the delta
    marked, re-stamped by nits-fixed, refused for a hunk far from the nit and for a blocking verdict; selfcheck."""
    out = []
    (root / ".agents/agents").mkdir(parents=True, exist_ok=True)
    (root / ".agents/agents/code-reviewer.md").write_text("# code-reviewer\n")  # the judge joins finish's plan
    src = root / "main/a.cpp"
    src.parent.mkdir(parents=True, exist_ok=True)
    body = "int f(int x)\n{\n    return x + 1;  // one\n}\n" + "".join(f"int g{i}() {{ return {i}; }}\n"
                                                                    for i in range(20))
    src.write_text(body)
    nit = "main/a.cpp" + ":3"  # kept apart so the source holds no file:line reference
    code, said = cli("review", "code-reviewer", "pass", "--nit", f"{nit} name the one")
    out.append(("cli: a pass with a nit is recorded with it", code == 0 and "1 nit(s)" in said))
    code, _ = cli("review", "code-reviewer", "pass", "--nit", nit.replace("a.cpp", "b.cpp") + " x")
    out.append(("cli: a nit on a file the judge never read is refused", code == 2))
    src.write_text(body.replace("// one", "// add one").replace("    return x + 1", "  return x+1"))
    _, said = cli("status")
    out.append(("cli: a comment and whitespace edit leaves the review standing, and status says so",
                "stands: only comments or whitespace" in said))
    _, said = cli("finish")
    out.append(("cli: finish does not hold a review stale for a comment edit",
                "code-reviewer reviewed an older version" not in said))
    src.write_text(body.replace("x + 1", "x + kOne"))
    _, said = cli("status")
    _, done = cli("finish")
    out.append(("cli: a code edit makes the review stale", "its files changed since (verify.py delta" in said
                and "code-reviewer reviewed an older version of its files — give it only what changed" in done))
    code, said = cli("delta", "code-reviewer")
    out.append(("cli: delta prints the diff since the snapshot, marked, with the verdict and the nit",
                code == 0 and f"[changed] [by the nit {nit}" in said and f"its nit: {nit}" in said
                and "+    return x + kOne;" in said and "last verdict: pass" in said))
    code, said = cli("nits-fixed", "code-reviewer")
    _, status = cli("status")
    out.append(("cli: nits-fixed re-stamps a pass whose hunks lie by its nit, and status shows it",
                code == 0 and "re-stamped" in said and "carried forward: its pass re-stamped" in status
                and "its files changed since" not in status))
    src.write_text(body.replace("x + 1", "x + kOne").replace("return 19;", "return 91;"))
    code, said = cli("nits-fixed", "code-reviewer")
    out.append(("cli: nits-fixed refuses a hunk far from every nit", code == 1 and "verify.py delta" in said))
    cli("review", "code-reviewer", "blocking", "--nit", f"{nit} x")
    src.write_text(body.replace("x + 1", "x + 2"))
    code, said = cli("nits-fixed", "code-reviewer")
    _, done = cli("finish")
    out.append(("cli: nits-fixed never clears a blocking verdict, and finish keeps it",
                code == 1 and "blocking" in said and "code-reviewer said blocking" in done))
    src.write_text(body)
    cli("ask", "code-reviewer")
    src.write_text(body.replace("return 5;", "return 55;"))  # an edit while the judge reads
    code, said = cli("review", "code-reviewer", "pass")
    _, status = cli("status")
    _, delta = cli("delta", "code-reviewer")
    out.append(("cli: a review after `ask` rests on the files as asked; an edit made meanwhile shows in the delta",
                code == 0 and "as they were when asked" in said and "its files changed since" in status
                and "+int g5() { return 55; }" in delta))
    (root / "tool.py").write_text("x = 1\ny = '" + "a" * 130 + "'\n")
    code, said = cli("selfcheck")
    out.append(("cli: selfcheck flags a changed line over 120 characters", code == 1
                and "tool.py" + ":2 is 136" in said))
    return out


def main() -> int:
    if sys.argv[1:] == ["--test"]:
        return self_test()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    s = sub.add_parser("start")
    s.add_argument("task")
    r = sub.add_parser("run")
    r.add_argument("--only", help="exactly these checks, comma-separated: " + ",".join(CHECKS))
    v = sub.add_parser("review")
    v.add_argument("judge", choices=sorted(JUDGES))
    v.add_argument("verdict", choices=["pass", "blocking"])
    v.add_argument("--note", help="with a score: a reason per dimension, \"dim: why; dim: why\"")
    v.add_argument("--score", help="every quality dimension 0–4 or na: dim=n,dim=n (.agents/evals/weights.json)")
    v.add_argument("--scores-file", help="a JSON file {dim: {\"score\": n, \"reason\": \"…\"}} in place of --score")
    v.add_argument("--no-proxy", action="store_true",
                   help="do not run the judge's proxy first; its last results are used only if not stale")
    v.add_argument("--out-of-scope", action="store_true",
                   help="the change touches none of the judge's measured scope: the verdict, no score, not held to "
                        "the bar — refused unless the judge's proxy shows the scope empty")
    v.add_argument("--nit", action="append", metavar="PATH:LINE[-LINE] TEXT",
                   help="a nit the judge raised, on lines of a file it read; repeat it for each — a pass with nits "
                        "is approve-with-nits, and nits-fixed re-stamps it once they are fixed")
    for name, what in (("ask", "keep the judge's files as they are now, before briefing it, for its review to rest on"),
                       ("nits-fixed", "re-stamp the judge's pass when every hunk since lies by a nit it raised"),
                       ("delta", "the diff since the judge read its files, with its verdict, note and nits")):
        sub.add_parser(name, help=what).add_argument("judge", choices=sorted(JUDGES))
    sub.add_parser("selfcheck", help="the fast checks on the changed files, before asking the judges")
    quality_judges = sorted(load_weights()["judges"])
    ac = sub.add_parser("accept")
    ac.add_argument("judge", choices=quality_judges)
    ac.add_argument("words", help="the person's words accepting the score below the bar")
    ts = sub.add_parser("taste")
    ts.add_argument("words", help="the person's view, in their words")
    ts.add_argument("--judge", required=True, choices=quality_judges)
    ts.add_argument("--dimension", required=True)
    ts.add_argument("--anchor", help="an image or file that shows it — copied to .agents/evals/anchors/img/")
    good = ts.add_mutually_exclusive_group()
    good.add_argument("--good", action="store_true", help="an example of good")
    good.add_argument("--poor", action="store_true", help="an example of poor (the default)")
    ra = sub.add_parser("rate")
    ra.add_argument("file", help="what the person scored: a screenshot, a doc, a file")
    ra.add_argument("--judge", required=True, choices=quality_judges)
    ra.add_argument("--dimension", required=True)
    ra.add_argument("--score", required=True, type=int, choices=range(SCORE_MAX + 1))
    ra.add_argument("--note")
    wt = sub.add_parser("weight")
    wt.add_argument("--judge", required=True, choices=quality_judges)
    wt.add_argument("--dimension", required=True)
    wt.add_argument("--set", required=True, type=float, help=f"the new weight, {WEIGHT_MIN}–{WEIGHT_MAX}")
    wt.add_argument("--words", help="the person's words, logged with the change")
    au = sub.add_parser("audit")
    au.add_argument("judge", choices=quality_judges)
    au.add_argument("--scores-file", help="the judge's whole-product scores, as for review")
    au.add_argument("--note", help="a note kept with the audit; a reason per dimension, \"dim: why; dim: why\", "
                                   "where the file gives none")
    au.add_argument("--no-proxy", action="store_true", help="use the last whole-product proxy results, not a new run")
    px = sub.add_parser("proxies")
    px.add_argument("--judge", choices=quality_judges)
    px.add_argument("--all", action="store_true", help="the whole product, as an audit measures it, not the change")
    a = sub.add_parser("approve")
    a.add_argument("file", help="the file the person said yes to — a mock, a motion study, the copy, the built "
                                "screen beside its mock")
    a.add_argument("--kind", required=True, choices=list(KINDS_BEFORE + KINDS_AFTER))
    a.add_argument("--note")
    dc = sub.add_parser("decision")
    dc.add_argument("text")
    t = sub.add_parser("target")
    t.add_argument("--where", required=True, help="where it ran: a browser at localhost:3000, a simulator, a device")
    t.add_argument("--build", required=True, help="which build: dev, production, a branch or commit")
    t.add_argument("--health-exit", type=int, help="the health check's exit status")
    t.add_argument("--note")
    so = sub.add_parser("signoff")
    so.add_argument("text", help="what the person judged on the target and said yes to, in their words")
    u = sub.add_parser("unverified")
    u.add_argument("--hook", action="store_true", help="as the Stop hook: read the event on stdin, ask once")
    f = sub.add_parser("finding")
    f.add_argument("text")
    f.add_argument("--route", required=True, choices=ROUTES)
    f.add_argument("--source", choices=["person", "agent"], default="person",
                   help="who found it: the person (the default) or the agent during the task")
    f.add_argument("--about", choices=AREAS, help="what the lesson is about, so a repeated area shows in calibration")
    f.add_argument("--judge", choices=rubric_owners(), help="the agent that looked at it, whose rubric a rubric "
                                                            "lesson teaches")
    f.add_argument("--caught", choices=["yes", "no"])
    f.add_argument("--edit", help="the file the lesson's edit landed in, when it was made before "
                                   "the lesson was recorded")
    f.add_argument("--for-run", type=int, help="recorded after the code it led to ran on the target: that run's number, "
                                               "as `target` printed it — it closes the gap before that run")
    d = sub.add_parser("dispute")
    d.add_argument("judge", choices=rubric_owners())
    d.add_argument("text")
    d.add_argument("--about", choices=AREAS)
    d.add_argument("--edit", help="the file the lesson's edit landed in, when it was made before "
                                   "the lesson was recorded")
    d.add_argument("--source", choices=["agent", "person"], default="agent",
                   help="who raised the false alarm: the agent (the default) or the person")
    k = sub.add_parser("kitdiff")
    k.add_argument("out", help="where to write the diff the person reads before their kit yes")
    n = sub.add_parser("decline")
    n.add_argument("file", help="the draft the person said no to — a UX brief, an option, a mock, a motion study, the "
                                "copy, the built screen beside its mock")
    n.add_argument("text", help="what the person said, in their words")
    n.add_argument("--kind", required=True, choices=list(KINDS_BEFORE + KINDS_AFTER) + ["option"])
    n.add_argument("--about", required=True, choices=AREAS)
    n.add_argument("--route", required=True, choices=ROUTES,
                   help="where the lesson goes — most often rubric, with --judge ui-designer or ux-designer")
    n.add_argument("--judge", choices=rubric_owners(), help="the agent whose rubric learns it")
    n.add_argument("--edit", help="the file the lesson's edit landed in, when it was made before "
                                   "the lesson was recorded")
    for name in ("status", "finish", "calibration", "doctor"):
        sub.add_parser(name)
    args = parser.parse_args()
    return {"start": cmd_start, "run": cmd_run, "review": cmd_review, "approve": cmd_approve,
            "decision": cmd_decision, "target": cmd_target, "signoff": cmd_signoff, "finding": cmd_finding,
            "decline": cmd_decline, "kitdiff": cmd_kitdiff,
            "dispute": cmd_dispute, "status": cmd_status, "finish": cmd_finish, "calibration": cmd_calibration,
            "doctor": cmd_doctor, "unverified": cmd_unverified, "accept": cmd_accept, "taste": cmd_taste,
            "rate": cmd_rate, "weight": cmd_weight, "audit": cmd_audit, "proxies": cmd_proxies,
            "nits-fixed": cmd_nits_fixed, "delta": cmd_delta, "selfcheck": cmd_selfcheck,
            "ask": cmd_ask}[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
