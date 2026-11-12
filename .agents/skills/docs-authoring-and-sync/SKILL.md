---
name: docs-authoring-and-sync
description: Creates, writes, restructures and keeps true the docs in docs/, carrying the documentation guidelines with it (references/guidelines.md) so the folder works in any repo — a new doc scaffolded from the template for its type (new_doc.py: rules, interface, system, config, notes, requirements) and listed in README, a new section, rule, trap or open item, a value, token or symbol that changed in code, a heading renamed or renumbered, a doc rewritten without loss — and runs the doc checks before committing (title, contents table, numbering, anchors, § citations, fences, bold headings, history and filler words, tag legend, ASCII art, Mermaid colours, line numbers, README listing, long sections, links). Use when creating a doc, adding or editing anything in docs/, documenting a feature, a system or a decision, changing code or a design token a doc describes, closing an open item, splitting a long doc, or asked "write docs for", "document this", "update the docs", "rewrite this doc" or "check the docs".
---

# Docs authoring and sync

How every doc in `docs/` is created, written, kept in step with the code, and rewritten without losing anything. The
rules and their reasons are DOCUMENTATION_GUIDELINES (GUIDELINES below), kept in this skill at
[references/guidelines.md](references/guidelines.md); this page indexes them — each rule is one line citing the § that
holds it — and is the home of the steps the guidelines point to: the Procedure and the Checks. The guidelines win if
this page and they disagree — fix this page. In the agent-harness kit, the `doc-writer` agent creates and writes docs
with this skill and the `doc-reviewer` checks them (`.agents/agents/`).

**Portable.** This folder is self-contained, and links to nothing outside itself (it names the rest of a kit in
backticks): the guidelines, a template per doc type
([references/templates/](references/templates/)), the doc scaffolder and the doc checks
([scripts/](scripts/)). Copy it into any repo's `.agents/skills/` (or `.claude/skills/`) and it works there: the
scripts read `PROJECT_NAME`, `DOC_PREFIX` and the code's paths from `.agents/project.py` when the repo has one, and
fall back to their defaults when it does not ([scripts/_config.py](scripts/_config.py)). They need git and Python 3.9+.

## When to use

- Creating a new doc — for a feature, a system, the design tokens, a setting, a requirement, the open items.
- Writing a new section, rule, trap, measurement or open item.
- Changing a design token, component, API, setting, stored key or behaviour that a doc or code comment describes.
- Renaming a doc or a heading, renumbering, or splitting a long doc.
- Rewriting or reorganising a doc; closing an open item; the last pass before a commit.

## Rules

### Do

1. **Optimize, never minimize** — remove only for a §4.6 reason (GUIDELINES §1 Principle 3, §4.6, §8).
2. **Put workflow in the kit and knowledge in the doc**; a section emptied this way keeps its number as a one-line
   pointer (GUIDELINES §1 Principle 7, §3.3, §4.6).
3. **Cite only `docs/` and the rules kept in the kit** — `.agents/HARNESS.md` and skills' `references/` (GUIDELINES §1
   Principle 8).
4. **Open with what the doc type needs** (GUIDELINES §2), **in the §3.2 order**; a project doc is
   `docs/<PREFIX>_<TOPIC>.md` titled `# <Project> — <Topic>`; a project-wide doc drops the prefix, names no project
   and links only its siblings (GUIDELINES §3.1, §3.2).
5. **Keep blocks in §3.3 order and omit empty ones** — no "None" or "TBD" (GUIDELINES §3.3).
6. **Number in order, never renumber; add under the next free number** — an unavoidable renumber updates every inbound
   `§n` in the same change (GUIDELINES §3.4, §7).
7. **Put an open item's status in its heading or row; a closed item's outcome goes into the owning doc and the item
   leaves** (GUIDELINES §3.4, §4.3).
8. **Keep a contents table on a doc over ~150 lines**, three columns, GitHub slugs, updated with every heading edit
   (GUIDELINES §3.5).
9. **Make each section self-contained and answer first**, in the §3.6 order (GUIDELINES §3.6).
10. **Capture what §4.1 lists; state each rule in one line, then its reason**, keeping every reason that stops a known
    failure returning (GUIDELINES §4.1, §4.2).
11. **Describe the repo as it is now** — keep the reason, drop the story (GUIDELINES §4.3).
12. **Restate a code, config or token value with its name and the file a person edits** — the source file, not the
    generated one; keep restated tables complete (GUIDELINES §4.4).
13. **Source every figure with a tag the legend defines**; a measurement records its conditions; a tuned constant's
    comment carries its method, date and value (GUIDELINES §4.5).
14. **Keep the project facts in the doc type that owns each** (GUIDELINES §4.7).
15. **Keep one owner per fact** — within a doc and across docs; the others link (GUIDELINES §4.6, §5).
16. **Write in the §5 style and the §6 mechanics; draw every flow in Mermaid** (GUIDELINES §5, §6, §6.1).
17. **Change docs in the same commit as the code; grep the symbol and the behaviour first** (GUIDELINES §7).
18. **List every doc in README.md's Documentation section** (GUIDELINES §7).

### Never

- **Remove for length** (GUIDELINES §4.6, §9).
- **Write history** — *used to*, *was*, *former*, *originally*, *until recently*, *closed on*, changelogs,
  investigation narratives (GUIDELINES §4.3).
- **Leave knowledge only in code comments, config comments, commit history, a design file or a skill** (GUIDELINES §1
  Principle 1).
- **Put a suspected bug from reading code into a doc** — what the product does wins; ask the person to check it on the
  target, then write what it does (GUIDELINES §7).
- **Write filler or "as above" / "the earlier table"** (GUIDELINES §3.6, §5).
- **Use ASCII art, `style` or `classDef` in Mermaid, or diagram a lookup** (GUIDELINES §6.1).

## Procedure

### Creating a doc

GUIDELINES §2, §3 and §4 hold the rules these steps follow.

1. **Check it needs a new doc** — grep `docs/` for the topic (`git grep -n -i "<topic words>" docs`); a topic another
   doc owns is a new section there, under its next free number (GUIDELINES §3.4, §5).
2. **Pick the type** by what readers come for (GUIDELINES §2) —
   `python3 .agents/skills/docs-authoring-and-sync/scripts/new_doc.py --list`.
3. **Scaffold it**:
   `python3 .agents/skills/docs-authoring-and-sync/scripts/new_doc.py --type <type> --topic <TOPIC> --purpose "<1–4
   lines>"` [`--summary "<one line for README>"`]. It writes `docs/<PREFIX>_<TOPIC>.md` with the opening block and
   the blocks for its type, in §3.3 order, and lists it in README's Documentation section in one line — the summary,
   or the purpose's first sentence. It never overwrites a doc.
4. **Gather the facts before writing** — read the code, config and design files it describes; ask the person for what
   only they know (why a decision was made, what the target showed). A fact you could not verify is an open item,
   tagged `[?]`, never a guess written as fact (GUIDELINES §4.5).
5. **Fill every `<…>`** — one fact per bullet, the rule first and its reason after, names in backticks, a unit on every
   number, a source tag on every figure (GUIDELINES §3.6, §4.2, §5). Draw any flow in Mermaid (§6.1).
6. **Drop the blocks that stayed empty**, and add a contents table once the doc passes ~150 lines (GUIDELINES §3.3,
   §3.5).
7. **Keep workflow out** — steps, recipes and checklists go to the skill that runs them, linked (GUIDELINES §1
   Principle 7).
8. **Run the checks** below; leave no hit. Then ask the `doc-reviewer`.

### Keeping docs true

GUIDELINES §7 holds the rules these steps follow.

1. Grep the symbol and the behaviour: `git grep -n "<symbol>\|<behaviour words>"`.
2. Update every doc value, table row and code comment that restates it, in the same commit.
3. Before renaming a doc or renaming or renumbering a heading, find inbound links and citations — code comments and the
   kit included: `git grep -n "<DOC_FILE>.md\|<DOC> §[0-9]"`.
4. Where doc and code disagree, find which side is intended (ask the person when only the target can say), fix the
   other, record the decision if it is not obvious.

### Rewriting a doc

GUIDELINES §8 holds the rules these steps follow.

1. **Inventory** every rule, value, decision, reason, measurement, procedure, trap, exception and open item — a
   procedure or checklist found in the doc is mapped to its skill. With uncommitted edits, inventory the committed copy
   too: `git show HEAD:docs/<DOC_FILE>.md`.
2. **Verify** each against the code; mark wrong and obsolete items.
3. **Map** each to a destination: a new section, another doc, a skill or agent (workflow, GUIDELINES §1 Principle 7),
   a merge with its duplicate, or removal with a §4.6 reason.
4. **Rewrite** into the §3 structure.
5. **Check the map** — every item at its destination; nothing missing without a §4.6 reason.
6. **Report** moved and removed items in the commit message ("Nothing dropped" when true) — see the
   `commit-message` skill, where the repo has one.
7. **Fix inbound links and `§n` citations** (Keeping docs true, step 3).

### Length and splitting

GUIDELINES §9 holds when to restructure and when to split. Measure words per doc and per section:

```sh
wc -lw docs/<DOC_FILE>.md
awk '/^## /{if(n)printf "%5d  %s\n", w, n; n=$0; w=0; next} {w+=NF} END{printf "%5d  %s\n", w, n}' docs/<DOC_FILE>.md
```

## Checks

Every new or changed doc:

- [ ] (script) No `<…>` placeholder left in a project doc — `grep -n '<[A-Za-z][^>]*>' docs/<DOC>.md` prints only
  intended examples in backticks
- [ ] Its type's opening and blocks, empty blocks dropped (§2, §3.2, §3.3)

Judgment — the pre-commit pass GUIDELINES §11 points here for; each item cites the § it tests:

- [ ] Opening block complete and in §3.2 order: status banner, purpose, source of truth, related docs, legend of every
  tag; the opening matches the doc type (§2)
- [ ] Blocks in §3.3 order, empty ones gone; no step lists or checklists in the doc — they are in a skill, linked
  (§1 Principle 7)
- [ ] Contents table present when required: three columns, every `##`, "Look here for" not the heading restated; rows
  match the headings (§3.5) — S2, S4
- [ ] Each section reads alone: answer first, where it lives, related links (§3.6)
- [ ] Every rule stated once per doc with its reason (§4.2, §5); a fact another doc owns is linked, not restated
- [ ] Current state only — no history, changelog, or status of finished work (§4.3) — S7, then read for *was*
- [ ] Figures carry a tag, source or conditions and date (§4.5) — S9
- [ ] Style: bold lead, one fact per bullet, a unit on every number, names in backticks, no filler (§5) — S8
- [ ] Every symbol, value, token and path grepped in the code (§7)
- [ ] Rewrites: inventory mapped, nothing dropped without a §4.6 reason, removals reported (§8)
- [ ] Inbound links and `§n` citations still resolve — docs, code, the kit (§7) — S4, S15
- [ ] Flows drawn as Mermaid, not ASCII art (§6.1) — S10, S11
- [ ] Nothing cites material outside `docs/` and the kit's rules (§1 Principle 8)
- [ ] No new lint warnings on touched lines; leave unrelated old ones for their own change (§7)
- [ ] Listed in README's Documentation section (§7) — S13

Scripts — in [`scripts/`](scripts/), run from the repo root **with `bash` and `python3`** (under zsh an unquoted file
list does not split). Each prints its check's name, its hit count and the baseline, then one line per hit; `verify.py
run` runs them, and the scaffolder's self-test, when a doc, the kit or the code changes:

```sh
bash .agents/skills/docs-authoring-and-sync/scripts/doc_checks.sh               # S1–S3, S5–S14, every doc
bash .agents/skills/docs-authoring-and-sync/scripts/doc_checks.sh docs/<DOC>.md  # some docs, no baselines
python3 .agents/skills/docs-authoring-and-sync/scripts/check_anchors.py         # S4
python3 .agents/skills/docs-authoring-and-sync/scripts/check_links.py           # S15
python3 .agents/skills/docs-authoring-and-sync/scripts/new_doc.py --test        # the scaffolder's own cases
```

Baselines are counts sanctioned today: a new hit on a line you touched is yours to fix, an old one elsewhere is left
for its own change (§7). When a hit is sanctioned, raise the baseline beside the check with its reason, here and in the
script.

- [ ] (script) **S1 Title** — every doc has one; a project doc `# <Project> — <Topic>` once `PROJECT_NAME` is set in
  `.agents/project.py`; a project-wide doc names no project and links nothing outside `docs/` — or, kept in a skill
  like the guidelines, outside its skill's folder (§3.1) — 0 hits.
- [ ] (script) **S2 Contents table** on every doc over 150 lines (§3.5) — 0 hits.
- [ ] (script) **S3 Numbering** gaps, duplicates, `###` under the wrong `##` (§3.4) — 0 hits.
- [ ] (script) **S4 Contents rows, anchors, `§n` citations** — every `##` in the contents table, every `#anchor`
  resolves, every `<DOC> §n` in docs, README, the kit and code names a real heading (§3.5, §7) — 0 hits.
- [ ] (script) **S5 Fence without a language**, MD040 (§6) — 0 hits.
- [ ] (script) **S6 Bold paragraph as a heading**, MD036 (§6) — 0 hits.
- [ ] (script) **S7 History words** (§4.3) — 0 hits. Plain *was* is too common to grep; read for it.
- [ ] (script) **S8 Filler and "as above"** (§3.6, §5) — 0 hits.
- [ ] (script) **S9 Tag used but not in the legend** (§4.5) — 0 hits.
- [ ] (script) **S10 ASCII art** in prose or an unlabelled fence (§6.1) — 0 hits; a fence with a language is code, not a
  diagram.
- [ ] (script) **S11 `style`/`classDef` in Mermaid** (§6.1) — 0 hits.
- [ ] (script) **S12 Line-number references** (§6) — 0 hits.
- [ ] (script) **S13 Doc missing from README** (§7) — 0 hits.
- [ ] (script) **S14 Section over 600 words with no table or subheading** (§9) — 0 hits.
- [ ] (script) **S15 Links** — every relative link and anchor in `.agents/`, `docs/`, AGENTS.md and README resolves —
  0 hits.

## Traps

- **A new doc duplicates a section another doc owns** → the topic was not grepped first → make it a section there,
  and link from where readers look (GUIDELINES §5; Creating a doc, step 1).
- **A scaffolded doc is committed with `<…>` left in it** → the template's blocks were kept, not filled → fill or drop
  every block before the commit (Checks).
- **An anchor that looks right does not resolve** → an em dash, backtick or `&` in the heading changes the slug → run
  the anchors script; `—` leaves `--` (GUIDELINES §3.5).
- **A renumber silently breaks code comments** → `§n` citations live in the code and the kit, not only docs → run the
  §7 grep before any heading change (GUIDELINES §7).
- **A bare `§n` in a code comment** → it belongs to the doc the file's header names → check it by hand; the script
  resolves named citations only.
- **A justifying comment kept a wrong behaviour alive** → it shows the behaviour was considered, not that it is still
  right → grep the behaviour across the code and change every claim together (GUIDELINES §7).
- **A rewrite loses a reason nobody re-reads** → inventory against `git show HEAD:` before writing (GUIDELINES §8).
- **A design decision lives only in the design file** → the next agent cannot read it → write the rule and its reason
  into the doc that owns the topic, and link the design file as a source (GUIDELINES §1 Principle 1).

## Sources

| Topic | Where |
| --- | --- |
| Principles | [DOCUMENTATION_GUIDELINES §1](references/guidelines.md#1-principles) |
| Doc types and openings | [DOCUMENTATION_GUIDELINES §2](references/guidelines.md#2-doc-types) |
| Opening block | [DOCUMENTATION_GUIDELINES §3.2](references/guidelines.md#32-opening-block) |
| Building blocks | [DOCUMENTATION_GUIDELINES §3.3](references/guidelines.md#33-section-building-blocks) |
| Numbering | [DOCUMENTATION_GUIDELINES §3.4](references/guidelines.md#34-numbering-and-headings) |
| Contents table, slugs | [DOCUMENTATION_GUIDELINES §3.5](references/guidelines.md#35-contents-table) |
| Writing a section | [DOCUMENTATION_GUIDELINES §3.6](references/guidelines.md#36-writing-a-section) |
| Current state, closing items | [DOCUMENTATION_GUIDELINES §4.3](references/guidelines.md#43-current-state-not-history) |
| Sources and tags | [DOCUMENTATION_GUIDELINES §4.5](references/guidelines.md#45-sources-and-confidence) |
| What may be removed | [DOCUMENTATION_GUIDELINES §4.6](references/guidelines.md#46-what-may-be-removed) |
| Style | [DOCUMENTATION_GUIDELINES §5](references/guidelines.md#5-writing-style) |
| Markdown, Mermaid | [DOCUMENTATION_GUIDELINES §6](references/guidelines.md#6-markdown-mechanics), [§6.1](references/guidelines.md#61-diagrams) |
| Keeping docs true | [DOCUMENTATION_GUIDELINES §7](references/guidelines.md#7-keeping-docs-true) |
| Rewrite process | [DOCUMENTATION_GUIDELINES §8](references/guidelines.md#8-rewriting-an-existing-doc) |
| Length and splitting | [DOCUMENTATION_GUIDELINES §9](references/guidelines.md#9-length-and-splitting) |
| Template | [DOCUMENTATION_GUIDELINES §10](references/guidelines.md#10-template) |
| README listing | The repo's `README.md` → Documentation, which `new_doc.py` keeps |
