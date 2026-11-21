#!/usr/bin/env python3
"""The storybook skill's check: story files against the story layout in references/storybook.md (cited
`STORYBOOK §n`). It finds what the text of a story file and its component shows; the docs page, the controls and the
stories' own tests show the rest.

    python3 .agents/skills/storybook/scripts/story_check.py            # every story file, against the baseline
    python3 .agents/skills/storybook/scripts/story_check.py FILE …     # some story files, no baseline
    python3 .agents/skills/storybook/scripts/story_check.py --test     # the self-test

Which files: `*.stories.{tsx,ts,jsx,js}` — in a repo with the agent-harness kit, those under UI_PATHS from
`.agents/project.py` (empty there means none yet); in any other repo, every tracked one outside vendored and generated
folders. A line that carries `story-exception` is skipped — write the reason beside it.

  SB1  the default export names no `component:` — no docs page, no props table, no manifest entry      STORYBOOK §2
  SB2  a story export with no JSDoc comment directly above it — the summary people and agents read      STORYBOOK §5
  SB3  a prop the component declares that no story mentions — in `args`, `argTypes` or the JSX           STORYBOOK §3
  SB4  the component's export, or one of its own props, has no JSDoc comment                            STORYBOOK §5
  SB5  a theme the preview's theme switch offers, past the first, that no story pins with `globals`     STORYBOOK §6
  SB6  a story name that joins two concepts — `…And…`, or `All…`                                        STORYBOOK §4
  SB7  a callback mocked with `fn()` and no `play` function in the file to check it is called           STORYBOOK §7

The component: the one `component:` names, found through the file's relative import (`.tsx`, `.ts`, `.jsx`, `.js` or
a folder's `index`). Its props: the body of `interface <Name>Props` or `type <Name>Props = … { … }` — a props type
with no body of its own (`type ButtonProps = ButtonHTMLAttributes<…>`) has no own props, and SB3 and SB4's props
rule pass. The themes: the nearest `.storybook/preview.*` above the story file — a toolbar global's `{ value: '…' }`
items, or `@storybook/addon-themes`' `themes: { … }` keys; the first, or `initialGlobals`' or `defaultTheme`'s, is
the default.

What it cannot see: whether a story shows one concept, whether a summary says why rather than what, whether a prop's
values each have their story, or whether a play function checks the right thing. Its limits: SB3 counts a prop
mentioned anywhere in the story file, as a word; SB3 and SB4 read one props type per component and skip a component
it cannot resolve, saying so; SB6 keys on the name only. A pass is a floor, never a review.

Prints one line per hit — `file:line: SB<n> what — fix` — then a count and how many story files it read. A whole-tree
run over BASELINE exits 1; a run on named files exits 1 on any hit. Python 3.9+, standard library only.
"""

from __future__ import annotations

import fnmatch
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip()
            or ".")

# Hits sanctioned today, each with its reason. A new hit on a line you touched is yours to fix.
BASELINE = 0
STORY = re.compile(r"\.stories\.(?:tsx|ts|jsx|js)$")
SKIP_DIRS = ("node_modules/", "vendor/", "third_party/", "build/", "dist/", "out/", "coverage/", ".cache/", ".venv/",
             "storybook-static/", ".agents/", ".claude/", ".codex/", ".github/")
SOURCE_EXT = (".tsx", ".ts", ".jsx", ".js")

EXPORT_STORY = re.compile(r"^export\s+const\s+([A-Za-z_$][\w$]*)\b", re.M)
COMPONENT = re.compile(r"\bcomponent\s*:\s*([A-Za-z_$][\w$]*)")
NAMED_IMPORT = re.compile(r"import\s*(?:type\s+)?\{([^}]*)\}\s*from\s*['\"](\.[^'\"]*)['\"]")
DEFAULT_IMPORT = re.compile(r"import\s+([A-Za-z_$][\w$]*)\s*(?:,\s*\{[^}]*\})?\s*from\s*['\"](\.[^'\"]*)['\"]")
PROP_KEY = re.compile(r"^\s*(?:readonly\s+)?['\"]?([A-Za-z_$][\w$]*)['\"]?\s*\??\s*[:(]")
JOINED = re.compile(r"[a-z0-9]And[A-Z]|^All[A-Z]")
THEME_ITEM = re.compile(r"\{\s*value\s*:\s*['\"]([^'\"]+)['\"]")
ADDON_THEMES = re.compile(r"\bthemes\s*:\s*\{([^}]*)\}")
ADDON_KEY = re.compile(r"['\"]?([A-Za-z_$][\w$-]*)['\"]?\s*:")
INITIAL = re.compile(r"(?:initialGlobals\s*:\s*\{[^}]*\btheme\s*:|defaultTheme\s*:)\s*['\"]([^'\"]+)['\"]")


def line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def has_jsdoc_before(text: str, pos: int) -> bool:
    """A `/** … */` comment ends on the lines just above `pos` (blank lines between are allowed)."""
    before = text[:pos].rstrip()
    if not before.endswith("*/"):
        return False
    start = before.rfind("/*")
    return start >= 0 and before.startswith("/**", start)


def body_after(text: str, pos: int) -> str | None:
    """The `{ … }` body of a type that starts at `pos`, or None when the type closes before any brace of its own."""
    depth_angle = 0
    i = pos
    while i < len(text):
        c = text[i]
        if c == "<":
            depth_angle += 1
        elif c == ">" and depth_angle:
            depth_angle -= 1
        elif depth_angle == 0 and c == "{":
            depth, j = 0, i
            while j < len(text):
                if text[j] == "{":
                    depth += 1
                elif text[j] == "}":
                    depth -= 1
                    if depth == 0:
                        return text[i + 1:j]
                j += 1
            return text[i + 1:]
        elif depth_angle == 0 and (c == ";" or text.startswith("\n\n", i) or text.startswith("\nexport", i)):
            return None
        i += 1
    return None


def own_props(component_text: str, name: str) -> list[tuple[str, bool]] | None:
    """(prop, documented) for each own prop of `<name>Props`, or of the file's only `…Props` type; None when no props
    type is found."""
    m = re.search(r"\b(?:interface|type)\s+" + re.escape(name) + r"Props\b", component_text)
    if not m:
        found = list(re.finditer(r"\b(?:interface|type)\s+\w*Props\b", component_text))
        m = found[0] if len(found) == 1 else None
    if not m:
        return None
    body = body_after(component_text, m.end())
    if body is None:
        return []
    props, depth, prev = [], 0, ""
    for line in body.split("\n"):
        if depth == 0:
            k = PROP_KEY.match(line)
            if k:
                props.append((k.group(1), prev.rstrip().endswith("*/")))
        depth += line.count("{") + line.count("(") + line.count("[") - line.count("}") - line.count(")") \
            - line.count("]")
        if line.strip():
            prev = line
    return props


def resolve(story: Path, spec: str) -> Path | None:
    base = (story.parent / spec)
    for cand in [base] + [base.with_name(base.name + e) for e in SOURCE_EXT] + [base / f"index{e}" for e in SOURCE_EXT]:
        if cand.is_file() and cand.suffix in SOURCE_EXT:
            return cand
    return None


def component_file(story: Path, text: str, name: str) -> Path | None:
    for m in NAMED_IMPORT.finditer(text):
        names = [n.strip().split(" as ")[-1].strip() for n in m.group(1).split(",")]
        if name in names:
            return resolve(story, m.group(2))
    for m in DEFAULT_IMPORT.finditer(text):
        if m.group(1) == name:
            return resolve(story, m.group(2))
    return None


def preview_themes(story: Path) -> list[str]:
    """The themes the nearest `.storybook/preview.*` offers, the default first; empty when there is no switch."""
    for folder in [story.parent, *story.parent.parents]:
        for ext in SOURCE_EXT:
            preview = folder / ".storybook" / f"preview{ext}"
            if preview.is_file():
                text = preview.read_text(errors="replace")
                themes = THEME_ITEM.findall(text)
                if not themes:
                    a = ADDON_THEMES.search(text)
                    themes = ADDON_KEY.findall(a.group(1)) if a else []
                initial = INITIAL.search(text)
                if initial and initial.group(1) in themes:
                    themes.remove(initial.group(1))
                    themes.insert(0, initial.group(1))
                return themes
        if (folder / ".git").exists() or folder == ROOT:
            break
    return []


def scan(story: Path, text: str) -> list[tuple[int, str]]:
    """Every hit in one story file: (line, message)."""
    hits: list[tuple[int, str]] = []
    comp = COMPONENT.search(text)
    if not comp:
        dflt = re.search(r"^export\s+default\b", text, re.M)
        hits.append((line_of(text, dflt.start()) if dflt else 1,
                     "SB1 the default export names no `component:` — name it, so the docs page, the props table and "
                     "the manifest find it"))
    stories = [m for m in EXPORT_STORY.finditer(text) if m.group(1) != "meta"]
    for m in stories:
        if not has_jsdoc_before(text, m.start()):
            hits.append((line_of(text, m.start()), f"SB2 {m.group(1)} has no JSDoc comment above it — add `/** "
                         "@summary <why to reach for this story> */`"))
        if JOINED.search(m.group(1)):
            hits.append((line_of(text, m.start()), f"SB6 {m.group(1)} joins two concepts — split it into one story "
                         "per concept"))
    if comp:
        cfile = component_file(story, text, comp.group(1))
        if cfile is not None:
            ctext = cfile.read_text(errors="replace")
            exp = re.search(r"^export\s+(?:default\s+)?(?:function|const|class)\s+" + re.escape(comp.group(1))
                            + r"\b", ctext, re.M)
            if exp and not has_jsdoc_before(ctext, exp.start()):
                hits.append((line_of(text, comp.start()), f"SB4 {comp.group(1)} has no JSDoc comment on its export "
                             f"in {cfile.name} — say what it is and when to use it, with `@summary`"))
            props = own_props(ctext, comp.group(1)) or []
            body = "\n".join(l for l in text.split("\n") if not l.lstrip().startswith("import "))
            for prop, documented in props:
                if not re.search(r"(?<![\w$])" + re.escape(prop) + r"(?![\w$])", body):
                    hits.append((line_of(text, comp.start()), f"SB3 the prop `{prop}` appears in no story — give it "
                                 "an arg, an argType or a story of its own"))
                if not documented:
                    hits.append((line_of(text, comp.start()), f"SB4 the prop `{prop}` has no JSDoc comment in "
                                 f"{cfile.name} — one line on what it does"))
    for theme in preview_themes(story)[1:]:
        if not re.search(r"\bglobals\s*:\s*\{[^}]*\btheme\s*:\s*['\"]" + re.escape(theme) + r"['\"]", text):
            hits.append((line_of(text, comp.start()) if comp else 1, f"SB5 no story pins the `{theme}` theme — add "
                         f"one with `globals: {{ theme: '{theme}' }}` and `tags: ['!manifest']`"))
    if re.search(r"\bfn\s*\(\s*\)", text) and not re.search(r"\bplay\s*[:(]", text):
        pos = re.search(r"\bfn\s*\(\s*\)", text).start()
        hits.append((line_of(text, pos), "SB7 a callback is mocked with `fn()` and no story has a `play` function — "
                     "check it is called"))
    lines = text.split("\n")
    return sorted({(n, msg) for n, msg in hits if not (0 < n <= len(lines) and "story-exception" in lines[n - 1])})


def ui_patterns() -> tuple | None:
    """UI_PATHS from the kit's settings, or None when the repo has no kit."""
    settings = ROOT / ".agents/project.py"
    if not settings.is_file():
        return None
    sys.path.insert(0, str(settings.parent))
    import project  # noqa: E402 — the kit's settings
    return tuple(getattr(project, "UI_PATHS", ()))


def matches(path: str, patterns) -> bool:
    def one(p: str) -> bool:
        glob = any(c in p for c in "*?[")
        if p.endswith("/"):
            return fnmatch.fnmatch(path, p + "*") if glob else path.startswith(p)
        return fnmatch.fnmatch(path, p) if glob else path == p
    return any(one(p) for p in patterns)


def story_files() -> list[str]:
    tracked = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=ROOT,
                             capture_output=True, text=True).stdout.splitlines()
    patterns = ui_patterns()
    keep = (lambda f: matches(f, patterns)) if patterns is not None else (lambda f: not f.startswith(SKIP_DIRS)
                                                                         and "/node_modules/" not in f)
    return [f for f in tracked if STORY.search(f) and keep(f) and (ROOT / f).is_file()]


def run(files: list, named: bool) -> tuple:
    out: list[str] = []
    hits: list[str] = []
    read = 0
    for f in files:
        if not STORY.search(f):
            out.append(f"{f}: not a story file — skipped")
            continue
        path = ROOT / f
        try:
            text = path.read_text(errors="replace")
        except OSError:
            out.append(f"{f}: cannot be read — not checked")
            continue
        read += 1
        hits += [f"{f}:{n}: {msg}" for n, msg in scan(path, text)]
    out += hits
    limit = 0 if named else BASELINE
    out.append(f"SB1–SB7 story layout — {len(hits)} hits in {read} story files"
               + ("" if named else f" (baseline {BASELINE})"))
    if not read:
        why = ("no named file is a readable story file" if named
               else "UI_PATHS in .agents/project.py is empty or holds no story file" if ui_patterns() is not None
               else "no tracked file is a story file")
        out.append(f"read no story files — nothing was checked: {why}")
    if len(hits) > limit:
        out.append("FAIL — fix each hit, or mark a sanctioned one `story-exception` with its reason")
        return out, 1
    return out, 0


GOOD_COMPONENT = """import styles from './chip.module.css'

export interface ChipProps {
  /** The words on the chip */
  label: string
  /** Shown selected, with a check */
  selected?: boolean
  /** Called when the person presses the chip */
  onToggle?: (next: boolean) => void
}

/**
 * A choice that can be turned on and off.
 * @summary for filters a person turns on and off
 */
export function Chip({ label, selected = false, onToggle }: ChipProps) {
  return <button aria-pressed={selected} onClick={() => onToggle?.(!selected)}>{label}</button>
}
"""

GOOD_STORIES = """import type { Meta, StoryObj } from '@storybook/react-vite'
import { expect, fn } from 'storybook/test'
import { Chip } from './chip'

const meta = {
  title: 'UI/Chip',
  component: Chip,
  args: { label: 'Vegetarian', onToggle: fn() },
  argTypes: { selected: { control: 'boolean' } },
} satisfies Meta<typeof Chip>

export default meta
type Story = StoryObj<typeof meta>

/** @summary the default: a filter not yet chosen */
export const Default: Story = {
  play: async ({ args, canvas, userEvent }) => {
    await userEvent.click(canvas.getByRole('button', { name: 'Vegetarian' }))
    await expect(args.onToggle).toHaveBeenCalledWith(true)
  },
}

/** @summary a filter the person has chosen */
export const Selected: Story = { args: { selected: true } }

/** The default in the dark theme, for the eye and the accessibility test */
export const Dark: Story = { globals: { theme: 'dark' }, tags: ['!manifest'] }
"""

PREVIEW = """const preview = {
  globalTypes: { theme: { toolbar: { items: [
    { value: 'light', title: 'Light' },
    { value: 'dark', title: 'Dark' },
  ] } } },
  initialGlobals: { theme: 'light' },
}
export default preview
"""


def self_test() -> int:
    failures = []

    def expect(what: str, got, want) -> None:
        if got != want:
            failures.append(f"{what}: got {got!r}, want {want!r}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / ".git").mkdir()
        (root / ".storybook").mkdir()
        (root / ".storybook/preview.tsx").write_text(PREVIEW)
        ui = root / "src/components/ui"
        ui.mkdir(parents=True)
        (ui / "chip.tsx").write_text(GOOD_COMPONENT)
        story = ui / "chip.stories.tsx"

        def rules(text: str) -> list[str]:
            return sorted(msg[:3] for _, msg in scan(story, text))

        expect("a story file in the layout is clean", rules(GOOD_STORIES), [])
        expect("themes from the toolbar, default first", preview_themes(story), ["light", "dark"])
        expect("SB1 no component", "SB1" in rules(GOOD_STORIES.replace("  component: Chip,\n", "")), True)
        expect("SB2 a story with no JSDoc", rules(GOOD_STORIES.replace("/** @summary a filter the person has chosen "
                                                                        "*/\n", "")), ["SB2"])
        expect("SB2 a line comment is not JSDoc", rules(GOOD_STORIES.replace("/** @summary a filter the person has "
                                                                              "chosen */", "// chosen")), ["SB2"])
        expect("SB3 a prop no story mentions", rules(GOOD_STORIES.replace("  argTypes: { selected: { control: "
                                                                          "'boolean' } },\n", "").replace(
            "{ args: { selected: true } }", "{}")), ["SB3"])
        (ui / "chip.tsx").write_text(GOOD_COMPONENT.replace("  /** Shown selected, with a check */\n", ""))
        expect("SB4 an undocumented prop", rules(GOOD_STORIES), ["SB4"])
        (ui / "chip.tsx").write_text(GOOD_COMPONENT.replace("/**\n * A choice that can be turned on and off.\n"
                                                            " * @summary for filters a person turns on and off\n */\n",
                                                            ""))
        expect("SB4 an undocumented component", rules(GOOD_STORIES), ["SB4"])
        (ui / "chip.tsx").write_text("import type { ButtonHTMLAttributes } from 'react'\n\n"
                                     "export type ChipProps = ButtonHTMLAttributes<HTMLButtonElement>\n\n"
                                     "/** A chip */\nexport function Chip(props: ChipProps) { return null }\n")
        expect("a props type with no body has no own props", rules(GOOD_STORIES), [])
        (ui / "chip.tsx").write_text(GOOD_COMPONENT)
        expect("SB5 the dark theme unpinned", rules(GOOD_STORIES.replace("{ globals: { theme: 'dark' }, tags: "
                                                                         "['!manifest'] }", "{}")), ["SB5"])
        expect("SB6 two concepts in a name", rules(GOOD_STORIES.replace("Selected: Story", "SelectedAndDisabled: "
                                                                         "Story")), ["SB6"])
        expect("SB6 a kitchen sink", rules(GOOD_STORIES.replace("Selected: Story", "AllStates: Story")), ["SB6"])
        no_play = re.sub(r"export const Default: Story = \{.*?\n\}\n", "export const Default: Story = {}\n",
                         GOOD_STORIES, flags=re.S)
        expect("SB7 fn() never checked", rules(no_play), ["SB7"])
        expect("story-exception skips its line", rules(GOOD_STORIES.replace(
            "export const Selected: Story", "export const SelectedAndDisabled: Story // story-exception: the pair is "
            "the point")), [])
        (root / ".storybook/preview.tsx").write_text("import { withThemeByDataAttribute } from "
                                                     "'@storybook/addon-themes'\nexport const decorators = "
                                                     "[withThemeByDataAttribute({ themes: { light: 'light', "
                                                     "dark: 'dark', contrast: 'contrast' }, defaultTheme: 'light', "
                                                     "attributeName: 'data-theme' })]\n")
        expect("themes from addon-themes", preview_themes(story), ["light", "dark", "contrast"])
        expect("SB5 every extra theme", rules(GOOD_STORIES), ["SB5"])
        (root / ".storybook/preview.tsx").write_text("export default {}\n")
        expect("no theme switch, no SB5", rules(GOOD_STORIES.replace("{ globals: { theme: 'dark' }, tags: "
                                                                     "['!manifest'] }", "{}")), [])
    for f in failures:
        print(f"FAIL {f}")
    print(f"story_check self-test — {'FAIL' if failures else 'pass'} ({len(failures)} failures)")
    return 1 if failures else 0


def main(argv: list[str]) -> int:
    if argv[:1] == ["--test"]:
        return self_test()
    named = bool(argv)
    lines, code = run(argv if named else story_files(), named)
    for line in lines:
        print(line)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
