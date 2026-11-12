#!/usr/bin/env python3
"""Runs a build, test or install command and prints its result, not its work: the exit status, the time it took, the
error and warning lines it printed, and on a failure the last lines that matter. The full output goes to a log file,
so a long build log never lands in the agent's context (docs/AGENT_HARNESS.md §7.2, §18.1).

    python3 .agents/skills/build-run-test/scripts/quiet.py -- npm run build
    python3 .agents/skills/build-run-test/scripts/quiet.py --name test -- pytest -q
    python3 .agents/skills/build-run-test/scripts/quiet.py --tail 40 -- xcodebuild -scheme App build

Logs go to .cache/harness/logs/<name>-<time>.log (git-ignored); `--log-dir` puts them elsewhere. The exit status is
the command's own.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip()
            or ".")
PROBLEM = re.compile(r"\b(error|err!|fatal|failed|failure|exception|traceback|warning|warn)\b", re.I)
MAX_PROBLEMS = 15


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--name", help="a short name for the log file; the program's name by default")
    parser.add_argument("--log-dir", default=str(ROOT / ".cache/harness/logs"))
    parser.add_argument("--tail", type=int, default=20, help="lines of the output's end to print on a failure")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="the command, after --")
    args = parser.parse_args()
    cmd = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not cmd:
        parser.error("no command — put it after --")
    log_dir = Path(args.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    log = log_dir / f"{args.name or Path(cmd[0]).name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.log"
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, errors="replace")
        code, out = proc.returncode, proc.stdout + proc.stderr
    except FileNotFoundError:
        code, out = 127, f"{cmd[0]}: not found"
    log.write_text(out)
    lines = [line.rstrip() for line in out.splitlines() if line.strip()]
    problems = [line for line in lines if PROBLEM.search(line)]
    print(f"{'PASS' if code == 0 else 'FAIL'}  `{' '.join(cmd)}` exit {code} in {time.time() - t0:.0f} s — "
          f"{len(lines)} lines, log: {log}")
    if problems:
        print(f"  {len(problems)} error/warning line(s)" + (f", first {MAX_PROBLEMS}:" if len(problems) > MAX_PROBLEMS
                                                             else ":"))
        for line in problems[:MAX_PROBLEMS]:
            print(f"    | {line[:200]}")
    if code != 0:
        print(f"  last {min(args.tail, len(lines))} line(s):")
        for line in lines[-args.tail:]:
            print(f"    | {line[:200]}")
    return code


if __name__ == "__main__":
    sys.exit(main())
