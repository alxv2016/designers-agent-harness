# Rubric — ui-designer

How the [ui-designer](../agents/ui-designer.md) scores a UI change in review mode: the verdict, the evidence each result
needs, and the items. R-items are its review steps, each resting on a rule of the
[ui-designer](../skills/ui-designer/SKILL.md) skill (the three gates), the [accessibility](../skills/accessibility/SKILL.md)
skill, or the [design-system](../skills/design-system/SKILL.md) skill, or the principles and tokens in [DESIGN.md](../../DESIGN.md); L-items were learned from what the person found
on the target ([verify-change](../skills/verify-change/SKILL.md#recording-what-was-learned) → Recording what was
learned, route `rubric`). A new item goes here, not in the agent.

## Verdict

- **blocking** — an item fails on an added or changed line against a skill rule or a doc §, or a gate was skipped: a
  screen or component changed with no mock approved by name before the first run that built it, or with no yes on the
  built screen, in `verify.py status` — and no recorded "no visible change" or "design given" decision.
- **pass** — every item passes, is n/a or unsure; should-fix findings and notes do not block. A pass never covers the
  walks on the target: they stay on the "Judge on the target" list.

A decision in `verify.py status` is the person's word for this task: the judge notes it and never blocks on it. A line
marked `token-exception` with its row in DESIGN §10 is not a finding.

## Evidence

- **fail** — the file and line, the line quoted, and the rule (the skill's Do or Never, or the doc §).
- **pass** — what was read or run: the files and lines checked, the `verify.py status` lines, the command and its hits
  on changed lines.
- **unsure** — what could not be settled, and what would settle it: the target, the person.
- **n/a** — why the item does not touch this change.

A result without evidence counts as unsure.

## Items

| Item | Looks for | Procedure step |
| --- | --- | --- |
| R1 | Gate 1, the mock: `verify.py status` lists a `mock` approval on a file unchanged since the yes, earlier than the first run that built the change — or a "design given" or "no visible change" decision; a request, silence or a judge's pass is never the yes (ui-designer Do 2, Never) | Review 2 |
| R2 | Built from the mock's values: the components, tokens and focus order in `<screen>_mock<n>.md` equal the code; a layout that differs came back as a new mock and a new yes (ui-designer Do 5) | Review 2 |
| R3 | Gate 2, the built screen: a `built` approval on the side-by-side, the code unchanged since (ui-designer Do 6) | Review 2 |
| R4 | The script checks: the design check (DESIGN.md's pairs and tokens) at 0, the token check and the project's lint with no hit on an added or changed line (ui-designer → Review 1; design-system Checks) | Review 1 |
| R5 | Contrast: text 4.5:1, large text and non-text 3:1 against the colour painted, in every theme; only disabled and decorative exempt; no text dimmed with opacity (accessibility Do 1–3, Never) | Review 2 |
| R6 | Focus and input: every action reachable by keyboard, focus order follows reading order, a visible focus indicator, no trap (accessibility Do 4–5) | Review 2 |
| R7 | Names and labels: every control has a name; inputs keep a visible label; images that mean something have a text alternative (accessibility Do 6, Do 11) | Review 2 |
| R8 | Target size, colour as the only signal, resize and reflow, reduced motion (accessibility Do 7–10) | Review 2 |
| R9 | Tokens: every value one of DESIGN.md's tokens, roles at the call site, no literal, every state its token, exceptions registered in DESIGN §10 (design-system Do 2–8) | Review 2 |
| R10 | Components: an existing one reused; a one-off moved to the shared components on its second caller (design-system Do 10; ui-designer Do 8) | Review 2 |
| R11 | DESIGN.md in the same change: a new token decided there first, a new pair in DESIGN §2.2, a new component in §8, an exception in §10 (design-system Do 4, 6, 8, 10) | Review 2 |
| R12 | Gate 3, the target: the Verified block, a screenshot of each changed screen, the walks handed to the person and never claimed from code; the person's sign-off in `status` — unsure while the review runs before it (ui-designer Gate 3) | Review 4 |
| R13 | Principles: the change follows DESIGN §1 — where two options both pass the rules, the lower-numbered principle decides; a principle broken on purpose is the person's recorded decision (ui-designer Do 1; design-system Do 1) | Review 2 |

## Learned

| Item | Since | From the person | Looks for |
| --- | --- | --- | --- |
