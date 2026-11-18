# HCI Principles

The principles, models and laws of human–computer interaction that interaction and experience decisions rest on: what
usability means, the heuristics and rules that judge an interface, how people act on a system and read it back, how
they perceive, remember, decide, move and stay motivated, how errors happen and are prevented, and every law on Laws of
UX with the decision it informs. People read it to make a UX decision with reasons; coding agents read it, through the
`ux-designer` skill, before they frame a flow, write a UX brief or review an experience.

**Where it lives.** In the `ux-designer` skill, beside the steps that apply it — [its SKILL.md](../SKILL.md) — with the
research and evaluation methods in [methods.md](methods.md) (UX_METHODS) and the review items in
[rubric.md](rubric.md) (UX_REVIEW_RUBRIC). The skill folder is self-contained: copy it into any repo's
`.agents/skills/` and these come with it. The product's own principles, in its design brief (`DESIGN.md` in the
agent-harness kit), win over this reference where they rank two good options; the screen, its tokens and its
components are the `ui-designer` skill's; the accessibility floors, the words and the motion are the `accessibility`,
`ux-content` and `motion` skills'.

**Platforms.** The principles are about people and hold on every platform — the web, iOS, Android, a watch, an
embedded device with a screen, encoder and buttons. Where a principle lands differently on one, the bullet says so.

**Stability.** Cite this doc as `HCI §n`. Do not renumber; add new material under the next free number.

| § | Section | Look here for |
| --- | --- | --- |
| 1 | [Principles](#1-principles) | Usability in a context of use; people's goals first; laws that help, never manipulate |
| 2 | [Usability heuristics](#2-usability-heuristics) | Nielsen's ten |
| 3 | [Golden rules and interaction principles](#3-golden-rules-and-interaction-principles) | Shneiderman's eight; ISO 9241-110's seven |
| 4 | [Norman's principles](#4-normans-principles) | Visibility, affordances, signifiers, mapping, feedback, constraints, the conceptual model |
| 5 | [Interaction models](#5-interaction-models) | The seven stages, the two gulfs, direct manipulation, GOMS and the keystroke model |
| 6 | [Mental models](#6-mental-models) | What people believe about a system, and closing the gap with the designer's |
| 7 | [Perception and attention](#7-perception-and-attention) | Gestalt grouping, isolation, selective attention, banner and change blindness, aesthetics |
| 8 | [Memory and cognitive load](#8-memory-and-cognitive-load) | Working memory, chunking, recognition over recall, progressive disclosure, serial position |
| 9 | [Decisions and complexity](#9-decisions-and-complexity) | Hick's law, choice overload, Occam's razor, Tesler's law, Pareto, biases, conventions |
| 10 | [Movement and time](#10-movement-and-time) | Fitts's law, the Doherty threshold, Parkinson's law, Postel's law |
| 11 | [Motivation and the memory of an experience](#11-motivation-and-the-memory-of-an-experience) | Flow, goal gradient, Zeigarnik, peak-end, the active user |
| 12 | [Errors](#12-errors) | Slips and mistakes, prevention, confirmation, undo, recovery |
| 13 | [The laws of UX, by decision](#13-the-laws-of-ux-by-decision) | All thirty laws, each with the decision it informs |

---

## 1. Principles

**Design for named people doing a named task in a known context, and judge it by whether they reach their goal well.**

- **Usability is measured in a context of use** — effectiveness (do people achieve their goal), efficiency (at what
  cost in time and effort) and satisfaction, for specified users, tasks and environments (ISO 9241-11, as described on
  Wikipedia, "ISO 9241"; "System usability scale"). A design is usable for someone, for something, somewhere.
- **Start from the person's goal and task, not the feature** — usability "can only be assessed relative to two
  variables: who are the users and what do they need to do" (Nielsen Norman Group, "Personas vs. Jobs-to-Be-Done").
- **Human-centred design involves people throughout** — it "relies heavily on user participation and user feedback"
  (Wikipedia, "Human-centered design"); the methods are in UX_METHODS.
- **A principle is a reason, not a rule to apply blindly** — the golden rules "require validation and tuning for
  specific design domains" (Ben Shneiderman, "The Eight Golden Rules of Interface Design"); when two principles pull
  apart, the product's own ranked principles decide, and the trade-off is written down.
- **The designer, not the person, owns an error-prone design** (Nielsen Norman Group, "Preventing User Errors:
  Avoiding Conscious Mistakes").
- **Laws that describe human bias are used to help people finish what they came to do, never against their
  interest** — artificial progress, defaults, scarcity and delay are honest or they are not used.
- **Evidence over opinion** — a claim about what people do comes from research with people; a heuristic or a law
  predicts, and research confirms (UX_METHODS §1).

## 2. Usability heuristics

**Ten broad rules of thumb judge an interface's usability; they have stayed unchanged since 1994** (Nielsen Norman
Group, "10 Usability Heuristics for User Interface Design").

| # | Heuristic | What it asks of a design |
| --- | --- | --- |
| H1 | Visibility of system status | Keep people informed of what is going on, with timely feedback |
| H2 | Match between the system and the real world | Speak the person's language; follow real-world conventions and natural mappings |
| H3 | User control and freedom | A clearly marked way out of an unwanted state — undo, redo, cancel |
| H4 | Consistency and standards | The same word or action means the same thing; follow platform and industry conventions |
| H5 | Error prevention | Remove error-prone conditions, or check and confirm before committing |
| H6 | Recognition rather than recall | Make elements, actions and options visible, so people need not remember them |
| H7 | Flexibility and efficiency of use | Accelerators for experts — shortcuts, tailoring frequent actions — that novices never need |
| H8 | Aesthetic and minimalist design | Nothing irrelevant or rarely needed; each extra unit competes with what matters |
| H9 | Help users recognize, diagnose and recover from errors | Plain-language messages that state the problem precisely and suggest a solution |
| H10 | Help and documentation | Ideally none needed; otherwise searchable, task-focused, concise, in context |

- **Cite a heuristic by its number** (`HCI §2 H6`) in a review finding.
- **The words in error messages and help are the `ux-content` skill's** — this skill decides that a message, a way out
  or a hint is needed and where it appears.

## 3. Golden rules and interaction principles

**Shneiderman's eight rules and ISO 9241-110's seven principles say the same things from two traditions; a design
that meets the heuristics meets most of them.**

| Rule | Shneiderman's eight golden rules (*Designing the User Interface*, 6th ed.) |
| --- | --- |
| S1 | Strive for consistency — action sequences, terms, colour, layout; few, comprehensible exceptions |
| S2 | Seek universal usability — novice to expert, age, disability, language, technology |
| S3 | Offer informative feedback — modest for frequent minor actions, substantial for major ones |
| S4 | Design dialogs to yield closure — a beginning, a middle and an end that says it is done |
| S5 | Prevent errors — disable what does not apply, block invalid input, give simple, specific recovery |
| S6 | Permit easy reversal of actions — reversal relieves anxiety and invites exploration |
| S7 | Keep users in control — the interface responds to them and does not surprise them |
| S8 | Reduce short-term memory load — never make people carry information from one display to another |

| Principle | ISO 9241-110:2020 interaction principles (as listed on Wikipedia, "ISO 9241") |
| --- | --- |
| I1 | Suitability for the user's tasks |
| I2 | Self-descriptiveness |
| I3 | Conformity with user expectations |
| I4 | Learnability |
| I5 | Controllability — the 2020 edition folds individualisation into it |
| I6 | Use error robustness |
| I7 | User engagement — added in the 2020 edition |

- **Closure (S4) matters most at the end of a flow** — a confirmation that the task is done is also the "end" the
  peak-end rule weighs (§11).

## 4. Norman's principles

**A design communicates how to use it: what can be done, where, and what happened.** (Don Norman, *The Design of
Everyday Things*, as described on Wikipedia and by Nielsen Norman Group.)

| Principle | Means | In an interface |
| --- | --- | --- |
| Visibility | The person can tell the state and the actions available | Status shown, controls visible, nothing important hidden behind a gesture alone |
| Affordance | What an object makes possible between it and the person | A slider can be dragged; a field can be typed in |
| Signifier | The signal that shows the affordance | A handle, a raised button, a caret, a label that says "Drag" |
| Mapping | The relationship between a control and its effect | Controls laid out like what they change; up means more |
| Feedback | Full, continuous information about the result of an action | A pressed state, progress, the changed value, a confirmation |
| Constraints | Limits that make wrong actions impossible or unlikely | A date picker that cannot pick an impossible date; a disabled action |
| Conceptual model | A coherent story of how the system works, shown through its image | A cart that holds items, a folder that holds files |

- **Signifiers are the designer's job** — an affordance nobody can see is a feature nobody uses; Norman added the term
  in the 2013 edition to make that distinction.
- **The system image is all the person sees of the conceptual model** — the interface, its words and its behaviour;
  the model in the designer's head reaches people only through it.

## 5. Interaction models

**People cross two gulfs on every action — from their goal to the system's controls, and from the system's response
back to knowing whether they succeeded.**

### 5.1 The seven stages and the two gulfs

| Phase | Stages (Norman) | The gulf | Narrowed by |
| --- | --- | --- | --- |
| Execution | 1 form the goal, 2 form the intention, 3 specify an action, 4 execute it | Of execution — between the goal and the means to act on it | Signifiers, mapping, constraints, conventions, recognition over recall |
| Evaluation | 5 perceive the state, 6 interpret it, 7 compare it with the goal | Of evaluation — the effort to tell whether the goal was met | Visible status, immediate feedback, a clear result in the person's terms |

- **"Successful execution usually depends on correct evaluation"** — people alternate between the two until they reach
  their goal (Nielsen Norman Group, "The Two UX Gulfs: Evaluation and Execution"; the terms are Hutchins, Hollan and
  Norman's, 1986).
- **Name the gulf in a finding** — "the gulf of evaluation is wide: after saving, nothing shows it saved" points to
  the fix.

### 5.2 Direct manipulation

- **Continuous representation of the objects of interest, with rapid, reversible, incremental actions and feedback**
  (Ben Shneiderman, 1982, as described on Wikipedia, "Direct manipulation interface").
- **Seeing the result while acting reduces errors** — dragging a crop handle shows the crop; how a drag behaves under
  the finger is the `touch-and-gesture` skill's.
- **Direct manipulation suits spatial, visual, reversible work; a form or a command suits precise values, many items
  at once, and repetition** — choose the interaction model by the task (UX brief, the `ux-designer` skill).

### 5.3 GOMS and the keystroke-level model

- **GOMS describes skilled work as Goals, Operators, Methods and Selection rules** (Card, Moran and Newell, 1983, as
  described on Wikipedia, "GOMS").
- **The keystroke-level model sums operators to predict an expert's time** — compare two designs by the sum; M, at
  1.35 s, is the longest fixed operator a design can remove (Card, Moran and Newell, "The keystroke-level model for user performance time with
  interactive systems", Communications of the ACM 23(7), 1980; the times as given on Wikipedia, "Keystroke-level
  model"):

| Operator | What | Time |
| --- | --- | --- |
| K | A keystroke or button press; Shift and a mouse click each count as one | 0.08 s best typist (135 wpm), 0.12 s good (90 wpm), 0.20 s average skilled (55 wpm), 0.28 s average non-secretary (40 wpm), 0.50 s random letters, 0.75 s complex codes, 1.20 s unfamiliar with the keyboard |
| P | Pointing a mouse at a target | 1.1 s, held constant though it varies with distance and size (§10, Fitts's law) |
| H | Homing the hands between keyboard and mouse | 0.4 s |
| D | Drawing n straight segments, l cm in all, with a mouse on a 0.56 cm grid | 0.9n + 0.16l s |
| M | Mentally preparing | 1.35 s |
| R | The system's response | Measured on the system; counted only where the person waits |

- **Place M by the model's rules** — one before every keystroke that is not part of an argument string and before
  every point that chooses a command; then delete it where the next operator is fully anticipated (a point then its
  click), inside one cognitive unit such as a command name (keep the first), before a redundant terminator, and
  before the keystroke that ends a constant string; keep it before the end of an argument string (Wikipedia,
  "Keystroke-level model", rules 0–4).
- **The times are for a mouse and a keyboard.** For touch, the Touch-Level Model (Rice and Lartigue, 2014) keeps K,
  H, M and R and adds tap, swipe, drag, pinch, zoom, rotate, tilt, distraction and an initial act (same source); its
  times are not carried here. On a watch's crown or a device's encoder and buttons, time the operators on the device.
- **Its limits** — expert, error-free, routine tasks only; execution time only, never the time to learn; a
  root-mean-square error of 21% (same source). A count compares designs; it never replaces watching
  people (UX_METHODS §6).

## 6. Mental models

**People act on what they believe about a system; a design either matches that belief or teaches a better one.**

- **A mental model is "what the user believes about the system at hand"** — built from experience, different for each
  person, based on belief rather than fact, and changing over time (Nielsen Norman Group, "Mental Models").
- **People bring models from other products** — "Users spend most of their time on other sites" (Jakob's law, §9);
  conforming to them is cheaper for people than teaching a new one.
- **Close a gap in one of two ways** — change the design to fit the model, or improve the model with clearer
  signifiers, labels and explanation in context.
- **Find the model with people, not by guessing** — think-aloud testing and interviews show it (UX_METHODS §3, §7).
- **The conceptual model (§4) is the designer's side** — the UX brief writes it down in one sentence: what the objects
  are and what can be done to them.

## 7. Perception and attention

**People see groups, differences and order before they read; design the grouping and the emphasis on purpose.**

| Law (Laws of UX) | Says | Decide with it |
| --- | --- | --- |
| Law of Proximity | Objects near each other are grouped | Related controls together, groups apart — the spacing is the `layout` skill's |
| Law of Similarity | Similar elements are seen as related | Things that work alike look alike; a link never looks like plain text |
| Law of Common Region | A shared, bounded area groups elements | A card, a section background or a border shows what belongs together |
| Law of Uniform Connectedness | Visually connected elements read as more related | A line, a frame or a shared colour ties steps or items together |
| Law of Prägnanz | Complex images are read as the simplest form | Simple, regular shapes and structures are understood and remembered |
| Von Restorff effect | The item that differs is remembered | One distinct primary action; restraint so emphasis is not mistaken for an ad; never colour alone |
| Selective attention | People attend to what serves their goal | Banner blindness — never style content like an ad; change blindness — a change that matters gets a strong cue |
| Aesthetic-usability effect | Attractive designs are perceived as more usable | Polish earns tolerance, and hides problems in testing — test the task, not the impression |

Source: Laws of UX (Jon Yablonski), each law's page.

- **The Gestalt laws are how layout communicates structure** — the grouping is decided here; the spacing and surfaces
  that draw it are the `layout` and `design-system` skills'.

## 8. Memory and cognitive load

**Working memory is small and fades fast; the design carries the memory so people do not have to.**

- **Cognitive load is the mental effort an interface asks for** — intrinsic load is the task's own; extraneous load is
  effort the design adds and removes nothing from the task (Laws of UX, Cognitive Load; John Sweller, 1988).
- **Working memory holds about four to seven chunks, each fading after 20 to 30 seconds** (Laws of UX, Working
  Memory) — Miller's "seven, plus or minus two" is not a design limit to justify, such as "seven menu items" (Laws of
  UX, Miller's Law).
- **Chunk content into meaningful groups** — a phone number in groups, a long form in sections, a page in modules with
  clear hierarchy (Laws of UX, Chunking).
- **Recognition rather than recall** — show the options, recent items, what was viewed (visited links, breadcrumbs);
  a menu is recognition, a command line is recall (Nielsen Norman Group, "Memory Recognition and Recall in User
  Interfaces").
- **Carry information across screens** — a comparison table, a summary before submit, the details of what is being
  paid for beside the payment (Laws of UX, Working Memory; Shneiderman S8).
- **Progressive disclosure** — the most important options first, the rest on request; get the split right and make
  the way forward obvious; more than two levels usually fails (Nielsen Norman Group, "Progressive Disclosure").
- **Staged disclosure (a wizard) suits steps that do not depend on each other**; when people must go back and forth
  between steps, one page with sections serves better (Nielsen Norman Group, "Progressive Disclosure").
- **Serial position** — the first and last items in a list are remembered best; the least important go in the middle,
  key navigation at the ends (Laws of UX, Serial Position Effect).

## 9. Decisions and complexity

**Every choice costs time; complexity that cannot be removed belongs to the system, not the person.**

- **Hick's law: decision time grows with the number and complexity of choices** — fewer choices where speed matters,
  a recommended option highlighted, complex tasks broken into steps, features revealed progressively — but never
  simplified to abstraction (Laws of UX, Hick's Law; Hick and Hyman, 1952).
- **Choice overload** — many options overwhelm; offer comparison side by side for decisions such as plans, a featured
  choice, and search and filters up front (Laws of UX, Choice Overload).
- **Occam's razor** — remove every element that can go without losing function; the work is done when nothing else can
  be removed (Laws of UX, Occam's Razor).
- **Tesler's law: a core of complexity cannot be removed, only moved** — move it to the system: defaults, inference,
  autofill, sensible automation; an engineer's extra week beats millions of people's extra minute (Laws of UX,
  Tesler's Law).
- **The Pareto principle** — about 80 % of use comes from 20 % of features; put the effort and the prominence where
  most people benefit (Laws of UX, Pareto Principle).
- **Jakob's law: people expect a product to work like the others they use** — follow conventions; when a familiar
  design must change, let people keep the old one for a while (Laws of UX, Jakob's Law).
- **Cognitive bias shapes every judgment, the designer's included** — defaults are chosen most, framing changes
  choices, and knowing a bias does not remove it; design defaults in the person's interest and test the designer's
  assumptions (Laws of UX, Cognitive Bias; Tversky and Kahneman, 1972).

## 10. Movement and time

**Targets people can reach, responses that keep pace with them, input they need not format.**

- **Fitts's law: the time to reach a target depends on its distance and size** — large enough targets, ample spacing,
  and the controls of a task near where attention is (Laws of UX, Fitts's Law; Paul Fitts, 1954). The minimum target
  is the `accessibility` skill's floor; on a device with an encoder, distance is steps of focus, and the frequent
  action is few steps away.
- **The Doherty threshold: a response within 400 ms keeps people and system at the same pace** — feedback within that
  time; perceived performance (progress, a skeleton, optimistic updates) when the work takes longer; a progress
  indicator makes a wait tolerable (Laws of UX, Doherty Threshold; Doherty and Thadani, 1982). Feedback on a press
  comes sooner still — the `touch-and-gesture` and `motion` skills hold its timing.
- **Parkinson's law: a task expands into the time it is given** — make tasks shorter than people expect: autofill,
  remembered details, fewer fields (Laws of UX, Parkinson's Law).
- **Postel's law: be liberal in what you accept, conservative in what you send** — accept the many ways people enter a
  phone number, a date or a card, normalise it, set clear limits, and say plainly what was understood (Laws of UX,
  Postel's Law).

## 11. Motivation and the memory of an experience

**People keep going when they see progress, and judge an experience by its best or worst moment and its end.**

- **Flow — immersed, energised focus** — happens when the challenge matches the skill; give clear feedback on each
  action, remove friction that interrupts, and make features discoverable (Laws of UX, Flow; Csíkszentmihályi, 1975).
- **Goal-gradient effect: effort rises near the goal** — show progress clearly; a head start (two of ten steps already
  done) raises completion — and is honest about the steps that remain (Laws of UX, Goal-Gradient Effect).
- **Zeigarnik effect: unfinished tasks are remembered** — a visible incomplete state (a profile 60 % done, a draft)
  invites return; never use it to nag (Laws of UX, Zeigarnik Effect).
- **Peak-end rule: an experience is judged by its peak and its end** — design the most intense moment and the last
  one; negative moments are remembered more vividly than positive ones (Laws of UX, Peak-End Rule; Kahneman and
  others, 1993).
- **Paradox of the active user: people start using a product without reading anything** — put guidance in context,
  at the moment it is needed, never in an up-front tour people must sit through (Laws of UX, Paradox of the Active
  User; Rosson and Carroll, 1987).

## 12. Errors

**Most errors are the design's: prevent slips with constraints and defaults, prevent mistakes with a clear model, and
make every action recoverable.**

| Kind | What happens | Prevent it with |
| --- | --- | --- |
| Slip | The person meant one action and did another, often a similar one, on autopilot — experts slip more | Constraints, good defaults, suggestions, forgiving formats, distance between similar destructive and safe actions |
| Mistake | The person's goal or plan is wrong for the task, from a wrong mental model | Conventions, visible affordances, previews before heavy actions, research into the gap |

Source: Nielsen Norman Group, "Preventing User Errors: Avoiding Unconscious Slips" and "… Avoiding Conscious
Mistakes".

- **Warn before the error** — a character count, an unavailable date already greyed, an inline check as the person
  finishes a field.
- **Confirm sparingly** — a confirmation on every action is clicked through by habit ("the computer that cried
  confirm"); keep it for what cannot be undone, and say what will be lost.
- **Undo beats confirmation** where the action can be reversed (Shneiderman S6).
- **Recovery** — say what happened and how to fix it, keep what the person entered, and put them back where they were
  (H9; the words are the `ux-content` skill's).
- **Remove memory burdens** — show the context a person needs to resume after an interruption.

## 13. The laws of UX, by decision

**Every law on Laws of UX, with the decision it informs and the section that holds it.** Source: Laws of UX (Jon
Yablonski), each law's page, read for this reference.

| Law | In one line | Use when deciding | § |
| --- | --- | --- | --- |
| Aesthetic-Usability Effect | Attractive designs are perceived as more usable | How much polish a test build needs; reading test results | §7 |
| Choice Overload | Many options overwhelm | How many options to show; whether to add comparison, search or filters | §9 |
| Chunking | Information grouped into meaningful wholes is easier to process | How to break up long content, forms and numbers | §8 |
| Cognitive Bias | Systematic errors in judgment | Defaults, framing; checking the team's own assumptions | §9 |
| Cognitive Load | The mental effort an interface demands | What to remove; what the system should carry | §8 |
| Doherty Threshold | Productivity soars below a 400 ms response | Feedback timing; perceived performance during waits | §10 |
| Fitts's Law | Target time depends on distance and size | Size and placement of frequent and primary actions | §10 |
| Flow | Full, energised focus when challenge matches skill | Friction, feedback and discoverability in repeated tasks | §11 |
| Goal-Gradient Effect | Effort rises near the goal | Progress indicators; how many steps to show | §11 |
| Hick's Law | Decision time grows with choices | Menus, options, onboarding, a recommended choice | §9 |
| Jakob's Law | People expect the conventions of other products | Whether to follow a convention or break it | §6, §9 |
| Law of Common Region | A shared boundary groups elements | Cards, sections, containers | §7 |
| Law of Prägnanz | Complex images are read as the simplest form | Simplifying icons, shapes and structure | §7 |
| Law of Proximity | Near objects are grouped | Which elements sit together | §7 |
| Law of Similarity | Similar elements are seen as related | What looks alike, and what must look different | §7 |
| Law of Uniform Connectedness | Connected elements read as related | Connecting steps, items and their details | §7 |
| Mental Model | What people believe about how a system works | The conceptual model; conventions; labels | §6 |
| Miller's Law | About seven items in working memory, with wide variation | Chunking — never as a hard limit on items | §8 |
| Occam's Razor | The simplest sufficient answer wins | What to remove | §9 |
| Paradox of the Active User | People use software without reading manuals | Onboarding and help in context | §11 |
| Pareto Principle | About 80 % of effects come from 20 % of causes | Prioritising features, fixes and prominence | §9 |
| Parkinson's Law | A task expands into the time available | Autofill, defaults, fewer steps | §10 |
| Peak-End Rule | Experiences are judged by their peak and end | The moments to design hardest: the peak, the confirmation, the error | §11 |
| Postel's Law | Liberal in what you accept, conservative in what you send | Input formats, validation, normalising | §10 |
| Selective Attention | People attend to what serves their goal | Banner and change blindness; where to place what matters | §7 |
| Serial Position Effect | First and last items are remembered best | Order of lists and navigation | §8 |
| Tesler's Law | A core of complexity cannot be removed | Who carries complexity — the system or the person | §9 |
| Von Restorff Effect | The item that differs is remembered | Emphasising one primary action | §7 |
| Working Memory | A few chunks, fading in seconds | Carrying information across screens; recognition over recall | §8 |
| Zeigarnik Effect | Unfinished tasks are remembered | Showing incomplete states that invite return | §11 |
