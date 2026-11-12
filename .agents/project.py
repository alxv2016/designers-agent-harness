"""The one file a project fills in. Everything else in the harness is generic and reads its project facts from here:
the guard (.agents/hooks/guard.py), the injection flag (.agents/hooks/untrusted.py), the pre-commit hook
(.agents/githooks/pre-commit) and the loop (.agents/skills/verify-change/scripts/verify.py).

Fill it in once, when the harness is set up (docs/AGENT_HARNESS.md §17), and keep it true as the project grows: a new
check, judge, secret or generated folder lands here in the same change as the thing it covers. An empty list or dict
means "none yet" — the harness then runs only its generic checks (the doc lint and its own self-tests).

Paths are relative to the repo root. A pattern that ends in `/` matches everything under that folder; a pattern with
`*`, `?` or `[` is a glob (`*` also matches `/`, so `*.css` matches every CSS file in the repo); anything else matches
that exact file. Python 3.9+, standard library only — the guard imports this file, and a guard that cannot import it
lets every call through.

The guard asks the person before an agent edits this file: it is part of the harness's controls.
"""

# --- The project ------------------------------------------------------------------------------------------------

# The name used in doc titles (`# <PROJECT_NAME> — <Topic>`) and the prefix of the project's own docs
# (`docs/<DOC_PREFIX>_<TOPIC>.md`). Leave DOC_PREFIX empty to give no prefix to any doc.
PROJECT_NAME = "<Project>"
DOC_PREFIX = ""

# Docs that apply to any project and travel between repos unchanged: they name no project and link only to each
# other (DOCUMENTATION_GUIDELINES §3.1).
PROJECT_WIDE_DOCS = ("docs/AGENT_HARNESS.md", ".agents/skills/docs-authoring-and-sync/references/guidelines.md")

# --- Where things are -------------------------------------------------------------------------------------------

# The source code. Empty means "every file outside docs/, the harness, the root's Markdown and GENERATED".
#   Web:     ("src/", "app/", "public/", "package.json")
#   Mobile:  ("ios/", "android/", "lib/", "pubspec.yaml")
#   Python:  ("src/", "tests/", "pyproject.toml")
CODE_PATHS = ()

# The files that change what a person sees: screens, components, styles, copy, icons. Empty: no UI gates and no
# ui-designer judge. Fill it in for any project with an interface.
#   Web:     ("src/components/", "src/pages/", "src/app/", "*.css", "*.scss", "src/styles/")
#   Mobile:  ("ios/*/Views/", "android/app/src/main/res/", "lib/widgets/", "lib/screens/")
UI_PATHS = ()

# The design brief at the repo root: the product's principles and every design token by role, with its value per
# theme (DESIGN.md is the template's demo). The ui-designer and design-system skills read it first; the design check
# proves its contrast pairs meet their floors and its tokens exist in TOKEN_FILES. Changing it calls the ui-designer.
DESIGN_FILE = "DESIGN.md"

# Where the design tokens live in code — the values DESIGN.md decides, in the platform's format. A screen takes its
# values from these files, never from a literal (the design-system skill). Empty: the token check and the design
# check's token-drift half do not run.
#   ("src/styles/tokens.css",)  ("design/tokens.json",)  ("lib/theme/tokens.dart",)
TOKEN_FILES = ()

# Files a build or a tool writes. Never committed — the pre-commit hook refuses them — and the guard asks before an
# agent edits one. Keep these in .gitignore as well.
GENERATED = ("build/", "dist/", "out/", "coverage/", ".cache/", "node_modules/", ".venv/", "__pycache__/")

# Files a tool manages that ARE committed: lock files, vendored dependencies. The guard asks before an agent edits
# one by hand — change the manifest and let the tool regenerate it. Trim to your stack.
MANAGED = ("package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "uv.lock", "Pipfile.lock",
           "Cargo.lock", "Gemfile.lock", "Podfile.lock", "pubspec.lock", "go.sum", "vendor/")

# Third-party or generated folders whose text the injection flag treats as outside content, like a web page.
# GENERATED and MANAGED folders are included automatically.
VENDORED = ("third_party/",)

# --- Secrets ----------------------------------------------------------------------------------------------------

# The project's own secret files, by file name, wherever they sit. Denied to every agent from every tool, even with
# a yes, and refused by the pre-commit hook. `.env` files (not `.env.example`, `.sample` or `.template`), private
# keys (`*.pem`, `*.p12`, `*.pfx`, `*.key`, `id_rsa`-style) and the usual credential folders (`~/.ssh`, `~/.aws`, …) are
# denied already. Each name here also needs a `Read(**/<name>)` deny in .claude/settings.json — `verify.py doctor`
# checks it.
#   ("service-account.json", "api_key.txt")
SECRET_FILES = ()

# --- The network ------------------------------------------------------------------------------------------------

# The hosts a build, a fetch and the docs need. A `curl` or `wget` to any other host asks the person; a subdomain
# matches its host. The one home of the list: .codex/config.toml repeats it for Codex's sandbox, and
# `verify.py doctor` checks the two agree.
#   npm: "npmjs.org", "npmjs.com"   Python: "pypi.org", "pythonhosted.org"   Your platform's docs host.
ALLOWED_HOSTS = ("github.com", "githubusercontent.com")

# --- What needs the person ---------------------------------------------------------------------------------------

# Commands that need the person's yes: (program, words that must all appear in its arguments, why). The program is
# matched by name, after wrappers (`sudo`, `env`, `npx`, `uv run`, `bash -c "…"`) are peeled. Words () matches
# every call of the program. Publishing is gated by default; add deploys, migrations, paid API calls and anything
# that loses data on the target.
ASK_COMMANDS = [
    ("npm", ("publish",), "publishes a package to the registry"),
    ("pnpm", ("publish",), "publishes a package to the registry"),
    ("yarn", ("publish",), "publishes a package to the registry"),
    ("twine", ("upload",), "publishes a package to the registry"),
    ("cargo", ("publish",), "publishes a crate to the registry"),
    ("gh", ("release", "create"), "publishes a release"),
    # ("vercel", ("--prod",), "deploys to production"),
    # ("firebase", ("deploy",), "deploys to production"),
    # ("terraform", ("apply",), "changes real infrastructure"),
    # ("prisma", ("migrate", "deploy"), "migrates a shared database"),
    # ("kill", (), "stops a process — the person's dev server may be the one"),
]

# Commands denied even with a yes, because their output would put a secret into the chat: (program, words, why).
#   ("kubectl", ("get", "secret"), "prints a cluster secret")
#   ("vercel", ("env", "pull"), "writes the project's secrets to a local file the agent would read")
DENY_COMMANDS = []

# Lines that must never be committed: a temporary debug marker, a focused test, a debug flag left on. A regular
# expression, matched in the code (CODE_PATHS) by the pre-commit hook and by `verify.py finish`. Mark every
# temporary line you add for debugging with `DEBUG-TEMP` in a comment, and these catch it.
#   JavaScript: r"DEBUG-TEMP|\bdebugger;|\.only\("   Python: r"DEBUG-TEMP|\bbreakpoint\(\)"
DEBUG_MARKERS = r"DEBUG-TEMP"

# Lines a file must always hold — a setting at its shipping value: (file, regular expression, why). The pre-commit
# hook and `verify.py finish` refuse a tree where the file lacks the line.
#   ("src/config.ts", r"^export const USE_MOCK_API = false;", "the shipped app talks to the real API")
INVARIANTS = []

# --- The loop: checks, judges and gates (docs/AGENT_HARNESS.md §10) -------------------------------------------

# The project's checks, which `verify.py run` picks by the files a change touches and runs in parallel. Each:
#   "run":  the command, as a list, run from the repo root; exit 0 is a pass. Its output goes to a log file, and only
#           the last lines of a failure are printed.
#   "when": the paths that call for it (patterns as above).
#   "wait": True to run it after the parallel ones — for a check that reads what another one writes.
# A check whose program is not installed fails with "not found" — add the tool, or take the check out.
CHECKS = {
    # "build": {"run": ["npm", "run", "build"], "when": ("src/", "package.json")},
    # "test":  {"run": ["npm", "test", "--", "--run"], "when": ("src/", "tests/")},
    # "lint":  {"run": ["npm", "run", "lint"], "when": ("src/",)},
    # "types": {"run": ["npx", "tsc", "--noEmit"], "when": ("src/",)},
}

# The project's own judges, beyond the kit's (doc-reviewer, code-reviewer, ui-designer): agent name → the paths
# that call for it. A judge joins the plan once its file exists in .agents/agents/.
#   {"security-reviewer": ("src/auth/", "src/api/")}
JUDGES = {}

# The person's yes each kind of change needs before it is handed over: (what, the paths that call for it, the kinds
# of yes). Kinds given before the build: "mock" (a still of a screen or component), "motion" (a GIF or video of a
# move), "copy" (the words). Given after: "built" (the built screen beside its mock) — it covers the code as it was
# at the yes. `verify.py approve <file> --kind <kind>` records each yes with the file's hash.
GATES = [
    ("a screen or component", UI_PATHS, ("mock", "built")),
    # A token value is seen on every screen at once: its change is drafted as a specimen (swatches, the type scale,
    # a screen or two before and after) and approved before the token files change.
    ("a design token or principle", (DESIGN_FILE,) + TOKEN_FILES, ("mock",)),
]

# Where the change finally runs, in a few words — the Verified block names it.
#   "the app in a browser at localhost:3000"  "the iOS simulator"  "a phone over USB"  "the staging site"
TARGET = "<target>"

# Extra guard self-test cases for the project's own gates: (command, "deny" | "ask" | None). Give each gate a case,
# and a near-miss that must pass.
#   ("vercel --prod", "ask"), ("vercel dev", None)
GUARD_CASES = []


# --- Helpers — the harness's scripts call these; leave them as they are -----------------------------------------

HARNESS_DIRS = (".agents/", ".claude/", ".codex/", ".github/")


def matches(path, patterns):
    """Whether a repo-relative path matches any of the patterns (a folder with `/`, a glob, or an exact file)."""
    import fnmatch
    for p in patterns:
        if p.endswith("/"):
            if path.startswith(p):
                return True
        elif any(c in p for c in "*?["):
            if fnmatch.fnmatch(path, p):
                return True
        elif path == p:
            return True
    return False


def is_doc(path):
    """docs/, and the Markdown at the repo root."""
    return path.startswith("docs/") or ("/" not in path and path.endswith(".md"))


def is_code(path):
    """A source file: in CODE_PATHS, or — with CODE_PATHS empty — anything that is not a doc, the harness, or
    generated."""
    if CODE_PATHS:
        return matches(path, CODE_PATHS)
    return not (is_doc(path) or path.startswith(HARNESS_DIRS) or matches(path, GENERATED)
                or path in (".gitignore", ".mcp.json", "LICENSE"))


def code_pathspec():
    """A git pathspec for the code, for `git grep` and `git diff`."""
    if CODE_PATHS:
        return [p if not any(c in p for c in "*?[") else f":(glob){p}" for p in CODE_PATHS]
    return [".", ":(exclude)docs", ":(exclude)*.md", ":(exclude).agents", ":(exclude).claude", ":(exclude).codex",
            ":(exclude).github"] + [f":(exclude){g.rstrip('/')}" for g in GENERATED]
