# UX Methods

How experience work is done and checked: the human-centred process and the Double Diamond, choosing a research method
by the question it answers, understanding people and their tasks, structuring information, the UX brief that hands a
flow to the screen designer, evaluating a design with and without users, rating severity, measuring usability, and
what an agent can and cannot do itself. People read it to plan UX work with reasons; coding agents read it, through
the `ux-designer` skill, before they frame a flow, plan a study or review an experience.

**Where it lives.** In the `ux-designer` skill, beside [its SKILL.md](../SKILL.md), the principles in
[hci.md](hci.md) (HCI) and the review items in [rubric.md](rubric.md) (UX_REVIEW_RUBRIC). The skill folder is
self-contained: copy it into any repo's `.agents/skills/` and these come with it.

**Platforms.** The methods are about people and hold on every platform; testing on a device in the hand, a watch on
the wrist or a panel on a wall is done on that device, in its setting.

**Stability.** Cite this doc as `UX_METHODS §n`. Do not renumber; add new material under the next free number.

| § | Section | Look here for |
| --- | --- | --- |
| 1 | [Process](#1-process) | Human-centred design, the Double Diamond, iteration |
| 2 | [Choosing a method](#2-choosing-a-method) | Attitudinal or behavioural, qualitative or quantitative, the stage |
| 3 | [Understanding people](#3-understanding-people) | Interviews, field studies, diaries, surveys; personas and jobs to be done; journey maps |
| 4 | [Tasks](#4-tasks) | Task analysis, top tasks, frequency |
| 5 | [Information architecture](#5-information-architecture) | Structure and labels; card sorting; tree testing |
| 6 | [Evaluating without users](#6-evaluating-without-users) | Heuristic evaluation, cognitive walkthrough, keystroke counts |
| 7 | [Evaluating with users](#7-evaluating-with-users) | Usability testing, how many people, think-aloud, A/B tests, analytics |
| 8 | [Severity](#8-severity) | The 0 to 4 scale and how it is set |
| 9 | [Measuring usability](#9-measuring-usability) | Effectiveness, efficiency, satisfaction; task success, time, SEQ, SUS |
| 10 | [The UX brief](#10-the-ux-brief) | What a brief holds, and how it hands a flow to the screen design |
| 11 | [What an agent can do](#11-what-an-agent-can-do) | Inspection and planning, never findings about people it has not met |

---

## 1. Process

**Understand the problem with the people who have it, then try answers small and often, and keep the ones that work.**

- **Human-centred design makes systems "usable and useful by focusing on the users, their needs and requirements"**
  (ISO 9241-210:2019, Introduction). The 2019 second edition replaces the 2010 first (its Foreword), and its
  principles and activities "have not changed substantially since ISO 13407" (its Introduction).
- **Its six principles** (ISO 9241-210:2019, clauses 5.2–5.7, by their headings): the design rests on an explicit
  understanding of users, tasks and environments; users are involved throughout design and development; user-centred
  evaluation drives and refines the design; the process is iterative; the design addresses the whole user experience;
  the team brings multidisciplinary skills and perspectives.
- **Its four activities, repeated as evaluation feeds back into the design** (clauses 7.2–7.5, and 7.4.4 "Altering
  the design solutions based on user-centred evaluation and feedback"):

| Activity (ISO 9241-210:2019) | What it covers, from its sub-clause headings | In this reference |
| --- | --- | --- |
| 7.2 Understanding and specifying the context of use | A context-of-use description in enough detail to design for | §3, §4; the brief's people and context |
| 7.3 Specifying the user requirements | User and other stakeholder needs, the requirements derived from them, trade-offs resolved | §4; the brief's outcome and tasks |
| 7.4 Producing design solutions | Tasks, interaction and interface designed for the whole experience, made more concrete, altered on evaluation | §5, §10 |
| 7.5 Evaluating the design | User-based testing, inspection-based evaluation, long-term monitoring | §6–§9 |

The activity names and the sub-clause topics are from the standard's table of contents (ISO's free preview); the
right-hand column is this reference's mapping.

- **The Double Diamond: Discover, Define, Develop, Deliver** (Design Council, "The Double Diamond"):

| Phase | Purpose | Typical methods (this reference's mapping) |
| --- | --- | --- |
| Discover | Understand what the problem is rather than assume it — time with the people affected | Interviews, field studies, diary studies, analytics, existing research (§3) |
| Define | Use what was learned to define the challenge differently | Task analysis, personas or jobs, journey maps, the problem statement (§3, §4) |
| Develop | Give different answers to the defined problem; co-design | Flows, the UX brief, card sorting, sketches and prototypes (§5, §10) |
| Deliver | Test answers at small scale, reject what fails, improve what works | Heuristic evaluation, walkthroughs, usability tests, measures (§6–§9) |

The phase names and purposes are the Design Council's; the method column is this reference's mapping, not theirs.

- **Iterate in small rounds** — "3 studies with 5 users each" find more than one study with 15 (Nielsen Norman
  Group, "Why You Only Need to Test with 5 Users").
- **Size the work to the change** — a new product or flow earns discovery; a new screen in a known flow earns a brief
  and a walkthrough; a small change to a screen earns a check against the heuristics.

## 2. Choosing a method

**Pick the method by the question: what people say or what they do, why or how many, and whether they use the real
thing.** (Nielsen Norman Group, "When to Use Which User-Experience Research Methods".)

| Dimension | One end | The other end |
| --- | --- | --- |
| What is observed | Attitudinal — what people say | Behavioural — what people do; usability work leans here |
| The answer | Qualitative — why, and how to fix it | Quantitative — how many, how much |
| Context of use | Natural use of the product | Scripted, limited, or no product at all |

| Stage | Goal | Methods |
| --- | --- | --- |
| Strategize (generative) | Find new directions and opportunities | Field studies, diary studies, interviews, surveys, participatory design, concept testing |
| Design (formative) | Improve the usability of a design | Card sorting, tree testing, usability testing, remote testing (moderated and unmoderated) |
| Launch and assess (summative) | Measure against itself or the competition | Usability benchmarking, unmoderated testing, A/B testing, analytics, surveys |

- **What people say and what they do differ** — a survey answers how people feel; only observation answers whether
  they can.

## 3. Understanding people

**Know who uses the product, what they are trying to get done, and the path they take today.**

- **Interviews, field studies and diary studies** show goals, context and workarounds; surveys reach many people with
  a few closed questions (§2).
- **Jobs to be done** — people "hire" a product to make progress on a job; a job names what they need, independent of
  who they are (Nielsen Norman Group, "Personas vs. Jobs-to-Be-Done").
- **Personas** add who: goals, attitudes, behaviour, context; they build empathy and help choose between users. The
  two are compatible — a persona holds its jobs (same source).
- **A persona or job comes from research** — one written from the team's assumptions is labelled an assumption.
- **A journey map visualises the process a person goes through to reach a goal** — one actor, a scenario and its
  expectations, the phases, actions, mindsets and emotions at each, and the opportunities; it rests on research data
  (Nielsen Norman Group, "Journey Mapping 101"). A user flow, a service blueprint and a story map are its neighbours.

## 4. Tasks

**A task is an observable activity with a start and an end; know each one's steps, frequency and difficulty before
designing for it.**

- **Gather by watching, not only asking** — contextual inquiry, critical-incident interviews, records, activity
  sampling; "you are not the user" (Nielsen Norman Group, "Task Analysis").
- **Structure it as a hierarchy** — the goal, its subtasks, their steps (hierarchical task analysis).
- **Note each task's frequency, complexity, physical demands and time** — frequent tasks earn accelerators and
  prominence (Pareto, HCI §9); rare and risky ones earn guidance and protection (HCI §12).
- **List the top tasks** — the few that most people come to do; the flow and the navigation serve them first.

## 5. Information architecture

**Structure and label content the way the people who use it think about it, and test that they can find things.**

- **Card sorting** — people group labelled cards in the way that makes sense to them: open (they name the groups),
  closed (the groups are given, to validate), hybrid (generally not recommended); 30 to 50 cards; at least 15 people
  for qualitative insight, 30 to 50 for quantitative; one level of grouping only (Nielsen Norman Group, "Card
  Sorting: Uncover Users' Mental Models").
- **Tree testing** — people find where a resource lives in a text-only tree, with no visual design; used at the start
  of a redesign and after a card sort, before content and layouts; answers are leaves, not branches (Nielsen Norman
  Group, "Tree Testing").
- **Labels are the architecture's words** — the `ux-content` skill's rules hold for them.

## 6. Evaluating without users

**Inspection finds many problems cheaply and fast; it predicts what people will struggle with, and never replaces
watching them.**

### 6.1 Heuristic evaluation

- **Three to five evaluators, each alone, against the heuristics** (HCI §2), then consolidated (Nielsen Norman Group,
  "How to Conduct a Heuristic Evaluation").
- **Narrow the scope** — one task, section, user group or device; about one to two hours each, going through the task
  twice.
- **Rate each problem's severity** (§8) and cite the heuristic or law it breaks.
- **"Useful for stretching a limited UX research budget"; it "cannot replace user research"** (same source).

### 6.2 Cognitive walkthrough

**Step through a task as a new user, asking at each step** (the Wharton method, as listed on Wikipedia, "Cognitive
walkthrough"):

1. Will the user try to achieve the effect that the subtask has?
2. Will the user notice that the correct action is available?
3. Will the user understand that the wanted subtask can be achieved by the action?
4. Does the user get appropriate feedback?

- **It starts from a task analysis** (§4), and checks learnability for first use; it can run before any code.
- **No designing and no defending during the walkthrough** — record each failure, then fix (same source).

### 6.3 Keystroke counts

- **Compare two designs for expert speed by counting operators** — keystrokes, pointing, homing, mental steps — with the
  operator times and the rules for placing mental steps in HCI §5.3.

## 7. Evaluating with users

**Watch people try to do real tasks; qualitative tests find problems, quantitative ones measure.**

- **A facilitator, tasks and a participant**, often thinking aloud (Nielsen Norman Group, "Usability Testing 101").
- **Five people find most of the common problems of one user group** — the first five find about 85 %; test, fix,
  test again (Nielsen Norman Group, "Why You Only Need to Test with 5 Users", from Nielsen and Landauer, 1993).
- **Distinct user groups each need their own** — three or four per group when comparing two, three per group for
  three or more (same source).
- **Quantitative studies need about 20 people**; card sorting about 15 (same source).
- **The simplest study takes about three days** — plan, test five people, analyse and recommend (Nielsen Norman Group,
  "Usability Testing 101").
- **Test on the target, in its setting** — a phone in the hand, a watch on the wrist, a panel where it is mounted;
  include people who use assistive technology (the `accessibility` skill holds the walks).
- **A/B tests and analytics measure what people do at scale** — they answer which and how many, never why.

## 8. Severity

**Rate each problem by its frequency, its impact and its persistence, on one scale.** (Nielsen Norman Group, "Severity
Ratings for Usability Problems".)

| Rating | Meaning |
| --- | --- |
| 0 | Not a usability problem |
| 1 | Cosmetic — fix only if time allows |
| 2 | Minor — low priority |
| 3 | Major — important to fix, high priority |
| 4 | Catastrophe — imperative to fix before release |

- **Several raters, then the mean** — "the mean of a set of ratings from three evaluators is satisfactory for many
  practical purposes"; one rater's ratings are unreliable (same source). An agent's rating alone is labelled as one
  rater's.

## 9. Measuring usability

**Measure effectiveness, efficiency and satisfaction for the tasks that matter, the same way each time.**

| Measure | Of | How |
| --- | --- | --- |
| Task success | Effectiveness | The share of people who complete the task |
| Time on task | Efficiency | Seconds to complete, for those who succeed |
| Single Ease Question | Perceived difficulty of one task | One question on a seven-point scale, after the task |
| System Usability Scale | Perceived usability of the whole product | Ten statements on a five-point scale, scored 0 to 100 |

Sources: Wikipedia, "ISO 9241" and "System usability scale" (John Brooke, 1986).

- **SUS scoring** — SUS = 2.5 × (20 + the sum of items 1, 3, 5, 7, 9 − the sum of items 2, 4, 6, 8, 10), each item
  answered 1 to 5 (Wikipedia, "System usability scale"); above 80 is read as high usability and below 70 as low
  (Wikipedia, "ISO 9241", citing Georgsson and Staggers, 2016).
- **Benchmark before a redesign, measure after** — a number alone says little; the change says more.

## 10. The UX brief

**The UX brief settles the task, the flow and the behaviour before the screen is drawn; the screen designer draws
from it.**

A brief is written for a new flow, a new screen or a change to how something works, and skipped for a change to how
an existing screen looks. It is a scratch file, `<flow>_ux<n>.md`, from the skill's
[template](../templates/ux-brief.md), and holds:

| Part | Holds |
| --- | --- |
| Outcome | The problem, for whom, and how success is measured |
| People and context | Who, their job to be done, where and on what device and input, how often |
| Tasks | The top tasks, each with its frequency and risk |
| Flow | Entry points, steps, decisions, exits, and back, as a list or a Mermaid flowchart |
| Structure | Where it lives in the product, the navigation to it, the labels |
| Interaction model | Direct manipulation, a form, a wizard, a command; the conceptual model in one sentence; defaults |
| States | Empty, loading, partial, error, success, offline, and the first and last moments |
| Errors | Slips and mistakes to prevent, what can be undone, what asks first |
| Principles applied | Each decision with the heuristic or law behind it, and any trade-off |
| Evidence | What is known from research, and what is an assumption |
| Open questions | Each with concrete options, and the research that would settle it |

- **The person's yes on the brief, naming the file, is recorded** before the screen is drafted — with the agent-harness
  kit, `verify.py approve <flow>_ux<n>.md --kind ux`.
- **The screen designer's draft follows the brief's flow, states and behaviour** — a change to them is a new brief.

## 11. What an agent can do

**An agent inspects, plans and predicts; only people show what people do.**

- **It can** run a heuristic evaluation and a cognitive walkthrough, count keystrokes, check a flow against the laws,
  write a UX brief, plan a study, write its tasks and script, and analyse findings the person brings back.
- **It cannot** observe people; a finding about what people do, think or feel, without research behind it, is written
  as a prediction or an assumption, never as a result.
- **One agent is one evaluator** — its severity ratings are one rater's (§8), and a heuristic evaluation asks for three
  to five.
- **Name the research that would settle an open question** — the method, the people, the tasks, the cost (§2, §7).
