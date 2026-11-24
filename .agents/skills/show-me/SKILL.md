---
name: show-me
description: >-
  Makes every picture the work needs, at the lowest fidelity that answers the question — a diagram (a Mermaid flow, sequence or state diagram drawn in one small HTML page and opened, or a text view for code: pseudocode, a call tree, a file tree, a short diff), a sketch (a screen as labelled grey boxes, a new feature beside the real frames already on disk), or a mock (a screen at the target's real size in the project's tokens and fonts, with a spacing-overlay copy and a values file). The one place the ux-designer and the ui-designer draw from, and the person can ask it for a diagram or a mock at any time. A picture approves nothing by itself; whether a mock needs the person's yes is the ui-designer's gates' to say. Portable — the folder works in any repo. Use when the person says /show-me, "show me", "draw it", "mock it up" or "what does that look like", when the ux-designer maps a flow or a new feature, when the ui-designer drafts a screen for gate 1, or when a flow, a structure or a change would be judged quicker as a picture than as prose.
metadata:
  scope: portable
---

# Show me

The one skill that makes pictures: a diagram to see how something works, a sketch to see where something new goes,
a mock to see how a screen will look. Pick the lowest fidelity that answers the question; each step up costs more.

**Portable.** This folder is self-contained: the page that draws diagrams and lays out frames is
[references/template.html](references/template.html). A project's colours, type, sizes and screens come from its own
design brief (`DESIGN.md`), its token files and the frames it already renders, never from this skill. When a mock
needs the person's yes is the `ui-designer` skill's gates' to say; when a flow needs it, the `ux-designer`'s brief.

## When to use

- **The person asks** — `/show-me`, "show me", "draw it", "mock it up": make the view they asked for, at the fidelity
  they named, or the lowest one that answers them.
- **The `ux-designer`** maps a flow, a path or a new feature: a diagram, or a sketch beside the screens that exist.
- **The `ui-designer`** drafts a screen or a component for gate 1: a mock.
- **Any agent** whose point would be judged quicker as a picture offers one — in the main session, "Want me to show
  this?"; in a subagent's report, a last line `Offer show-me: <the view and what it shows>` — and makes it only on the
  person's yes.

## Rules

### Do

1. **Choose the fidelity by the question, the lowest that answers it:**

   | Fidelity | Answers | Made as | Cost |
   | --- | --- | --- | --- |
   | Diagram | How it works, in what order, who calls whom, which file holds what | Text views in the reply for code; a Mermaid diagram drawn in the page for flows | Seconds |
   | Sketch | Where something new goes, beside what exists | The page: real frames from disk, the new part as a labelled grey box | A minute |
   | Mock | How a screen will look | The screen at the target's real size in the project's tokens and fonts, a spacing-overlay copy, a values file | Minutes |

2. **Pick the view inside a diagram by the question** — pseudocode for logic, a call tree for who calls what, a
   shallow file tree with notes for where things live, a short `diff` for what a code change moves, a Mermaid
   flowchart for steps and paths, a sequence diagram for who talks to whom, a state diagram for modes.
3. **Show every picture as a picture** — Mermaid's source reads as code in a chat, so draw it in the page
   ([references/template.html](references/template.html)), open it (`open` on macOS, `xdg-open` on Linux, `start` on
   Windows), and hand it over as a link with its absolute path. Text views for code stay in the reply.
4. **A complex flow is an overview, then detail** — 5 to 8 boxes for the whole, then one small diagram per busy step,
   each under a heading and one line of context; one idea per diagram, about 15 boxes at most, split past that; error
   paths and alternatives in a diagram of their own; related steps grouped in a labelled subgraph.
5. **Draw anything new as new** — in a diagram, a dashed box labelled "New"; in a sketch, a grey box with its parts as
   plain words. A diagram or sketch never draws a screen that does not exist yet as a design; that is a mock.
6. **Use only frames already on disk** in a diagram or a sketch — the project's screenshots, a host render, an earlier
   mock — each named in its caption.
7. **Make a mock as the target shows it** (Making a mock, below) — at its real size, in its real tokens and fonts,
   every state that changes the layout, a values file beside it, and the spacing overlays on a copy.
8. **Keep every picture outside the tracked tree** — the session's scratchpad, or `build/` where it is ignored. A
   diagram's or sketch's footer says "Explains; approves nothing."
9. **Place each picture next to the short text it supports**, keeping only the steps, calls, files, states and
   elements the question needs.

### Never

- **Make a picture nobody asked for** — offer it, and wait for the person's yes; a mock for gate 1 is part of the
  `ui-designer`'s work, which the person asked for.
- **Treat a diagram or a sketch as a design to approve**, or a mock as approved because it exists — a yes is the
  person's, recorded by the gates that need it.
- **Answer a question about the look with a diagram, or a question about how it works with a mock.**
- **Build, flash or deploy the product to make a diagram or a sketch** — they use what is on disk. A mock draws in the
  project's tokens with the cheapest renderer that shows the target truly.
- **Commit a picture, or put it in the repo** — a doc that needs a diagram writes its own Mermaid.

## Making a diagram

1. Name the point in one sentence; pick the view (Do 2).
2. Code: write the text view in the reply, next to its sentence.
3. A flow: write the Mermaid, split it past about 15 boxes (Do 4), copy the template to
   `<scratchpad>/show-me/show-me-<topic>.html`, fill in the title, one line of context and the diagrams, open it, and
   hand over its path as a link.

## Making a sketch

1. List the real screens around the new part, and find their frames on disk.
2. Copy the template; put the frames in its frame row, in the order a person meets them, each captioned; put the new
   part between them as a grey box labelled "New — sketch", its contents as plain words.
3. Open it and hand over its path. A sketch that grows into a design question becomes a mock.

## Making a mock

1. **Read first** — the project's design brief (its principles, tokens, components and the screens nearby), the
   brief the mock follows (a UX brief for a new flow), and the skills its parts call for: `layout`, `typography`,
   `accessibility`, `ux-content`; motion goes to the `motion` skill, a gesture to `touch-and-gesture`.
2. **Draw it where it costs nothing** — in the scratchpad, at the target's real sizes, in the project's real tokens
   and type, never as a change to the product:
   - **Web** — a static page that loads the project's token file, at each breakpoint the product supports.
   - **iOS, Android** — a frame at the device sizes the product supports, in the platform's text sizes.
   - **Embedded (ESP-IDF, LVGL)** — a frame at the panel's resolution, pixel for pixel, in the fonts compiled into
     the firmware; a host build of the UI on LVGL renders it in the real widgets. Judge it also at the panel's
     physical size, and on its shape when it is round or has cut corners.
   - **A design file** — a frame exported from it, when the person designs there.
3. **Draw every state that changes the layout** — empty, loading, error, long text, the largest text size; the layout
   at each tier where it changes.
4. **Write the values file beside it** — `<screen>_mock<n>.md`: each element's component, its tokens (colour role,
   type role, spacing, radius), its states, the focus order, each text's contrast against what is painted under it,
   the accessibility decisions, the layout spec tier by tier (regions, navigation, panes, margins, spacing, density,
   what survives a resize), and each text's role, emphasis, measure, wrap and numbers.
5. **Draw the spacing overlays on a copy beside the clean frame, never over it** — margins (the space between
   elements) in yellow or orange hatching, padding (the space inside an element) in green, each band labelled with
   its px and, where there is room, its role or token. A built sheet gets the same, on a copy of the built frame.
6. **Look at it yourself, then show it** — fix every contrast failure first; save `<screen>_mock<n>.png` with its
   values file; a change is a new mock, `n + 1`.
7. **Ask open questions with concrete outcomes** — "a sheet or a full screen?", with a mock of each when it matters.

## Checks

- [ ] The fidelity is the lowest that answers the question, and the person asked for the picture or said yes to it
- [ ] A diagram: one idea, about 15 boxes at most, an overview before detail; drawn in the page and opened
- [ ] Anything new is drawn as new; every frame shown is on disk and named
- [ ] A mock: real size, real tokens and fonts, every layout state, a values file, an overlay copy beside the clean
      frame, contrast fixed before it was shown
- [ ] Every picture is outside the tracked tree, handed over as a link with its absolute path

## Traps

- **The diagram shows as code in the chat** → Mermaid was pasted as text → draw it in the page and open it.
- **The page is blank** → the browser could not load Mermaid from its CDN, offline → hand over the Mermaid as text
  with a line saying why, or open the page once online.
- **A sketch is read as a design** → a new part was drawn as pixels, or the footer was dropped → a grey box labelled
  "New — sketch", and keep the footer.
- **A mock looks right on the monitor and small on the target** → it was judged at the monitor's size → judge it at
  the target's physical size too.
- **The overlays hide the design** → they were drawn on the only frame → draw them on a copy beside it.

## Sources

| Topic | Where |
| --- | --- |
| The technique of the smallest visual that makes the point | Inspired by [HumanLayer's show-me](https://github.com/humanlayer/skills/tree/main/plugins/show-me) |
| Mermaid's diagram types and syntax | [Mermaid](https://mermaid.js.org/intro/) |
