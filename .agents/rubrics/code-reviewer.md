# Rubric — code-reviewer

How the [code-reviewer](../agents/code-reviewer.md) scores a diff to the code: the verdict, the evidence each result
needs, and the items. R-items are its Procedure steps, each resting on the project's own rules — AGENTS.md, the docs'
Do and Never lists, the skills the touched files call for. L-items were learned from what the person found on the
target, recorded with `verify.py finding --route rubric`
([verify-change](../skills/verify-change/SKILL.md#recording-what-was-learned) → Recording what was learned). A new item
goes here, not in the agent.

## Verdict

- **blocking** — an item fails on an added or changed line against a doc § or a skill rule, or the change does not do
  what it claims.
- **pass** — every item passes, is n/a or unsure; should-fix findings and notes do not block.

A decision in `verify.py status` is the person's word for this task: the judge notes it and never blocks on it.

## Evidence

- **fail** — the file and line, the line quoted, and the rule (doc § or skill rule).
- **pass** — what was read or run: the files and lines checked, or the command and its result.
- **unsure** — what could not be settled, and what would settle it: a test, the target, the person.
- **n/a** — why the item does not touch this diff.

A result without evidence counts as unsure.

## Items

| Item | Looks for | Procedure step |
| --- | --- | --- |
| R1 | Correctness: the change does what it claims — edge cases (empty, missing, slow, failed), async order, state that outlives its screen | 1 |
| R2 | The project's rules: each Do and Never in the docs and skills the touched files call for; layering and imports in the allowed directions; AGENTS.md's conventions | 2 |
| R3 | Coupled changes: a setting, schema, token or API changed with its callers, types, migrations, tests and the other platforms | 3 |
| R4 | What must never ship: a `DEBUG_MARKERS` line, a switch off its shipping value (`INVARIANTS`), a secret in code or a log line (`.agents/project.py`; AGENTS.md → Safety) | 4 |
| R5 | Errors and the person's data: failures handled and shown, nothing the user owns lost or sent where they did not ask | 5 |
| R6 | Tests: new behaviour tested where the project tests that kind of thing; a fixed bug with a test that fails without the fix | 6 |
| R7 | Docs in the same change: no doc outside the diff still states the old behaviour or value (GUIDELINES §7) | 7 |

## Learned

| Item | Since | From the person | Looks for |
| --- | --- | --- | --- |
