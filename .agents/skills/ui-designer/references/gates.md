# Design Gates

How UI work reaches the person at the moments only they can judge: a draft they say yes to before anything is built,
the built thing shown beside that draft, and their sign-off on the real device. What counts as their yes, how it is
recorded so it cannot drift from the file it approved, how a draft is made so it costs nothing, how a build is held to
it, and what a review of a UI change reads first. People read it to know where they will be asked and why; coding
agents read it, through the `ui-designer` skill, before any UI work.

**Where it lives.** In the `ui-designer` skill, beside the steps and checks that apply it — [its SKILL.md](../SKILL.md).
The skill folder is self-contained: copy it into any repo's `.agents/skills/` and the gates come with it. With the
agent-harness kit, `verify.py` records each yes and refuses a hand-over that skipped one; without it, the record in §3
does the same job by hand. The product's values come from its own `DESIGN.md`; the floors, the tokens, layout, type,
motion and touch come from the `accessibility`, `design-system`, `layout`, `typography`, `motion` and
`touch-and-gesture` skills.

**Stability.** Cite this doc as `DESIGN_GATES §n`. Do not renumber; add new material under the next free number.

| § | Section | Look here for |
| --- | --- | --- |
| 1 | [The three gates](#1-the-three-gates) | What each gate settles, its artifact, when it passes, where an answer goes back to; the UX brief before them |
| 2 | [The person's yes](#2-the-persons-yes) | What approves and what never does; the kinds of draft; a design handed over |
| 3 | [Recording a yes](#3-recording-a-yes) | With the kit, and by hand without it; checking the record before the hand-over |
| 4 | [The draft](#4-the-draft) | Where and how a draft is made; the values file beside it |
| 5 | [The build](#5-the-build) | Building from the draft unchanged; the side-by-side |
| 6 | [The target](#6-the-target) | The evidence, the walks, the sign-off |
| 7 | [The modes of UI work](#7-the-modes-of-ui-work) | What drafting, building, staging and reviewing each may and may not do |
| 8 | [Reviewing a UI change](#8-reviewing-a-ui-change) | The order a review reads in, how findings rank, what it hands over |

---

## 1. The three gates

**A screen, component or style passes three gates, each its own step with its own yes: a draft, the build beside it,
the target.**

| Gate | Settles | Artifact | Passes when |
| --- | --- | --- | --- |
| 1. Draft | Layout, look, words; motion; how a gesture behaves | A mock at the target's sizes with its values file, in the scratchpad; a motion study; a gesture spec and prototype | The person's yes names the draft |
| 2. Built | That the real screen holds the draft and passes the checks | The screen built from the draft's values; its screenshot beside the draft | The checks pass, then the person's yes on the side-by-side |
| 3. Target | Feel, speed, touch, the real screen | Screenshots, a recording, the walks | The person's sign-off, in their words |

- **Each answer goes back to the gate that owns it** — what it should look like or say to gate 1; a logic, layout or
  focus fault to gate 2; feel and the real device to gate 3. A change from the target never goes straight into code.
- **A design the person handed over starts at gate 2** — it is the approved draft.
- **A new flow, feature or screen starts with a UX brief** — the task, the flow, the states and the behaviour, approved
  by the person before gate 1 (the `ux-designer` skill); the draft follows it, and a change to how it works is a new
  brief. A change to how an existing screen looks starts at gate 1.
- **A token or a principle in the design brief is a draft too** — a specimen of the old and new values on the screens
  that use them, approved before the brief or the token files change.

## 2. The person's yes

**Only the person's own yes approves, and it names the draft it approves.**

- **A yes covers exactly the draft it names** — a changed draft needs a new yes; an unchanged draft keeps it.
- **Never a yes**: a request to build, silence, a yes to something else, a reviewer's pass, a check that passed, or the
  agent's own reading of the draft.
- **The kinds of draft**: a mock (a still), a motion study (a GIF or video at real speed — a still cannot show
  timing), copy (the words in place, when the words are the change), a specimen (tokens), a gesture prototype (tried
  on the device — a video approves timing, not feel), and after the build, the built screen beside its draft.
- **Two words stand in for a draft**: "design given: <where>" when the person handed the design over, and "no visible
  change: <why>" when a change to UI files shows nothing.

## 3. Recording a yes

**Record the yes the moment it is given, with the file it names and that file's hash, so a later change to the file
is visible.**

| Event | With the agent-harness kit | Without it |
| --- | --- | --- |
| A yes on a UX brief | `verify.py approve <flow>_ux<n>.md --kind ux` | A line in the change's record: the brief's path, `shasum -a 256 <file>`, the kind, the person's words, the time |
| A yes on a draft | `verify.py approve <file> --kind mock\|motion\|copy` | A line in the change's record: the file's path, `shasum -a 256 <file>`, the kind, the person's words, the time |
| A yes on the built screen | `verify.py approve <side-by-side> --kind built` | The same, for the side-by-side, with the commit or the working tree it showed |
| A gesture prototype | `verify.py decision "gesture prototype approved on device: <screen> — <their words>"` | The same words in the record |
| A design handed over | `verify.py decision "design given: <where>"` | The same words in the record |
| Nothing visible changed | `verify.py decision "no visible change: <why>"` | The same words in the record |
| The sign-off on the target | `verify.py signoff "<their words>"` after `verify.py target` | Their words, the device, and the commit or build that ran |

- **The change's record** is wherever the change is reviewed — the pull request description, or a `design-record.md`
  kept with the change's notes — never only the chat.
- **Before the hand-over, check the record** — every gate the change needs has its yes; each approved file's hash still
  matches (`shasum -a 256`); the draft's yes came before the code that built it; the code is unchanged since the built
  yes and since the sign-off, or they are taken again. With the kit, `verify.py finish` does
  this and refuses a hand-over with a gate open.
- **A yes from an earlier task is recorded again** before the build, or named as "design given" — a new task starts
  with no approvals.

## 4. The draft

**Draft where it costs nothing — in a scratch folder, at the target's real sizes, in the project's real tokens and
type — never as a change to the product.**

- **Every state that changes the layout** — empty, loading, error, long text, the largest text size.
- **What renders it at real size** — something that draws the project's tokens and type as the product will; look at
  the picture before showing it, and fix every contrast failure first.
  - **Web** — a static page that loads the project's token file, at each breakpoint the product supports.
  - **iOS, Android** — a frame at the device sizes the product supports, in the platform's text sizes.
  - **Embedded (ESP-IDF, LVGL)** — a frame at the panel's resolution, pixel for pixel, in the fonts compiled into the
    firmware; a host build of the UI on LVGL's SDL display renders it in the real widgets. Judge it also at the
    panel's physical size — the same pixels on a small dense panel read far smaller than on a monitor — and on the
    panel's shape when it is round or has cut corners.
- **Or a frame exported from the design file**, when the person designs there.
- **The values file beside it** (`<screen>_mock<n>.md`) — each element's component, its tokens (colour role, type
  role, spacing, radius), its states, the focus order, each text's contrast against what is painted under it, and the
  accessibility decisions (the `accessibility` skill).
- **The layout is drafted tier by tier** — the draft is drawn at each tier where the layout changes and its values
  file holds the layout spec: regions, navigation, panes, margins, spacing, density, what survives a resize (the
  `layout` skill).
- **Each text has its role** — the values file holds the type spec: each text's role from the brief, emphasis,
  measure, wrap and numbers; the draft is drawn with the longest strings and at the largest text size too (the
  `typography` skill).
- **Motion and gestures are drafted as themselves** — the motion brief and study (the `motion` skill); the gesture
  spec and a prototype on the device (the `touch-and-gesture` skill).
- **Ask open questions with concrete outcomes** — "a sheet or a full screen?", with a draft of each when it matters.
- **A change is a new draft, `n + 1`, and a new yes.**

## 5. The build

**Build from the approved draft's values, unchanged, and show the result beside the draft before asking for a yes.**

- **The values file is the build's input** — no value from memory, no value the draft did not fix.
- **A layout that must differ is a new draft and a new yes**, never a quiet change during the build.
- **The design brief changes in the same change** — a new component's row, a new contrast pair, an exception with its
  reason.
- **The side-by-side** — a screenshot of the built screen at the draft's sizes, in one image with the draft; read it,
  and fix or name every difference before showing it.
  - **Web** — a headless browser's screenshot at each breakpoint; **iOS, Android** — the simulator's or emulator's.
  - **Embedded (ESP-IDF, LVGL)** — the screen as LVGL drew it: `lv_snapshot_take()` on the device, sent off it over
    the console or a file, or the same screen from the host build at the panel's resolution. A photo of the panel is
    evidence for gate 3, not a screenshot: it adds the panel's colour, brightness and angle.

## 6. The target

**Run the change where people use it, gather the evidence, and hand the person what only they can judge.**

- **The evidence** — a screenshot of each changed screen at the sizes that matter, a recording for motion and
  gestures, the console and the logs.
  - **Web** — the browser at each breakpoint and its console; **iOS, Android** — the simulator, then a real device.
  - **Embedded (ESP-IDF, LVGL)** — the firmware flashed with the person's yes, the boot log over the serial console,
    a snapshot of each changed screen, and a video of the panel itself for motion — filmed, since only the panel
    shows its refresh, tearing and brightness.
- **The walks** — each input the target has, motion and timing, contrast and legibility on the real screen, and for
  each gesture its device walk (the `touch-and-gesture` skill).
  - **Web, iOS, Android** — touch, the keyboard, the screen reader.
  - **Embedded (ESP-IDF, LVGL)** — touch, the encoder and buttons, in the light and at the angles the device is used
    in; sound and haptics where the product gives them.
- **The sign-off is the person's, in their words** — never claimed from code or a screenshot. What they report wrong
  goes back to the gate that owns it (§1).

## 7. The modes of UI work

**A UI agent or skill carries the gates in its own modes, so no session skips them.**

| Mode | May | Never |
| --- | --- | --- |
| Draft | Read the repo; write drafts and their values in a scratch folder; ask open questions | Edit the repo; build what nobody approved |
| Build | Build from a named, approved draft; run the checks; make the side-by-side | Change a value the draft fixed; skip the side-by-side |
| Stage | Run on the target; gather evidence; hand over the walks | Claim the walks passed; call it done before the sign-off |
| Review | Read the diff, the record of yeses and the checks; score findings | Edit anything; overrule a decision the person recorded |

## 8. Reviewing a UI change

**A review reads in a fixed order — accessibility first — and ranks its findings the same way.**

1. **The scripts** — the design and token checks, the accessibility, layout, typography, motion and touch checks, the
   project's lint; a hit counts only on an added or changed line.
2. **The record** — each gate's yes, its file unchanged since, the draft's yes before the build (§3). A decision the
   person recorded is settled and never blocks.
3. **Accessibility** — contrast against what is painted, focus order and visibility, target size, names and labels,
   motion (the `accessibility` skill).
4. **The design brief's principles**, then **tokens and components** (the `design-system` skill), then **layout**
   across its tiers (the `layout` skill), then **type** at the default and the largest text size (the `typography`
   skill).
5. **Motion** through its review categories (the `motion` skill), then **each gesture against its spec** (the
   `touch-and-gesture` skill).
6. **The gates** — built from the draft's values; the side-by-side shown.

- **Each finding**: the file and symbol, the rule broken with its source, the fix. Accessibility ranks highest.
- **What needs the target** is listed for the person, never claimed from reading code.
