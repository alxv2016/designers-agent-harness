---
name: teach
description: Explains a body of work plainly so the person understands it — what it is, how it works and why it is built that way — for code, a screen's behaviour, a design decision (a token's value, a principle in the design brief), a doc's rule, a firmware module or the agent harness itself. Reads the code for how, and the record for why — the doc that owns the topic and its Decisions, the design brief, code comments that cite a doc, then the git history — marking what the record says, what is inferred and what is not recorded; builds diagrams up one part at a time; answers the smallest complete answer first and goes deeper on request; changes nothing. Portable — the folder works in any repo. Use when the person says "teach me", "explain this", "help me understand", "how does X work", "why is it like this", "walk me through this change", "where does this value come from", or "say that more plainly".
disable-model-invocation: true
metadata:
  scope: portable
---

# Teach

Explains what a thing is, how it works and why it is that way, in one plain account at the person's pace. The goal is
that they understand it; nothing is changed. The project's own docs hold the reasons and win over anything inferred
here; its writing style rules govern the words.

**Who it serves.** The person may be a designer reading firmware, an engineer new to the design system, or anyone
about to change, review or debug something. The explanation starts from what they know, read from the conversation.

**Portable.** This folder is self-contained and links to nothing outside itself; it names the rest of a kit in
backticks. It has no script. Copy it into any repo's `.agents/skills/` (or `.claude/skills/`) and it works there.

## When to use

- "Teach me this", "explain this to me", "help me really understand X".
- "How does X work?" — a module, a screen's behaviour, a build step, the harness's loop.
- "Why is it like this?" — a design decision, a token's value, a threshold, a rule in a doc.
- "Walk me through this change" — a diff, a branch, a commit.
- "Say that more plainly" — the last answer again, in plain words.

## Rules

### Do

1. **Pick the two or three things the person should walk away with** from why they ask — about to change it,
   reviewing it, debugging it, new to it, deciding something — and what they already know, read from the
   conversation, never quizzed out of them.
2. **Read the code for how, and the record for why** — the owning doc's Decisions and rules with their reasons, the
   design brief, comments that cite a doc, then `git log` and the commit messages that introduced and changed it.
3. **Label every reason by where it came from** — "the doc says" with a link, "the commit says", "inferred", or "not
   recorded"; keep those labels in the plain account, because they are findings, not style.
4. **Start with a plain definition** — name the thing, give its common name if it has one, say what it is in general,
   then tie it to this case ("here, we use it to…").
5. **Give the smallest complete answer first** — a sentence or two — then stop, and add a layer when they ask.
6. **Explain each part by the problem it solves and how it works**; walk through what happens when the person does the
   thing — presses the button, scrolls the list, flashes the board.
7. **Build a picture up one part at a time** — for three or more moving parts, a series of small Mermaid diagrams,
   each redrawing the last and adding one part; plain Mermaid with no styling, so it reads in light and dark themes.
8. **Show the real thing when it lands faster** — the diff, the line, a screenshot of the actual screen.
9. **Define a term the first time it matters, and keep one name for it**; map it to a design word only where the
   match is true.
10. **Make every file, doc section and URL a link the person can click.**
11. **End with an offer to go deeper on the threads worth chasing**, named in a few words.

### Never

- **Edit a file, run a change or start the work** — a request to change something is a new task.
- **State a reason the record does not give as fact** — label it inferred, or say it is not recorded.
- **Draw one diagram with every part at once and call it the explanation** — that is a reference, not teaching.
- **Draw or describe a screen you did not capture as if it were real.**
- **Lecture** — no quizzes, no "repeat it back", no "pause here", no labels such as "key insight", "the tricky part"
  or "TL;DR"; say the thing.
- **List functions and constants as the explanation** — that is reference, not understanding.
- **Report what you did** — the reply is the explanation itself.

## Procedure

### Teaching a thing

1. **Read the question and the conversation** — what they ask, why, and what they already know (Do 1).
2. **Get oriented** — find the files, the doc that owns the topic, and the design brief's section if it is about the
   look or the experience. For broad reading, hand it to a read-only helper agent and keep its conclusion.
3. **How** — read the code path from the trigger to the result: the entry, each step, the data it carries, where it
   ends. Run something read-only only when that shows it faster — a test, a dry run, a log.
4. **Why** — in this order, stopping when the question is answered:
   1. The owning doc's rules, Decisions and Traps, with their section numbers.
   2. The design brief's principles, tokens and exceptions, for a design choice.
   3. Comments in the code that cite a doc section.
   4. `git log --follow -- <file>`, `git log -S '<name>'` and `git blame -L <range> <file>`, then the commit
      messages; a pull request's discussion where the repo's tools reach it.
   5. Your own inference, labelled as one, and what the record does not say.
5. **Write the smallest complete answer** — the plain definition, tied to this case, in a sentence or two (Do 4, Do 5).
6. **Add the first layer only if the question needs it** — how it works, with the walk-through or the first diagram.
7. **Offer the next threads** and stop (Do 11).

### A change or a branch

1. **Read the diff in full**, the commit messages, and any doc section it updates.
2. **Say what changes for the person who uses it**, first, in one or two sentences.
3. **Then how the change does it** — the files in the order the data flows, not the order of the diff.
4. **Then why** — from the commit message and the docs it touches, labelled.

### Saying it more plainly

1. **Restate the last answer** in short sentences, everyday words and no jargon, as one person talking to another.
2. **Keep every fact and every confidence label**; drop only the words.

## Checks

No script reads an explanation; these are read.

- [ ] The answer starts with a plain definition tied to this case (Do 4)
- [ ] The first reply is the smallest complete answer, not a wall of text (Do 5)
- [ ] Every reason is labelled — the record with a link, inferred, or not recorded (Do 3)
- [ ] A system of three or more parts is drawn as a build-up, one part per diagram (Do 7)
- [ ] Every file, doc section and URL is a link (Do 10)
- [ ] No file was changed

## Traps

- **The person nods along and still cannot change the code** → the answer listed functions instead of explaining the
  problem each solves → explain by problem and walk-through (Do 6).
- **A confident "it was done for performance" that nobody wrote down** → an inference stated as fact → label it, and
  say the record is silent (Do 3).
- **One diagram with twelve boxes** → the whole system at once → build it up one part at a time (Do 7).
- **A designer lost at the third term** → jargon undefined → define each term once and keep its name (Do 9).
- **"Explain" turned into an edit** → the request read as a task → explain only; a change is a new task.
- **Five paragraphs for a yes-or-no question** → depth placed before the answer → the smallest complete answer first
  (Do 5).

## Sources

| Topic | Where |
| --- | --- |
| Teaching from how and why, built-up diagrams, no lecture | pstack's `teach`, `how`, `why` and `bro` skills, a Cursor plugin by Lauren Tan (MIT licence), rewritten for this kit |
| Reading the history of a line | `git log --follow`, `git log -S` and `git blame -L`, in the git documentation |
| Diagrams in Markdown | Mermaid's flowchart and sequence diagram syntax |
