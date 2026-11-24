#!/usr/bin/env python3
"""The code-reviewer judge's measured proxies, on the change against HEAD: what a reviewer otherwise judges by eye, as
numbers with a range. A proxy outside its range caps its quality dimension at 2; it never fails a run.

    python3 .agents/skills/verify-change/scripts/code_proxies.py                 # the change against HEAD
    python3 .agents/skills/verify-change/scripts/code_proxies.py --all           # every source: the audit
    python3 .agents/skills/verify-change/scripts/code_proxies.py --save-baseline # this tree's warnings and size as the baseline
    python3 .agents/skills/verify-change/scripts/code_proxies.py --log L         # a build log other than the newest kept
    python3 .agents/skills/verify-change/scripts/code_proxies.py --self-test

A review scores the change, an audit the product: bare, only the functions the diff against HEAD touches are measured
(a new file: all of its functions), the warnings new since the baseline, and the changed sources; with --all, every
function in the project's own sources, every warning in the build log, and every source. Measures, by dimension (the
keys of .agents/evals/weights.json):
  simplicity  the longest changed function, in lines (at most 60), and its deepest nesting of control blocks (at most
              4) — [J] ranges, the common review limits; a test file's functions count too
  fit         new warnings in the project's own sources (none), in the `file:line[:col]: warning: …` form compilers and
              most linters print, from the newest build log quiet.py kept in .cache/harness/logs/, against the
              baseline's warnings, else those in changed files
  robustness  the sizes SIZE_COMMAND reports, when the project sets one: each part's share of its budget (at most 90 %)
              and its growth since the baseline (at most the part's own limit) — [J] ranges; no command, not measured
  tests       changed sources no test touches — a test names them on a `host-sources:` comment line, or includes or
              imports them; the paths only the target can run (TARGET_ONLY_PATHS) left out; no test, not measured
The languages are CODE_LANGS in .agents/project.py — "c", "cpp", "python", "js", "ts"; all five when it is unset. Brace
languages are read by their braces, Python by its indentation.
What is not measured is said so, and no metric is written for it. Writes .cache/harness/proxies/code-reviewer.json —
{"judge", "at", "scope": "change" | "product", "metrics": [{"dimension", "name", "value", "range": [lo, hi], "ok",
"where", "base"?, "offenders"?, "base_offenders"?}]} — and prints a summary. In the change's scope a metric carries its
value at HEAD (`base`): the changed functions as HEAD holds them, with the functions over a limit there and here by
file and name; none for warnings and growth, which are new by construction; the untested sources HEAD already had. So
verify.py caps only what the change made worse (.agents/HARNESS.md §12.5).
SIZE_COMMAND is optional: a command, as a list run from the repo root, that prints JSON
{"<part>": {"used": bytes, "budget": bytes or null, "growth": the most it may grow in bytes, or null}} for the build in
the tree. The baseline is .cache/harness/proxies/baseline/ (warnings.json, size.json); the first run with a build log or
a size saves one. Python 3.9+, standard library only. The project's GENERATED and VENDORED paths in .agents/project.py
are never the project's own sources, and the sources are those the code-reviewer reads — CODE_PATHS, or with none set,
every file but the docs, the harness and what is generated.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip()
            or ".")
PROXIES = ROOT / ".cache/harness/proxies"
BASELINE = PROXIES / "baseline"
LANG_EXT = {"c": (".c", ".h"), "cpp": (".cc", ".cpp", ".cxx", ".hh", ".hpp", ".hxx"), "python": (".py",),
            "js": (".js", ".jsx", ".mjs", ".cjs"), "ts": (".ts", ".tsx", ".mts", ".cts")}
C_FAMILY = LANG_EXT["c"] + LANG_EXT["cpp"]


def _settings():
    """The project's settings, .agents/project.py, or None outside the kit."""
    path = ROOT / ".agents/project.py"
    if not path.is_file():
        return None
    import importlib.util
    spec = importlib.util.spec_from_file_location("_code_proxies_project", path)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception:  # a settings file that does not load leaves the defaults
        return None
    return module


_P = _settings()
_tuple = lambda name: tuple(p for p in (getattr(_P, name, ()) or ()) if "*" not in p)  # prefixes; a glob never starts a path
# Never the project's own sources: what a tool writes, what it manages, and code kept as its makers ship it.
SKIP = tuple(dict.fromkeys(("build/", ".cache/", "managed_components/", "node_modules/") + _tuple("GENERATED")))
VENDORED = _tuple("VENDORED")
# What only the target can run — the board, its drivers, the display and input tasks, the app's start: no host test
# reaches it, so the tests proxy leaves it out.
TARGET_ONLY = tuple(getattr(_P, "TARGET_ONLY_PATHS", ()) or ()) + VENDORED
LANGS = tuple(l for l in (getattr(_P, "CODE_LANGS", ()) or tuple(LANG_EXT)) if l in LANG_EXT)
CODE_EXT = {e for l in LANGS for e in LANG_EXT[l]}
SIZE_COMMAND = tuple(getattr(_P, "SIZE_COMMAND", ()) or ())
TEST_DIRS = ("tests/", "test/", "__tests__/")
TEST_NAME = re.compile(r"(?:^test_.*\.py$|_test\.\w+$|\.(?:test|spec)\.\w+$)")
LONGEST, DEEPEST, SIZE_SHARE = 60, 4, 0.9


def is_own(path: str) -> bool:
    """The project's own code, as the code-reviewer reads it — project.is_code: CODE_PATHS, or with none set, anything
    that is not a doc, the harness or generated — never vendored."""
    if path.startswith(SKIP + VENDORED):
        return False
    return _P.is_code(path) if _P is not None and hasattr(_P, "is_code") else True


def is_test(path: str) -> bool:
    return path.startswith(TEST_DIRS) or "/__tests__/" in path or bool(TEST_NAME.search(Path(path).name))


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, errors="replace").stdout


# --- What changed -------------------------------------------------------------------------------------------------------

def changed_files() -> list:
    names = set(git("diff", "--name-only", "HEAD").split()) | set(git("ls-files", "--others", "--exclude-standard").split())
    return sorted(n for n in names if Path(n).suffix in CODE_EXT and is_own(n) and (ROOT / n).is_file())


def all_sources() -> list:
    """Every source of the project's own, in its languages — tracked or new — vendored code left out."""
    names = set(git("ls-files").split()) | set(git("ls-files", "--others", "--exclude-standard").split())
    return sorted(n for n in names if Path(n).suffix in CODE_EXT and is_own(n) and (ROOT / n).is_file())


def changed_lines(path: str) -> set | None:
    """The new file's changed lines; None when the file is new (every line)."""
    if git("ls-files", "--", path).strip() == "":
        return None
    lines: set = set()
    for m in re.finditer(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", git("diff", "-U0", "HEAD", "--", path), re.M):
        start, count = int(m.group(1)), int(m.group(2) or 1)
        lines.update(range(start, start + max(count, 1)))
    return lines


# --- Functions in the brace languages: C, C++, JavaScript and TypeScript ------------------------------------------------

def blank(text: str, preprocessor: bool = True) -> str:
    """Comments, string and character literals (and in C, preprocessor lines) blanked to spaces, newlines kept."""
    out, i, n = list(text), 0, len(text)

    def wipe(a: int, b: int):
        for k in range(a, min(b, n)):
            if out[k] != "\n":
                out[k] = " "

    line_start = True
    while i < n:
        c = text[i]
        if preprocessor and line_start and c == "#":
            j = i
            while j < n and not (text[j] == "\n" and text[j - 1] != "\\"):
                j += 1
            wipe(i, j)
            i = j
            continue
        if c in " \t":
            i += 1
            continue
        line_start = c == "\n"
        if text.startswith("//", i):
            j = text.find("\n", i)
            j = n if j < 0 else j
            wipe(i, j)
            i = j
        elif text.startswith("/*", i):
            j = text.find("*/", i + 2)
            j = n if j < 0 else j + 2
            wipe(i, j)
            i = j
        elif c in "\"'" or (c == "`" and not preprocessor):
            j = i + 1
            while j < n and text[j] != c and (c == "`" or text[j] != "\n"):
                j += 2 if text[j] == "\\" else 1
            wipe(i + 1, j)
            i = j + 1
        else:
            i += 1
    return "".join(out)


QUALIFIERS = re.compile(r"(?:\s*(?:const|noexcept(?:\([^()]*\))?|override|final|mutable|volatile|&|&&|->\s*[\w:<>,\s*&]+))*\s*$")
TYPE_ANNOTATION = re.compile(r"\)\s*:\s*[\w.<>\[\]|&,\s?'\"]+$")  # TypeScript's return type after the parameters
CONTROL = re.compile(r"(?:\)|\belse|\bdo|\btry|\bfinally)\s*$")
KEYWORDS = {"if", "for", "while", "switch", "catch", "sizeof", "return", "function", "with", "new", "typeof", "await"}
ARROW = re.compile(r"(?:\b([A-Za-z_$][\w$]*)\s*[=:]\s*)?(?:async\s+)?(?:\([^()]*\)|[A-Za-z_$][\w$]*)\s*(?::[^=]+)?=>$")


def function_name(header: str, script: bool = False) -> str | None:
    """The name of the function whose body follows `header`, or None when the brace opens no function body. `script`:
    JavaScript or TypeScript, where an arrow opens a function and a return type may follow the parameters."""
    h = header.rstrip()
    if re.search(r"\b(namespace|class|struct|union|enum|interface)\b", h.split("(")[0]) or re.search(r"\breturn\b", h):
        return None
    if script:
        arrow = ARROW.search(h)
        if arrow:
            return arrow.group(1) or "(arrow)"
    if re.search(r"=\s*$", h):
        return None
    if not script:
        init = re.search(r"\)\s*:\s*[\w:]+\s*[({]", h)  # a constructor's initialiser list: cut at its colon
        if init:
            h = h[: init.start() + 1]
        h = QUALIFIERS.sub("", h)
    else:
        ts = TYPE_ANNOTATION.search(h)
        if ts:
            h = h[: ts.start() + 1]
    if not h.endswith(")"):
        return None
    depth, k = 0, len(h) - 1
    while k >= 0:
        depth += {")": 1, "(": -1}.get(h[k], 0)
        if depth == 0:
            break
        k -= 1
    m = re.search(r"(~?[A-Za-z_$][\w:~$]*|operator\s*\S+)\s*$", h[:k])
    if not m or m.group(1) in KEYWORDS:
        return None
    return m.group(1)


def brace_functions(text: str, script: bool = False) -> list:
    """[(name, first line, last line, nesting)] for every function body in a brace-language file."""
    code = blank(text, preprocessor=not script)
    found, stack, last_stop = [], [], 0
    fn = None  # [name, line, depth, deepest]
    for i, c in enumerate(code):
        if c in ";":
            last_stop = i + 1
        elif c == "{":
            header = code[last_stop:i]
            if not script and fn is None and re.search(r"\)\s*:[^;{}]*\w\s*$", header):
                stack.append("member")  # a constructor's member initialised with braces: the body is still to come
                continue
            if fn is None:
                name = function_name(header, script)
                if name:
                    line = code.count("\n", 0, last_stop + len(header) - len(header.lstrip())) + 1
                    fn = [name, line, 1, 1]
                    stack.append("fn")
                else:
                    stack.append("ns")
            elif CONTROL.search(header):
                fn[2] += 1
                fn[3] = max(fn[3], fn[2])
                stack.append("block")
            else:
                stack.append("init")
            last_stop = i + 1
        elif c == "}":
            kind = stack.pop() if stack else "ns"
            if kind == "member":
                continue
            if kind == "block" and fn:
                fn[2] -= 1
            elif kind == "fn" and fn:
                found.append((fn[0], fn[1], code.count("\n", 0, i) + 1, fn[3] - 1))
                fn = None
            last_stop = i + 1
    return found


# --- Functions in Python ------------------------------------------------------------------------------------------------

PY_DEF = re.compile(r"^(?:async\s+)?def\s+([A-Za-z_]\w*)\s*\(")
PY_CONTROL = re.compile(r"^(?:if|elif|else|for|while|try|except|finally|with|match|case|async\s+for|async\s+with)\b")


def python_lines(text: str) -> list:
    """Each line's (indent, text stripped), None for a blank or comment line or a line inside a triple-quoted string."""
    out, quote = [], None
    for line in text.split("\n"):
        s = line.strip()
        if quote:
            out.append(None)
            if s.count(quote) % 2:
                quote = None
            continue
        if not s or s.startswith("#"):
            out.append(None)
            continue
        for q in ('"""', "'''"):
            if s.count(q) % 2:
                quote = q
        out.append((len(line) - len(line.lstrip()), s))
    return out


def python_functions(text: str) -> list:
    """[(name, first line, last line, nesting)] for every def; nesting counts control blocks inside it."""
    lines, found = python_lines(text), []
    for k, item in enumerate(lines):
        m = PY_DEF.match(item[1]) if item else None
        if not m:
            continue
        indent, last, stack, deepest = item[0], k, [], 0
        for j in range(k + 1, len(lines)):
            if lines[j] is None:
                continue
            ind, s = lines[j]
            if ind <= indent:
                break
            last = j
            while stack and ind <= stack[-1]:
                stack.pop()
            if PY_CONTROL.match(s):
                stack.append(ind)
                deepest = max(deepest, len(stack))
        found.append((m.group(1), k + 1, last + 1, deepest))
    return found


def functions(text: str, path: str = "x.cpp") -> list:
    """[(name, first line, last line, nesting)] for the file's language, by its extension."""
    ext = Path(path).suffix
    if ext in LANG_EXT["python"]:
        return python_functions(text)
    return brace_functions(text, script=ext in LANG_EXT["js"] + LANG_EXT["ts"])


# --- Warnings -----------------------------------------------------------------------------------------------------------

WARNING = re.compile(r"^(?P<path>[^\s:][^:]*):(?P<line>\d+):(?:\d+:)? warning: (?P<msg>.*?)(?: \[(?P<flag>-W[^\]]+)\])?$", re.M)


def project_path(path: str, root: str | None = None, vendored: tuple | None = None) -> str | None:
    """A warning's file as the repo names it, or None when it is not the project's own source: outside the repo, or
    generated, managed or vendored."""
    root = (root or str(ROOT)).rstrip("/") + "/"
    if path.startswith(root):
        rel = path[len(root):]
    elif not path.startswith("/"):
        rel = os.path.normpath(path)
    else:
        return None
    if rel.startswith(SKIP + (VENDORED if vendored is None else vendored)) or "/managed_components/" in "/" + rel:
        return None
    return rel


def warnings_in(log: str, root: str | None = None, vendored: tuple | None = None) -> list:
    out = []
    for m in WARNING.finditer(log):
        p = project_path(m.group("path"), root, vendored)
        if p:
            out.append({"file": p, "line": int(m.group("line")), "key": f"{p}: {m.group('msg')} [{m.group('flag') or ''}]"})
    return out


def newest_build_log() -> Path | None:
    """The newest log quiet.py kept that holds a warning in the `file:line: warning:` form, or a build's progress."""
    logs = sorted(glob.glob(str(ROOT / ".cache/harness/logs/*.log")), key=os.path.getmtime, reverse=True)
    for path in logs[:40]:
        text = Path(path).read_text(errors="replace")
        if WARNING.search(text) or re.search(r"^\[\d+/\d+\]|build complete|built in", text, re.M | re.I):
            return Path(path)
    return None


# --- Size ---------------------------------------------------------------------------------------------------------------

def sizes(command: tuple) -> dict | None:
    """{part: {"used", "budget", "growth"}} from the project's SIZE_COMMAND, or None when it has none or it fails."""
    if not command or any(str(a).startswith("<") for a in command):
        return None
    try:
        proc = subprocess.run(list(command), cwd=ROOT, capture_output=True, text=True, timeout=300)
        data = json.loads(proc.stdout) if proc.returncode == 0 else None
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return None
    if not isinstance(data, dict):
        return None
    return {k: v for k, v in data.items() if isinstance(v, dict) and isinstance(v.get("used"), (int, float))}


def size_metrics(now: dict, base: dict | None, product: bool = False) -> list:
    """Each part's share of its budget, and its growth since the baseline against its own limit. In the change's
    scope the share carries the baseline's share as its base, and growth a base of 0 — it is new by construction."""
    out = []
    for part, s in sorted(now.items()):
        old = (base or {}).get(part) or {}
        if s.get("budget"):
            was = {"base": round(old["used"] / s["budget"], 4)} \
                if not product and isinstance(old.get("used"), (int, float)) else {}
            out.append(metric("robustness", f"{part}'s share of its budget", round(s["used"] / s["budget"], 4), 0,
                              SIZE_SHARE, f"{s['used']} of {s['budget']} bytes", **was))
        if base and part in base and s.get("growth") is not None:
            out.append(metric("robustness", f"{part} growth (bytes)", s["used"] - base[part]["used"], -10**12,
                              s["growth"], f"{base[part]['used']} → {s['used']} bytes",
                              **({} if product else {"base": 0})))
    return out


# --- Tests --------------------------------------------------------------------------------------------------------------

def imported(test: str, text: str, root: Path) -> set:
    """The repo paths a test names on a `host-sources:` line, includes (C, C++) or imports (Python, JS, TS)."""
    found: set = set()
    here = Path(test).parent

    def exists(rel) -> bool:
        return (root / rel).is_file()

    for m in re.finditer(r"^\s*(?://|#)\s*host-sources:(.*)$", text, re.M):
        for pattern in m.group(1).split():
            found.update(Path(p).relative_to(root).as_posix() for p in glob.glob(str(root / pattern)))
    for m in re.finditer(r'^\s*#include\s+"([^"]+)"', text, re.M):
        inc = m.group(1)
        beside = os.path.normpath(here / inc)
        if exists(beside):
            found.add(beside)
            continue
        for pattern in (f"**/include/**/{inc}", f"**/src/**/{inc}", f"**/{inc}"):
            hits = [p for p in glob.glob(str(root / pattern), recursive=True)
                    if not Path(p).relative_to(root).as_posix().startswith(SKIP)]
            if hits:
                found.update(Path(p).relative_to(root).as_posix() for p in hits)
                break
    for m in re.finditer(r"^\s*(?:from\s+(\.*[\w.]*)\s+import|import\s+([\w.]+)\s*$)", text, re.M):
        mod = m.group(1) or m.group(2)
        dots = len(mod) - len(mod.lstrip("."))
        parts = [p for p in mod.lstrip(".").split(".") if p]
        bases = [here.joinpath(*[".."] * (dots - 1))] if dots else [Path("."), Path("src"), here]
        for b in bases:
            for cand in ((Path(b, *parts).with_suffix(".py"),) if parts else ()) + (Path(b, *parts, "__init__.py"),):
                if exists(os.path.normpath(cand)):
                    found.add(os.path.normpath(cand))
    for m in re.finditer(r"""(?:\bfrom\s+|\bimport\s*\(\s*|\brequire\s*\(\s*|^\s*import\s+)['"](\.{1,2}/[^'"]+)['"]""",
                         text, re.M):
        rel = os.path.normpath(here / m.group(1))
        for cand in [rel] + [rel + e for e in (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs")] + \
                [os.path.join(rel, "index" + e) for e in (".ts", ".tsx", ".js", ".jsx")]:
            if exists(cand):
                found.add(cand)
                break
    return found


def host_tested(tests: list, root: Path = ROOT) -> set:
    """Every repo path a test compiles, includes or imports."""
    touched: set = set()
    for test in tests:
        touched |= imported(test, (root / test).read_text(errors="replace"), root)
    return touched


# --- The proxies --------------------------------------------------------------------------------------------------------

def metric(dimension: str, name: str, value: float, lo: float, hi: float, where: str, **base) -> dict:
    """A metric; `base`, in the change's scope, is its value at HEAD (`base`) and what was out of range there
    (`base_offenders`, beside this tree's `offenders`), so verify.py caps only what the change made worse."""
    return {"dimension": dimension, "name": name, "value": value, "range": [lo, hi], "ok": lo <= value <= hi,
            "where": where, **base}


def at_head(path: str) -> str | None:
    """The file as HEAD holds it; None when HEAD does not have it."""
    proc = subprocess.run(["git", "show", f"HEAD:{path}"], cwd=ROOT, capture_output=True, text=True, errors="replace")
    return proc.stdout if proc.returncode == 0 else None


def over_limits(path: str, text: str | None) -> tuple:
    """({"path name": lines} over LONGEST, {"path name": nesting} over DEEPEST, {"path name": (lines, nesting)}) for
    every function in a file — the places the simplicity metrics name."""
    longer, deeper, every = {}, {}, {}
    for name, first, last, nest in functions(text or "", path):
        key = f"{path} {name}"
        size = last - first + 1
        every[key] = (max(size, every.get(key, (0, 0))[0]), max(nest, every.get(key, (0, 0))[1]))
        if size > LONGEST:
            longer[key] = max(size, longer.get(key, 0))
        if nest > DEEPEST:
            deeper[key] = max(nest, deeper.get(key, 0))
    return longer, deeper, every


def measure(save_baseline: bool, log_file: Path | None = None, product: bool = False) -> tuple:
    metrics, notes = [], []
    files = all_sources() if product else changed_files()
    # Simplicity: the changed functions (the audit: every function).
    changed_fns = []
    for f in files:
        text = (ROOT / f).read_text(errors="replace")
        lines = None if product else changed_lines(f)
        for name, first, last, nest in functions(text, f):
            if lines is None or any(first <= n <= last for n in lines):
                changed_fns.append((f, name, first, last, nest))
    if changed_fns:
        by_len = sorted(changed_fns, key=lambda t: t[3] - t[2], reverse=True)
        by_nest = sorted(changed_fns, key=lambda t: t[4], reverse=True)
        long_base, deep_base = {}, {}
        if not product:
            # The base: each changed function as HEAD holds it, by file and name — a function already over a limit
            # there and no worse is carried debt; a new one, or one the change made longer or deeper, is not.
            heads = {f: over_limits(f, at_head(f)) for f in {t[0] for t in changed_fns}}
            keys = {f"{t[0]} {t[1]}" for t in changed_fns}
            was = [heads[k.split(" ", 1)[0]][2][k] for k in keys if k in heads[k.split(" ", 1)[0]][2]]
            long_base = {"base": max((w[0] for w in was), default=None),
                         "offenders": {f"{t[0]} {t[1]}": t[3] - t[2] + 1 for t in changed_fns
                                       if t[3] - t[2] + 1 > LONGEST},
                         "base_offenders": {k: v for h in heads.values() for k, v in h[0].items()}}
            deep_base = {"base": max((w[1] for w in was), default=None),
                         "offenders": {f"{t[0]} {t[1]}": t[4] for t in changed_fns if t[4] > DEEPEST},
                         "base_offenders": {k: v for h in heads.values() for k, v in h[1].items()}}
        f, name, first, last, _ = by_len[0]
        over = [t for t in by_len if t[3] - t[2] + 1 > LONGEST]
        metrics.append(metric("simplicity", "longest changed function (lines)", last - first + 1, 0, LONGEST,
                              f"{f}:{first} {name}; {len(over)} of {len(changed_fns)} changed functions over {LONGEST}: "
                              + ", ".join(f"{t[1]} {t[3] - t[2] + 1}" for t in over[:4]), **long_base))
        f, name, first, _, nest = by_nest[0]
        deep = [t for t in by_nest if t[4] > DEEPEST]
        metrics.append(metric("simplicity", "deepest nesting in a changed function", nest, 0, DEEPEST,
                              f"{f}:{first} {name}; {len(deep)} over {DEEPEST}", **deep_base))
    else:
        notes.append(f"simplicity: no changed function in {', '.join(LANGS)}")
    # Fit: new warnings.
    log = log_file or newest_build_log()
    current = warnings_in(log.read_text(errors="replace")) if log else []
    base_file = BASELINE / "warnings.json"
    if log is None:
        notes.append("fit: no build log in .cache/harness/logs/ — build through quiet.py to measure warnings")
    else:
        if product:
            new, against = current, "every warning in the log (the product)"
        elif base_file.is_file():
            known = set(json.loads(base_file.read_text()))
            new = [w for w in current if w["key"] not in known]
            against = "the baseline's"
        else:
            new = [w for w in current if w["file"] in files]
            against = "none in changed files"
        # Against the baseline the count is already what the change added: none at the base.
        metrics.append(metric("fit", "new warnings in the project's sources", len(new), 0, 0,
                              f"{log.name} against {against}: "
                              + ("; ".join(f"{w['file']}:{w['line']} {w['key'].split(': ', 1)[1][:80]}" for w in new[:3])
                                 or "none"), **({"base": 0} if against == "the baseline's" else {})))
    # Robustness: the sizes the project's own command reports.
    size = sizes(SIZE_COMMAND)
    size_file = BASELINE / "size.json"
    if size is None:
        notes.append("robustness: no SIZE_COMMAND in .agents/project.py, or it printed no sizes — not measured")
    else:
        base = json.loads(size_file.read_text()) if size_file.is_file() else None
        metrics += size_metrics(size, base, product)
        if base is None:
            notes.append("robustness: no size baseline yet — this build's sizes are saved as it")
            save_baseline = True
    # Tests: a test touches each changed source.
    tests = [f for f in all_sources() if is_test(f)]
    sources = [f for f in files if not is_test(f) and not f.startswith(TARGET_ONLY)]
    if not tests:
        notes.append("tests: no test among the project's sources — not measured")
    elif sources:
        touched = host_tested(tests)
        bare = [f for f in sources if f not in touched]
        # The base: a source HEAD already had, untested there — known only while no test changed.
        was = {} if product or any(is_test(f) for f in files) else {
            "base": None if not bare else sum(1 for f in bare if at_head(f) is not None),
            "offenders": {f: 1 for f in bare}, "base_offenders": {f: 1 for f in bare if at_head(f) is not None}}
        metrics.append(metric("tests", "changed sources no test touches", len(bare), 0, 0,
                              (", ".join(bare[:5])
                               or f"each of {len(sources)} is compiled, included or imported by a test"), **was))
    else:
        notes.append("tests: no changed source outside the tests and the target-only parts")
    if save_baseline:
        BASELINE.mkdir(parents=True, exist_ok=True)
        if log:
            base_file.write_text(json.dumps(sorted({w["key"] for w in current}), indent=1))
        if size:
            size_file.write_text(json.dumps(size, indent=1))
        notes.append(f"baseline saved: {BASELINE.relative_to(ROOT)}/")
    return metrics, notes, len(files), [f"{t[0]}:{t[2]} {t[1]}" for t in changed_fns]


def write(judge: str, metrics: list, scope: str = "change", in_scope: list | None = None) -> Path:
    """The results; `in_scope` names the functions measured — empty, the change is out of this judge's scope."""
    PROXIES.mkdir(parents=True, exist_ok=True)
    path = PROXIES / f"{judge}.json"
    at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    path.write_text(json.dumps({"judge": judge, "at": at, "scope": scope, "scope_what": "the functions the change "
                                "wrote in", "in_scope": in_scope or [], "metrics": metrics}, indent=1,
                               ensure_ascii=False) + "\n")
    return path


def self_test() -> int:
    failures, total = [], 0

    def check(ok: bool, what: str):
        nonlocal total
        total += 1
        if not ok:
            failures.append(what)

    src = '''#include "x.h"  // { not a brace
namespace a {
namespace {
struct S { int x; };
const char *kWords = "if (x) { y }";
int Flat(int x) { return x + 1; }
void Deep(int x)
{
    Box b{1, 2};
    if (x) {
        for (int i = 0; i < x; ++i) {
            while (true) {
                if (i) { break; }
            }
        }
    } else {
        auto f = [](int y) { return y; };
    }
}
}  // namespace
Thing::Thing(int v) : value_(v), other_{v}
{
    if (v) {
        value_ = 0;
    }
}
bool Thing::Ok() const noexcept { return true; }
}  // namespace a
'''
    fns = {name: (first, last, nest) for name, first, last, nest in functions(src, "a.cpp")}
    check(set(fns) == {"Flat", "Deep", "Thing::Thing", "Thing::Ok"}, f"every function body, no struct or namespace: {sorted(fns)}")
    check(fns.get("Flat") == (6, 6, 0), f"a one-line function: 1 line, nesting 0 — {fns.get('Flat')}")
    check(fns.get("Deep", (0, 0, 0))[2] == 4, f"Deep nests if > for > while > if: 4, an initialiser and a lambda's body "
                                              f"aside — {fns.get('Deep')}")
    check(fns.get("Deep", (0, 0, 0))[:2] == (7, 19), f"Deep runs from its name to its brace — {fns.get('Deep')}")
    check(fns.get("Thing::Thing", (0, 0, 0))[2] == 1, "a constructor with an initialiser list is one function")
    ts = '''import { x } from "./x";
const label = `a ${"{"} b`;
export function load(id: string): Promise<Item> {
  if (id) {
    for (const k of keys) {
      if (k) { return k; }
    }
  }
  return fetch(id);
}
export const save = async (item: Item) => {
  const body = { id: item.id };
  return post(body);
};
class Store {
  get(key: string): string { return this.map[key]; }
}
'''
    tfns = {name: (first, last, nest) for name, first, last, nest in functions(ts, "a.ts")}
    check(set(tfns) == {"load", "save", "get"}, f"TypeScript: a function, an arrow and a method: {sorted(tfns)}")
    check(tfns.get("load") == (3, 10, 3), f"load runs 3–10 and nests if > for > if: {tfns.get('load')}")
    check(tfns.get("save", (0, 0, 9))[2] == 0, f"an object literal in an arrow is no nesting: {tfns.get('save')}")
    py = '''import os


def flat(x):
    return x + 1


class C:
    def deep(self, x):
        """A docstring with def fake(): inside."""
        if x:
            for i in x:
                try:
                    pass
                except ValueError:
                    pass
        else:
            return 0
        return 1
'''
    pfns = {name: (first, last, nest) for name, first, last, nest in functions(py, "a.py")}
    check(set(pfns) == {"flat", "deep"}, f"Python: two defs, none in the docstring: {sorted(pfns)}")
    check(pfns.get("deep") == (9, 19, 3), f"deep runs 9–19 and nests if > for > try: {pfns.get('deep')}")
    at = ":12:5: "  # a compiler's file, line and column, kept apart so the source holds no file:line reference
    log = (f"/Users/x/repo/src/ui/ui.cpp{at}warning: unused variable 'y' [-Wunused-variable]\n"
           f"/Users/x/repo/build/generated/gen.c{at}warning: deprecated [-Wdeprecated]\n"
           f"/Users/x/repo/third_party/zlib/z.c{at}warning: shadow [-Wshadow]\n"
           f"/opt/sdk/include/sys.h{at}warning: outside [-Wother]\n"
           "[12/40] Building CXX object\n")
    ws = warnings_in(log, root="/Users/x/repo", vendored=("third_party/",))
    check([w["file"] for w in ws] == ["src/ui/ui.cpp"], f"only the project's own warnings count: {ws}")
    check(ws and ws[0]["key"] == "src/ui/ui.cpp: unused variable 'y' [-Wunused-variable]", "a warning's key has no line")
    m = metric("tests", "x", 1, 0, 0, "w")
    check(m["ok"] is False and m["range"] == [0, 0], "a value past its range is not ok")
    check(project_path("/a/b/main/main.cpp", root="/a/b", vendored=()) == "main/main.cpp", "a file in the repo is the project's")
    check(sizes(()) is None and sizes(("<the size command>",)) is None, "no SIZE_COMMAND, or a placeholder: no size")
    sm = {x["name"]: x for x in size_metrics({"app": {"used": 950, "budget": 1000, "growth": 40}},
                                              {"app": {"used": 900}})}
    check(not sm["app's share of its budget"]["ok"] and not sm["app growth (bytes)"]["ok"],
          f"95 % of a budget and 50 bytes over a 40-byte growth are out of range: {sm}")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for rel, body in (("src/a.c", ""), ("src/b/util.py", ""), ("src/b/__init__.py", ""), ("web/c.ts", ""),
                          ("tests/a_test.c", '#include "../src/a.c"\n'),
                          ("tests/test_b.py", "from src.b.util import f\n"),
                          ("web/c.test.ts", 'import { c } from "./c";\n')):
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            (root / rel).write_text(body)
        got = host_tested(["tests/a_test.c", "tests/test_b.py", "web/c.test.ts"], root)
        check({"src/a.c", "src/b/util.py", "web/c.ts"} <= got, f"a C include, a Python import and a TS import: {sorted(got)}")
    check(is_test("tests/x.cpp") and is_test("src/a.spec.ts") and is_test("test_x.py") and not is_test("src/x.ts"),
          "tests by folder and by name")
    # The base: the places over a limit, by file and function, as HEAD holds them.
    big = "void Big()\n{\n" + "    x();\n" * 70 + "}\nvoid Small() { y(); }\n"
    longer, deeper, every = over_limits("a.cpp", big)
    check(longer == {"a.cpp Big": 73} and not deeper and set(every) == {"a.cpp Big", "a.cpp Small"},
          f"a function over the limit is named by file and name: {longer}, {sorted(every)}")
    check(over_limits("a.cpp", None) == ({}, {}, {}), "a file HEAD does not have has nothing at the base")
    m = metric("simplicity", "x", 73, 0, 60, "w", base=73, offenders={"a.cpp Big": 73}, base_offenders=longer)
    check(m["base"] == 73 and m["offenders"] == m["base_offenders"], "a metric carries its base and its places")
    sm = size_metrics({"app": {"used": 95, "budget": 100, "growth": 10}}, {"app": {"used": 90}})
    check([(x["name"], x.get("base")) for x in sm] == [("app's share of its budget", 0.9), ("app growth (bytes)", 0)],
          f"a size's share carries the baseline's as its base, its growth a base of 0: {sm}")
    for f in failures:
        print(f"FAIL  {f}")
    print(f"code_proxies self-test: {total - len(failures)} of {total} checks pass")
    return 1 if failures else 0


def summary(judge: str, metrics: list, notes: list, extra: str) -> None:
    outside = [m for m in metrics if not m["ok"]]
    print(f"{judge}: {len(metrics)} metrics, {len(outside)} outside their range — {extra}")
    for m in metrics:
        lo, hi = m["range"]
        print(f"  {'ok ' if m['ok'] else 'OUT'} {m['dimension']}: {m['name']} = {m['value']:g} "
              f"(range {lo:g}–{hi:g}) — {m['where'][:170]}")
    for n in notes:
        print(f"  - {n}")


def main(argv: list) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--save-baseline", action="store_true", help="save this tree's warnings and sizes as the baseline")
    parser.add_argument("--log", help="the build log to read warnings from (the newest in .cache/harness/logs/)")
    parser.add_argument("--all", action="store_true", help="every source and function: the whole-product audit")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    metrics, notes, n_files, fns = measure(args.save_baseline, Path(args.log).resolve() if args.log else None, args.all)
    scope = "product" if args.all else "change"
    path = write("code-reviewer", metrics, scope, fns)
    what = "" if args.all else "changed "
    summary(f"code-reviewer ({scope})", metrics, notes, f"{n_files} {what}source files, {len(fns)} {what}functions; "
                                                       f"{path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
