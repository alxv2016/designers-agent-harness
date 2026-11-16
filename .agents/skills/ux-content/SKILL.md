---
name: ux-content
description: How the words in an interface are written — every label, button, title, message, hint and accessible name — carried in the skill (references/ux-content.md), with the principles for every platform and guidance labelled for the web, iOS, Android and embedded ESP-IDF devices with an LVGL screen — one voice and a tone set by the moment; the four tests and editing passes (purposeful, short, human, one meaning); the important words first, plain words, length heuristics and room for the longest translation, a label's width on a small panel and LVGL's label long modes; sentence case, and Apple's title case labelled iOS; punctuation, numbers, units, dates from a formatter, abbreviations, and every character a glyph the compiled font holds; one name per thing, a word list, naming a feature or a setting, the verbs each input takes; the pattern for each element — titles, buttons, links, fields, settings, confirmations, errors, empty states, success and status, progress, notifications, permission requests, onboarding, tooltips; accessible content — the WCAG criteria that govern words, names a screen reader speaks, status messages read alone, cognitive accessibility, inclusive language, strings ready for translation; plus ux_lint.py, which reads the UI strings in web, iOS, Android and C/C++ LVGL files and flags generic buttons, "please", exclamation marks, blame, "Error" titles, title case, all capitals, three full stops, "e.g.", "successfully", "click here", "the user" and "enable". Builds on the accessibility skill's floors for names, forms, errors and status messages. The product's voice, case convention and word list come from its own DESIGN.md. Portable — the folder works in any repo. Use when writing or changing any UI string — a label, a button, a title, an error, a toast, a dialog, an empty state, a notification, a hint, an accessible name — naming a feature or a setting, reviewing a screen's words or a diff that changes strings, or building a voice or a word list.
metadata:
  scope: portable
---

# UX content

How the words on every screen are written — clearly, briefly, in one voice — and how they work for everyone. The
rules and their reasons are kept in this skill at [references/ux-content.md](references/ux-content.md) (cited
`UX_CONTENT §n`); this page indexes them in one-line rules and holds the steps: writing the words for a screen,
reviewing them, and the string check. The product's own content decisions — its voice traits, its case convention,
its word list, the verbs its inputs take, the characters its fonts hold — come from the project's own `DESIGN.md` (or
a file it names); that file wins over the reference, and the reference over this page.

**Platforms.** The rules below hold on every platform. The reference labels where guidance differs — **Web**,
**iOS**, **Android**, **Embedded (ESP-IDF, LVGL)** — notably Apple's title case on iOS (UX_CONTENT §3.1), the verbs
each input takes (UX_CONTENT §4.3), and on a device's small panel the room a label has, the glyphs its fonts hold and
words carried with no screen reader (UX_CONTENT §2.4, §3.4, §6.1).

**Portable.** This folder is self-contained and links to nothing outside itself (it names the rest of a kit in
backticks): the reference and the string check ([scripts/ux_lint.py](scripts/ux_lint.py)). Copy it into any repo's
`.agents/skills/` (or `.claude/skills/`) and it works there: the check reads `UX_STRINGS` from `.agents/project.py`
when the repo has one, and with no kit scans every tracked file that can hold UI strings — web, Swift, Kotlin and
Java, Android XML, Apple `.strings`, and C and C++. It needs git and Python 3.9+.

**Builds on.** The `accessibility` skill owns the floors the words serve — that every control has a name containing
its visible words (`ACCESSIBILITY §4`), that a field has a visible label and typed text is checked on commit with the
problem said beside the field (`ACCESSIBILITY §9`), that a status reaches a screen reader (`ACCESSIBILITY §10`), that
instructions and links never rest on sense or place alone and one function has one name (`ACCESSIBILITY §13`), and
what a device with no screen reader carries instead (`ACCESSIBILITY §14`); its focus reference says where a message
puts focus (`FOCUS §9`). The `touch-and-gesture` skill's feedback reference says when pending, done and failed show,
and that success is said only once it happened (`FEEDBACK §3`, `FEEDBACK §5`). The `design-system` skill's brief
chooses the control and the look of a destructive action and its confirmation (`DESIGN_BRIEF §13`). This skill writes
the words on them and does not restate the floors. In the agent-harness kit, the `ui-designer` skill and agent apply
it at their gates, and `verify.py run` runs the check.

## When to use

- Writing or changing any string a person reads or hears: a label, a button, a title, a caption, an error, a toast, a
  dialog, an empty state, a notification, a hint.
- Naming a feature, a setting or a screen; choosing between two words for one thing.
- Writing an accessible name for an icon-only control, or a status message that is announced.
- Reviewing a screen's or a flow's words, or a diff that changes strings.
- Setting up a voice, a case convention or a word list in the design brief.

## The four tests

Every string is purposeful, short, human and means one thing — and is edited in four passes in that order
(UX_CONTENT §2):

| Pass | Ask | Cut or add |
| --- | --- | --- |
| Purpose | Does it help the person do what they came to do, here? | Cut what serves no decision; add the missing next step or reason |
| Short | Can a word go without losing meaning? | Filler, "please", "successfully", "you can", repetition |
| Human | Would a person say it aloud? | "An error occurred" → what happened |
| One meaning | Could it be misread under stress? | Specific verbs, one term per thing, no double negative |

## Rules

### Do

1. **Put the words that carry the meaning first** — people read the first few words of a line and decide
   (UX_CONTENT §2.1).
2. **Use the common word and the present tense, active voice, addressed to "you"** — no idioms, no jargon a person
   must learn (UX_CONTENT §1.3, §2.3).
3. **Set the tone by the moment** — plain and calm when something failed, brief for the routine, serious before
   something that cannot be undone (UX_CONTENT §1.2).
4. **Use sentence case, and no full stop on a label, button, title or one-line status** — or Apple's title case where
   the design brief says the product follows it on iOS (UX_CONTENT §3.1, §3.2).
5. **Give every measured number its unit, and dates and numbers from the locale's formatter** — on a device, from its
   clock, time zone and language setting (UX_CONTENT §3.3).
6. **Give each thing one name everywhere, and keep the verbs of a flow the same in every flow** (UX_CONTENT §4.1).
7. **Name a feature or a setting for what the person gets; describe a setting by what happens when it is on**
   (UX_CONTENT §4.2, §5.5).
8. **Use the verb every input can follow; an input's own verb only where it is the only way in** — "press" a button,
   "turn" a knob, "tap" only where touch is all there is (UX_CONTENT §4.3).
9. **Label a button with the verb of its result, and the object only where the screen has not named it**
   (UX_CONTENT §5.2).
10. **Confirm only what cannot be undone, as the specific action asked, with the verb on the button and a safe way
    out** — the confirmation's control and first focus are `DESIGN_BRIEF §13`'s (UX_CONTENT §5.6).
11. **Write an error as what happened, why if known, and what to do, beside the problem, with the fix one action
    away** — when it is checked and where it sits are `ACCESSIBILITY §9`'s (UX_CONTENT §5.7).
12. **Give an empty state what will be here and one next action** (UX_CONTENT §5.8).
13. **Say what was done in a success, past tense, only once it happened, and only where the person cannot already
    see it** (UX_CONTENT §5.9; `FEEDBACK §5`).
14. **Word every accessible name as the action, starting with the visible words, without its role** (UX_CONTENT §6.2).
15. **Write a status or an error to be understood when announced, or glimpsed, alone** (UX_CONTENT §6.3).
16. **Leave room for the longest translation, wrap rather than cut, and never build a sentence from fragments**
    (UX_CONTENT §2.4, §6.6).
17. **On a device, put every character the strings use in the fonts' glyph ranges** — "…", "’", "°" — rather than
    dropping the rule the character serves (UX_CONTENT §3.4).
18. **Keep the product's word list current** — a new term is added with the words not to use and its meaning, in the
    change that brings it in (UX_CONTENT §4.1).

### Never

- **A generic button where the action has a name** — OK, Yes, No, Submit, Confirm (UX_CONTENT §5.2).
- **Blame, alarm or jokes in an error** — "invalid", "illegal", "Oops", "Error" as a title, an exclamation
  (UX_CONTENT §5.7).
- **"Please" in an instruction, or "sorry" for a routine fault** (UX_CONTENT §7.5).
- **"Click here", "Learn more" alone, or a link whose words do not say where it goes** (UX_CONTENT §5.3).
- **A placeholder as the only label** — on LVGL, an `lv_textarea`'s placeholder text included (UX_CONTENT §5.4).
- **A direction, a colour or a shape as the only way to find a control** — name it (UX_CONTENT §4.3).
- **Something essential only in a toast or an empty state** — both disappear (UX_CONTENT §5.9).
- **Words cut to fit a box** — a label that ends in dots or scrolls when it must be read (UX_CONTENT §2.4).
- **All capitals for words** (UX_CONTENT §3.1).
- **A readability score as the test of interface text** — test the words with people (UX_CONTENT §7.4).

## Procedure

### Writing the words for a screen or a flow

1. **Know the moment** — who reads it, what they are doing, how they likely feel, what is at stake; the product's
   voice, case convention and word list from its design brief (UX_CONTENT §1).
2. **Write what you would say to the person**, then shape it to the element's pattern (UX_CONTENT §5).
3. **Edit in the four passes** — purpose, short, human, one meaning.
4. **Check each name against the word list and the rest of the product**; add a new term to the list.
5. **Read every string aloud, and every status as if announced alone**; write the accessible name of each icon-only
   control (UX_CONTENT §6.2, §6.3).
6. **Check the room** — the string fits the space with the translation allowance and wraps rather than cuts; on a
   device, measured in the real font on the panel, with every glyph in the font (UX_CONTENT §2.4, §3.4, §6.6).
7. **Return a string table**: element, string, its accessible name where it differs, its length, and why it is worded
   so where that is not obvious. In the kit, the person's yes on the words is recorded as the `ui-designer` skill's
   copy draft.

### Reviewing a screen's words or a diff

1. **Run the string check on the changed files** (below) and read every hit on a changed line.
2. **Read each changed string through the four tests and its element's pattern** (UX_CONTENT §5).
3. **Check consistency against the rest of the product**: the same thing, the same name; the same action, the same
   verb (UX_CONTENT §4.1).
4. **Check the accessible names, the status messages and the translation allowance** (UX_CONTENT §6).
5. **Report each finding with the string, the rule (`UX_CONTENT §n`) and a rewrite.** Voice, tone and whether a word
   helps are judgment — the reviewer's, never the script's.

## Checks

```sh
python3 .agents/skills/ux-content/scripts/ux_lint.py            # every file UX_STRINGS names, against its baseline
python3 .agents/skills/ux-content/scripts/ux_lint.py <file> …   # the files a change touched, every hit
python3 .agents/skills/ux-content/scripts/ux_lint.py --test      # the self-test
```

- [ ] (script) **U1** a generic button word where the action has a name — 0 hits, or an information-only "OK" marked
- [ ] (script) **U2** "please" — 0 hits
- [ ] (script) **U3** an exclamation mark — 0 hits
- [ ] (script) **U4** "oops", "uh-oh" or "whoops" — 0 hits
- [ ] (script) **U5** "invalid" or "illegal" — 0 hits
- [ ] (script) **U6** "Error" as a title or a prefix — 0 hits
- [ ] (script) **U7** title case — 0 hits, or the brief follows Apple's title case (`"case": "title"`)
- [ ] (script) **U8** three full stops — 0 hits
- [ ] (script) **U9** "e.g.", "i.e.", "etc.", "and/or" or "via" — 0 hits
- [ ] (script) **U10** "successfully" — 0 hits
- [ ] (script) **U11** "click here", "tap on" or "click on" — 0 hits
- [ ] (script) **U12** "the user" — 0 hits
- [ ] (script) **U13** "enable", "disable" or "toggle" for something a person switches — 0 hits
- [ ] (script) **U14** words in all capitals, counting letters only — 0 hits, or the term listed in `names` (common
  acronyms such as LED, USB, PIN, AM and PM never count)
- [ ] Each changed string passes the four tests and its element's pattern
- [ ] One name for each thing and one verb for each action across the product; the word list updated
- [ ] Every icon-only control has a name; every status reads alone
- [ ] Every string fits with its translation allowance, and wraps rather than cuts
- [ ] The words read on the screen or the device they appear on — needs the person

The check reads the strings it can find: every string literal at the own level of a call `calls` names — each
argument, so a message box's title and text are both read, but never a literal inside a nested call — the literal
after an assignment `calls` names, the text between tags in markup and JSX, and Android's `<string>` resources
(inline tags and CDATA read through, `translatable="false"` skipped). A small lexer reads each file, so comments,
regular expressions, interpolation, raw and triple-quoted strings and C's adjacent literals are read as the language
reads them; files are UTF-8, or UTF-16 with its byte-order mark. Its settings, from `UX_STRINGS` in
`.agents/project.py` (a single string counts as one item): `paths` (the files to read; empty falls back to
`UI_PATHS`, and with no kit every tracked file of a known kind outside vendored and generated folders), `calls`
(regular expressions that replace its defaults for the web, iOS, Android and LVGL), `names` (proper nouns and
acronyms that keep their capitals), `baseline` (the hits accepted today) and an optional `case` (`"title"` turns U7
off). It reports the hits, the strings checked and the files read, and says "nothing was checked" when it read no
files or found no UI strings in them. A hit is a string to look at, not always a fault; a sanctioned one carries
`ux-exception` on its line with the reason. It cannot read a string built at run time, one kept in a table it was
not told about, `stringResource` or `lv_tr` keys (it reads the resource files instead), or whether a word helps.

## Traps

- **The fix makes it longer than the space** → the English fitted, the rewrite does not → wrap or rethink the element;
  never cut the words to a box (UX_CONTENT §2.4).
- **"Save" on a button, "Saved" in its toast and "Stored" in the help** → three words for one action → the word list
  (UX_CONTENT §4.1).
- **A friendly error is still a vague one** → "Hmm, something's not right" names nothing → what failed and what to do
  (UX_CONTENT §5.7).
- **A visible label and an accessible name that disagree** → a voice-control user says what they see and nothing
  happens → the visible words start the name (UX_CONTENT §6.2).
- **A status that makes sense only next to the screen** → "Done!" heard alone tells a screen-reader user nothing →
  name the outcome (UX_CONTENT §6.3).
- **A sentence built from pieces** → it cannot be translated → one whole string with placeholders (UX_CONTENT §6.6).
- **"Saving…" shows a box on the device** → the font was compiled without U+2026 → add it to the glyph range; three
  full stops is the wrong fix (UX_CONTENT §3.4).
- **A device label ends in dots** → `LV_LABEL_LONG_MODE_DOTS` on text that must be read → wrap it and give it the
  lines, or shorten the words (UX_CONTENT §2.4).
- **A guide's rule taken as universal** → Apple's title case on the web, or a car screen's character limit on a
  phone → the platform's convention, decided in the brief, and UX_CONTENT §7.5's choices.

## Sources

| Topic | Where |
| --- | --- |
| The rules, the patterns, accessible content, and every source with what it gave | [references/ux-content.md](references/ux-content.md) |
| Voice, tone, writing, alerts, buttons, notifications, accessibility labels, case on iOS | Apple Human Interface Guidelines (Writing and the component pages); Apple Style Guide; WWDC19, WWDC22, WWDC25 and WWDC26 sessions on writing |
| Sentence case, plain words, errors, buttons, fields | Microsoft Writing Style Guide; Material; GOV.UK Design System; Shopify Polaris; Atlassian; Mailchimp |
| The criteria that govern words; cognitive accessibility; translation | WCAG 2.2 Understanding; W3C, Making content usable for people with cognitive and learning disabilities; W3C Internationalization |
| How people read; errors, confirmations, placeholders | Nielsen Norman Group |
| Strings, plurals and formatters on each platform | MDN (`Intl`); Apple Developer (String Catalogs); Android Developers (string resources) |
| Labels, placeholders, message boxes, fonts and translation on a device | LVGL 9 documentation and headers (`lv_label.h`, `lv_textarea.h`, `lv_msgbox.h`, `lv_translation.h`, `lv_conf_template.h`) |
