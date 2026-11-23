#!/usr/bin/env python3
"""The ux-content-writer judge's measured proxies: the UI strings ux_lint.py reads, measured against the room their
element has, and the share of them its rules flag. A proxy outside its range caps its quality dimension at 2; it never
fails a run.

    python3 .agents/skills/ux-content/scripts/ux_proxies.py          # the change: the strings on its changed lines
    python3 .agents/skills/ux-content/scripts/ux_proxies.py --all    # every UI file whole: the whole-product audit
    python3 .agents/skills/ux-content/scripts/ux_proxies.py FILE …   # these files, whole
    python3 .agents/skills/ux-content/scripts/ux_proxies.py --self-test

A review scores the change, an audit the product: bare, only the strings on the lines the diff against HEAD wrote in
the changed UI files are read (a new file: all of them); a string the change never touched never caps its review.
Measures, by dimension (the keys of .agents/evals/weights.json):
  short      strings longer than their element's room, in characters — none. The room is the project's own
             arithmetic, in UX_STRINGS["rooms"] in .agents/project.py: each a call (or `.field` for a string assigned
             to a config's field), the argument that holds the words, the characters that fit and the element's name —
             {"call": "MakeButton", "arg": 1, "chars": 10, "element": "a half button"}. A string whose element has no
             room wraps or is not measured; with no rooms, the room is not measured at all.
             Also the share of strings with a U8 or U10 hit (three full stops, "successfully")
  clear      the share of strings with a hit of U1, U5, U9, U11 or U13 (a generic button, "invalid", "e.g.", "click here",
             "enable") — none
  human      the share with U2, U3, U4, U7, U12 or U14 ("please", "!", "oops", title case, "the user", capitals) — none
  next-step  the share with U6 ("Error" as a title) — none
The rules are ux_lint.py's (UX_CONTENT §n there); the strings are those its reader finds with the project's calls, and for
the room also the calls and fields the rooms name. Writes
.cache/harness/proxies/ux-content-writer.json — {"judge", "at", "scope": "change" | "product" | "files", "metrics":
[{"dimension", "name", "value", "range": [lo, hi], "ok", "where"}]} — and prints a summary. Python 3.9+, standard library
only.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("ux_lint", HERE / "ux_lint.py")
ux_lint = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ux_lint)
ROOT = ux_lint.ROOT
PROXIES = ROOT / ".cache/harness/proxies"
JUDGE = "ux-content-writer"

DIMENSION_OF = {"U1": "clear", "U5": "clear", "U9": "clear", "U11": "clear", "U13": "clear",
                "U2": "human", "U3": "human", "U4": "human", "U7": "human", "U12": "human", "U14": "human",
                "U8": "short", "U10": "short", "U6": "next-step"}


def load_rooms() -> list:
    """The project's rooms, UX_STRINGS["rooms"]: [{"call", "arg", "chars", "element"}]; empty when it names none."""
    settings = ux_lint.load_settings()
    return list((settings[0] if settings else {}).get("rooms") or [])


def room_calls(rooms: list) -> tuple:
    """The patterns that place words in a sized element: each room's call, or its field's assignment."""
    out = []
    for r in rooms:
        c = r["call"]
        out.append(rf"\.{re.escape(c[1:])}\s*=" if c.startswith(".") else rf"\b{re.escape(c)}\b")
    return tuple(dict.fromkeys(out))


def room(call: str, arg: int, rooms: list) -> tuple | None:
    """(characters, the element) for the string at argument `arg` of `call` (`.field` for a field's assignment), from
    the project's rooms; None when the element wraps or is not measured."""
    for r in rooms:
        name = r["call"]
        same = call == name if name.startswith(".") else (call == name or call.endswith(("::" + name, "." + name)))
        if same and int(r.get("arg", 0)) == arg:
            return int(r["chars"]), r.get("element", name)
    return None


def enclosing(code: str, tokens: list, pos: int) -> tuple:
    """(the call's name, the argument's index, the call's text) for the literal at `pos`; for a literal assigned to a
    field, (".field", 0, the text before it)."""
    i = next((k for k, t in enumerate(tokens) if t[0] == pos), None)
    depth, commas = 0, 0
    for k in range(i - 1 if i is not None else -1, -1, -1):
        start, end, typ, content = tokens[k]
        if typ == "b" and content in ")]}":
            depth += 1
        elif typ == "b" and content in "([{":
            if depth == 0:
                if content != "(":
                    break
                name = re.search(r"([\w:]+)\s*$", code[:start])
                close = next((t[0] for t in tokens[i:] if t[2] == "b" and t[3] == ")"), pos)
                return (name.group(1) if name else "", commas, code[start:close + 1])
            depth -= 1
        elif typ == "p" and depth == 0:
            commas += 1
    stmt = code[max(code.rfind(";", 0, pos), code.rfind("{", 0, pos)) + 1:pos]
    field = re.search(r"\.(\w+)\s*=", stmt)
    if field:
        return "." + field.group(1), 0, code[max(0, pos - 1200):pos]
    return "", 0, ""


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, errors="replace").stdout


def changed_lines(path: str) -> set | None:
    """The file's lines the change wrote, numbered in the new file; None when the file is new (all of it)."""
    if git("ls-files", "--", path).strip() == "":
        return None
    lines: set = set()
    for m in re.finditer(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", git("diff", "-U0", "HEAD", "--", path), re.M):
        start, count = int(m.group(1)), int(m.group(2) if m.group(2) is not None else 1)
        lines.update(range(start, start + count))
    return lines


def measure(files: list, lines_of: dict | None = None, rooms: list | None = None, calls: tuple | None = None) -> tuple:
    """(strings read, hits by dimension, strings over their room, strings in sized elements); with `lines_of`
    {file: lines or None}, only the strings on those lines of each file (None: every line). `rooms` defaults to the
    project's; `calls`, the project's string calls (else ux_lint's defaults)."""
    rooms = load_rooms() if rooms is None else rooms
    fields = [r["call"][1:] for r in rooms if r["call"].startswith(".")]
    settings = ux_lint.load_settings()
    ux = settings[0] if settings else {}
    names = ux_lint.as_tuple(ux.get("names"))
    calls = calls or ux_lint.as_tuple(ux.get("calls")) or ux_lint.DEFAULT_CALLS
    cfg = {"calls": calls, "names": names, "case": ux.get("case", "sentence")}
    strings, by_dim, over, measured = 0, {d: [] for d in set(DIMENSION_OF.values())}, [], 0
    for f in files:
        try:
            text = ux_lint.decode((ROOT / f).read_bytes())
        except OSError:
            continue
        newlines = [m.start() for m in re.finditer("\n", text)]
        wanted = (lines_of or {}).get(f)
        keep = (lambda pos: True) if wanted is None else \
            (lambda pos: ux_lint.bisect.bisect_left(newlines, pos) + 1 in wanted)
        excepted = {ux_lint.bisect.bisect_left(newlines, m.start()) for m in re.finditer("ux-exception", text)}
        # The rules, as ux_lint runs them.
        for pos, raw in ux_lint.literals(f, text, calls):
            n = ux_lint.bisect.bisect_left(newlines, pos)
            if n in excepted or not keep(pos):
                continue
            for piece in ux_lint.pieces(raw):
                strings += 1
                dims = {DIMENSION_OF[r] for r in ux_lint.check(piece, cfg)}
                for d in dims:
                    by_dim[d].append(f"{f}:{n + 1} \"{piece[:50]}\"")
        # The room, with the calls that place words in a sized element.
        if not rooms:
            continue
        lx = ux_lint.Lexer(f)
        code, tokens = lx.lex(text)
        found = dict(ux_lint.literals(f, text, tuple(calls) + room_calls(rooms)))
        for m in (re.finditer(r"\.(?:%s)\s*=" % "|".join(map(re.escape, fields)), code) if fields else ()):  # each arm of a ternary assigned to a field
            end = code.find(";", m.end())
            found.update((t[0], t[3]) for t in tokens if t[2] == "s" and m.end() <= t[0] < end)
        for pos, raw in sorted(found.items()):
            if not keep(pos):
                continue
            call, arg, _ = enclosing(code, tokens, pos)
            fit = room(call, arg, rooms)
            if fit is None:
                continue
            for piece in ux_lint.pieces(raw):
                measured += 1
                if len(piece) > fit[0]:
                    over.append(f"{f}:{ux_lint.bisect.bisect_left(newlines, pos) + 1} \"{piece}\" {len(piece)} for "
                                f"{fit[1]}'s {fit[0]}")
    return strings, by_dim, over, measured


def metric(dimension: str, name: str, value: float, lo: float, hi: float, where: str) -> dict:
    return {"dimension": dimension, "name": name, "value": value, "range": [lo, hi], "ok": lo <= value <= hi,
            "where": where}


def proxies(strings: int, by_dim: dict, over: list, measured: int) -> list:
    out = []
    if measured:
        out.append(metric("short", "strings longer than their element's room", len(over), 0, 0,
                          "; ".join(over[:4]) or f"{measured} strings in sized elements, each fits"))
    if strings:
        for dim in ("clear", "short", "human", "next-step"):
            hits = by_dim.get(dim, [])
            out.append(metric(dim, f"share of strings with a {dim} hit", round(len(hits) / strings, 4), 0, 0,
                              "; ".join(hits[:3]) or f"none of {strings} strings"))
    return out


def self_test() -> int:
    failures = []

    def check(ok: bool, what: str):
        if not ok:
            failures.append(what)

    src = '''void Build(Screen *s) {
    MakeButton(row, "Calibrate the touch screen", true, OnGo);
    MakeButton(row, "Full", true, OnFull);
    ui::NewRow(list, "Display", "Refresh modes, contrast and the screen saver", OnEntry, nullptr);
    ui::NewRow(list, "Sound", "Volume", OnEntry, nullptr);
    KeyboardConfig config{};
    config.action = s_password ? "Join" : "Save changes";
    ui::NewLabel(s, Type::kBody, "Please wait!");
}
'''
    rooms = [{"call": "MakeButton", "arg": 1, "chars": 10, "element": "a half button"},
             {"call": "NewRow", "arg": 2, "chars": 33, "element": "a row's line"},
             {"call": ".action", "arg": 0, "chars": 6, "element": "the keyboard's footer button"}]
    path = "src/selftest.cpp"
    lx = ux_lint.Lexer(path)
    code, tokens = lx.lex(src)
    calls = ux_lint.DEFAULT_CALLS + (r"\b(?:ui::)?(?:Make|New)[A-Z]\w*",)  # the self-test's own, whatever the project's
    found = {raw: enclosing(code, tokens, pos)[:2] for pos, raw in ux_lint.literals(path, src, calls + room_calls(rooms))}
    check(found.get("Full") == ("MakeButton", 1), f"a button's words are its second argument: {found.get('Full')}")
    check(found.get("Volume") == ("ui::NewRow", 2), f"a row's line is its third argument: {found.get('Volume')}")
    arm = next((t[0] for t in tokens if t[2] == "s" and t[3] == "Save changes"), -1)
    check(enclosing(code, tokens, arm)[:2] == (".action", 0), f"a ternary's arm assigned to a field: "
                                                              f"{enclosing(code, tokens, arm)[:2]}")
    import tempfile
    with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
        f = Path(tmp) / "selftest.cpp"
        f.write_text(src)
        rel = str(f.relative_to(ROOT))
        strings, by_dim, over, measured = measure([rel], rooms=rooms, calls=calls)
        none = measure([rel], rooms=[], calls=calls)
    text = " ".join(over)
    check('"Calibrate the touch screen" 26' in text and '"Full"' not in text, f"26 characters overflow a half "
          f"button's 10, 4 fit: {over}")
    check('"Refresh modes, contrast and the screen saver" 44' in text and '"Volume"' not in text,
          "a row's line holds 33")
    check('"Save changes" 12' in text and '"Join"' not in text, "the keyboard's footer holds 6")
    check(measured == 6 and none[3] == 0, f"six strings in sized elements, none with no rooms: {measured}, {none[3]}")
    ms = proxies(strings, by_dim, over, measured)
    human = next((m for m in ms if m["name"] == "share of strings with a human hit"), None)
    check(human is not None and human["value"] > 0 and "Please wait" in human["where"], f"'Please wait!' is human's: {human}")
    # The change's scope: only the strings on the changed lines — here the line with "Full" alone.
    with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
        f = Path(tmp) / "selftest.cpp"
        f.write_text(src)
        rel = str(f.relative_to(ROOT))
        line = next(k for k, ln in enumerate(src.split("\n"), 1) if '"Full"' in ln)
        strings, by_dim, over, measured = measure([rel], {rel: {line}}, rooms, calls)
    check(strings == 1 and measured == 1 and not over, f"a change to one line reads its one string: {strings}, "
          f"{measured}, {over}")
    check(not any("Please wait" in h for hits in by_dim.values() for h in hits), "the untouched 'Please wait!' caps "
          "nothing in the change's scope")
    for f in failures:
        print(f"FAIL  {f}")
    total = 10
    print(f"ux_proxies self-test: {total - len(failures)} of {total} checks pass")
    return 1 if failures else 0


def main(argv: list) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("files", nargs="*", help="files to read (default: the UI files changed against HEAD)")
    parser.add_argument("--all", action="store_true", help="every UI file")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    ui_files, _ = ux_lint.select(ux_lint.tracked_files(), ux_lint.load_settings())
    scope, lines_of = ("files" if args.files else "product" if args.all else "change"), None
    if args.files:
        files = args.files
    elif args.all:
        files = ui_files
    else:
        changed = set(git("diff", "--name-only", "HEAD").split()) | set(git("ls-files", "--others",
                                                                            "--exclude-standard").split())
        files = [f for f in ui_files if f in changed]
        lines_of = {f: changed_lines(f) for f in files}
    strings, by_dim, over, measured = measure(files, lines_of)
    metrics = proxies(strings, by_dim, over, measured)
    # What was measured, file by file: empty, the change wrote no string a person reads.
    in_scope = [f for f in files if sum(measure([f], lines_of)[0::3])] if strings or measured else []
    PROXIES.mkdir(parents=True, exist_ok=True)
    path = PROXIES / f"{JUDGE}.json"
    at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    path.write_text(json.dumps({"judge": JUDGE, "at": at, "scope": scope, "scope_what": "the UI strings on the lines "
                                "the change wrote", "in_scope": in_scope, "metrics": metrics}, indent=1,
                               ensure_ascii=False) + "\n")
    outside = [m for m in metrics if not m["ok"]]
    print(f"{JUDGE} ({scope}): {len(files)} UI files, {strings} strings, {measured} in sized elements; {len(metrics)} metrics, "
          f"{len(outside)} outside their range — {path.relative_to(ROOT)}"
          + ("" if files else " (no changed UI file; --all reads every one)"))
    for m in metrics:
        lo, hi = m["range"]
        print(f"  {'ok ' if m['ok'] else 'OUT'} {m['dimension']}: {m['name']} = {m['value']:g} (range {lo:g}–{hi:g})"
              f" — {m['where'][:170]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
