#!/usr/bin/env python3
"""The verify-change loop's fixed part: picks the checks and the judges a change needs from the files it touches, runs
the checks in parallel, keeps the task's state, records the judges' verdicts and the person's approvals, counts failed
attempts, stops at the retry limit, and refuses a hand-over while anything is open (.agents/HARNESS.md §4–§5;
docs/AGENT_HARNESS.md §10).

    verify.py start "<task>"          # a new task: state reset, the last one kept in history/
    verify.py run [--only docs,harness,design,<the project's checks>]
    verify.py review <judge> pass|blocking [--note TEXT]
    verify.py approve <file> --kind ux|mock|motion|copy|built [--note TEXT]   # the person's yes, naming the file
    verify.py decision "<what the person decided>"   # settled for this task: the judges read it in `status`
    verify.py target --where "<where it ran>" --build "<which build>" [--health-exit N] [--note TEXT]
    verify.py signoff "<what the person judged on the target>"   # their yes on the target, in their words
    verify.py finding "<what was seen or learned>" --route test|rubric|guard|skill|doc|open-item|none
                      [--source person|agent] [--judge JUDGE --caught yes|no]
    verify.py dispute <judge> "<what the judge flagged that was not a problem>" [--source agent|person]
    verify.py status | finish | calibration | doctor
    verify.py unverified [--hook]     # the tree changed since the last run? --hook: the agents' Stop hook

Run it with python3 from the repo root. The project's checks, judges and gates come from .agents/project.py.

State is .cache/harness/task.json (git-ignored). `finding` and `dispute` also append to .agents/evals/judgements.jsonl
(committed), which `calibration` reads — never put a token, a key, a password or a person's data in their text.

Exit status: 0 pass, 1 a check failed or `finish` found something open, 2 usage, 3 the retry limit is reached — stop
and ask the person.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / ".agents"))
import project  # noqa: E402 — the project's facts: .agents/project.py

STATE = ROOT / ".cache/harness"
TASK = STATE / "task.json"
JUDGEMENTS = ROOT / ".agents/evals/judgements.jsonl"
MAX_FAILURES = 3
SKILLS = ".agents/skills"
DOC_SCRIPTS = f"{SKILLS}/docs-authoring-and-sync/scripts"
TOKEN_CHECK = f"{SKILLS}/design-system/scripts/token_check.py"
DESIGN_CHECK = f"{SKILLS}/design-system/scripts/design_check.py"
A11Y_SKILL = f"{SKILLS}/accessibility/"
A11Y_SCRIPTS = f"{A11Y_SKILL}scripts"
HARNESS_TESTS = (".agents/hooks/guard.py", ".agents/hooks/untrusted.py", ".agents/skills/verify-change/scripts/verify.py")
ROUTES = ["test", "rubric", "guard", "skill", "doc", "open-item", "none"]
KINDS_BEFORE = ("ux", "mock", "motion", "copy")  # a draft, approved before the build; `ux` is the UX brief
KINDS_AFTER = ("built",)                   # the built thing beside its draft, approved after
KIND_NAMES = {"ux": "UX brief", "mock": "mock", "motion": "motion study", "copy": "copy",
              "built": "built screen beside its mock"}
# The person's word that waives a gate: no visible change waives them all; a design they gave waives the draft.
NO_VISIBLE_CHANGE = "no visible change"
DESIGN_GIVEN = "design given"

# --- Which files call for which check and which judge (.agents/HARNESS.md §4) -----------------------------------
HARNESS = (".agents/hooks/", ".agents/githooks/", ".agents/project.py", ".agents/skills/verify-change/",
           ".claude/settings.json", ".codex/", ".github/")


def is_kit_or_doc(f: str) -> bool:
    return project.is_doc(f) or f.startswith(".agents/")


def is_design(f: str) -> bool:
    """The design brief, the token files and the UI: what the design check and the ui-designer cover."""
    return f == project.DESIGN_FILE or project.matches(f, project.UI_PATHS + project.TOKEN_FILES)


JUDGES = {
    # Docs describe the code, and the kit is kept true like a doc: both call for the doc-reviewer.
    "doc-reviewer": lambda f: is_kit_or_doc(f) or project.is_code(f),
    "code-reviewer": lambda f: project.is_code(f),
    "ui-designer": lambda f: is_design(f),
    **{name: (lambda f, p=paths: project.matches(f, p)) for name, paths in project.JUDGES.items()},
}


def judge_ready(name: str) -> bool:
    return (ROOT / ".agents/agents" / f"{name}.md").is_file()


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout


def changed_files() -> list[str]:
    files = git("diff", "--name-only", "HEAD").splitlines() + git("ls-files", "--others", "--exclude-standard") \
        .splitlines()
    return sorted(set(files))


def content_hash(paths, salt: str = "") -> str:
    h = hashlib.sha256(salt.encode())
    for f in paths:
        p = ROOT / f
        h.update(f.encode() + b"\0" + (p.read_bytes() if p.is_file() else b"(deleted)") + b"\0")
    return h.hexdigest()[:16]


def judge_fingerprint(judge: str, files: list[str] | None = None) -> str:
    """The content of the changed files a judge reads, so a change elsewhere leaves its review standing."""
    return content_hash([f for f in (files if files is not None else changed_files()) if JUDGES[judge](f)], judge)


def tree_fingerprint() -> str:
    """HEAD and every changed file's content — the same whether a file is staged, unstaged or untracked."""
    return content_hash(changed_files(), git("rev-parse", "HEAD"))


def deployed_fingerprint() -> str:
    """HEAD and the changed files that reach the target — everything but docs and the harness; a doc edit leaves a
    sign-off standing."""
    return content_hash([f for f in changed_files() if not is_kit_or_doc(f) and not f.startswith(HARNESS)],
                        git("rev-parse", "HEAD"))


def gated_fingerprint(files: list[str] | None = None) -> str:
    """The content of the changed files any gate covers — what a `built` yes saw."""
    paths = tuple(p for _, ps, _ in project.GATES for p in ps)
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


def load() -> dict:
    try:
        return json.loads(TASK.read_text())
    except (OSError, ValueError):
        return {}


def save(task: dict) -> None:
    STATE.mkdir(parents=True, exist_ok=True)
    TASK.write_text(json.dumps(task, indent=2))


def new_task(name: str) -> dict:
    return {"task": name, "started": now(), "commit": git("rev-parse", "--short", "HEAD").strip(), "failures": 0,
            "runs": [], "reviews": {}, "approvals": [], "decisions": [], "target": None, "signoffs": [],
            "findings": [], "gated_at_start": gated_contents()}


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


def scope_of(text: str) -> str | None:
    """`metadata: scope:` (or a top-level `scope:`) from a SKILL.md's or an agent's frontmatter."""
    m = re.match(r"---\n(.*?)\n---", text, re.S)
    if not m:
        return None
    s = re.search(r"^(?:metadata:\s*\n(?:[ \t]+\S.*\n)*?[ \t]+|)scope:\s*(\S+)", m.group(1) + "\n", re.M)
    return s.group(1).strip("'\"") if s else None


def requires_of(text: str) -> list[str]:
    """`metadata: requires: [a, b]` from an agent's frontmatter — the skills a portable agent needs."""
    m = re.match(r"---\n(.*?)\n---", text, re.S)
    r = re.search(r"^[ \t]+requires:\s*\[([^\]]*)\]", m.group(1), re.M) if m else None
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


BUILTIN = {"docs": check_docs, "harness": check_harness, "design": check_design, "a11y": check_a11y,
           "motion": check_motion, "touch": check_touch, "layout": check_layout,
           "typography": check_typography, "ux": check_ux,
           "esp-idf": check_esp_idf, "react-vite": check_react_vite, "secrets": check_secrets, "scope": check_scope}
CHECKS = {**BUILTIN, **{name: project_check(name) for name in project.CHECKS}}
WAIT = {name for name, spec in project.CHECKS.items() if spec.get("wait")}


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
    old = load()
    if old.get("runs"):
        hist = STATE / "history"
        hist.mkdir(parents=True, exist_ok=True)
        (hist / f"{old['started'].replace(':', '')}.json").write_text(json.dumps(old, indent=2))
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
    task["failures"] = 0 if ok else task["failures"] + 1
    task["runs"].append({"n": n, "at": now(), "ok": ok,
                         "checks": {c: {k: v for k, v in r.items() if k != "tail"} for c, r in results.items()},
                         "files": files, "gated": gated_contents(files), "fingerprint": tree_fingerprint(),
                         "debug": bool(hits),
                         "seconds": round(time.time() - t0)})
    save(task)
    print(f"run {n}: {'PASS' if ok else 'FAIL'} in {time.time() - t0:.0f} s — logs in {run_dir.relative_to(ROOT)}")
    if not ok:
        return stop_or_retry(task)
    judges = [j for j, wants in JUDGES.items() if judge_ready(j) and any(wants(f) for f in files)]
    if judges:
        print(f"next: the judges — {', '.join(judges)} (ask them in parallel; record each with `verify.py review`)")
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
    task = load() or new_task("(unnamed)")
    task["reviews"][args.judge] = {"verdict": args.verdict, "note": args.note,
                                   "fingerprint": judge_fingerprint(args.judge), "at": now()}
    if args.verdict == "blocking":
        task["failures"] += 1
    save(task)
    print(f"review recorded: {args.judge} {args.verdict}")
    return stop_or_retry(task) if args.verdict == "blocking" else 0


def cmd_approve(args: argparse.Namespace) -> int:
    """The person's yes to a draft — a mock, a motion study, the copy — or to the built thing beside it, recorded
    with the file's hash, so a file changed after the yes is not the one approved (.agents/HARNESS.md §9). Only the
    person's own words name the file; a request, a silence or a judge's pass is not a yes."""
    path = Path(args.file).expanduser()
    digest = file_hash(path)
    if digest is None:
        print(f"approve: no file at {path}", file=sys.stderr)
        return 2
    task = load() or new_task("(unnamed)")
    task["approvals"].append({"kind": args.kind, "file": str(path.resolve()), "sha": digest, "note": args.note,
                              "at": now(), "code": gated_fingerprint()})
    save(task)
    print(f"approval recorded: {args.kind} {path.name} ({digest})")
    return 0


def cmd_decision(args: argparse.Namespace) -> int:
    """The person's word on something a judge might flag — settled for this task. A rule meant to last goes into the
    doc that owns it as well."""
    task = load() or new_task("(unnamed)")
    task["decisions"].append({"text": args.text, "at": now()})
    save(task)
    print(f"decision recorded: {args.text} — the judges read it in `verify.py status`; a rule meant to last goes in "
          "its doc too")
    return 0


def cmd_target(args: argparse.Namespace) -> int:
    task = load() or new_task("(unnamed)")
    task["target"] = {"where": args.where, "build": args.build, "health_exit": args.health_exit, "note": args.note,
                      "at": now(), "deployed": deployed_fingerprint()}
    save(task)
    print(f"target recorded: {args.build} on {args.where}"
          + (f", health check exit {args.health_exit}" if args.health_exit is not None else ""))
    return 0


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
    task["signoffs"].append({"text": args.text, "at": now(), "deployed": target["deployed"]})
    save(task)
    print(f"sign-off recorded: {args.text} — the person's yes on the target, for the code as it ran at {target['at']}")
    return 0


def signoff_state(s: dict) -> str:
    return "" if s["deployed"] == deployed_fingerprint() else " — the code changed since"


def log_judgement(entry: dict) -> None:
    JUDGEMENTS.parent.mkdir(parents=True, exist_ok=True)
    entry = {"date": datetime.now().date().isoformat(), "task": load().get("task", "(unnamed)"),
             "commit": git("rev-parse", "--short", "HEAD").strip(), **entry}
    with JUDGEMENTS.open("a") as f:
        f.write(json.dumps(entry) + "\n")


def cmd_finding(args: argparse.Namespace) -> int:
    if args.judge and args.caught is None:
        print("--judge needs --caught yes|no", file=sys.stderr)
        return 2
    task = load() or new_task("(unnamed)")
    entry = {"kind": "finding", "source": args.source, "text": args.text, "route": args.route, "judge": args.judge,
             "caught": args.caught == "yes" if args.judge else None}
    task["findings"].append(entry)
    save(task)
    log_judgement(entry)
    print(f"finding recorded ({args.source}) → route: {args.route} — make the edit the route names in this change "
          "(verify-change → Recording what was learned)")
    return 0


def cmd_dispute(args: argparse.Namespace) -> int:
    entry = {"kind": "false-alarm", "source": args.source, "text": args.text, "route": "rubric", "judge": args.judge,
             "caught": None}
    task = load() or new_task("(unnamed)")
    task["findings"].append(entry)
    save(task)
    log_judgement(entry)
    print(f"false alarm recorded against {args.judge} → route: rubric — tighten the item it misread")
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
        if no_visible or not paths or not any(project.matches(f, paths) for f in files):
            continue
        touched = True
        first = first_build(task, paths)
        for kind in kinds:
            if kind in KINDS_BEFORE and design_given:
                continue
            yes = [a for a in task.get("approvals", []) if a["kind"] == kind]
            if not yes:
                problems.append(f"{what} changed with no yes from the person on its {KIND_NAMES[kind]} — verify.py approve "
                                f"<file> --kind {kind}, or their word: verify.py decision \"{NO_VISIBLE_CHANGE}: "
                                f"<why>\" (or \"{DESIGN_GIVEN}: <where>\" for a design they handed over)")
                continue
            a = yes[-1]
            name = Path(a["file"]).name
            if approval_state(a):
                problems.append(f"the approved {kind} {name}{approval_state(a)} — show the person the new file")
            elif kind in KINDS_AFTER and a.get("code") != gated_fingerprint(files):
                problems.append(f"the code changed after the person's yes on {name} — show them the built thing again")
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
    for judge, r in task["reviews"].items():
        stale = " — its files changed since" if judge in JUDGES and r["fingerprint"] != judge_fingerprint(judge) else ""
        print(f"review: {judge} {r['verdict']}" + (f" — {r['note']}" if r.get("note") else "") + stale)
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
    if debug_hits():
        open_items.append(f"a debug marker is in the tree — /{project.DEBUG_MARKERS}/ (.agents/project.py)")
    open_items += broken_invariants()
    open_items += gate_problems(task, files)
    for judge, wants in JUDGES.items():
        if judge_ready(judge) and any(wants(f) for f in files):
            r = task["reviews"].get(judge)
            if not r:
                open_items.append(f"no review recorded from {judge}")
            elif r["verdict"] != "pass":
                open_items.append(f"{judge} said blocking")
            elif r["fingerprint"] != judge_fingerprint(judge, files):
                open_items.append(f"{judge} reviewed an older version of its files")
    checks = last["checks"]
    target = task.get("target")
    print("## Verified")
    print(f"- Base: {task['commit']} + working tree, {len(files)} changed file(s)")
    for name, r in checks.items():
        print(f"- {name.capitalize()}: {'PASS' if r['ok'] else 'FAIL'} — {r['detail']}")
    if not checks:
        print("- Checks: none ran — no file a check covers changed")
    for judge, r in task["reviews"].items():
        print(f"- Review: {judge} {r['verdict']}" + (f" — {r['note']}" if r.get("note") else ""))
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
    routed = [f for f in task["findings"] if f["route"] != "none"]
    if routed:
        print("## Lessons routed (verify-change → Recording what was learned)")
        for f in routed:
            print(f"- {f['text']} → {f['route']}")
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
    for j in sorted(JUDGES):
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
        routes[r["route"]] = routes.get(r["route"], 0) + 1
    print("  by route: " + (", ".join(f"{k} {v}" for k, v in sorted(routes.items())) or "none yet"))
    return 0


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
    cases = cases + scopes + [("requires", "", "")]
    print(f"verify self-test: {len(cases) - bad}/{len(cases)} cases pass")
    return 1 if bad else 0


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
    v.add_argument("--note")
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
    f.add_argument("--judge", choices=sorted(JUDGES))
    f.add_argument("--caught", choices=["yes", "no"])
    d = sub.add_parser("dispute")
    d.add_argument("judge", choices=sorted(JUDGES))
    d.add_argument("text")
    d.add_argument("--source", choices=["agent", "person"], default="agent",
                   help="who raised the false alarm: the agent (the default) or the person")
    for name in ("status", "finish", "calibration", "doctor"):
        sub.add_parser(name)
    args = parser.parse_args()
    return {"start": cmd_start, "run": cmd_run, "review": cmd_review, "approve": cmd_approve,
            "decision": cmd_decision, "target": cmd_target, "signoff": cmd_signoff, "finding": cmd_finding,
            "dispute": cmd_dispute, "status": cmd_status, "finish": cmd_finish, "calibration": cmd_calibration,
            "doctor": cmd_doctor, "unverified": cmd_unverified}[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
