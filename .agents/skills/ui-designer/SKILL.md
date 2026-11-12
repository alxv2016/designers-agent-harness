---
name: ui-designer
description: Designs, builds and reviews UI through three gates, from the principles and tokens in DESIGN.md — a mock the person says yes to before any code (a still at the target's real sizes in DESIGN.md's tokens, with its component list, states, focus order and accessibility decisions), the screen built from the mock's values and shown beside it, then the person's sign-off on the target — applying the accessibility skill (contrast against what is painted, focus, target size, motion) and the design-system skill (tokens, components, exceptions). Read first for any UI work. Use when designing, adding, changing or reviewing a screen, component, style, icon, animation or piece of copy, drawing a mock, turning a design file into code, before committing UI work, or when asked "is this screen right?".
---

# UI designer — the three gates

The three gates every piece of UI passes — a mock, the built screen beside it, the target — each its own step with its
own yes, and the review of a UI diff. **Read this first for any UI work, then [DESIGN.md](../../../DESIGN.md) — the
product's principles and tokens, which every mock and every build takes its values from — then the two skills every
gate applies**:
[`accessibility`](../accessibility/SKILL.md) — contrast, focus, target size, motion — and
[`design-system`](../design-system/SKILL.md) — tokens, components, exceptions. A screen is designed against both from
its first mock.

Source of truth: [DESIGN.md](../../../DESIGN.md) (cited `DESIGN §n`) for the principles, tokens, contrast pairs and
components; the design file the person works in, as a source. The gates and the approvals they take are
[HARNESS](../../HARNESS.md) §9 and [AGENT_HARNESS](../../../docs/AGENT_HARNESS.md) §20. A doc wins if this skill and a
doc disagree — fix the skill.

## When to use

- Designing a screen, component, state or flow: a mock for the person's yes before any code (gate 1).
- Turning a design the person handed over (a design file, a screenshot, a sketch) into code.
- Adding or changing anything in `UI_PATHS` (`.agents/project.py`): a screen, a component, a style, an icon, copy.
- An animation or a transition: a motion study for the person's yes before it is built.
- Reviewing a UI diff, or asked "is this screen right?" before a commit.

## Rules

### Do

1. **Design from DESIGN.md** — its principles decide between two good options, the lower number winning (DESIGN §1);
   every value is one of its tokens; every colour pair is in DESIGN §2.2, or is added there before the build.
2. **Agree the look on a mock before any code** — gate 1; only the person's yes, naming the mock
   (`<screen>_mock<n>.png`), passes it. A yes from an earlier task is not carried over — `verify.py start` clears approvals: re-record it
   before the build, or record `decision "design given: <the approved file>"` (HARNESS §9).
3. **Draw the mock where it costs nothing** — in the scratchpad, at the target's real sizes (the breakpoints or devices
   that matter), in the project's real tokens and type, every state that changes the layout (empty, loading, error,
   long text) — never as a change to the product (AGENT_HARNESS §20.1).
4. **Write the mock's values down beside it** — `<screen>_mock<n>.md`: each element with its component, tokens (colour
   role, type role, spacing, radius), its states, the focus order, and each text's contrast against what is painted
   under it.
5. **Build from the approved mock's values, unchanged** — a layout change is a new mock and a new yes, back at gate 1
   (AGENT_HARNESS §20.1).
6. **Show the built screen beside the mock** — a screenshot at the same size, side by side, read against the mock
   before showing it; the person's yes on it is gate 2 (`--kind built`).
7. **Take each answer back to the gate that owns it** — what the screen should look like or say goes to gate 1; a
   logic, layout or focus fault is fixed and re-shown at gate 2; feel, speed and the real device stay at gate 3.
8. **Reuse before making** — an existing component first; a second caller moves a one-off into the shared components
   in the same change ([`design-system`](../design-system/SKILL.md) Do 10).
9. **Design for every input the target has** — pointer, touch, keyboard, screen reader; the focus order is part of the
   mock ([`accessibility`](../accessibility/SKILL.md) Do 4–6).
10. **Draft motion as motion** — a GIF or video at real speed, approved as `--kind motion`; a still cannot show timing.
11. **Draft copy as copy** — the words in place in the mock; a change to meaning is the person's (`--kind copy` when
    the words are the change).
12. **Ask the open questions with concrete outcomes** — "a sheet or a full screen?", with a mock of each when it
    matters; never guess a behaviour the target can show.

### Never

- **Take a request to build a UI, a silence, a judge's pass or a check that passed as the person's yes** — a request is
  not approval of a proposal; only the person's yes names the mock (HARNESS §9).
- **Write production code just to get the first picture, or put a mock in the repo** — the mock lives in the scratchpad.
- **Change a value at gate 2 that the mock fixed** — a different layout is a new mock and a new yes.
- **Claim how it feels on the target from reading code or a screenshot** — touch, speed, motion and the real screen
  are the person's to judge at gate 3.
- **Call an element exempt from contrast unless it is disabled or decorative** ([`accessibility`](../accessibility/SKILL.md)).
- **Use a colour, size or duration that is not a token** — or register it as an exception with its reason
  ([`design-system`](../design-system/SKILL.md)).

## Procedure — the three gates

UI work passes three gates, each a separate step with its own yes. A design the person handed over starts at gate 2:
record it with `V decision "design given: <where>"`. `V` is `python3 .agents/skills/verify-change/scripts/verify.py`.

| Gate | Settles | Artifact | Passes when |
| --- | --- | --- | --- |
| 1. Mock | Layout, look, words | `<screen>_mock<n>.png` (and `.md` with its values) in the scratchpad, at the target's sizes | The person's yes names the mock: `V approve <png> --kind mock` |
| 2. Built | That the real screen holds the mock and passes the checks | The screen built from the mock's values; its screenshot beside the mock, `<screen>_side<n>.png` | The checks pass, then the person's yes on the side-by-side: `V approve <png> --kind built` |
| 3. Target | Feel, speed, touch, the real screen | Evidence from the target: screenshots, a recording | The person's sign-off: `V signoff "<their words>"` |

### Gate 1 — the mock (no repo edits)

Input: a described screen, component or flow. Everything here is written in the scratchpad.

1. **Read what exists** — DESIGN.md's principles, tokens and components (DESIGN §1–§8), the screens nearby; a
   screenshot of the screen as it is today when it is a change.
2. **Choose the surface and each control by what it does** — a screen, a sheet, a dialog, a toast; a typed value is an
   input, a choice of few is a segmented control or radio, an action that cannot be undone asks for a confirmation.
3. **List the components top to bottom** — each element's component from DESIGN §8 (existing ones first), its DESIGN.md
   tokens and states; any off-scale value with its reason, for DESIGN §10.
4. **Write the focus order** — every stop a keyboard or switch user reaches, in order.
5. **Settle the accessibility decisions** — each text and icon against the colour painted under it, as a DESIGN §2.2
   pair (`python3 .agents/skills/accessibility/scripts/contrast.py <fg> <bg>` for a new one), target sizes, what is disabled or decorative
   and why, what reduced motion does ([`accessibility`](../accessibility/SKILL.md)).
6. **Draw the mock** in DESIGN.md's tokens at the sizes DESIGN §7 names, with what renders them at real size — a static HTML page that loads the token
   file, an SVG, a frame exported from the design file — and save it as `<screen>_mock<n>.png` with its values in
   `<screen>_mock<n>.md`. Look at the PNG yourself; fix every contrast failure before showing it.
7. **Show the mock and stop.** The gate passes when the person's yes names it: `V approve <png> --kind mock`. A change
   is a new mock, `n + 1`, and a new yes.

### Gate 2 — the built screen

1. **Build from the mock's values, unchanged** (Do 5), with the existing components; tokens only.
2. **Update DESIGN.md in the same change** — a new component's row (DESIGN §8), a new contrast pair (DESIGN §2.2), an
   exception and its reason (DESIGN §10) ([`design-system`](../design-system/SKILL.md)).
3. **Run the checks** — `V run` runs the design check (DESIGN.md's pairs and tokens), the token check, the project's
   build, tests and lint; leave no new hit.
4. **Screenshot the built screen** at the mock's sizes ([`build-run-test`](../build-run-test/SKILL.md) → screenshots),
   and put it beside the mock in one image, `<screen>_side<n>.png`. Read it: every difference from the mock is either
   fixed or named.
5. **Ask the judges `V run` named** — `ui-designer` in review mode among them.
6. **Show the side-by-side and stop.** The gate passes when the checks pass and the person says yes to it:
   `V approve <png> --kind built`. A layout change goes back to gate 1.

### Gate 3 — the target

1. **Run it on the target** — [`verify-change` → The target](../verify-change/SKILL.md#the-target); record it with
   `V target`.
2. **Hand over the Verified block, then what needs the person** for each changed screen: the walk with each input the
   target has (touch, keyboard, screen reader), motion and timing, contrast and legibility on the real screen, how it
   feels.
3. **The gate passes on the person's sign-off**: `V signoff "<their words>"`. What they report wrong is a finding,
   routed back to the gate that owns it (Do 7).

### Review a UI diff (read-only)

Input: a diff — `git diff`, `git diff <base>...HEAD` — or the paths given. Read every changed UI file in full, and
`V status` first: its approvals and the person's decisions are settled, never blocking.

1. **Run the script checks** — `python3 .agents/skills/design-system/scripts/design_check.py`,
   `python3 .agents/skills/design-system/scripts/token_check.py <changed UI files>` and the project's lint; a hit is a
   finding only on an added or changed line.
2. **Judge what no script can**, each against its skill's rule: accessibility first (contrast against what is painted,
   focus order and visibility, target size, names and labels, motion), then DESIGN.md's principles, then tokens and
   components, then the gates.
3. **Rank the findings, accessibility highest**; each one `file:line` — rule broken — fix.
4. **List what needs the target** — gate 3's hand-over list; never claim it passed from reading code.

## Checks

- [ ] Gate 1: a mock the person said yes to, by name, before the first repo edit — or their recorded "design given" or
  "no visible change" (Do 2)
- [ ] Gate 2: the screen built from the mock's values; the checks pass; the person said yes to the side-by-side
  (Do 5, Do 6)
- [ ] Gate 3: the Verified block, a screenshot of each changed screen, and what needs the person handed over
- [ ] (script) `V finish` shows no open gate
- [ ] (script) The design check at 0 — DESIGN.md's pairs meet their floors and its tokens are in the token files
- [ ] (script) No colour literal on a changed UI line — `python3 .agents/skills/design-system/scripts/token_check.py`
  at its baseline
- [ ] The change follows DESIGN.md's principles, and every value is one of its tokens (Do 1)
- [ ] Every text and icon pair meets its contrast floor — `contrast.py`, against the colour painted

## Traps

- **The built screen drifts from the mock** → it was built from memory or from other values → build from
  `<screen>_mock<n>.md`; a layout that must differ is a new mock and a new yes, never a quiet change at gate 2.
- **`V finish`: "the yes on the mock came after the first run that built it"** → the code came first → draft, take
  the yes, and rebuild from the mock's values.
- **The mock passes contrast but the screen fails** → the mock measured the token, the screen paints a translucent
  fill over a photo or another colour → measure against what is painted ([`accessibility`](../accessibility/SKILL.md)).
- **Text fits in the mock and wraps on the target** → the mock used another font, size or line height → draw the mock
  in the project's fonts, and test long text at gate 1.
- **A screenshot looks right and the screen feels wrong** → a still cannot show timing, scroll or touch → gate 3.

## Sources

| Topic | Where |
| --- | --- |
| Principles, tokens, contrast pairs, components | [DESIGN.md](../../../DESIGN.md) |
| The gates and their approvals | [HARNESS §9](../../HARNESS.md#9-the-person-in-the-loop), [AGENT_HARNESS §20](../../../docs/AGENT_HARNESS.md#20-human-in-the-loop) |
| Approval before building | [AGENT_HARNESS §20.1](../../../docs/AGENT_HARNESS.md#201-approval-before-building) |
| Contrast, focus, target size, motion | [`accessibility`](../accessibility/SKILL.md) |
| Tokens, components, exceptions | [`design-system`](../design-system/SKILL.md) |
| Screenshots and the target | [`build-run-test`](../build-run-test/SKILL.md), [`verify-change` → The target](../verify-change/SKILL.md#the-target) |
