---
name: commit-message
description: Writes a commit message in this repo's convention — a subject `<areas>: <outcome the user sees>` naming every area touched, a body of per-area bullets, a `Docs:` bullet naming each doc § updated, an honest verification line (what ran, what the person approved and signed off, what was not checked), moved and removed items for a doc rewrite, and the coding tool's trailer. Use when asked to commit, write or review a commit message, or squash; never commit unless the person asked.
---

# Commit message

The shape of a commit message in this repo. The DOCUMENTATION_GUIDELINES rules it carries — docs in the same commit,
rewrites reporting what moved — are cited; the docs win if this skill and a doc disagree — fix the skill. A project
with a convention of its own (Conventional Commits, a ticket prefix) writes it here, in Rules, and the rest of the
skill follows it.

## When to use

- The person asks for a commit, a commit message, or a squash.
- Drafting a message for review from the staged diff.
- Checking that a change carries its docs before it is committed.

## Rules

### Do

1. **Commit only when the person asks.** Drafting a message is not permission to run `git commit`; the guard asks
   before every commit.
2. **Subject: `<areas>: <outcome>`** — the areas are the top-level folders or components the change touches (`ui`,
   `api`, `tokens`, `kit` for `.agents/`), comma-separated with no spaces; `docs` last when docs changed. A docs-only
   commit is `docs: …`.
3. **Write the outcome as the user or the person sees it, present tense** — "the settings screen keeps its scroll
   position after a save", not "fix scroll bug". An em dash may follow with the mechanism.
4. **Leave a blank line after the subject**, then the body; wrap the body near 100 columns, continuation lines
   indented 2 spaces.
5. **One bullet per area**, `- <area>: <what it does now and why>`; a new one says `(new)`. Name components, tokens
   and settings by their names, values with units.
6. **End with a `Docs:` bullet naming every doc and § the change updated** — docs change in the same commit as the
   code they describe (GUIDELINES §7).
7. **State the verification honestly** — what `verify.py finish` shows ran and passed; the person's approvals by file
   name and their sign-off on the target in their words ("Signed off on the target by the person: …"); and what was
   not checked ("Built; not yet seen on the target").
8. **For a doc rewrite, report what moved and what was removed, with the §4.6 reason**, and old → new § numbers for
   moved sections; say "Nothing dropped" when true (GUIDELINES §8).
9. **Name renumbered sections and the inbound citations fixed** (GUIDELINES §3.4, §7).
10. **End with the trailer the coding tool asks for**, after a blank line. Add no trailer the tool did not ask for.

### Never

- **Commit, amend or push unasked** — the person decides when.
- **Split docs into a later commit** — the code commit then describes a repo the docs contradict (GUIDELINES §7).
- **Claim a result on the target that nobody saw** — write "not yet seen on the target" instead.
- **Stage or quote a secret** — a key, a token, an `.env` file; the pre-commit hook refuses them, and a quote in a
  message is just as public.

## Procedure

1. Read the change: `git diff --cached --stat` and `git diff --cached` (or `git diff` when nothing is staged).
2. List the areas: `git diff --cached --name-only | awk -F/ '{print (NF>1 ? $1 : "root")}' | sort -u` — then name
   each the way earlier commits do (`git log -20 --format=%s`), and put `docs` last.
3. Check docs came with the code: for each component, token, setting or behaviour the diff changes,
   `git grep -n "<name>" docs`; a hit in a doc outside the diff, or one whose value differs from the new code, is a doc
   not yet updated (GUIDELINES §7). For a deeper pass, ask the [`doc-reviewer`](../../agents/doc-reviewer.md).
4. Find the § touched: `git diff --cached -U0 docs | grep -E '^@@|^[-+]#{2,4} '` and read the headings above each hunk.
5. Read `python3 .agents/skills/verify-change/scripts/verify.py status` for what ran, what the person approved and
   what they signed off.
6. Write the subject, the area bullets, the `Docs:` bullet, the verification line, the trailer.
7. Show the message to the person; commit only on their word, passing the body through a file or heredoc so the blank
   line and wrapping survive (`git commit -F <file>`).

## Checks

- [ ] Subject is `areas: outcome`, `docs` last, no spaces after commas
- [ ] Blank line after the subject
- [ ] Every area in the diff named in the subject and has a bullet
- [ ] `Docs:` bullet lists each doc and §; no code change left without its doc (GUIDELINES §7)
- [ ] Verification stated: what ran, what was approved and signed off, what was not checked
- [ ] Rewrites list moved and removed items, or "Nothing dropped" (GUIDELINES §8)
- [ ] (script) Subject shape — prints nothing when it fits: `git log -1 --format=%s | grep -vE '^[a-z0-9_.-]+(,[a-z0-9_.-]+)*: '`
- [ ] (script) Blank line after subject — prints nothing when present: `git log -1 --format=%B | sed -n 2p | grep .`

## Traps

- **The subject reads as the whole body in `git log --oneline`** → no blank line after the subject → always leave
  line 2 empty.
- **`git commit -m` with a long body loses the wrapping or the blank line** → write the message to a file and use
  `git commit -F <file>`.
- **A `§n` in the message drifts from the doc** → a heading was renumbered in the same change → cite the final
  numbers, after running the inbound-link grep (GUIDELINES §7).

## Example

```text
ui,tokens,docs: the settings screen in the new type scale, with a 44 px tap target on every row

- tokens: type scale from 12/14/16/20/28 to 13/15/17/22/28 (font-size-*), line heights to match.
- ui: SettingsRow takes its height from space-11 (44 px); the chevron is an icon token, not a literal.
- Docs: the type scale and the row's tap target (DESIGN §3, §4).

Verified: build, tests and doc checks pass. Approved by the person: settings_mock2.png, settings_side1.png.
Signed off on the target by the person: "rows feel right on the phone, type is readable".
```

## Sources

| Topic | Where |
| --- | --- |
| Docs change with the code | [DOCUMENTATION_GUIDELINES §7](../../../docs/DOCUMENTATION_GUIDELINES.md#7-keeping-docs-true) |
| Reporting moved and removed items | [DOCUMENTATION_GUIDELINES §8](../../../docs/DOCUMENTATION_GUIDELINES.md#8-rewriting-an-existing-doc) |
| Renumbering and citations | [DOCUMENTATION_GUIDELINES §3.4](../../../docs/DOCUMENTATION_GUIDELINES.md#34-numbering-and-headings) |
| What ran, what was approved | [`verify-change`](../verify-change/SKILL.md) |
| The convention itself | `git log -40 --format='%h %s%n%b'` |
