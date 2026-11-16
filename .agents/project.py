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
PROJECT_WIDE_DOCS = ("docs/AGENT_HARNESS.md", ".agents/skills/docs-authoring-and-sync/references/guidelines.md",
                     ".agents/skills/accessibility/references/criteria.md",
                     ".agents/skills/design-system/references/brief.md",
                     ".agents/skills/motion/references/motion.md",
                     ".agents/skills/touch-and-gesture/references/touch.md",
                     ".agents/skills/ui-designer/references/gates.md",
                     ".agents/skills/ui-designer/references/rubric.md",
                     ".agents/skills/esp-idf-setup/references/esp-idf.md")

# --- Where things are -------------------------------------------------------------------------------------------

# The source code. Empty means "every file outside docs/, the harness, the root's Markdown and GENERATED".
#   Web:     ("src/", "app/", "public/", "package.json")
#   Mobile:  ("ios/", "android/", "lib/", "pubspec.yaml")
#   Python:  ("src/", "tests/", "pyproject.toml")
#   ESP-IDF: ("main/", "components/", "CMakeLists.txt", "sdkconfig.defaults", "partitions.csv")
CODE_PATHS = ()

# The files that change what a person sees: screens, components, styles, copy, icons. Empty: no UI gates and no
# ui-designer judge. Fill it in for any project with an interface.
#   Web:     ("src/components/", "src/pages/", "src/app/", "*.css", "*.scss", "src/styles/")
#   Mobile:  ("ios/*/Views/", "android/app/src/main/res/", "lib/widgets/", "lib/screens/")
#   ESP-IDF with LVGL: ("components/app_shell/screen_*", "components/ui_*/", "components/<feature>/*_screen.cpp")
UI_PATHS = ()

# The design brief at the repo root: the product's principles and every design token by role, with its value per
# theme (DESIGN.md is the template's demo). The ui-designer and design-system skills read it first; the design check
# proves its contrast pairs meet their floors and its tokens exist in TOKEN_FILES. Changing it calls the ui-designer.
DESIGN_FILE = "DESIGN.md"

# Where the design tokens live in code — the values DESIGN.md decides, in the platform's format. A screen takes its
# values from these files, never from a literal (the design-system skill). Empty: the token check and the design
# check's token-drift half do not run.
#   ("src/styles/tokens.css",)  ("design/tokens.json",)  ("lib/theme/tokens.dart",)
#   ESP-IDF with LVGL: ("components/ui_theme/include/ui_theme.h",) — constants named by role, colours as 0xRRGGBB
TOKEN_FILES = ()

# Files a build or a tool writes. Never committed — the pre-commit hook refuses them — and the guard asks before an
# agent edits one. Keep these in .gitignore as well.
GENERATED = ("build/", "dist/", "out/", "coverage/", ".cache/", "node_modules/", ".venv/", "__pycache__/",
             "managed_components/", "sdkconfig", "sdkconfig.old")  # the last three: ESP-IDF's

# Files a tool manages that ARE committed: lock files, vendored dependencies. The guard asks before an agent edits
# one by hand — change the manifest and let the tool regenerate it. Trim to your stack.
MANAGED = ("package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "uv.lock", "Pipfile.lock",
           "Cargo.lock", "Gemfile.lock", "Podfile.lock", "pubspec.lock", "go.sum", "vendor/",
           "dependencies.lock")  # ESP-IDF's component manager

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
# every call of the program. A program or a word with `*`, `?` or `[` is a glob, matched whole (`esptool*`,
# `write[_-]flash`); a word that is a tuple is any of its alternatives — for tools that spell a command several ways.
# Name each real command rather than a loose glob: a word is matched against every argument, file names included.
# Publishing and writing a board are gated by default; add deploys, migrations, paid API calls and anything that
# loses data on the target.
FLASH_TARGETS = ("flash", "app-flash", "bootloader-flash", "partition-table-flash", "encrypted-flash",
                 "encrypted-app-flash", "dfu-flash", "erase-flash", "erase_flash", "erase-otadata", "erase_otadata")
ASK_COMMANDS = [
    ("npm", ("publish",), "publishes a package to the registry"),
    ("pnpm", ("publish",), "publishes a package to the registry"),
    ("yarn", ("publish",), "publishes a package to the registry"),
    ("twine", ("upload",), "publishes a package to the registry"),
    ("cargo", ("publish",), "publishes a crate to the registry"),
    ("gh", ("release", "create"), "publishes a release"),
    # ESP-IDF: writing the board — through idf.py, the build tool under it, esptool and the partition tools — and
    # installing ESP-IDF itself (gigabytes in the home folder)
    ("idf.py", (FLASH_TARGETS,), "writes the board's flash"),
    ("ninja", (FLASH_TARGETS,), "writes the board's flash"),
    ("cmake", ("--build", FLASH_TARGETS), "writes the board's flash"),
    ("esptool*", (("write[_-]flash", "write[_-]flash[_-]status", "write[_-]mem", "erase[_-]flash",
                   "erase[_-]region"),), "writes or erases the board's flash"),
    ("parttool*", (("write[_-]partition", "erase[_-]partition"),), "writes a partition on the board"),
    ("otatool*", (("write[_-]ota[_-]partition", "erase[_-]ota[_-]partition", "erase[_-]otadata",
                   "switch[_-]ota[_-]partition"),), "writes the board's OTA partitions"),
    ("espota*", (), "uploads firmware to a board over the network"),
    ("openocd", ("*program_esp*",), "writes the board's flash through JTAG"),
    ("eim", (("install", "wizard"),), "installs ESP-IDF into the home folder"),
    ("idf_tools*", ("install",), "installs ESP-IDF's tools into the home folder"),
    # ("vercel", ("--prod",), "deploys to production"),
    # ("firebase", ("deploy",), "deploys to production"),
    # ("terraform", ("apply",), "changes real infrastructure"),
    # ("prisma", ("migrate", "deploy"), "migrates a shared database"),
    # ("kill", (), "stops a process — the person's dev server may be the one"),
]

# Commands denied even with a yes, because their output would put a secret into the chat, or they change a device
# for good: (program, words, why). The person runs them themselves.
#   ("kubectl", ("get", "secret"), "prints a cluster secret")
#   ("vercel", ("env", "pull"), "writes the project's secrets to a local file the agent would read")
DENY_COMMANDS = [
    # ESP-IDF: an eFuse, once burnt or protected, cannot be changed again on that chip
    ("idf.py", (("efuse[_-]burn", "efuse[_-]burn[_-]key", "efuse[_-]write[_-]protect", "efuse[_-]read[_-]protect"),),
     "burns or protects an eFuse — permanent on the chip"),
    ("espefuse*", (("burn[_-]efuse", "burn[_-]key", "burn[_-]key[_-]digest", "burn[_-]bit", "burn[_-]block[_-]data",
                    "burn[_-]custom[_-]mac", "write[_-]protect[_-]efuse", "read[_-]protect[_-]efuse",
                    "set[_-]flash[_-]voltage"),), "burns or protects an eFuse — permanent on the chip"),
]

# Files a project makes only once a doc exists. Writing one that does not exist yet, while no doc in docs/ matches,
# is denied until corrected — the reason says what to ask the person and which doc to write (HARNESS §2.2). Each:
#   "files": path → a pattern the new file's content must show for the rule to apply (None: any content; a file
#            with a pattern is not judged from the shell, where its content cannot be read)
#   "doc":   (globs on the doc's file name, a pattern it must hold outside `<…>` placeholders) — case-insensitive
#   "ask":   what the agent asks the person, and where it writes the answers
NEEDS_DOC = [
    {"files": {"CMakeLists.txt": r"project\.cmake", "sdkconfig.defaults": None, "main/idf_component.yml": None},
     "doc": (("*hardware*", "*board*spec*", "*hw*spec*"), r"\bESP32"),
     "ask": "an ESP-IDF project is generated from the board's hardware spec, and docs/ has none — ask the person for "
            "the chip or module, the flash, the PSRAM, the console, the display and its pins, and write their answers "
            "to a hardware spec in docs/ from the esp-idf-setup skill's template first"},
]

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
#   "the ESP32-S3 board over USB, its serial console on the same port"
TARGET = "<target>"

# Extra guard self-test cases for the project's own gates: (command, "deny" | "ask" | None). Give each gate a case,
# and a near-miss that must pass.
#   ("vercel --prod", "ask"), ("vercel dev", None)
GUARD_CASES = [
    # ESP-IDF: writing the board asks, burning an eFuse is denied, reading either passes
    ("idf.py -p /dev/cu.usbmodem1101 flash monitor", "ask"), ("idf.py app-flash", "ask"),
    ("idf.py erase-flash", "ask"), ("idf.py build", None), ("idf.py monitor", None), ("idf.py size", None),
    ("python -m esptool --port /dev/x write-flash 0x0 a.bin", "ask"), ("esptool.py erase_flash", "ask"),
    ("esptool.py chip_id", None),
    ("idf.py efuse-burn --do-not-confirm DIS_USB_JTAG 1", "deny"), ("idf.py efuse-write-protect X", "deny"),
    ("espefuse.py burn_key BLOCK_KEY0 key.bin", "deny"), ("espefuse --port /dev/x burn-efuse X 1", "deny"),
    ("espefuse.py write_protect_efuse X", "deny"), ("espefuse.py set_flash_voltage 3.3V", "deny"),
    ("espefuse.py summary", None), ("idf.py efuse-summary", None),
    ("eim install -i v6.1", "ask"), ("eim wizard", "ask"), ("eim list", None),
    # the same writes, spelled through the build tool, a runner or a shell
    ("ninja -C build flash", "ask"), ("cmake --build build --target app-flash", "ask"),
    ("uvx --from esptool esptool write-flash 0x0 a.bin", "ask"), ("pipx run esptool erase-flash", "ask"),
    ('bash -lc "idf.py flash"', "ask"), ('bash -c -l "idf.py flash"', "ask"), ("timeout 60 idf.py -p /dev/x flash", "ask"),
    ("parttool.py write_partition --partition-name nvs --input n.bin", "ask"), ("otatool.py erase_otadata", "ask"),
    ("python -m espefuse burn_efuse X 1", "deny"),
    # near misses: a file or an option value that only looks like a write
    ("esptool.py read_flash 0 0x1000 write.bin", None), ("idf.py -B build-flash build", None),
    ("espefuse.py --port protect.log summary", None), ("espefuse.py execute_scripts burn.py", None),
    ("espefuse.py summary > burn.txt", None), ("ninja -C build", None), ("cmake --build build", None),
]


# --- Helpers — the harness's scripts call these; leave them as they are -----------------------------------------

HARNESS_DIRS = (".agents/", ".claude/", ".codex/", ".github/")


def matches(path, patterns):
    """Whether a repo-relative path matches any of the patterns (a folder with `/`, a glob, or an exact file)."""
    import fnmatch
    for p in patterns:
        if p.endswith("/"):
            # a folder: everything under it; with a glob in it (`components/ui_*/`), everything under each match
            if path.startswith(p) or (any(c in p for c in "*?[") and fnmatch.fnmatch(path, p + "*")):
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
