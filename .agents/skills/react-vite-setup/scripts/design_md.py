#!/usr/bin/env python3
"""Reads the tokens of a DESIGN.md in Google's format — YAML front matter between two `---` lines at the top of the
file (github.com/google-labs-code/design.md, docs/spec.md) — with Python's standard library alone.

    from design_md import front_matter, tokens
    data, body_start = front_matter(text)     # the front matter as nested dicts; the body's first line number
    for t in tokens(data): ...                # every token: its name, its theme or None, its value, its group

The YAML it reads is the subset a DESIGN.md uses: block mappings by indentation, plain, single- and double-quoted
scalars, `#` comments, and block lists of scalars. A flow mapping or list (`{a: 1}`, `[a, b]`), an anchor, a tag or a
block scalar (`|`, `>`) raises YamlError with its line, so a check reports it instead of misreading it (DESIGN_BRIEF
§15).

Token names (DESIGN_BRIEF §15): Google's groups keep the names code already uses — `colors` is `color`, `typography`
is `text`, `spacing` is `space`, `rounded` is `radius`; any other group keeps its own name. A theme is a sub-map whose
key names one (`light`, `dark`, `contrast`, `dim`, …) and is dropped from the name: `colors.light.bg.canvas` is
`color.bg.canvas` in theme `light`. A typography or motion token is one composite (`text.body`, `motion.menu-enter`)
with its properties. A value written `"{path.to.token}"` is a reference, resolved against the front matter.

    python3 design_md.py [FILE]     # print every token a DESIGN.md's front matter holds
    python3 design_md.py --test     # the reader's self-test
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

PREFIX = {"colors": "color", "typography": "text", "spacing": "space", "rounded": "radius"}
COMPOSITE = {"typography", "motion", "components"}  # each child is one token whose children are its properties
THEME = re.compile(r"^(?:light|dark|dim|contrast|high-contrast|light-contrast|dark-contrast|light-hc|dark-hc)$", re.I)
REF = re.compile(r"^\{([A-Za-z0-9_.-]+)\}$")
META = {"version", "name", "description", "omitted"}


class YamlError(ValueError):
    pass


def front_matter(text: str) -> tuple[dict, int]:
    """(the front matter as nested dicts, the 1-based number of the body's first line); ({}, 1) with none. The block
    opens on line 1 with exactly `---` and closes at the next line that is exactly `---`."""
    lines = text.splitlines()
    if not lines or lines[0].rstrip() != "---":
        return {}, 1
    for n, line in enumerate(lines[1:], 2):
        if line.rstrip() == "---":
            return parse_yaml("\n".join(lines[1:n - 1]), first_line=2), n + 1
    raise YamlError("line 1: the front matter opens with --- and never closes")


def scalar(raw: str, n: int) -> str:
    s = raw.strip()
    if s.startswith('"'):
        m = re.fullmatch(r'"((?:[^"\\]|\\.)*)"', s)
        if not m:
            raise YamlError(f"line {n}: an unclosed double-quoted string")
        return re.sub(r'\\(.)', lambda e: {"n": "\n", "t": "\t"}.get(e.group(1), e.group(1)), m.group(1))
    if s.startswith("'"):
        m = re.fullmatch(r"'((?:[^']|'')*)'", s)
        if not m:
            raise YamlError(f"line {n}: an unclosed single-quoted string")
        return m.group(1).replace("''", "'")
    if s[:1] in "{[&*!|>%@`":
        raise YamlError(f"line {n}: '{s[:20]}' — flow collections, anchors, tags and block scalars are not read; "
                        "write a block mapping, and quote a value that starts with one of {[&*!|>%@`")
    return s


def strip_comment(line: str) -> str:
    """The line without a `#` comment: a `#` at the start or after a space, outside quotes."""
    quote = None
    for i, c in enumerate(line):
        if quote:
            if c == quote and not (quote == '"' and line[i - 1] == "\\"):
                quote = None
        elif c in "\"'" and (i == 0 or line[i - 1] in " :-"):
            quote = c
        elif c == "#" and (i == 0 or line[i - 1] in " \t"):
            return line[:i].rstrip()
    return line.rstrip()


def parse_yaml(text: str, first_line: int = 1) -> dict:
    root: dict = {}
    stack: list[tuple[int, object]] = [(-1, root)]  # (indent, container)
    pending: tuple[int, dict, str] | None = None  # a key with no value yet: its indent, its parent, the key
    for n, raw in enumerate(text.splitlines(), first_line):
        if "\t" in raw[:len(raw) - len(raw.lstrip())]:
            raise YamlError(f"line {n}: indented with a tab")
        line = strip_comment(raw)
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        body = line.strip()
        if pending:
            p_indent, parent, key = pending
            pending = None
            if indent > p_indent:
                container: object = [] if body.startswith("- ") or body == "-" else {}
                parent[key] = container
                stack.append((indent, container))
            else:
                parent[key] = None
        while stack and indent < stack[-1][0]:
            stack.pop()
        if not stack or indent != stack[-1][0] and stack[-1][0] != -1:
            raise YamlError(f"line {n}: the indentation does not match the block above")
        if stack[-1][0] == -1 and indent:
            raise YamlError(f"line {n}: the first key is indented")
        holder = stack[-1][1]
        if body.startswith("- ") or body == "-":
            if not isinstance(holder, list):
                raise YamlError(f"line {n}: a list item where a key was expected")
            holder.append(scalar(body[2:], n) if body != "-" else None)
            continue
        m = re.fullmatch(r"((?:\"[^\"]*\"|'[^']*'|[^:\s][^:]*?))\s*:(?:\s+(.*))?", body)
        if not m:
            raise YamlError(f"line {n}: '{body[:30]}' is not `key: value`")
        if not isinstance(holder, dict):
            raise YamlError(f"line {n}: a key inside a list")
        key = scalar(m.group(1), n)
        if key in holder:
            raise YamlError(f"line {n}: the key '{key}' is defined twice")
        if m.group(2) is None or m.group(2) == "":
            holder[key] = None
            pending = (indent, holder, key)
        else:
            holder[key] = scalar(m.group(2), n)
    return root


def lookup(data: dict, path: str):
    node: object = data
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


def resolve(data: dict, value, seen: tuple = ()) -> str | None:
    """A value with its references followed; None for a reference that names nothing or loops."""
    if not isinstance(value, str):
        return None
    m = REF.match(value.strip())
    if not m:
        return value
    if m.group(1) in seen:
        return None
    return resolve(data, lookup(data, m.group(1)), seen + (m.group(1),))


def tokens(data: dict) -> list[dict]:
    """Every token in the front matter: {name, theme, value, group, props, raw}. `value` is the scalar, references
    followed; a composite (typography, motion, components) has `props` instead, each resolved; `raw` is what the
    file wrote, references unfollowed, so a generator can write a reference as one."""
    out: list[dict] = []

    def walk(group: str, node, path: list[str], theme: str | None) -> None:
        if isinstance(node, dict):
            if group in COMPOSITE and len(path) == 1 and theme is None and not THEME.match(path[0]):
                raw = {k: v for k, v in node.items() if not isinstance(v, dict)}
                out.append({"name": ".".join([PREFIX.get(group, group)] + path), "theme": None, "value": None,
                            "group": group, "props": {k: resolve(data, v) for k, v in raw.items()}, "raw": raw})
                return
            for k, v in node.items():
                if THEME.match(str(k)) and theme is None:
                    walk(group, v, path, str(k).lower())
                else:
                    walk(group, v, path + [str(k)], theme)
        elif node is not None and path:
            out.append({"name": ".".join([PREFIX.get(group, group)] + path), "theme": theme,
                        "value": resolve(data, node), "group": group, "props": None, "raw": node})

    for group, node in data.items():
        if group not in META:
            walk(group, node, [], None)
    return out


def themes(data: dict) -> list[str]:
    """The themes the front matter names, in the order they first appear."""
    seen: list[str] = []
    for t in tokens(data):
        if t["theme"] and t["theme"] not in seen:
            seen.append(t["theme"])
    return seen


def self_test() -> int:
    doc = ("---\nversion: alpha\nname: Demo  # a comment\ncolors:\n  light:\n    bg:\n      canvas: \"#FFFFFF\"\n"
           "    primary: \"#2457D6\"\n  dark:\n    bg:\n      canvas: '#111317'\n    primary: \"#7EA2FF\"\n"
           "font:\n  sans: \"system-ui, \\\"Segoe UI\\\", sans-serif\"\ntypography:\n  body:\n"
           "    fontFamily: \"{font.sans}\"\n    fontSize: 17px\nspacing:\n  xs: 4px\nmotion:\n  hover:\n"
           "    duration: \"{duration.fast}\"\nduration:\n  fast: 120ms\nomitted:\n  - components\n---\n\n# Demo\n")
    data, start = front_matter(doc)
    toks = {(t["name"], t["theme"]): t for t in tokens(data)}
    cases = [
        (start == doc.splitlines().index("---", 1) + 2, "the body starts after the closing ---"),
        (data["name"] == "Demo", "a comment after a value is dropped"),
        (toks[("color.bg.canvas", "light")]["value"] == "#FFFFFF", "colors.light.bg.canvas is color.bg.canvas, light"),
        (toks[("color.bg.canvas", "dark")]["value"] == "#111317", "a single-quoted value is read"),
        (toks[("text.body", None)]["props"]["fontFamily"] == 'system-ui, "Segoe UI", sans-serif',
         "a reference resolves, escapes and all"),
        (toks[("space.xs", None)]["value"] == "4px", "spacing is space"),
        (toks[("motion.hover", None)]["props"]["duration"] == "120ms", "a motion token's reference resolves"),
        (toks[("motion.hover", None)]["raw"]["duration"] == "{duration.fast}", "the raw reference is kept"),
        (data["omitted"] == ["components"], "a block list is read"),
        (themes(data) == ["light", "dark"], "the themes, in order"),
        (front_matter("# No front matter\n") == ({}, 1), "no front matter is empty"),
    ]
    for bad, what in (("---\na: {b: 1}\n---\n", "a flow mapping is refused"),
                      ("---\na: 1\na: 2\n---\n", "a duplicate key is refused"),
                      ("---\na:\n  b: 1\n c: 2\n---\n", "a broken indent is refused"),
                      ("---\na: 1\n", "an unclosed front matter is refused")):
        try:
            front_matter(bad)
            cases.append((False, what))
        except YamlError:
            cases.append((True, what))
    failed = [what for ok, what in cases if not ok]
    for what in failed:
        print(f"FAIL  {what}")
    print(f"design_md self-test: {len(cases) - len(failed)}/{len(cases)} cases pass")
    return 1 if failed else 0


def main(argv: list[str]) -> int:
    if "--test" in argv:
        return self_test()
    path = Path(argv[0]) if argv else Path("DESIGN.md")
    try:
        data, _ = front_matter(path.read_text(encoding="utf-8", errors="replace"))
    except YamlError as e:
        print(f"{path}: {e}")
        return 1
    for t in tokens(data):
        value = t["value"] if t["props"] is None else ", ".join(f"{k}={v}" for k, v in t["props"].items())
        print(f"{t['name']}" + (f" [{t['theme']}]" if t["theme"] else "") + f" = {value}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
