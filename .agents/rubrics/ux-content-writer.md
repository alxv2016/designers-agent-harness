# Rubric — ux-content-writer

How the [ux-content-writer](../agents/ux-content-writer.md) scores an interface's words in review mode. The verdict,
the evidence rules, the items C1–C6, the report's shape and the quality score travel with the skill, in
[`ux-content/references/rubric.md`](../skills/ux-content/references/rubric.md) (UX_CONTENT_RUBRIC), so the agent and
the skill work in any repo. This file holds what this project adds: the items learned from what the person found on
the target ([verify-change](../skills/verify-change/SKILL.md#recording-what-was-learned) → Recording what was learned,
route `rubric`), and the person's taste. A review scores the skill's items and every item here. A new learned item
goes here, not in the skill or the agent.

## Learned

| Item | Since | From the person | Looks for |
| --- | --- | --- | --- |

## Quality

The ux-content-writer scores its dimensions as [HARNESS §12](../HARNESS.md#12-quality-taste-and-weights) says; its anchors are in `.agents/evals/anchors/ux-content-writer/`. The ux-content-writer's review scores what the change touches, and `verify.py audit` scores the whole product.

## Taste

The ux-content-writer reads every row below before it scores; [HARNESS §12.3](../HARNESS.md#123-the-persons-taste) says how a row is recorded and promoted.

| Item | Since | From the person | Dimension | Anchor |
| --- | --- | --- | --- | --- |
