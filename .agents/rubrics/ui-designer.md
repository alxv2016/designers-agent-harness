# Rubric — ui-designer

How the [ui-designer](../agents/ui-designer.md) scores a UI change in review mode. The verdict, the evidence rules, the
items R1–R20 and the report's shape travel with the skill, in
[`ui-designer/references/rubric.md`](../skills/ui-designer/references/rubric.md) (UI_REVIEW_RUBRIC), so the agent and
the skill work in any repo. This file holds what this project adds: the items learned from what the person found on the
target ([verify-change](../skills/verify-change/SKILL.md#recording-what-was-learned) → Recording what was learned, route
`rubric`). Each item is a pattern in a draft or a screen the person said no to or found wrong — from `verify.py decline`
or `verify.py finding --route rubric --judge ui-designer` — and the ui-designer reads them before its next draft as well
as in review. A review scores the skill's items and every item here. A new learned item goes here, not in the skill or
the agent.

## Learned

| Item | Since | From the person | Looks for |
| --- | --- | --- | --- |

## Quality

The ui-designer scores its dimensions as [HARNESS §12](../HARNESS.md#12-quality-taste-and-weights) says; its anchors are in `.agents/evals/anchors/ui-designer/`. The ui-designer's review scores what the change touches, and `verify.py audit` scores the whole product.

## Taste

The ui-designer reads every row below before it scores; [HARNESS §12.3](../HARNESS.md#123-the-persons-taste) says how a row is recorded and promoted.

| Item | Since | From the person | Dimension | Anchor |
| --- | --- | --- | --- | --- |
