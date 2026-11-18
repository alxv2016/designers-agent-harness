---
name: ui-designer
description: Designs, builds and reviews UI through three gates, carried in the skill (references/gates.md) — a draft the person says yes to before any code (a mock at the target's real sizes in the project's tokens, with its values file, component list, states, focus order and accessibility decisions; a motion study; a gesture spec and prototype), the screen built from the draft's values and shown beside it, then the person's sign-off on the target — with each yes recorded against the file it names, by verify.py in the agent-harness kit or by hand without it, and the review of a UI change in a fixed order, accessibility first. Reads the project's own DESIGN.md and applies the accessibility, design-system, layout, typography, motion and touch-and-gesture skills. Portable — the folder works in any repo. Read first for any UI work. Use when designing, adding, changing or reviewing a screen, component, style, icon, animation, gesture or piece of copy, drawing a mock, turning a design file into code, before committing UI work, or when asked "is this screen right?".
metadata:
  scope: portable
---

# UI designer — the three gates

The three gates every piece of UI passes — a draft, the built screen beside it, the target — each its own step with
its own yes, and the review of a UI change. How the gates work and why is kept in this skill at
[references/gates.md](references/gates.md) (cited `DESIGN_GATES §n`); this page holds the rules and the steps. **Read
this first for any UI work, then the project's `DESIGN.md`** — its principles and tokens, which every draft and every
build takes its values from, each section named by what it holds — and the skills every gate applies: `accessibility`
(contrast, focus, target size, input), `design-system` (tokens, components, exceptions), `layout` (breakpoints,
regions, navigation, panes, spacing, how a screen adapts), `typography` (roles, hierarchy, the measure, text that
scales), `motion` (anything that moves) and `touch-and-gesture` (gestures, touch, safe areas and the keyboard).
The project's `DESIGN.md` wins over this skill; the
reference wins over this page.

**Portable.** This folder is self-contained and links to nothing outside itself (it names the rest of a kit in
backticks). Copy it into any repo's `.agents/skills/` (or `.claude/skills/`) with the six skills it applies, and it
works there. In the agent-harness kit, `verify.py` records each yes and `finish` refuses a hand-over that skipped a
gate — `V` below is `python3 .agents/skills/verify-change/scripts/verify.py`; without the kit, each yes goes in the
change's record by hand (DESIGN_GATES §3), and the same steps apply.

## When to use

- Designing a screen, component, state or flow: a draft for the person's yes before any code (gate 1).
- Turning a design the person handed over (a design file, a screenshot, a sketch) into code.
- Adding or changing a screen, a component, a style, an icon or copy (in the kit, anything in `UI_PATHS`).
- An animation, a transition or a gesture: a study or a prototype for the person's yes before it is built.
- Reviewing a UI change, or asked "is this screen right?" before a commit.

## Rules

### Do

1. **Design from the project's DESIGN.md** — where its principles rank, the higher-ranked one decides between two good
   options; every value is one of its tokens; every colour pair is in its contrast pairs, or is added there before the
   build.
2. **Agree the look on a draft before any code** — gate 1; only the person's yes, naming the draft
   (`<screen>_mock<n>.png`), passes it, recorded against that file; a yes from an earlier task is recorded again
   (DESIGN_GATES §2, §3).
3. **Draw the draft where it costs nothing** — in the scratchpad, at the target's real sizes, in the project's real
   tokens and type, every state that changes the layout — never as a change to the product (DESIGN_GATES §4).
4. **Write the draft's values down beside it** — `<screen>_mock<n>.md`: each element's component, tokens, states, the
   focus order, and each text's contrast against what is painted under it (DESIGN_GATES §4).
5. **Build from the approved draft's values, unchanged** — a layout change is a new draft and a new yes, back at gate 1
   (DESIGN_GATES §5).
6. **Show the built screen beside the draft** — a screenshot at the same size, side by side, read against the draft
   before showing it; the person's yes on it is gate 2 (DESIGN_GATES §5).
7. **Take each answer back to the gate that owns it** — look and words to gate 1; a logic, layout or focus fault to
   gate 2; feel, speed and the real device to gate 3 (DESIGN_GATES §1).
8. **Reuse before making** — an existing component first; a second caller moves a one-off into the shared components
   in the same change (the `design-system` skill).
9. **Design for every input the target has** — pointer, touch, keyboard, screen reader on the web and phones; touch, a
   rotary encoder and buttons on an embedded device (DESIGN_GATES §6); the focus order is part of the
   draft, and so is the plain alternative to each gesture, drag and hover (the `accessibility` skill); how each
   gesture behaves is the `touch-and-gesture` skill's.
10. **Draft motion as motion** — the motion brief first, then a GIF or video at real speed beside it; a still cannot
    show timing, and a gesture needs a prototype on the device (the `motion` and `touch-and-gesture` skills).
11. **Draft copy as copy** — the words in place in the draft, written to the `ux-content` skill's rules (its
    `ux-content-writer` agent writes and reviews them); a change to meaning is the person's.
12. **Ask the open questions with concrete outcomes** — "a sheet or a full screen?", with a draft of each when it
    matters; never guess a behaviour the target can show.

### Never

- **Take a request to build a UI, a silence, a judge's pass or a check that passed as the person's yes** — only their
  yes, naming the draft, approves (DESIGN_GATES §2).
- **Write production code just to get the first picture, or put a draft in the repo** — the draft lives in the
  scratchpad.
- **Change a value at gate 2 that the draft fixed** — a different layout is a new draft and a new yes.
- **Claim how it feels on the target from reading code or a screenshot** — touch, speed, motion and the real screen
  are the person's to judge at gate 3.
- **Call an element exempt from contrast unless it is disabled, decorative or a logotype** (the `accessibility`
  skill).
- **Use a colour, size or duration that is not a token** — or register it as an exception with its reason (the
  `design-system` skill).

## Procedure — the three gates

UI work passes three gates, each a separate step with its own yes (DESIGN_GATES §1). A design the person handed over
starts at gate 2 — record "design given: <where>" (`V decision "design given: <where>"` in the kit).

| Gate | Settles | Artifact | Passes when |
| --- | --- | --- | --- |
| 1. Draft | Layout, look, words; motion; gestures | `<screen>_mock<n>.png` and its `.md` in the scratchpad, at the target's sizes; `<screen>_motion<n>.md` and its study; `<screen>_gesture<n>.md` and its prototype | The person's yes names the draft — `V approve <file> --kind mock\|motion\|copy`, or by hand (DESIGN_GATES §3) |
| 2. Built | That the real screen holds the draft and passes the checks | The screen built from the draft's values; `<screen>_side<n>.png` | The checks pass, then the person's yes on the side-by-side — `V approve <png> --kind built`, or by hand |
| 3. Target | Feel, speed, touch, the real screen | Screenshots, a recording, the walks | The person's sign-off — `V signoff "<their words>"`, or by hand |

### Gate 1 — the draft (no repo edits)

Input: a described screen, component or flow. Everything here is written in the scratchpad.

1. **Read what exists** — the approved UX brief for a new flow, feature or screen (the `ux-designer` skill), whose
   flow, states and behaviour the draft follows; DESIGN.md's principles, tokens and components, the screens nearby; a
   screenshot of the screen as it is today when it is a change.
2. **Choose the surface and each control by what it does** — a screen, a sheet, a dialog, a toast; a typed value is an
   input, a choice of few is a segmented control or radio, an action that cannot be undone asks for a confirmation.
3. **List the components top to bottom** — each element's component from DESIGN.md's components (existing ones first),
   its DESIGN.md tokens and states; any off-scale value with its reason, for DESIGN.md's exceptions.
4. **Write the focus order** — every stop a keyboard or switch user reaches, in order.
5. **Settle the accessibility decisions** — the `accessibility` skill's "Deciding a screen's accessibility, before it
   is built": contrast pairs (its `contrast.py` for a new one), focus on open and close, names and alternatives,
   targets, the alternative to each gesture, drag and hover, reduced motion, what is announced and what times out.
6. **Settle the layout tier by tier** — the `layout` skill's "Deciding a screen's layout": the tiers it changes at,
   regions, navigation, panes, margins and spacing tokens, density, what survives a resize; on a watch or a round
   panel, its shape and insets — written into the values file as its layout spec.
7. **Give each text its role** — the `typography` skill's "Choosing type for a screen": role, emphasis, measure,
   wrap and numbers, and the largest text size — written into the values file as its type spec.
8. **Draw the draft** in DESIGN.md's tokens at the sizes its layout section names, with what renders them at real size
   — a static page that loads the token file, an SVG, a frame exported from the design file — and save it as
   `<screen>_mock<n>.png` with its values in `<screen>_mock<n>.md`. Look at the picture yourself; fix every contrast
   failure before showing it.
9. **When anything moves, brief it and draft it as motion** (the `motion` skill → Deciding motion, Drafting the
   study); **a gesture gets its spec and a prototype on the device** (the `touch-and-gesture` skill → Specifying a
   gesture, Prototyping and building).
10. **Show the draft and stop.** The gate passes when the person's yes names it, recorded against the file
    (DESIGN_GATES §3). A change is a new draft, `n + 1`, and a new yes.

### Gate 2 — the built screen

1. **Build from the draft's values, unchanged** (Do 5), with the existing components; tokens only.
2. **Update DESIGN.md in the same change** — a new component's row, a new contrast pair, an exception and its reason,
   each in its DESIGN.md section (the `design-system` skill).
3. **Run the checks** — the design and token checks, the accessibility, layout, typography, motion and
   touch checks, the project's build, tests and lint; leave no new hit. In the kit, `V run` runs them.
4. **Screenshot the built screen** at the draft's sizes, and put it beside the draft in one image,
   `<screen>_side<n>.png`. Read it: every difference from the draft is either fixed or named.
5. **Ask for a review** — in the kit, the judges `V run` names, the `ui-designer` agent in review mode among them.
6. **Show the side-by-side and stop.** The gate passes when the checks pass and the person says yes to it, recorded
   against the file. A layout change goes back to gate 1.

### Gate 3 — the target

1. **Run it on the target** — where people use it; in the kit, `verify-change` → The target, and `V target`.
2. **Hand over the evidence, then what needs the person** for each changed screen: the walk with each input the target
   has, motion and timing, contrast and legibility on the real screen, how it feels, and for each gesture its device
   walk (DESIGN_GATES §6, which names them per platform).
3. **The gate passes on the person's sign-off**, in their words, recorded (DESIGN_GATES §3). What they report wrong is
   a finding, routed back to the gate that owns it (Do 7).

### Review a UI change (read-only)

Input: a diff — `git diff`, `git diff <base>...HEAD` — or the paths given. Read every changed UI file in full, and the
record of yeses first (in the kit, `V status`): the person's approvals and decisions are settled, never blocking. Score
each step against [references/rubric.md](references/rubric.md) (UI_REVIEW_RUBRIC) and the project's learned items, and
return its report.

1. **Run the script checks** (Checks, below) on the changed UI files; a hit is a finding only on an added or changed
   line.
2. **Judge what no script can, in DESIGN_GATES §8's order** — the record of yeses, accessibility, the brief's
   principles, tokens and components, layout through the `layout` skill's review, type through the `typography` skill's
   review, motion through the `motion` skill's review, each gesture against its spec through the `touch-and-gesture`
   skill's review, then the gates.
3. **Rank the findings, accessibility highest**; each one the file and symbol — the rule broken — the fix.
4. **List what needs the target** — gate 3's hand-over list; never claim it passed from reading code.

## Checks

The scripts below belong to the skills this one applies; run each that is present.

```sh
python3 .agents/skills/design-system/scripts/design_check.py              # the brief's pairs and tokens
python3 .agents/skills/design-system/scripts/token_check.py <files>       # colour literals in UI files
python3 .agents/skills/accessibility/scripts/a11y_check.py <files>        # accessibility patterns
python3 .agents/skills/layout/scripts/layout_check.py <files>             # layout patterns
python3 .agents/skills/typography/scripts/typography_check.py <files>     # typography patterns
python3 .agents/skills/motion/scripts/motion_check.py <files>             # motion patterns
python3 .agents/skills/touch-and-gesture/scripts/touch_check.py <files>   # touch patterns
```

- [ ] Gate 1: a draft the person said yes to, by name, recorded against its file, before the first repo edit — or
  their recorded "design given" or "no visible change" (Do 2)
- [ ] Gate 2: the screen built from the draft's values; the checks pass; the person said yes to the side-by-side
  (Do 5, Do 6)
- [ ] Gate 3: the evidence, a screenshot of each changed screen, and what needs the person handed over
- [ ] The record checked before the hand-over: every gate's yes, each file's hash unchanged (in the kit, `V finish`
  shows no open gate)
- [ ] (script) The design check at 0, and no colour literal on a changed UI line
- [ ] (script) No accessibility, layout, typography, motion or touch pattern on a changed UI line
- [ ] The layout spec in the draft, tier by tier, and the build resized across each tier — or rotated on a panel —
  with the walk handed over
- [ ] The type spec in the draft — each text's role from the brief — and the screen read at its largest text size
- [ ] The change follows DESIGN.md's principles, and every value is one of its tokens (Do 1)
- [ ] Every text and icon pair meets its contrast floor, against the colour painted
- [ ] Anything that moves has its brief and an approved study; every gesture has its spec, an approved prototype and
  its device walk handed over

## Traps

- **The built screen drifts from the draft** → it was built from memory or from other values → build from
  `<screen>_mock<n>.md`; a layout that must differ is a new draft and a new yes, never a quiet change at gate 2.
- **The yes came after the code** → the build started before the draft was approved (in the kit, `V finish` says the
  yes came after the first run that built it) → draft, take the yes, and rebuild from the draft's values.
- **The draft passes contrast but the screen fails** → the draft measured the token, the screen paints a translucent
  fill over a photo or another colour → measure against what is painted (the `accessibility` skill).
- **Text fits in the draft and wraps on the target** → the draft used another font, size or line height → draw it in
  the project's fonts, and test long text at gate 1.
- **A screenshot looks right and the screen feels wrong** → a still cannot show timing, scroll or touch → gate 3.
- **The yes is only in the chat** → nobody can check it against the file later → record it with the file's hash
  (DESIGN_GATES §3).

## Sources

| Topic | Where |
| --- | --- |
| The gates, the yes, the record, drafting, building, the target, review | [references/gates.md](references/gates.md) |
| How the experience works — the UX brief, flows, states, the laws of UX | The `ux-designer` skill |
| How a review is scored: verdict, evidence, R1–R20, the report | [references/rubric.md](references/rubric.md) |
| Principles, tokens, contrast pairs, components | The project's `DESIGN.md` |
| Contrast, focus, target size, input | The `accessibility` skill |
| Tokens, components, exceptions | The `design-system` skill |
| Breakpoints, navigation, panes, spacing, density, resizing, watches and round panels | The `layout` skill |
| Type roles, hierarchy, fonts, line height, the measure, emphasis, numbers, text that scales | The `typography` skill |
| Whether and how things move | The `motion` skill |
| Gestures, touch, safe areas and the keyboard | The `touch-and-gesture` skill |
