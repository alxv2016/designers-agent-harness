#!/usr/bin/env python3
"""The verify-change loop's fixed part: picks the checks and the judges a change needs from the files it touches, runs
the checks in parallel, keeps the task's state, records the judges' verdicts and the person's approvals, counts failed
attempts, stops at the retry limit, and refuses a hand-over while anything is open (.agents/HARNESS.md §4–§5;
docs/AGENT_HARNESS.md §10).

    verify.py start "<task>"          # a new task: state reset, the last one kept in history/
    verify.py run [--only docs,harness,design,<the project's checks>]
    verify.py review <judge> pass|blocking [--note TEXT]
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
    verify.py status | finish | calibration | doctor
    verify.py unverified [--hook]     # the tree changed since the last run? --hook: the agents' Stop hook

Run it with python3 from the repo root. The project's checks, judges and gates come from .agents/project.py.

State is .cache/harness/task.json (git-ignored). `finding`, `decline`, `dispute` and `approve` also append to
.agents/evals/judgements.jsonl (committed), which `calibration` reads — never put a token, a key, a password or a
person's data in their text. `finish` refuses a lesson whose route's edit is not in the change — made after it was
recorded, or named with --edit — and a rubric lesson that added no learned item to that agent's rubric.

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
           "rubrics": check_rubrics, "ux": check_ux,
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
    counted = any(not results[c]["ok"] for c in COUNTED if c in results)
    task["failures"] = 0 if ok else task["failures"] + 1 if counted else task["failures"]
    task["runs"].append({"n": n, "at": now(), "ok": ok,
                         "checks": {c: {k: v for k, v in r.items() if k != "tail"} for c, r in results.items()},
                         "files": files, "gated": gated_contents(files), "fingerprint": tree_fingerprint(),
                         "debug": bool(hits), "partial": bool(only),
                         "seconds": round(time.time() - t0)})
    save(task)
    print(f"run {n}: {'PASS' if ok else 'FAIL'} in {time.time() - t0:.0f} s — logs in {run_dir.relative_to(ROOT)}")
    if not ok and not counted:
        print(f"failed, not counted — only {', '.join(sorted(COUNTED)) or 'no check'} count toward the retry limit "
              "(\"counts\": True in .agents/project.py); fix and run again")
        return 1
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
    save(task)  # a blocking verdict is fixed and asked again; it does not count toward the retry limit
    print(f"review recorded: {args.judge} {args.verdict}")
    if args.verdict == "blocking":
        print(f"each item {args.judge} raised that you fix is a catch: verify.py finding \"<what>\" --source agent "
              f"--route <route> --judge {args.judge} --caught yes; one that was not a problem: verify.py dispute")
        return 1
    return 0


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
    no = next((d for d in task.get("declines", []) if d["sha"] == digest), None)
    if no:
        print(f"approve: the person said no to {path.name} as it is — \"{no['text']}\"; draw the next draft and show "
              "them that", file=sys.stderr)
        return 1
    task["approvals"].append({"kind": args.kind, "file": str(path.resolve()), "sha": digest, "note": args.note,
                              "at": now(), "code": gated_fingerprint(kind=args.kind)})
    save(task)
    # Logged too, so calibration can set the person's yeses against their noes per kind of draft
    log_judgement({"kind": "approval", "draft": args.kind, "file": path.name, "source": "person", "route": "none"})
    print(f"approval recorded: {args.kind} {path.name} ({digest})")
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
    task = load() or new_task("(unnamed)")
    entry = {"kind": "decline", "draft": args.kind, "file": path.name, "sha": digest, "source": "person",
             "text": args.text, "about": args.about, "route": args.route, "judge": args.judge, "caught": None,
             "edit": args.edit}
    task.setdefault("declines", []).append({**entry, **lesson_snapshot(args.route, args.judge)})
    save(task)
    log_judgement(entry)
    print(f"no recorded: {args.kind} {path.name} ({args.about}) → route: {args.route}"
          + (f" ({args.judge}'s rubric)" if args.judge else "")
          + " — make the edit the route names in this change, then draw the next draft, n + 1")
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
    # Every run on the target, with how many findings and decisions were recorded by then — finish reads it
    # (unrecorded_redeploys).
    task.setdefault("target_log", []).append({"at": task["target"]["at"], "deployed": task["target"]["deployed"],
                                              "findings": len(task.get("findings", [])),
                                              "decisions": len(task.get("decisions", []))})
    save(task)
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
    task["findings"].append({**entry, **lesson_snapshot(args.route, args.judge)})
    save(task)
    log_judgement(entry)
    print(f"finding recorded ({args.source}) → route: {args.route} — make the edit the route names in this change "
          "(verify-change → Recording what was learned)")
    return 0


def cmd_dispute(args: argparse.Namespace) -> int:
    entry = {"kind": "false-alarm", "source": args.source, "text": args.text, "about": args.about, "route": "rubric",
             "judge": args.judge, "caught": None, "edit": args.edit}
    task = load() or new_task("(unnamed)")
    task["findings"].append({**entry, **lesson_snapshot("rubric", args.judge)})
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
                problems.append(f"{what} changed with no yes from the person on the change — show them its diff "
                                "(git diff -- .agents/skills .agents/agents > <scratch>/kit.diff) and record their "
                                "yes: "
                                "verify.py approve <that file> --kind kit; a request or a tool's own approval of an "
                                "edit is not their yes (AGENTS.md rule 9)")
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
    cases = cases + scopes + redeploys + lessons + rubrics + [("requires", "", ""), ("new rows", "", ""),
                                                               ("judgements", "", ""), ("draft stats", "", ""),
                                                               ("areas", "", "")]
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
            "decline": cmd_decline,
            "dispute": cmd_dispute, "status": cmd_status, "finish": cmd_finish, "calibration": cmd_calibration,
            "doctor": cmd_doctor, "unverified": cmd_unverified}[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
