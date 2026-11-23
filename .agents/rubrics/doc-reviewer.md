# Rubric — doc-reviewer

How the [doc-reviewer](../agents/doc-reviewer.md) scores docs or a diff: the verdict, the evidence each result needs, and
the items. R-items are its check families — the script checks as one, each judgment check of the form half, each drift
step; the Procedure step column names the half and its step. L-items are what it should have caught and the person
found, recorded with `verify.py finding --route rubric`
([verify-change](../skills/verify-change/SKILL.md#recording-what-was-learned) → Recording what was learned). A new item
goes here, not in the agent.

## Verdict

- **blocking** — an item fails against a GUIDELINES § or a skill rule.
- **pass** — every item passes, is n/a or unsure; should-fix findings and notes do not block.

A decision in `verify.py status` is the person's word for this task: the judge notes it and never blocks on it.

## Evidence

- **fail** — `file:line` and the line quoted, plus the rule; a drift fail quotes both sides, the doc's line and the
  code's.
- **pass** — what was read or run: the docs and lines checked, or the command and its result.
- **unsure** — what could not be settled and what would settle it (the target, a citation whose doc cannot be told).
- **n/a** — why the item does not touch this run: the half not run, or no doc of that kind.

A result without evidence counts as unsure.

## Items

| Item | Looks for | Procedure step |
| --- | --- | --- |
| R1 | Script checks: `doc_checks.sh` (S1–S3, S5–S14), `check_anchors.py` (S4), `check_links.py` (S15), each against `docs-authoring-and-sync`'s baselines; with a diff, hits on the touched lines only (GUIDELINES §7) | Form 1–2 |
| R2 | Opening block complete and in order for the doc type (GUIDELINES §2, §3.2) | Form 3 |
| R3 | Blocks in order, empty ones gone; no step list or checklist in a doc (GUIDELINES §3.3, §1 Principle 7) | Form 3 |
| R4 | Contents table: three columns, every `##`, "Look here for" not the heading restated (GUIDELINES §3.5) | Form 3 |
| R5 | Each section reads alone, answer first (GUIDELINES §3.6) | Form 3 |
| R6 | Every rule once per doc with its reason; a fact another doc owns linked, not restated (GUIDELINES §4.2, §5) | Form 3 |
| R7 | Current state only — no history; read for *was* past S7 (GUIDELINES §4.3) | Form 3 |
| R8 | Figures carry a tag, source or conditions and date (GUIDELINES §4.5) | Form 3 |
| R9 | Style: bold lead, one fact per bullet, a unit on every number, names in backticks, no filler (GUIDELINES §5) | Form 3 |
| R10 | A rewrite: inventory mapped, nothing dropped without a §4.6 reason, removals reported (GUIDELINES §8) | Form 3 |
| R11 | No suspected bug from reading code written as fact (`docs-authoring-and-sync` Never; GUIDELINES §7) | Form 3 |
| R12 | Existence: every backticked name, token, setting, path and key a doc gives found in the code; with a diff, every name it changes grepped in `docs/` (GUIDELINES §7) | Drift 1–2 |
| R13 | Values: each table row's value against its declaration, with units, expressions and shared names ruled out | Drift 3 |
| R14 | Citations, doc → doc and code → doc: every named `§n` and `#anchor` resolves (S4) | Drift 4 |
| R15 | No `§` in a code comment or kit script without its doc name, and no line-number reference (GUIDELINES §4.8); a bare `§n` inside a Markdown doc means that doc's own section | Drift 5 |
| R16 | Behaviour claims: comments justifying a changed behaviour agree with it (GUIDELINES §7) | Drift 6 |
| R17 | Classification: each disagreement's likely-current side named; a measured value or a behaviour only the target shows marked Needs the target — unsure, not fail | Drift 7 |

## Learned

| Item | Since | From the person | Looks for |
| --- | --- | --- | --- |
| L1 | 2026-11-19 | A doc's "never do X" rule passed while the code did X in five places | A rule in a doc that bounds what code does — *never*, *only*, *every* — over a set the code enumerates (commands sent, pins, keys): each member the code uses, grepped and checked against the rule's source, not the rule's wording alone |

## Quality

The doc-reviewer scores its dimensions as [HARNESS §12](../HARNESS.md#12-quality-taste-and-weights) says; its anchors are in `.agents/evals/anchors/doc-reviewer/`. The doc-reviewer's review scores what the change touches, and `verify.py audit` scores the whole product.

| Dimension | What it scores | Anchors: a 0, 2 and 4 |
| --- | --- | --- |
| `answer-first` | Answer first, findable (the form half) | [answer-first.md](../evals/anchors/doc-reviewer/answer-first.md) |
| `accuracy` | Accurate to code and sources (the drift half) | [accuracy.md](../evals/anchors/doc-reviewer/accuracy.md) |
| `concise` | Concise, one home per rule | [concise.md](../evals/anchors/doc-reviewer/concise.md) |
| `complete` | Complete for its reader | [complete.md](../evals/anchors/doc-reviewer/complete.md) |
| `plain` | Plain language | [plain.md](../evals/anchors/doc-reviewer/plain.md) |

The report adds this block after its findings; `verify.py review doc-reviewer <verdict> --score dim=n,… --note "dim: why;
…"` records it and computes the score.

```text
## Score — quality <n>/100 (bar <bar>)
| Dimension | Weight | Score | Evidence |
| --- | --- | --- | --- |
| answer-first … plain | <weight> | 0–4 / na (capped: <metric>) | <quoted line, output or measured value; the anchor held against> |

To raise: <dimension> — <what would lift it>   (below the bar only)
```

## Taste

The doc-reviewer reads every row below before it scores; [HARNESS §12.3](../HARNESS.md#123-the-persons-taste) says how a row is recorded and promoted.

| Item | Since | From the person | Dimension | Anchor |
| --- | --- | --- | --- | --- |
