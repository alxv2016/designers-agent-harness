# {{doc_title}}

The web app as its tooling sees it: its name and language, the Node it runs on, the ports its servers take, and the
browsers and sizes it is tested in. People read it to know what the app promises to run on; coding agents read it
before they generate or change the app's configuration. Source of truth: this doc — a value changes here first, then
in the file that carries it (§2). Related: `APP_ARCHITECTURE` — how the app is put together.

**Stability.** Code comments cite this doc's `§n`. Do not renumber; add new material under the next free number. The
`react-vite-setup` skill reads the Facts table by its rows, wherever it sits.

| Tag | Meaning |
| --- | --- |
| `[DEFAULT]` | The setup's default, kept until the person names another value |
| `[PERSON]` | Chosen by the person |
| `[?]` | Unverified — tracked in Open items |

| § | Section | Look here for |
| --- | --- | --- |
| 1 | [Facts](#1-facts) | The name, the language, Node, the ports, the browsers and the sizes |
| 2 | [Where each fact goes](#2-where-each-fact-goes) | The file and the setting that carry each fact |
| 3 | [Open items](#3-open-items) | What is still undecided, and what settles it |

---

## 1. Facts

**The facts the app's configuration is generated from — one row each, the value alone in its cell.**

| Fact | Value | Source |
| --- | --- | --- |
| Name | {{name}} | {{tag_name}} |
| Title | {{title}} | {{tag_title}} |
| Language | {{lang}} | {{tag_lang}} |
| Node | {{node}} | {{tag_node}} |
| Dev server port | {{dev_port}} | {{tag_dev_port}} |
| Preview port | {{preview_port}} | {{tag_preview_port}} |
| Storybook port | {{storybook_port}} | {{tag_storybook_port}} |
| Browsers | {{browsers}} | {{tag_browsers}} |
| Viewports | {{viewports}} | {{tag_viewports}} |

## 2. Where each fact goes

**Each fact has one home here and one carrier in the code; a change is made here, then there.**

| Fact | Carried by |
| --- | --- |
| Name | `package.json` → `name` |
| Title | `index.html` → `<title>`; Storybook's introduction |
| Language | `index.html` → `lang`, which a screen reader picks its voice by (WCAG 3.1.1) |
| Node | `.nvmrc`, `package.json` → `engines`, CI's `setup-node` — an even release, in active or maintenance LTS |
| Ports | `vite.config.ts` → `server.port` and `preview.port`; the `storybook` script; `.vscode/launch.json`. Each is strict, so a busy port fails loudly instead of moving |
| Browsers | `playwright.config.ts` → `projects`; CI's `playwright install`, with Chromium added when it is not listed — stories run as tests in Chromium alone |
| Viewports | `playwright.config.ts` → one project per browser and size; the smoke test also checks 320 px wide |

## 3. Open items

| Item | Status | Unblocked by |
| --- | --- | --- |
| Each `[DEFAULT]` fact in §1 | Open | The person keeps it — its tag becomes `[PERSON]` — or names another value |
