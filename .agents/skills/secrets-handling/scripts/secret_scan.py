#!/usr/bin/env python3
"""The secrets-handling skill's scan: key-shaped strings in a change or in named files, counted and placed, never
printed — from references/secrets.md (cited `SECRETS §11`).

    python3 .agents/skills/secrets-handling/scripts/secret_scan.py            # the change
    python3 .agents/skills/secrets-handling/scripts/secret_scan.py FILE …     # whole files
    python3 .agents/skills/secrets-handling/scripts/secret_scan.py --test     # the self-test

What it reads: with no files named, the lines a change adds — `git diff HEAD` (staged and unstaged, read with `--text
--no-textconv`, so a file marked `-diff` is still read) and every untracked file git does not ignore; in a repo with no
commit yet, every tracked and untracked file. With files named, the whole of each. A file whose first 8 KB holds a NUL
byte is binary and skipped; a file over 5 MB is not read, and the run says so.

The patterns (SECRETS §11):
  private-key  a PEM private key header (RSA, EC, DSA, OPENSSH, ENCRYPTED or bare)
  github       a GitHub token (classic `gh?_` and fine-grained `github_pat_`)
  aws          an AWS access key ID (`AKIA` or `ASIA` and 16 more)
  google       a Google API key (`AIza` and 35 more)
  slack        a Slack token (`xox?-`) or incoming-webhook URL
  sk           an `sk-` secret key (OpenAI, Anthropic and others)
  stripe       a Stripe live secret or restricted key (`sk_live_`, `rk_live_`)
  jwt          a JSON Web Token (`eyJ….eyJ….…`)
  hf           a Hugging Face token (`hf_`)
  npm          an npm token (`npm_`) or an `_authToken=` in an .npmrc
  url          a URL carrying a password (`scheme://user:password@host`)
  literal      a name that ends in a credential word (password, passphrase, secret, secret_key, api_key, access_key,
               private_key, token — so DB_PASSWORD, OPENAI_API_KEY, JWT_SECRET, apiKey) assigned a quoted value of 8
               or more characters, in code, JSON or YAML
  env          the same names at the start of a line, unquoted, in .env or YAML style (`PASSWORD=…`, `token: …`)
plus the project's own: SECRET_PATTERNS in `.agents/project.py`, a list of (regex, what) pairs, read when the repo has
the agent-harness kit; none when it does not.

Not counted: a value that is a placeholder — `undefined`, `changeme`, `example`, `<…>`, `${…}`, `%…%`, `{…}`, `*…`, a
word of letters only shorter than 16 (`"Passwort"`, an i18n label) — and any match ending in `EXAMPLE` (AWS's documented
example key). A line that carries `secret-exception` is skipped — write the reason beside it. Files that hold the scan's
patterns on purpose are skipped: this script, and the paths in SECRET_PATTERN_HOMES or PATTERN_HOMES in
`.agents/project.py`.

Prints one line per file and pattern — `file: N × what [id] (lines a, b)` — then a total. Nothing a file contains
reaches the output: only paths from git's file list or the command line, pattern ids, counts and line numbers. Open
each place in an editor; never search for it with a command that prints the line. A pass is a floor: a secret with no
fixed shape, one split across lines or encoded, an alphabetic-only password under 16 characters, binary files and files
over 5 MB are not seen.

Exit 0 when nothing matched, 1 on any hit, 2 when a named file cannot be read, `.agents/project.py` fails to load, a
project pattern does not compile, or git fails. Python 3.9+, standard library only.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip()
            or ".").resolve()
SELF = Path(__file__).resolve()
MAX_BYTES = 5 * 1024 * 1024
BINARY_PROBE = 8192
MARKER = "secret-exception"

# A value that is a placeholder, not a secret.
PLACEHOLDER_WORDS = {"undefined", "null", "none", "nil", "changeme", "change_me", "change-me", "example", "placeholder",
                     "password", "secret", "token", "redacted", "dummy", "sample", "notasecret"}
PLACEHOLDER_PARTS = ("example", "changeme", "change_me", "placeholder", "your_", "your-", "xxxx", "****", "redacted")


def is_placeholder(value: str) -> bool:
    v = value.strip().lower()
    return (not v or v in PLACEHOLDER_WORDS or v[0] in "<${%*[(" or any(p in v for p in PLACEHOLDER_PARTS)
            or len(set(v)) == 1 or (v.isalpha() and len(v) < 16))


def value_ok(m) -> bool:
    """A match whose `v` group (when it has one) is not a placeholder."""
    v = m.groupdict().get("v")
    return v is None or not is_placeholder(v)


# Every quantifier is bounded and each pattern is anchored on a fixed prefix or a line start, so a long line costs
# linear time (no catastrophic backtracking).
CRED = r"(?:password|passwd|passphrase|secret_?key|secret|api_?key|access_?key|private_?key|token)"
COMMON = [
    ("private-key", r"-----BEGIN (?:[A-Z0-9]{2,10} ){0,3}PRIVATE KEY-----", "a private key header"),
    ("github", r"(?<![A-Za-z0-9_])(?:gh[pousr]_[A-Za-z0-9]{36,251}|github_pat_[A-Za-z0-9_]{60,251})(?![A-Za-z0-9_])",
     "a GitHub token"),
    ("aws", r"(?<![A-Z0-9])(?:AKIA|ASIA)[A-Z0-9]{16}(?![A-Z0-9])", "an AWS access key ID"),
    ("google", r"(?<![A-Za-z0-9_-])AIza[A-Za-z0-9_-]{35}(?![A-Za-z0-9_-])", "a Google API key"),
    ("slack", r"(?<![A-Za-z0-9])xox[abposr]-[A-Za-z0-9-]{10,250}"
              r"|hooks\.slack\.com/services/T[A-Z0-9]{6,20}/B[A-Z0-9]{6,20}/[A-Za-z0-9]{20,40}",
     "a Slack token or webhook"),
    ("sk", r"(?<![A-Za-z0-9_-])sk-[A-Za-z0-9_-]{20,250}", "an sk- secret key"),
    ("stripe", r"(?<![A-Za-z0-9_])[sr]k_live_[A-Za-z0-9]{16,250}", "a Stripe live key"),
    ("jwt", r"(?<![A-Za-z0-9_-])eyJ[A-Za-z0-9_-]{8,2000}\.eyJ[A-Za-z0-9_-]{8,4000}\.[A-Za-z0-9_-]{10,1000}",
     "a JSON Web Token"),
    ("hf", r"(?<![A-Za-z0-9_])hf_[A-Za-z0-9]{30,250}(?![A-Za-z0-9_])", "a Hugging Face token"),
    ("npm", r"(?<![A-Za-z0-9_])npm_[A-Za-z0-9]{36}(?![A-Za-z0-9_])"
            r"|_authToken[ \t]{0,5}=[ \t]{0,5}(?P<v>[^\s'\"]{8,500})", "an npm token"),
    ("url", r"(?i)\b[a-z][a-z0-9+.-]{1,20}://[^\s:/@'\"<>]{0,100}:(?P<v>[^\s:/@'\"]{3,200})@[a-z0-9.-]{1,253}",
     "a URL carrying a password"),
    ("literal", r"(?i)" + CRED + r"[\"']?[ \t]{0,20}(?::=|=>|[:=])[ \t]{0,20}[\"'](?P<v>[^\"'\s]{8,200})[\"']",
     "a credential assigned as a string literal"),
    ("env", r"(?i)^[ \t]{0,20}(?:export[ \t]{1,5}|-[ \t]{1,5})?[A-Za-z0-9_.-]{0,60}?" + CRED +
            r"(?:=|:[ \t]{1,5})(?P<v>[^\s\"'#,;()\[\]{}]{8,200})[ \t]{0,20}(?:#.{0,500})?$",
     "a credential assigned unquoted (.env or YAML)"),
]


class SettingsError(Exception):
    pass


def load_project():
    """The kit's settings module, or None when the repo has none. Any failure to load it is a SettingsError."""
    settings = ROOT / ".agents/project.py"
    if not settings.is_file():
        return None
    sys.path.insert(0, str(settings.parent))
    try:
        import project  # noqa: E402 — the kit's settings
        return project
    except BaseException as e:  # a settings file that raises, exits or fails to parse
        raise SettingsError(f"cannot load .agents/project.py: {type(e).__name__}") from None
    finally:
        sys.path.pop(0)


def compile_patterns(extra) -> list:
    """(id, compiled, what) for the common patterns and the project's; a bad project pattern raises SettingsError."""
    out = [(pid, re.compile(rx), what) for pid, rx, what in COMMON]
    for i, item in enumerate(extra or (), 1):
        try:
            rx, what = item
            out.append((f"project-{i}", re.compile(rx), str(what)))
        except (ValueError, TypeError, re.error):
            raise SettingsError(f"SECRET_PATTERNS entry {i} is not a (regex, what) pair that compiles") from None
    return out


def pattern_homes(project) -> set:
    """Repo-relative paths that hold patterns on purpose: this script, and the project's listed homes."""
    homes = set()
    try:
        homes.add(SELF.relative_to(ROOT).as_posix())
    except ValueError:
        pass
    for name in ("SECRET_PATTERN_HOMES", "PATTERN_HOMES"):
        homes.update(str(p) for p in (getattr(project, name, ()) or ()))
    return homes


def scan_lines(lines, patterns) -> dict:
    """{(id, what): [line numbers]} for (number, text) pairs. Only ids, counts and places leave this function."""
    hits: dict = {}
    for number, text in lines:
        if MARKER in text:
            continue
        for pid, rx, what in patterns:
            n = sum(1 for m in rx.finditer(text) if value_ok(m) and not m.group(0).endswith("EXAMPLE"))
            if n:
                hits.setdefault((pid, what), []).extend([number] * n)
    return hits


def probe(path: Path) -> str:
    """'text', 'binary', 'large' or 'link' for a file. Raises OSError when it cannot be read."""
    st = os.lstat(path)
    if os.path.islink(path):
        return "link"
    if st.st_size > MAX_BYTES:
        return "large"
    with open(path, "rb") as fh:
        return "binary" if b"\0" in fh.read(BINARY_PROBE) else "text"


def file_lines(path: Path):
    """(number, text) for every line of a text file, streamed."""
    with open(path, "rb") as fh:
        for number, raw in enumerate(fh, 1):
            yield number, raw.decode("utf-8", errors="replace").rstrip("\r\n")


HUNK = re.compile(r"^@@ -\d+(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def hunk_added(lines):
    """(new line number, text) for every line a one-file unified diff adds. Lines are counted from each `@@` header,
    so an added line whose text begins `++ ` (shown as `+++ …`) is read as text, never as a header."""
    old_left = new_left = 0
    number = 0
    for line in lines:
        if old_left <= 0 and new_left <= 0:
            m = HUNK.match(line)
            if m:
                old_left = int(m.group(1)) if m.group(1) is not None else 1
                number = int(m.group(2))
                new_left = int(m.group(3)) if m.group(3) is not None else 1
            continue  # a file header (`diff --git`, `index`, `---`, `+++`) or `\ No newline at end of file`
        if line.startswith("+"):
            yield number, line[1:]
            number += 1
            new_left -= 1
        elif line.startswith("-"):
            old_left -= 1
        elif line.startswith(" "):
            number += 1
            old_left -= 1
            new_left -= 1
        elif not line.startswith("\\"):
            old_left = new_left = 0  # malformed: wait for the next `@@`


def git_env():
    return {k: v for k, v in os.environ.items() if not k.startswith("GIT_")} if os.environ.get("SECRET_SCAN_TEST") \
        else None


def git(*args: str, cwd: Path) -> str:
    r = subprocess.run(["git", "-c", "core.quotePath=false", *args], capture_output=True, cwd=cwd, env=git_env())
    if r.returncode != 0:
        raise RuntimeError(f"git {args[0]} failed (exit {r.returncode})")
    return r.stdout.decode("utf-8", errors="replace")


def git_diff_lines(path: str, cwd: Path):
    """The lines of `git diff HEAD` for one path, streamed."""
    cmd = ["git", "-c", "core.quotePath=false", "diff", "HEAD", "--no-color", "--no-ext-diff", "--text",
           "--no-textconv", "--no-renames", "-U0", "--", path]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, cwd=cwd, env=git_env())
    try:
        for raw in proc.stdout:
            yield raw.decode("utf-8", errors="replace").rstrip("\r\n")
    finally:
        proc.stdout.close()
        if proc.wait() != 0:
            raise RuntimeError("git diff failed")


def scan_change(cwd: Path, patterns, homes) -> tuple:
    """({path: hits}, notes): the lines `git diff HEAD` adds plus every untracked, unignored file; every file when the
    repo has no commit yet."""
    has_head = subprocess.run(["git", "rev-parse", "--verify", "-q", "HEAD"], capture_output=True, cwd=cwd,
                              env=git_env()).returncode == 0
    hits, notes = {}, []
    changed = []
    if has_head:
        changed = git("diff", "HEAD", "--name-only", "-z", "--no-renames", "--diff-filter=d", cwd=cwd).split("\0")
        whole = git("ls-files", "--others", "--exclude-standard", "-z", cwd=cwd).split("\0")
    else:
        whole = git("ls-files", "--cached", "--others", "--exclude-standard", "-z", cwd=cwd).split("\0")
    for name in filter(None, changed):
        if name in homes or (cwd / name).is_dir():  # a directory here is a submodule's pointer: nothing to read
            continue
        kind = probe(cwd / name) if (cwd / name).exists() or os.path.islink(cwd / name) else "text"
        if kind in ("binary", "large"):
            notes.append((name, kind))
            continue
        found = scan_lines(hunk_added(git_diff_lines(name, cwd)), patterns)
        if found:
            hits[name] = found
    for name in filter(None, whole):
        if name in homes:
            continue
        try:
            kind = probe(cwd / name)
        except OSError:
            continue  # gone between the listing and the read
        if kind in ("binary", "large"):
            notes.append((name, kind))
            continue
        if kind == "text":
            found = scan_lines(file_lines(cwd / name), patterns)
            if found:
                hits[name] = found
    return hits, notes, len([n for n in changed if n]) + len([n for n in whole if n])


def shown(path: str) -> str:
    """A path as printed: control characters replaced, so a file name cannot drive the terminal."""
    return "".join(c if c.isprintable() else "?" for c in path)


def report(hits: dict) -> int:
    """Prints counts and places per file and pattern; returns the number of hits."""
    total = 0
    for path in sorted(hits):
        for (pid, what), numbers in sorted(hits[path].items()):
            total += len(numbers)
            places = sorted(set(numbers))
            listed = ", ".join(str(n) for n in places[:20]) + (", …" if len(places) > 20 else "")
            print(f"{shown(path)}: {len(numbers)} × {what} [{pid}] (lines {listed})")
    return total


def main(argv: list) -> int:
    if argv[:1] == ["--test"]:
        return self_test()
    if any(a.startswith("-") for a in argv):
        print(__doc__, file=sys.stderr)
        return 2
    try:
        project = load_project()
        patterns = compile_patterns(getattr(project, "SECRET_PATTERNS", ()))
        homes = pattern_homes(project)
    except SettingsError as e:
        print(f"secret_scan: {e}", file=sys.stderr)
        return 2
    hits, notes = {}, []
    if argv:
        for name in argv:
            path = Path(name)
            try:
                rel = path.resolve().relative_to(ROOT).as_posix()
            except ValueError:
                rel = None
            if rel in homes:
                continue
            try:
                kind = probe(path)
                if kind in ("binary", "large"):
                    notes.append((name, kind))
                    continue
                found = scan_lines(file_lines(path), patterns) if kind == "text" else {}
            except OSError as e:
                print(f"secret_scan: cannot read {shown(name)}: {e.strerror}", file=sys.stderr)
                return 2
            if found:
                hits[name] = found
        scope = f"{len(argv)} file(s) named"
    else:
        try:
            hits, notes, n = scan_change(ROOT, patterns, homes)
        except (RuntimeError, OSError) as e:
            print(f"secret_scan: {e}", file=sys.stderr)
            return 2
        scope = f"the change ({n} file(s))"
    total = report(hits)
    for name, kind in notes:
        if kind == "large":
            print(f"{shown(name)}: not read — over {MAX_BYTES // (1024 * 1024)} MB")
    binary = sum(1 for _, k in notes if k == "binary")
    large = sum(1 for _, k in notes if k == "large")
    print(f"secret_scan: {total} key-shaped string(s) in {scope}; {binary} binary skipped, {large} not read (too large)"
          + (" — open each place in an editor; never print the line (SECRETS §11)" if total else ""))
    return 1 if total else 0


# --- Self-test ------------------------------------------------------------------------------------------------------
# Every fixture is assembled from parts, so this file holds no key-shaped literal for the pre-commit hook to refuse.

def _aws() -> str:
    return "AK" + "IA" + "Z9" * 8


def _fixtures() -> list:
    """(pattern id, a line that must hit, a near miss that must not)."""
    b36 = "Q7x" * 12
    val = "Zq9" * 4
    return [
        ("private-key", "-----" + "BEGIN RSA " + "PRIVATE" + " KEY-----", "-----" + "BEGIN PUBLIC" + " KEY-----"),
        ("private-key", "-----" + "BEGIN " + "PRIVATE" + " KEY-----", "-----" + "BEGIN CERTIFICATE" + "-----"),
        ("github", "token " + "gh" + "p_" + b36, "gh" + "p_" + b36[:20]),
        ("github", "gith" + "ub_pat_" + "A1b2_" * 13, "gith" + "ub_pat_" + "short"),
        ("aws", "id=" + _aws(), "AK" + "IA" + "Z9" * 7 + "z"),
        ("aws", "AS" + "IA" + "7Q" * 8, "XAS" + "IA" + "7Q" * 8),
        ("aws", "AS" + "IA" + "7Q" * 8, "AK" + "IA" + "IOSFODNN7" + "EXAMPLE"),
        ("google", "key: " + "AI" + "za" + "Sy" + "a_b-" * 8 + "c", "AI" + "za" + "Sy" + "a_b-" * 8),
        ("slack", "xo" + "xb-" + "1234567890-abcdef", "xo" + "xz-" + "1234567890-abcdef"),
        ("slack", "https://hooks.slack.com/services/" + "T0ABC1234/" + "B0ABC1234/" + "abcDEF123" * 3,
         "https://hooks.slack.com/services/" + "T0ABC1234/" + "B0ABC1234/" + "short"),
        ("sk", "Bearer " + "s" + "k-" + "proj-" + "aB3" * 8, "ta" + "sk-" + "aB3" * 8),
        ("stripe", "s" + "k_live_" + "aB3" * 8, "s" + "k_test_" + "aB3" * 8),
        ("stripe", "r" + "k_live_" + "aB3" * 8, "s" + "k_live_" + "aB3"),
        ("jwt", "Authorization: Bearer " + "ey" + "J" + "hbGciOiJI" + ".ey" + "J" + "zdWIiOiIx" + "." + "Sfl" * 5,
         "ey" + "J" + "hbGciOiJI" + ".notajwt"),
        ("hf", "HF=" + "h" + "f_" + "aB3" * 11, "h" + "f_" + "aB3" * 5),
        ("npm", "//registry.npmjs.org/:_auth" + "Token=" + "n" + "pm_" + "aB3x" * 9, "_auth" + "Token=${NPM_TOKEN}"),
        ("npm", "n" + "pm_" + "aB3x" * 9, "n" + "pm_" + "aB3x" * 8),
        ("url", "postgres://app:" + "s3cr" + "Et-99" + "@db.internal:5432/x", "https://user@" + "example.org/path"),
        ("url", "redis://:" + "s3cr" + "Et-99" + "@cache:6379", "postgres://user:" + "${DB_PW}" + "@db/x"),
        ("literal", "pass" + "word = '" + val + "'", "pass" + "word = os.environ['X']"),
        ("literal", '{"api' + '_key": "' + val + '"}', '{"api' + '_key": "' + "${API_KEY}" + '"}'),
        ("literal", "TO" + "KEN=" + '"' + val + '"', "to" + "ken = " + "'" + "short" + "'"),
        ("literal", "SECRET" + "_KEY = '" + val + "'", '{"pass' + 'word": "' + "Passwort" + '"}'),
        ("literal", "DB_PASS" + 'WORD="' + val + '"', "pass" + "word: '" + "undefined" + "'"),
        ("literal", "OPENAI_API" + '_KEY="' + val + '"', "api" + "Key: '" + "changeme" + "'"),
        ("literal", "AWS_SECRET_ACCESS" + "_KEY = \"" + val + "\"", "tok" + "en = '<" + "your token>'"),
        ("literal", "JWT_SEC" + "RET: '" + val + "'", "token" + "izer = '" + "bert-base-uncased" + "'"),
        ("literal", "this.api" + "Key = '" + val + "'", "pass" + "word = '" + "example-value" + "'"),
        ("env", "DB_PASS" + "WORD=" + val, "pass" + "word = user.password"),
        ("env", "export API" + "_TOKEN=" + val + "  # bench", "  pass" + "word: form.password,"),
        ("env", "  pass" + "word: " + val, "PASS" + "WORD=" + "changeme"),
    ]


def _write_git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", "-c", "commit.gpgsign=false",
                    "-c", "core.hooksPath=/dev/null", *args], cwd=repo, check=True, capture_output=True,
                   env=git_env())


def self_test() -> int:
    import contextlib
    import io

    global MAX_BYTES
    os.environ["SECRET_SCAN_TEST"] = "1"  # git in the test's repos runs without a hook's GIT_* variables
    failures = []
    patterns = compile_patterns([])
    by_id = {pid: rx for pid, rx, _ in patterns}

    def hits_for(line: str) -> set:
        return {pid for (pid, _), _ in scan_lines([(1, line)], patterns).items()}

    for pid, hit, miss in _fixtures():
        if pid not in hits_for(hit):
            failures.append(f"{pid}: a fixture that must hit did not")
        if hits_for(miss):
            failures.append(f"{pid}: a near miss hit {sorted(hits_for(miss))}")

    # The exemption marker skips a line.
    if hits_for("x = '" + _aws() + "'  # " + MARKER + ": the vendor's documented test key"):
        failures.append("marker: a line carrying it was counted")

    # Counts and places only: the report never carries a fixture's text.
    lines = [(i, hit) for i, (_, hit, _) in enumerate(_fixtures(), 1)]
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        n = report({"f.txt": scan_lines(lines, patterns)})
    out = buf.getvalue()
    if n < len(lines):
        failures.append(f"report: {n} hits for {len(lines)} fixtures")
    if any(part in out for _, hit, _ in _fixtures() for part in re.findall(r"[A-Za-z0-9_-]{10,}", hit)):
        failures.append("report: printed a fixture's text")

    # The project's patterns are added, and a bad one is refused.
    extra = compile_patterns([(r"\bacme_[a-z0-9]{24}\b", "an Acme token")])
    if not scan_lines([(1, "acme_" + "k3" * 12)], extra):
        failures.append("project pattern: no hit")
    try:
        compile_patterns([("(", "broken")])
        failures.append("project pattern: a regex that does not compile was taken")
    except SettingsError:
        pass

    # The diff reader counts from the `@@` header: an added line whose text begins `++ ` shows as `+++ …` and is
    # read as text; a removed line beginning `-- ` is not read; headers are skipped.
    key = _aws()
    diff = [
        "diff --git a/a.py b/a.py", "index 1..2 100644", "--- a/a.py", "+++ b/a.py", "@@ -3,0 +4,3 @@",
        "+clean = 1", "+++ k = '" + key + "'", "+--- also '" + key + "'",
        "@@ -9 +11 @@", "--- old '" + key + "'", "+new = 2", "\\ No newline at end of file",
    ]
    added = list(hunk_added(diff))
    if added != [(4, "clean = 1"), (5, "++ k = '" + key + "'"), (6, "--- also '" + key + "'"), (11, "new = 2")]:
        failures.append(f"diff reader: read {len(added)} lines wrongly")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        # A repo with no commit: tracked and untracked files are read, ignored, binary and large ones are not.
        fresh = root / "fresh"
        fresh.mkdir()
        _write_git(fresh, "init", "-q")
        (fresh / ".gitignore").write_text("local.env\n")
        (fresh / "local.env").write_text("x = '" + key + "'\n")
        (fresh / "app.py").write_text("ok = 1\nk = '" + key + "'\n")
        (fresh / "blob.bin").write_bytes(b"\0" + key.encode())
        (fresh / "big.log").write_text("pad\n" * 600 + "k = '" + key + "'\n")
        saved, MAX_BYTES = MAX_BYTES, 1000
        try:
            hits, notes, _ = scan_change(fresh, patterns, set())
        finally:
            MAX_BYTES = saved
        if sorted(hits) != ["app.py"] or list(hits["app.py"].values()) != [[2]]:
            failures.append(f"fresh repo: hits in {sorted(hits)}")
        if sorted(notes) != [("big.log", "large"), ("blob.bin", "binary")]:
            failures.append(f"fresh repo: notes {sorted(notes)}")

        # A repo with a commit: the diff is read with --text --no-textconv (a `-diff` file is still read), an added
        # line beginning `++ ` is caught, the path printed is git's, and a pattern home is skipped.
        repo = root / "repo"
        repo.mkdir()
        _write_git(repo, "init", "-q")
        (repo / ".gitattributes").write_text("*.dat -diff\n")
        (repo / "a.dat").write_text("one\n")
        (repo / "b.py").write_text("one\n")
        (repo / "home.py").write_text("one\n")
        _write_git(repo, "add", "-A")
        _write_git(repo, "commit", "-q", "--no-verify", "-m", "base")
        (repo / "a.dat").write_text("one\nk = '" + key + "'\n")
        (repo / "b.py").write_text("one\n++ k = '" + key + "'\n")
        (repo / "home.py").write_text("one\nk = '" + key + "'\n")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            hits, _, _ = scan_change(repo, patterns, {"home.py"})
            report(hits)
        if sorted(hits) != ["a.dat", "b.py"] or any(list(h.values()) != [[2]] for h in hits.values()):
            failures.append(f"diff mode: hits in {sorted(hits)}")
        if key in buf.getvalue() or "++ k" in buf.getvalue():
            failures.append("diff mode: printed a line's text")

        # A settings file that raises, and one with a bad pattern, exit 2 with a short message, not a traceback.
        for body in ("raise RuntimeError('boom')\n", "SECRET_PATTERNS = [('(', 'bad')]\n"):
            kit = root / "kit"
            (kit / ".agents").mkdir(parents=True, exist_ok=True)
            _write_git(kit, "init", "-q")
            (kit / ".agents/project.py").write_text(body)
            r = subprocess.run([sys.executable, str(SELF)], cwd=kit, capture_output=True, text=True, env=git_env())
            if r.returncode != 2 or "Traceback" in r.stderr:
                failures.append(f"settings error: exit {r.returncode}")

        # The project's pattern homes are read and skipped.
        kit = root / "kit"
        (kit / ".agents/project.py").write_text("PATTERN_HOMES = {'held.py'}\nSECRET_PATTERN_HOMES = ('also.py',)\n")
        for name in ("held.py", "also.py", "open.py"):
            (kit / name).write_text("k = '" + key + "'\n")
        r = subprocess.run([sys.executable, str(SELF)], cwd=kit, capture_output=True, text=True, env=git_env())
        if r.returncode != 1 or "open.py" not in r.stdout or "held.py" in r.stdout or "also.py" in r.stdout:
            failures.append(f"pattern homes: exit {r.returncode}")

    # No catastrophic backtracking: a 20,000-character line of each pattern's near-hit stays fast.
    worst = [
        "-----BEGIN " + "AB " * 6700, "gh" + "p_" + "a" * 20000 + "_", "AK" + "IA" * 10000, "AI" + "za" + "-" * 20000,
        "xo" + "xb-" + "-" * 20000, ("s" + "k-") * 6700, "s" + "k_live_" * 2500, "ey" + "J" + "a" * 20000,
        ("ey" + "J" + "a" * 9 + ".") * 1500, "h" + "f_" + "a" * 20000, "_auth" + "Token=" * 1800,
        "a://" + "b" * 20000, "a://b:" * 3300, "x://" * 5000, ("pass" + "word='") * 2200,
        ("to" + "ken=" + "\"") + "a" * 20000, "a " * 10000, "a_" * 10000 + "pass" + "word=x",
        "pass" + "word=" + "a" * 20000, "export " + "a" * 20000 + "token=" + "b" * 300, "a" * 20000,
    ]
    start = time.monotonic()
    scan_lines([(i, line) for i, line in enumerate(worst, 1)], patterns)
    elapsed = time.monotonic() - start
    if elapsed >= 1.0:
        failures.append(f"speed: 20,000-character lines took {elapsed:.2f} s")

    # This file holds no key-shaped literal of its own (it is skipped as a pattern home, so check it directly).
    own = scan_lines(file_lines(SELF), patterns)
    if own:
        failures.append(f"self: {sum(len(v) for v in own.values())} key-shaped string(s) in this file")

    for f in failures:
        print(f"FAIL {f}")
    print(f"secret_scan self-test: {'ok' if not failures else f'{len(failures)} failure(s)'} "
          f"(Python {sys.version.split()[0]}, worst lines {elapsed * 1000:.0f} ms)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
