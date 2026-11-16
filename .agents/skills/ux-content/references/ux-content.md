# UX Content

How the words in an interface are written — every label, button, title, message, hint and name a person reads or
hears: how they sound, how they read, how they are set, what each element says, and how they work for people using a
screen reader or voice control, people with cognitive disabilities, people reading in a second language, and the
translators who carry the product further. People read it to write or judge a screen's words; coding agents read it,
through the `ux-content` skill, before they write, change or review a UI string.

**Where it lives.** In the `ux-content` skill, beside the steps and the string check that apply it —
[its SKILL.md](../SKILL.md). The skill folder is self-contained: copy it into any repo's `.agents/skills/` and this
reference and the check come with it.

**Source of truth.** The product's own content decisions — its voice traits, its case convention, its word list, the
verbs its inputs take, the characters its fonts hold, and any length limit its screens set — live in its design brief
(`DESIGN.md` in the agent-harness kit), or in a file the brief names; they win over this reference. This reference
wins for the rules, and its sources (§7) for what the guides themselves say.

**What it builds on.** The floors are the `accessibility` skill's: names and labels (`ACCESSIBILITY §4`), forms and
errors — when typed text is checked and where the problem is said (`ACCESSIBILITY §9`), status messages
(`ACCESSIBILITY §10`), sensory instructions, link purpose and consistent names (`ACCESSIBILITY §13`), and a device
with no screen reader (`ACCESSIBILITY §14`); where a message puts focus is `FOCUS §9`'s. When a pending, done or failed
state shows, and that success is said only once it happened, is the `touch-and-gesture` skill's `FEEDBACK §3` and
`FEEDBACK §5`. Which control a setting or an action takes, and a destructive action's look and its confirmation's
first focus, are the design brief's (`DESIGN_BRIEF §13`). This doc does not restate them; it says how the words are
written.

**Platforms.** Each rule is stated once, for every platform. Where a platform's guidance differs, it is labelled
**Web**, **iOS**, **Android** or **Embedded (ESP-IDF, LVGL)**, in a bold lead or a table row. Embedded means a device
on ESP-IDF that draws with LVGL: a small fixed panel where every word competes for room, fonts compiled with only the
glyphs they were given, no screen reader, and words carried also by sound, haptics or speech where the product has
them. LVGL names are LVGL 9's, checked against its 9.6 headers.

**Stability.** Cite this doc as `UX_CONTENT §n`. Do not renumber; add new material under the next free number.

| § | Section | Look here for |
| --- | --- | --- |
| 1 | [Voice and tone](#1-voice-and-tone) | One voice, a tone set by the moment; you, not the user; the product's "we"; humour |
| 2 | [Clear and short](#2-clear-and-short) | The four tests, front-loading, cutting, plain words, the reason before the request, length and room |
| 3 | [Mechanics](#3-mechanics) | Case on each platform, punctuation, numbers and units, dates, abbreviations, symbols and glyphs |
| 4 | [Names and consistency](#4-names-and-consistency) | One name per thing, the word list, naming a feature or a setting, verbs for each input |
| 5 | [Patterns by element](#5-patterns-by-element) | Titles, buttons, links, fields, settings, confirmations, errors, empty states, success, progress, notifications, permissions, onboarding, tooltips |
| 6 | [Accessible content](#6-accessible-content) | The criteria that govern words, names a screen reader speaks, status messages, cognitive accessibility, inclusive language, translation |
| 7 | [Sources](#7-sources) | Apple; the other design systems; the standards; research; where the guides disagree and what this doc chooses; platform documentation |

---

## 1. Voice and tone

**A product has one voice and many tones: the voice is who is speaking, the tone is how they speak to someone in this
moment** — the same product is brisk on a routine save and plain and calm on a failed payment (§7.1, §7.2).

### 1.1 Voice

- **Write the voice down as three to five traits, each with what it means for the words and a pair of examples, one
  that sounds like the product and one that does not** — a trait with no example is a wish; the pair is what lets two
  writers sound alike.
- **The voice holds across every screen**; nothing in a corner of the product gets a different personality.
- **The product's voice is its design brief's** — this doc gives the method, never the traits.

### 1.2 Tone

**Set the tone from four things: why the text is there (to inform, to ask, to confirm), what the person is doing, how
they are likely to feel, and what is at stake.**

| The moment | The tone | What it does |
| --- | --- | --- |
| Something failed, or is blocked | Plain, calm, specific | Says what happened and the way out; no jokes, no exclamation, no apology for a routine fault |
| First use, or something unfamiliar | Patient, explanatory | One idea at a time, the reason before the request |
| A routine task, done often | Brief, efficient | The fewest words: "Saved" |
| A step that cannot be undone | Serious, transparent | The consequence in words, the safe way out as easy as the action |
| Something achieved | Warm, in proportion | Says what was done; a small celebration for a small win |

- **Match the tone to the stakes** — a light word on a heavy moment reads as indifference, a heavy word on a light one
  as alarm.
- **Humour only where nothing is at stake, and never in an error, a warning or anything sensitive** — it is subjective,
  wears thin on the tenth reading and rarely survives translation.

### 1.3 Who is speaking, and to whom

- **Speak to the person as "you"** — never "the user", "the player" or "the customer" in the interface.
- **Prefer no subject at all for a status**: "Couldn't load messages", "Changes saved". Status text that names no one
  is the shortest and blames no one.
- **"We" is the product, and only where the voice allows it and the product caused the problem**: "We couldn't reach
  the server". Never "we" for something the person did, and never "I" for the product.
- **"Your" only where ownership matters** — "Favourites", not "Your favourites"; "your account" when there are others.
- **"My" only in the person's own voice** — a consent they give ("I agree to the terms"), never as a label on their
  things ("My profile" makes the product speak for them); never mix "my" and "your" on one screen.

---

## 2. Clear and short

**Every string passes four tests, in this order, and is edited in four passes the same way: it has a purpose, it is as
short as it can be, it sounds like a person, and it means one thing** (§7.2, §7.4).

| Pass | The question | Typical edits |
| --- | --- | --- |
| Purpose | Does it help the person do what they came to do, right here? | Cut text that serves no decision; add the missing next step or reason |
| Short | Can any word go without losing meaning? | Drop filler ("just", "really", "please", "successfully"), redundancy, "you can" |
| Human | Would a person say it aloud to someone? | Replace system-speak ("An error occurred", "Operation completed") with what happened |
| One meaning | Could it be read two ways, or misread under stress? | Specific verbs, one term per thing, no double negatives |

### 2.1 Put the important words first

- **People scan; they read the first words of a line and decide whether to read on** — start a label, a title, a
  message and each list item with the words that carry its meaning (§7.4).
- **Lead with the reason, then the request, when the reason is what persuades**: "To hear when a backup finishes, turn
  on alerts", not "Turn on alerts to hear when a backup finishes".
- **One idea a sentence, one idea a screen** — the second idea is the second screen, the second sentence, or the help.

### 2.2 Cut

- **Remove every word that has no job** — adverbs and adjectives that add nothing ("quickly", "easily", "really"),
  pleasantries ("please" in an instruction), and anything said twice.
- **Keep a word that changes what the person expects** — "automatically" is information; "easily" is not.
- **Start an instruction with its verb**: "Enter your name", not "You can enter your name here".
- **Never trail off with an ellipsis**, except in the two places it means something (§3.2).

### 2.3 Plain words

- **Use the common word**: "use", not "utilise"; "buy", not "purchase"; "end", not "terminate"; "sign in", not
  "authenticate".
- **Say what the person sees and does, never how the system is built** — a feature is named for what it gives them
  (§4.2).
- **No idioms, metaphors or culture-bound references** — they confuse readers in a second language, people who read
  literally, and translators (§6.4).
- **Define a term the person must learn the first time it appears**, or replace it.
- **Active voice and the present tense by default**; the passive only where the actor is unknown or irrelevant
  ("Messages are deleted after 30 days").
- **State things positively** — "at least 8 characters", not "no fewer than 8"; never a double negative.

### 2.4 Length and room

**Short is a means, not the goal: the right length is the fewest words that answer the person's next question.** The
guides' numbers are heuristics that help an editor notice a long string, never limits a string is cut to fit (§7.4):

| Element | Heuristic |
| --- | --- |
| Button | 1–3 words, a verb first |
| Title | A few words; it names the screen or the task |
| Message or error body | 1–2 sentences |
| A sentence | Under about 20 words; past 25, split it |
| Notification title | Under about 50 characters |

- **Plan the space for the longest translation, not the English** — a short string can grow two to three times
  (§6.6).
- **A string that does not fit wraps, or the element is rethought; it is never cut to the box** — cut words are wrong
  words.
- **Embedded (ESP-IDF, LVGL): the room is a label's width in pixels, in a compiled font, on a panel that does not
  scroll the page.** Measure the longest string, and its longest translation, on the panel or in a simulator at the
  font's real size; a length the design brief sets per element is the limit there. A label set to
  `LV_LABEL_LONG_MODE_WRAP` grows in height, so the layout leaves it the lines; `LV_LABEL_LONG_MODE_DOTS` cuts, and is
  only for text the person supplied (a network name, a file name) whose whole text is reachable elsewhere;
  `LV_LABEL_LONG_MODE_SCROLL` and `_SCROLL_CIRCULAR` make the person chase words that move, and are never used for
  text that must be read. LVGL 8 and 9.0–9.1 spell the modes `LV_LABEL_LONG_WRAP` and `LV_LABEL_LONG_DOT` — the
  names LVGL's own 9.1 compatibility map (`lv_api_map_v9_1.h`) still points at the new ones.

---

## 3. Mechanics

### 3.1 Case

**Sentence case for everything a person reads in the interface — titles, labels, buttons, menus, messages: capitalise
the first word and proper nouns only.** It is the default of nearly every guide except Apple's, and it survives
translation. One convention per element, everywhere, decided in the design brief.

| Platform | The convention |
| --- | --- |
| Web | Sentence case (Microsoft, Material, GOV.UK, Polaris, Atlassian) |
| iOS | Apple's guidelines set title case for buttons, menu titles and items, and alert titles that are fragments; sentence case for sentences and alert titles that are sentences. A product native to Apple's platforms may follow them — its design brief says so, and the string check's title-case rule is then turned off |
| Android | Sentence case (Material 3) |
| Embedded (ESP-IDF, LVGL) | Sentence case — no platform convention to follow; the compiled font holds every letter the strings use, capitals and lowercase (§3.4) |

- **Never all capitals for words** — harder to read in a run and read as shouting. A style that sets capitals (CSS
  `text-transform`, Android's `textAllCaps`) still leaves the string in sentence case, so a screen reader and a
  translator get the words, not the look.
- **Refer to an on-screen element in the case it is shown in.**

### 3.2 Punctuation

- **No full stop on a label, a button, a title, a menu item or a one-line status**; a message of whole sentences ends
  each one with its stop.
- **No colon after a field label** — the layout already ties the label to its field.
- **An exclamation mark almost never** — never in an error, a warning or a status; at most once in a flow, for a real
  achievement.
- **The ellipsis means two things only**: a command that needs more input before it acts ("Rename…"), and work under
  way ("Saving…"). Use the single character "…", not three full stops.
- **No quotation marks around the name of a button you refer to** — write the name exactly as shown (Apple).
- **A question mark only on a real question** — a confirmation title that asks ("Delete 3 photos?") earns one.

### 3.3 Numbers, units, dates and times

- **Numerals for every quantity in an interface** — "3 photos", "1 minute left"; a UI is scanned, and digits are found
  faster than words.
- **A unit on every measured number, with a space**: "20 GB", "45 ms", "3.2 V"; no plural on a unit symbol. The percent
  and degree signs sit against the number in most interface style guides — "80%", "21°C" — and the brief
  settles it where the product writes otherwise.
- **Ranges with "to" where they are read aloud or may be** — "10 to 20 minutes"; an en dash only where space forces it
  (§6.2).
- **Dates and times in the person's locale, from a formatter**, never a hard-coded format; never an all-numeric date
  for a person to read (§6.6).
- **A relative time where it is what the person needs** — "2 minutes ago", "for 4 min" — and the absolute one where it
  matters for a record.
- **No false precision** — a percentage or a time remaining only when it is honest.
- **Web**: `Intl.DateTimeFormat`, `Intl.NumberFormat` and `Intl.RelativeTimeFormat`. **iOS**: `Date.FormatStyle`,
  `Measurement` and `Duration` formatting, or the `Formatter` classes. **Android**: `DateFormat` and
  `DateUtils.getRelativeTimeSpanString`, ICU's `MeasureFormat`.
- **Embedded (ESP-IDF, LVGL)**: firmware has no locale formatter of its own — dates and times come from the device's
  clock and time zone (`TZ`, `localtime_r`, `strftime`) in the one format the product's language setting chooses, with
  the month as a word where a date could be misread; units and their symbols are written by the product, so each
  symbol (°, µ) is a glyph the font must hold (§3.4).

### 3.4 Abbreviations, symbols and glyphs

- **Spell it out unless the abbreviation is the word people use** ("Wi-Fi", "USB", "PIN"); expand an unfamiliar one at
  its first use.
- **"For example", not "e.g."; "that is", not "i.e."; no "etc.", "and/or" or "via"** — they are read aloud oddly and
  translated badly.
- **Words, not symbols, in a sentence**: "and", not "&"; "about", not "~"; "plus", not "+".
- **An emoji or a glyph never carries meaning alone, and never stands in a sentence for a word** (§6.2).
- **Embedded (ESP-IDF, LVGL): every character a string uses is a glyph the compiled font holds** — the font holds only
  the ranges it was converted with, and a missing glyph draws as a box or nothing (`DESIGN_BRIEF §6`). The writing
  rules call for characters outside ASCII — "…" (U+2026), the apostrophe "’" (U+2019), the en dash "–" (U+2013),
  quotation marks “ ” (U+201C, U+201D), "°" (U+00B0) — so the brief's glyph ranges list them; dropping a rule because
  its character is missing from the font is the wrong fix. LVGL's built-in symbols (`LV_SYMBOL_…`) are icons, and carry
  a word beside them where they mean something (`ACCESSIBILITY §14`).

---

## 4. Names and consistency

### 4.1 One name for one thing

- **Each thing, action and setting has exactly one name, used on every screen, in the menu, in messages and in help**
  — "Search" here and "Find" there is two features to a reader; the floor is `ACCESSIBILITY §13` (WCAG 3.2.4).
- **Keep a word list**: the term, the words not to use for it, and what it means. Put the verbs on it too — the button
  that starts a flow, the one that moves it on, the one that ends it are the same words in every flow. The design brief
  holds the list, or names where it lives.
- **A flow's buttons are a set**: one word to begin, one to go on ("Next" or "Continue", never both), one to finish
  ("Done").
- **The same action keeps its verb in its button, its confirmation, its toast and its undo**: "Delete" → "Delete 3
  photos?" → "Delete" → "3 photos deleted" → "Undo".

### 4.2 Naming a feature or a setting

- **Name it for what the person gets, not for how it works** — "Clear speech", not "Vocal isolation".
- **Prefer the plain, expected word over a coined one**; a name a person must learn is a cost they pay on every screen.
- **A setting is named for what it turns on or does, and its description says what happens when it is on** — people
  infer the off state.
- **A toggle that can be ambiguous says the action**: "Show lyrics" and "Hide lyrics" as the label changes, or "Turn on
  night mode", never "Night mode on" where it could be read as a state or a command.
- **Test a name by saying it inside a sentence**: "Turn on ___", "___ is off".

### 4.3 Verbs for each input

**Use verbs that work for every input — "select", "choose", "enter", "turn on", "open" — in text that any input may
follow; use an input's own verb only where that is the only way in.**

| Platform | The input's own verbs |
| --- | --- |
| Web | "Select" for any input (Microsoft); "click" only where a pointer is the only way in |
| iOS | "Tap", "touch and hold", "swipe", "drag" (Apple Style Guide) |
| Android | "Tap", "touch & hold", "swipe", "drag" (Google's developer documentation style guide) |
| Embedded (ESP-IDF, LVGL) | "Press" for a physical button, "turn" for a knob or encoder, "tap" only where touch is the only input; a device with touch and an encoder says "select" |

- **Never "tap on" or "click on".**
- **"Turn on" and "turn off", not "enable", "disable" or "toggle"**, for anything a person switches — Apple's Style
  Guide's terms, adopted here for interface text (§7.5).
- **"Enter" information; "type" only for pressing keys** (Apple's Style Guide; adopted, §7.5).
- **Never only a direction, a colour or a shape as the way to find a control** — "the green button on the right"
  fails anyone who cannot see it; name the control (`ACCESSIBILITY §13`, WCAG 1.3.3).
- **The design brief names the verbs the product's own inputs take** — its buttons, knobs or gestures.

---

## 5. Patterns by element

**What each element says, and how: its job, its shape, and a before and after.** The rules every pattern follows are
§1–§4; what each needs for assistive technology is §6. Examples are illustrative, written for this doc — a product's
own strings follow its voice.

### 5.1 Titles

**A title tells the person where they are or what they are doing** — the screen's name, the task, or the question.

| Kind | Shape | Example |
| --- | --- | --- |
| Content | A noun for what is on the screen | "Saved routes", "Sound" |
| Category | A noun phrase that covers several tasks | "Account and sign-in" |
| Task | A verb phrase for the one job the screen does | "Add a network", "Choose a voice" |
| Question | The decision, asked | "Delete 3 photos?" |

- **Every screen has a title, and no two different screens share one** — the floor is `ACCESSIBILITY §4` (WCAG
  2.4.2).
- **Not the product's name on its own screens**, and never "Welcome" as a title that names nothing.
- **Embedded (ESP-IDF, LVGL)**: a panel with no room for a title bar still names each screen — a heading line, or the
  screen's one word at the top — so the person knows where a turn of the knob has taken them.

### 5.2 Buttons and actions

**A button says what happens when it is pressed: a verb, and its object where the screen has not already named it.**

- **A specific verb, never a generic one** — "Save", "Send", "Delete photo", "Scan again"; not "OK", "Yes", "Submit",
  "Go" or "Confirm" where the action has a name.
- **The object only when it is needed** — on a screen about one photo, "Delete"; in a list of actions, "Delete photo".
- **No articles, no end punctuation, in the product's case** (§3.1).
- **A pair is the action and the way out**: "Delete" and "Cancel". "Cancel" always means back out with nothing changed;
  "Stop" means end now and keep what was done.
- **A button that will take a while says so as it works** — "Save" becomes "Saving…" and keeps its width
  (`FEEDBACK §5`).
- **"OK" only where the message is purely information and the button only dismisses it**; "Done" where the person
  finishes something.
- **Which control an action takes is the design brief's** (`DESIGN_BRIEF §13`); the words on it are this section's.

| Before | After | Why |
| --- | --- | --- |
| OK / Cancel on "Discard changes?" | Discard / Keep editing | Both buttons name their result |
| Submit | Send message | The verb is the outcome |
| Yes / No | Delete file / Keep file | Read without the question |

### 5.3 Links

- **The link's words say where it goes or what it does, read alone** — "Read the privacy policy", never "Click here",
  "Learn more" or "Read more" on their own; the floor is `ACCESSIBILITY §13` (WCAG 2.4.4).
- **Two links to the same place have the same words; two to different places, different words.**

### 5.4 Form fields

| Part | Job | Pattern |
| --- | --- | --- |
| Label | Names what goes in | A short noun, always visible, above or beside the field: "Email address" |
| Hint | What makes the entry right, before it is typed | One short phrase: "At least 8 characters" |
| Placeholder | An example of the format, never the label or the hint | "name@example.com" — optional, and only beside a visible label |
| Error | What is wrong and how to fix it, beside the field | §5.7 |

- **The floors — a visible label, an error tied to its field, when typed text is checked — are
  `ACCESSIBILITY §9`'s.** This section says what the label, the hint and the error say.
- **Say what is required, and ask only for what the task needs; never ask twice for what the person already gave.**
- **Mark the exception, not the rule** — if most fields are required, mark the optional ones.
- **Embedded (ESP-IDF, LVGL)**: an `lv_textarea`'s placeholder text (`lv_textarea_set_placeholder_text`) is an
  example, never the label; the label is a visible line beside the field. On an on-screen keyboard, the hint says the
  rule before the first key ("4 to 8 digits"), since checking late costs many presses.

### 5.5 Settings and toggles

- **The name is what it turns on, in a few words; the description, if any, says what happens when it is on** — "Raise
  to wake" / "Turns the screen on when you lift the device."
- **The state is the control's own** — the switch shows on or off; the label does not repeat it.
- **A setting that cannot be changed now says why, in words, on the screen** — never a dimmed control alone.
- **The control a setting takes** — a switch, a field, a picker — is the design brief's (`DESIGN_BRIEF §13`).

### 5.6 Confirmations

**Ask only before something that cannot be undone, or that the person may not expect; offer undo instead where you
can.** A confirmation asked too often is answered without reading.

- **The title is the specific action, asked**: "Delete 3 photos?", not "Are you sure?" and not "Confirm".
- **The body says what will happen and whether it can be undone, only if the title has not said it**: "They'll be
  removed from all your devices."
- **The buttons repeat the verb and offer the safe way out**: "Delete" and "Cancel"; never "Yes" and "No".
- **The confirmation's look and where its focus opens — on the safe choice — are `DESIGN_BRIEF §13`'s**; the words are
  this section's.
- **For a rare action that destroys a great deal, ask the person to type or hold something** — a word, a press held —
  so a reflex cannot do it.

| Before | After |
| --- | --- |
| Confirm cancellation — Cancel / Confirm | Cancel subscription? You'll have access until 21 June. — Cancel subscription / Keep subscription (Apple, WWDC22) |
| Are you sure you want to delete? — Yes / No | Delete this song? — Delete / Cancel |

### 5.7 Errors

**An error says what happened, why if it is known and useful, and what to do now — beside the problem, without blame,
and with the fix one action away.** Prevent it first; an error many people hit is a design to change, not a message to
write.

| Kind | When | Shape | Example |
| --- | --- | --- | --- |
| Inline | A field's entry is wrong | What the field needs, in the field's own words | "Enter a date in the future" |
| Recoverable | An action failed and can be retried or worked round | What failed. The cause, if known. What to do. One button to do it | "Couldn't send. You're offline." — Try again |
| Blocking | The product cannot go on until something changes | What is unavailable. Why. When it will be back, or what fixes it. Reassurance about data | "Update required. This version no longer connects." — Update |
| Permission | Something is off that the feature needs | The benefit, then the thing to turn on | "To show nearby stops, turn on Location." — Open Settings |

- **Name the thing and the action in the title, never "Error", an error code alone, or "Something went wrong" when the
  cause is known.**
- **Say what the person can do** — the next step as an instruction with its verb first, and a button that does it.
- **No blame and no alarm** — not "invalid", "illegal", "wrong", "failed to"; not "Oops", "Uh-oh", or a joke. Describe
  what is needed: "Use only letters and numbers", not "Bad characters in name".
- **"Sorry" only when the product failed the person in a way that costs them** — lost work, a missed payment; never for
  a routine fault.
- **When the cause is unknown, do not invent one** — say what failed and the general way out: "Couldn't load. Try again
  in a minute."
- **Keep what the person typed** — an error never clears the field.
- **Several errors on one form are listed as the actions that fix them**, each linked to its field.
- **A code, if support needs it, after the words**, never instead of them.
- **When the check runs and where the message sits are `ACCESSIBILITY §9`'s; whether an error is a dialog or sits in
  place follows from whether it blocks** — a critical failure never lives only in a toast that disappears (`FOCUS §9`).
- **Embedded (ESP-IDF, LVGL)**: on a small panel the error is a short title and one line, with the fix as the panel's
  one button; the failure is also felt or heard where the product has a sound or a haptic (`FEEDBACK §5`), and a code
  support needs follows the words, since on a device with no network it is often all support sees.

| Before | After |
| --- | --- |
| The operation could not be completed (code 12). | Couldn't download the update. The device is out of storage — remove a recording and try again. |
| Invalid email | Enter an email address like name@example.com |
| Error 503 | Service unavailable. Try again in a few minutes. |
| Oops! Something went wrong :( | Couldn't load your playlist. — Try again |

### 5.8 Empty states

**An empty screen says what will be here and the one thing to do next.**

| Kind | Shape | Example |
| --- | --- | --- |
| First use | What will be here, the benefit, one action | "No recordings. Record a voice memo to keep it here." — Record |
| Cleared | The work is done; when more will come | "Nothing waiting. Requests show up here as they come in." |
| No results | What was not found; how to widen it | "No matches for 'jazz'. Try a shorter search." |
| No access | What is unavailable, why, and how to get it | "Turn on Bluetooth to see nearby devices." |

- **One action, not a menu of them**, and its words match the title's.
- **Neutral or encouraging, never negative** — "No messages yet", not "You have no messages"; no exclamation.
- **Never put something essential only in an empty state** — it disappears the moment the screen fills.

### 5.9 Success and status

- **Say what was done, past tense, no "successfully", no exclamation**: "Changes saved", "3 photos deleted".
- **Say it only once it happened** — a success shown before the answer cannot be taken back (`FEEDBACK §3`,
  `FEEDBACK §5`).
- **Confirm only what the person cannot see or needs to know** — people expect success and need to hear about failure;
  a visible result is its own confirmation.
- **Offer undo or a way to the result where it helps**: "Photo deleted" — Undo.
- **A toast is one line and is never the only place an important outcome is told** — it disappears, and may be missed
  or not announced (§6.3; `FOCUS §9`).

### 5.10 Progress and waiting

- **A wait long enough to notice says what is happening, with a present participle and an ellipsis**: "Connecting…",
  "Saving 3 photos…". When a wait is long enough to show a mark at all is `FEEDBACK §5`'s.
- **Say how long only when it is honest** — "About 2 minutes left"; no countdown that jumps, no percentage it cannot
  keep.
- **A long wait says what the person can do meanwhile, and whether leaving cancels it.**
- **The end of the wait says how it ended** — done, failed, or stopped (§5.7, §5.9).

### 5.11 Notifications

- **The most important thing first; the title is the news, the body the detail or the action** — "Your order shipped" /
  "It arrives Thursday."
- **Not the app's name or icon where the system already shows them.**
- **Specific and worth the interruption** — a notification that only says "Open the app" is not one; something
  important enough to require action is a dialog, not a notification.
- **Nothing private in what a locked screen shows**; a hidden preview says the kind of thing, not its content: "New
  message".
- **Honest urgency** — the higher levels only when it is.
- **An action button says its result in a word or two, and never just opens the app.**
- **iOS**: interruption levels — passive, active, time-sensitive, critical — chosen by the stakes. **Android**: a
  notification channel per kind, named in words the person will recognise in Settings, with its importance set by the
  stakes. **Web**: the Notifications API — a title and a body, under the browser's permission (§5.12).
- **Embedded (ESP-IDF, LVGL)**: no notification centre — the news is a banner on screen, a sound or a light
  (`FEEDBACK §6`), and anything the person must act on waits on the screen until they do.

### 5.12 Permission requests

- **Ask when the feature is first used, not at launch, and say what the person gets**: "To tag photos with where they
  were taken, allow location."
- **Where the platform shows its own prompt, the product supplies only the reason string** — written as the benefit, in
  the product's voice; the system's buttons are not the product's to change.
- **A declined permission is respected and recoverable** — the feature says what it needs and links to the setting.
- **iOS**: the reason is the purpose string in `Info.plist` (`NSCameraUsageDescription`, `NSLocationWhenInUseUsageDescription`),
  shown in the system's prompt. **Android**: the system's dialog has no text of the product's; the product explains
  first, on its own screen, when `shouldShowRequestPermissionRationale` says to. **Web**: the browser's prompt carries
  no reason — the product says why on its own screen before calling the API that asks.

### 5.13 Onboarding

- **Fast, useful, optional** — teach by letting the person do the thing, one idea a step, every optional step
  skippable, progress shown ("2 of 4").
- **Ask for nothing the first session does not need**; defaults over questions.
- **Prefer a tip in place, when the feature is met, to a tour before anything is used.**
- **A skipped tutorial is never forced back**, and stays easy to find.

### 5.14 Help, hints and tooltips

- **A tooltip adds; it never carries what the person needs to finish** — a requirement belongs on the screen. How a
  tooltip opens, stays and closes is `ACCESSIBILITY §7`'s.
- **A tooltip does not repeat the control's label**; if there is nothing to add, there is no tooltip.
- **Help is in place, at the point of need, and says one thing.**
- **Touch and embedded have no hover** — on a phone or a device panel, help is a word on the screen or a screen behind
  a press, never a tooltip a person must find.

---

## 6. Accessible content

**The words an interface needs so that everyone can use it.** The floors are the `accessibility` skill's, and each row
below names the one it meets; this section says what the writer does about each. Contrast, type size, target size and
focus are not words, and live there too.

### 6.1 The success criteria that govern words

**WCAG 2.2's criteria that a writer meets or breaks** — the level, what each asks of the words, and the floor that
owns it (§7.3):

| SC | Level | What the words do | Floor |
| --- | --- | --- | --- |
| 1.1.1 Non-text Content | A | An icon-only control is named for its purpose ("Share"), not its picture ("arrow box"); decoration has none | `ACCESSIBILITY §4` |
| 1.3.1 Info and Relationships | A | A meaning shown by layout or a mark is also in words — "Required fields are marked *" | `ACCESSIBILITY §4` |
| 1.3.3 Sensory Characteristics | A | Instructions never rely only on shape, colour, size, position or sound — name the control | `ACCESSIBILITY §13` |
| 1.4.1 Use of Color | A | A state that colour shows is also said: an error in red also says what is wrong | `ACCESSIBILITY §2` |
| 2.2.1 Timing Adjustable | A | A time limit warns in words and offers a plain way to extend | `ACCESSIBILITY §8` |
| 2.4.2 Page Titled | A | Every screen has a title that says what it is | `ACCESSIBILITY §4` |
| 2.4.4 Link Purpose (In Context) | A | A link's words, with what precedes them, say where it goes | `ACCESSIBILITY §13` |
| 2.4.6 Headings and Labels | AA | Headings and labels describe their topic or purpose | `ACCESSIBILITY §4` |
| 2.5.3 Label in Name | A | The name assistive technology uses contains the visible words — at its start | `ACCESSIBILITY §4` |
| 3.1.3 Unusual Words | AAA | Jargon and idioms are defined, or not used | This doc, §2.3 |
| 3.1.4 Abbreviations | AAA | An abbreviation is expanded where it is first used | This doc, §3.4 |
| 3.1.5 Reading Level | AAA | Text beyond lower-secondary reading has a simpler version or support — simplify first | This doc, §6.4 |
| 3.2.4 Consistent Identification | AA | One function, one name, everywhere | `ACCESSIBILITY §13` |
| 3.3.1 Error Identification | A | An error is identified and described in text | `ACCESSIBILITY §9` |
| 3.3.2 Labels or Instructions | A | Input has a label, and instructions where a format is unusual — not so many they hide the field | `ACCESSIBILITY §9` |
| 3.3.3 Error Suggestion | AA | A known fix is suggested, unless that would weaken security | `ACCESSIBILITY §9` |
| 3.3.4 Error Prevention | AA | Money, commitments and deleting data are reversible, checked, or confirmed | `ACCESSIBILITY §9` |
| 3.3.7 Redundant Entry | A | What the person already entered in a process is not asked again | `ACCESSIBILITY §9` |
| 3.3.8 Accessible Authentication | AA | No sign-in step depends on remembering or transcribing — let them paste | `ACCESSIBILITY §9` |
| 4.1.2 Name, Role, Value | A | Every control has a name software can read, even one with no visible text | `ACCESSIBILITY §4` |
| 4.1.3 Status Messages | AA | A status — a result, a wait, an error count — is written to be understood on its own | `ACCESSIBILITY §10` |

- **The A and AA criteria are the floor; the AAA criteria on words are this doc's target** — plain words, defined
  terms and expanded abbreviations cost a writer little and help many.
- **Embedded (ESP-IDF, LVGL)**: a device with no screen reader is closed functionality, and the criteria that need one
  give way to what `ACCESSIBILITY §14` sets — the visible words carry the name and the state, so every word on the
  panel is the only name the control has.

### 6.2 Names a screen reader speaks

**That every control has a name, and that it contains the visible words, are `ACCESSIBILITY §4`'s floors; how the
name is worded is this section's.**

- **An icon-only control's name is the action** — "Search", "Close", "Add to cart"; never the file name of its image,
  which some screen readers read when nothing else is given.
- **The visible words start the name** — a voice-control user says what they see; "Send" shown, "Send message" named,
  never "Submit form" named under "Send".
- **No control type in the name** — "Play", not "Play button"; the screen reader adds the role.
- **Names in a list are distinct** — three "Edit" buttons need "Edit address", "Edit card", "Edit name".
- **A name changes when the control's action changes** — "Play" to "Pause".
- **A hint is extra, only where the name does not make the result clear**: what happens, in the third person, ending
  with a full stop — "Plays the track." It never names the gesture ("Tap to play") or repeats the name.
- **Describe a meaningful image by what it means in this place; hide a decorative one.** A chart gets a one-line
  summary of what it shows.
- **Write for the ear** — "1 to 10", not "1–10"; "and", not "&"; "for example", not "e.g."; a unit's name where the
  symbol would be read oddly ("90 degrees"); an emoji only at the end of a sentence, never as a word or a label.
- **A name is localised with the rest of the interface.**

| Platform | Where the name and the hint are written |
| --- | --- |
| Web | The visible text, or `aria-label` on an icon-only control; `alt` on an image; a hint in visible text tied with `aria-describedby` |
| iOS | `accessibilityLabel` and `accessibilityHint` (Apple: a label is a word or short phrase with no full stop, a hint a sentence that ends with one) |
| Android | The visible text, or `contentDescription` on an icon-only control; Compose `semantics { contentDescription = … }` |
| Embedded (ESP-IDF, LVGL) | No screen reader and no name to set (`ACCESSIBILITY §14`): the visible word beside an icon is the name; where the product speaks, each spoken string follows this section |

### 6.3 Status and error messages

**How a status reaches a screen reader, or the person on a device without one, is `ACCESSIBILITY §10`'s; where focus
sits when a message appears is `FOCUS §9`'s. This section says how the message reads.**

- **A status message is written to be understood without the screen around it** — "3 results", "Saved", "Couldn't
  send: you're offline" make sense heard alone; "Done!" after a list of six actions does not.
- **An error names its field when it is announced**: the field's label and the error are read together, so the error
  reads well after the label — "Email address. Enter an address like name@example.com."
- **Urgent announcements are rare** — only a failure the person must act on interrupts; a routine result waits its
  turn.
- **A message that disappears is never the only place something important is said** — a toast may be missed, and some
  people cannot read it in the time it shows.
- **Embedded (ESP-IDF, LVGL)**: a message is read at a glance and may be caught only by its sound or haptic, so its
  first words say the outcome ("Saved", "Not saved") and the detail follows.

### 6.4 Cognitive accessibility

**Clear words help everyone and are essential for people with cognitive and learning disabilities** — the W3C's
patterns for usable content (§7.3):

- **Common words** — start with labels, navigation, instructions and errors; check a word against the most common
  words of the language; do not invent words.
- **Present tense, active voice, addressed to the person.**
- **Literal language** — no metaphors, similes or idioms, unless explained.
- **No double negatives and no nested clauses** — "Write clearly", not "Do not write unclearly".
- **One point a sentence, one topic a paragraph, the aim first.**
- **Each instruction a step of its own**, numbered, including the obvious ones.
- **Instructions before the field, not only in the error after it**, with an example.
- **Feedback for every action** — that it worked, or what failed.
- **Before a choice, its consequences** — what each option does and what it costs.
- **Easy recovery** — a review before a commitment, and errors fixed without losing work.

### 6.5 Inclusive language

- **Gender-neutral by default** — "they" for a person of unknown gender; roles, not gendered nouns; never "he/she".
- **People first, as the community prefers** — person-first ("a person who is blind") or identity-first ("a blind
  person") as the community asks; mention a disability only when it matters.
- **No pity, no "normal"** — not "suffers from", "wheelchair-bound", "special needs", and not "normal" or "healthy"
  for people without a disability (Microsoft, Google, Apple).
- **No violent, ableist or loaded terms where a plain one exists** — "stop responding", not "hang"; "final check", not
  "sanity check"; "primary" and "subordinate", not "master" and "slave" (Microsoft); "block list" and "allow list", not
  black and white (Apple).
- **Avoid a sense verb where it is the only cue** — Apple's style prefers "A message appears" to "You'll see a
  message"; the other guides do not call "see" exclusionary, and the fault is an instruction that only sight can
  follow. "Select", not "click", where any input may follow (§4.3).
- **Questions do not assume** — a family, a gender, a country, a car; ask only what the task needs, with a way to
  decline.

### 6.6 Ready for translation

**Leave room, keep every sentence whole, and let the platform handle plurals, dates and numbers.** The shorter the
English, the more it grows — plan for the W3C guide's figures, gathered from IBM's; a heuristic, as the growth depends
on the language and the words:

| English length | Plan for a translation of |
| --- | --- |
| Up to 10 characters | 200–300 % |
| 11–20 | 180–200 % |
| 21–30 | 160–180 % |
| 31–50 | 140–160 % |
| 51–70 | 151–170 % (as the guide prints it) |
| Over 70 | About 130 % |

- **A layout wraps or scrolls a string; it never fixes a label's width to the English** — a translated button or title
  that cannot fit is cut, and cut words are wrong words (§2.4).
- **Never build a sentence from fragments** — "You have " + n + " new " + "messages" cannot be translated; word order,
  gender and plurals differ. One whole string, with placeholders the translator can move, and a note saying what each
  holds.
- **Plurals through the platform's plural rules, or worded to avoid them** — "Messages: 3"; languages have up to six
  plural forms.
- **Dates, times, numbers and currency from the locale's formatter**, never assembled by hand (§3.3).
- **No idioms, puns or culture-bound references; consistent terms** — a translator given one word per concept gives
  one back.
- **No text baked into images**, and none on a launch screen that cannot be localised.

| Platform | Strings, plurals and notes for translators |
| --- | --- |
| Web | A message catalogue per language with ICU MessageFormat for plurals and placeholders, or `Intl.PluralRules`; a description beside each message |
| iOS | String Catalogs (`.xcstrings`) with plural variations; `Text("…")` and `String(localized:)` take a comment for the translator |
| Android | `res/values/strings.xml` per locale, `<plurals>` read with `pluralStringResource` or `getQuantityString`; `<xliff:g>` marks what not to translate |
| Embedded (ESP-IDF, LVGL) | A table of strings per language, kept apart from the code — LVGL's translation module (`LV_USE_TRANSLATION`, `lv_tr`) where it is turned on; each shipped language's glyphs compiled into the fonts, at a flash cost the brief records (§3.4); right-to-left text only with `LV_USE_BIDI` |

---

## 7. Sources

**Where this doc's rules come from, what each source gave it, and how it settles the places they disagree.** Every
rule is this doc's own wording, and its examples are written for it — except those marked with their source (Apple's,
chiefly), quoted because they are the clearest; the sources are named so a reader can go to the original. Read
2026-11-15; the LVGL names checked against LVGL 9.6's headers.

### 7.1 Apple

**Apple's guidance is a first source for the rules on words**: the Human Interface Guidelines' Writing page and the
component pages that carry rules for words, the Apple Style Guide, Apple's accessibility label and hint rules, and four
WWDC sessions on writing.

| Source | What it gave this doc |
| --- | --- |
| [HIG — Writing](https://developer.apple.com/design/human-interface-guidelines/writing) | Voice and tone; a word list; the important thing first; consistent flow buttons; errors that say how to fix; empty states with a next step; settings described by what they do on; avoid "we" in status text |
| [HIG — Alerts](https://developer.apple.com/design/human-interface-guidelines/alerts) | Alerts sparingly; the title says what happened; specific button verbs, not OK, Yes or No; Cancel always backs out; warn only before unexpected, irreversible loss |
| [HIG — Buttons](https://developer.apple.com/design/human-interface-guidelines/buttons), [Menus](https://developer.apple.com/design/human-interface-guidelines/menus) | A verb that names the result; a label that says the toggle's action ("Show map" / "Hide map"); the ellipsis for a command that needs more input or work under way |
| [HIG — Feedback](https://developer.apple.com/design/human-interface-guidelines/feedback) | Confirm success only for important actions; explain why a command can't run |
| [HIG — Notifications](https://developer.apple.com/design/human-interface-guidelines/notifications), [Managing notifications](https://developer.apple.com/design/human-interface-guidelines/managing-notifications) | Short and specific; no app name; hidden-preview text; honest interruption levels |
| [HIG — Onboarding](https://developer.apple.com/design/human-interface-guidelines/onboarding) | Fast, useful and optional; teach by doing; tips in place; permissions at first use with their benefit |
| [HIG — Inclusion](https://developer.apple.com/design/human-interface-guidelines/inclusion), [VoiceOver](https://developer.apple.com/design/human-interface-guidelines/voiceover) | "You", not "the user"; humour with care; describing images by meaning; a unique title per screen |
| [Apple Style Guide](https://support.apple.com/guide/applestyleguide/welcome/web) | Sentence and title style; terms for each input (tap, click, press; choose and select; turn on); numbers and units; no "please" in instructions; no "e.g."; inclusive and disability language |
| [Accessibility Programming Guide for iOS (archived)](https://developer.apple.com/library/archive/documentation/UserExperience/Conceptual/iPhoneAccessibility/Making_Application_Accessible/Making_Application_Accessible.html) | A label names the element in a word or short phrase, no control type, no full stop; a hint says the result in the third person, ending in a full stop, never the gesture |
| [WWDC19 — Writing great accessibility labels](https://developer.apple.com/videos/play/wwdc2019/254/) | Always set a label; context for similar buttons; update the label as the element changes |
| [WWDC22 — Writing for interfaces](https://developer.apple.com/videos/play/wwdc2022/10037/) | Text as a conversation; the next question answered; the subscription-cancel rewrite; no "Oops" |
| [WWDC25 — Make a big impact with small writing changes](https://developer.apple.com/videos/play/wwdc2025/404/) | Cut what adds nothing, keep what changes expectations; lead with the reason; the word-list columns |
| [WWDC26 — Craft clear names for features and labels](https://developer.apple.com/videos/play/wwdc2026/290/) | Name a feature for what it gives; the plain word; say the name inside a sentence |

- **Apple-specific, labelled iOS, not general rules**: title case for buttons, menus and fragment alert titles (§3.1);
  the macOS ellipsis on a button that opens a window; "settings" against "preferences" by OS version; the caution
  symbol; purpose strings in the system's permission prompt (§5.12); notification interruption levels (§5.11). A
  product native to Apple's platforms follows them.
- **Apple's Style Guide is written for documentation**; its terms ("turn on" rather than "enable", "enter" rather than
  "type", no "please", no "e.g.") are adopted here for interface text by choice, not because Apple states them for the
  interface (§7.5).

### 7.2 The other design systems

| Source | What it gave this doc |
| --- | --- |
| [Microsoft Writing Style Guide — top 10 tips](https://learn.microsoft.com/en-us/style-guide/top-10-tips-style-voice), [capitalization](https://learn.microsoft.com/en-us/style-guide/capitalization), [describing interactions](https://learn.microsoft.com/en-us/style-guide/procedures-instructions/describing-interactions-with-ui), [bias-free communication](https://learn.microsoft.com/en-us/style-guide/bias-free-communication) | Front-load, fewer words, verb-first instructions, cut "you can"; sentence case; input-neutral verbs; bias-free terms |
| [Windows apps — writing style](https://learn.microsoft.com/en-us/windows/apps/design/style/writing-style); the legacy Windows 7 UX guide, still published, on [errors](https://learn.microsoft.com/en-us/windows/win32/uxguide/mess-error), [confirmations](https://learn.microsoft.com/en-us/windows/win32/uxguide/mess-confirm), [notifications](https://learn.microsoft.com/en-us/windows/win32/uxguide/mess-notif), [progress](https://learn.microsoft.com/en-us/windows/win32/uxguide/progress-bars) | Problem, cause, solution; "anyway" on a risky confirmation; notification length; "Cancel" leaves nothing, "Stop" keeps what was done; progress text |
| [Material — communication codelab](https://codelabs.developers.google.com/codelabs/material-communication-guidance), [Android for Cars — writing](https://developer.android.com/design/ui/cars/guides/foundations/writing-guidelines) | Errors with a solution; one term per concept; glanceable limits for a car screen — a message under about 120 characters, buttons of three words or fewer. Material 3's own pages render only in a browser and were read from search extracts |
| [Shopify Polaris — content](https://github.com/Shopify/polaris-react-archive/tree/main/polaris.shopify.com/content), [shopify.dev content](https://shopify.dev/docs/apps/design/content) | Lean writing; verb-plus-noun buttons; errors near the problem, listed as fixes; action-led empty states; "your", not "my" |
| [Atlassian — content](https://atlassian.design/foundations/content/voice-tone), [error](https://atlassian.design/foundations/content/designing-messages/error-messages), [empty state](https://atlassian.design/foundations/content/designing-messages/empty-state), [success](https://atlassian.design/foundations/content/designing-messages/success-messages) | Message shape — a short title, one or two sentences, one action; no "successfully"; "please" can make a step sound optional |
| [GOV.UK — writing for user interfaces](https://www.gov.uk/service-manual/design/writing-for-user-interfaces), [error message](https://design-system.service.gov.uk/components/error-message/), [button](https://design-system.service.gov.uk/components/button/), [text input](https://design-system.service.gov.uk/components/text-input/), [clear language](https://guidance.publishing.service.gov.uk/writing-to-gov-uk-standards/writing-guidelines/clear-language/) | Errors in the field's own words; never clear a field; labels always visible, no placeholder as a label, no colon; no "please" or "valid/invalid"; ranges with "to" |
| [Mailchimp content style guide](https://styleguide.mailchimp.com/voice-and-tone/) | Voice against tone; when in doubt, no joke; no exclamation in failure |

- **What they share — the consensus this doc rests on**: people scan, so the key words come first; fewer words; plain
  words; sentence case; "you", active voice, verb-first instructions; a specific verb on a button; errors that say what
  happened and what to do, without blame; errors prevented first and shown at the problem; one word per concept; a
  steady voice and a tone that follows the moment; verbs that suit any input; inclusive language.

### 7.3 Accessibility standards

| Source | What it gave this doc |
| --- | --- |
| [WCAG 2.2 — Understanding](https://www.w3.org/WAI/WCAG22/Understanding/) | The criteria in §6.1, each from its Understanding page |
| [W3C — Making content usable for people with cognitive and learning disabilities](https://www.w3.org/TR/coga-usable/) | §6.4's patterns: clear words, simple tense, literal language, separate instructions, feedback, consequences before a choice |
| [Digital.gov plain language guide](https://digital.gov/guides/plain-language), where plainlanguage.gov now leads; ISO 24495-1:2023 | Active voice, present tense, short sentences, positive phrasing; relevant, findable, understandable, usable |
| [CDC Clear Communication Index](https://www.cdc.gov/ccindex/index.html) | A scored index for clear public messages: active voice, common words, chunks and headings, the action stated |
| [MDN — ARIA live regions](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Guides/Live_regions), [aria-label](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Reference/Attributes/aria-label); [Android — accessibility](https://developer.android.com/guide/topics/ui/accessibility/apps) | Status read on its own, urgent ones rare; no role in the name; unique names in a list |
| [W3C Internationalization — text size](https://www.w3.org/International/articles/article-text-size), [composite messages](https://www.w3.org/International/articles/composite-messages/), [date formats](https://www.w3.org/International/questions/qa-date-format) | §6.6's expansion table; no concatenation; locale dates |
| [Microsoft — global English](https://learn.microsoft.com/en-us/style-guide/global-communications/writing-tips), [writing for all abilities](https://learn.microsoft.com/en-us/style-guide/accessibility/writing-all-abilities); [Google — inclusive documentation](https://developers.google.com/style/inclusive-documentation) | Translation-ready wording; symbols read aloud; person-first and identity-first; ableist terms and their replacements |

### 7.4 Books and research

| Source | What it gave this doc |
| --- | --- |
| [Nielsen Norman Group — how users read on the web](https://www.nngroup.com/articles/how-users-read-on-the-web/), [F-shaped reading](https://www.nngroup.com/articles/f-shaped-pattern-reading-web-content/) | People scan (79 % scanned, 16 % read word by word); concise and scannable text measured as more usable; front-loading |
| [Nielsen Norman Group — error messages](https://www.nngroup.com/articles/error-message-guidelines/), [confirmation dialogs](https://www.nngroup.com/articles/confirmation-dialog/), [placeholders](https://www.nngroup.com/articles/form-design-placeholders/), [tooltips](https://www.nngroup.com/articles/tooltip-guidelines/), [OK and Cancel](https://www.nngroup.com/articles/ok-cancel-or-cancel-ok/) | Error, confirmation, placeholder and tooltip patterns; outcome labels instead of Yes and No |
| [GOV.UK — sentence length](https://insidegovuk.blog.gov.uk/2014/08/04/sentence-length-why-25-words-is-our-limit/) | Comprehension falls as sentences lengthen — above 90 % at 14 words, under 10 % at 43, from research on print |
| Torrey Podmajersky, *Strategic Writing for UX* (O'Reilly, 2019) — not re-read for this doc | The four standards — purposeful, concise, conversational, clear — that §2's four tests adapt |
| [content-designer/ux-writing-skill](https://github.com/content-designer/ux-writing-skill) (MIT) | An agent skill built on those four standards; the kinds of error and empty state, title kinds, a voice chart and a scored before-and-after method. Its ideas are reworded here, not its text or examples |
| [UXmatters — readability formulas](https://www.uxmatters.com/mt/archives/2019/07/readability-formulas-7-reasons-to-avoid-them-and-what-to-do-instead.php); [a study of formulas on short online text](https://pmc.ncbi.nlm.nih.gov/articles/PMC12919665) | Why a grade-level score is not a test of interface text |

- **Heuristics, not limits** — the sentence-length and comprehension figures come from research on print and the web,
  not on interface strings; this doc uses them to flag a long string, never to cut one to a number (§2.4). A
  readability formula is not used on interface text: fragments and labels break it, one full stop moves the score,
  and it cannot tell "waive" from "wave". Test words with the people who will read them.

### 7.5 Where the guides disagree, and what this doc chooses

| Question | The guides | This doc |
| --- | --- | --- |
| Title case or sentence case | Apple: title case for buttons, menus, fragment titles; nearly everyone else: sentence case | Sentence case; a product native to a platform follows that platform's convention, decided in its design brief (§3.1) |
| "We" | Apple: avoid it in status text; Microsoft and Atlassian: "We couldn't…" so the person is not blamed; Polaris: only when the product caused it | No subject for a status; "we" only where the voice allows and the product caused the failure; never "I" |
| "Please" | Microsoft: only for inconvenience or the product's fault; GOV.UK and Atlassian: avoid — it makes a step sound optional | Not in instructions; at most where the product asks a favour it caused |
| "Sorry" | Most: only for serious problems; Atlassian: avoid | Only when the product failed the person at a cost to them |
| Exclamation marks | Rare (Apple, Polaris, Atlassian); never in errors (Mailchimp, Microsoft) | Never in an error, warning or status; at most once in a flow |
| "Invalid", "incorrect" | The legacy Windows guide: "incorrect" for "invalid"; Nielsen Norman: "incorrect" blames too | Neither; say what is needed |
| Contractions | Encouraged by most; GOV.UK: avoid negative ones | Use common ones; write "cannot" where the negative must not be missed |
| Full stops | None on labels and buttons; sentences get them; Polaris: only for questions or two sentences | None on labels, buttons, titles and one-line status; whole sentences get them |
| Button length | 1–2 words (Atlassian), 1–3 (Material), up to 3 (Android for Cars) | 1–3 words, the verb first; more only where the object is needed |
| Yes and No | The legacy Windows guide allowed them where the question is clear; Nielsen Norman and Apple: outcome labels | Outcome labels, always |
| "Turn on" or "enable"; "enter" or "type" | Apple's Style Guide (for documentation): "turn on", "enter"; Microsoft: "select" and "enter"; many products say "enable" | "Turn on", "enter" — adopted for interface text |
| Numbers | Apple's Style Guide spells out one to nine in running text | Numerals for every quantity in the interface, which is scanned, not read |
| Ranges | Apple: an en dash ("2013–2019"); GOV.UK and Microsoft: "to", as a dash may be skipped when read aloud | "to" where it may be read aloud; a dash only where space forces it |
| "Click", "tap", "select" | Apple: by device; Microsoft: "select" everywhere; Google's developer style: "click" | Input-neutral where any input may follow; the device's own verb where only it applies, named in the design brief (§4.3) |

### 7.6 Platform documentation

| Source | What it gave this doc |
| --- | --- |
| MDN — `Intl` (`DateTimeFormat`, `NumberFormat`, `RelativeTimeFormat`, `PluralRules`), Notifications API | §3.3's formatters on the web; §5.11; §6.6's plurals |
| Apple Developer — String Catalogs, `Date.FormatStyle`, `UNNotificationInterruptionLevel`, `Info.plist` usage descriptions | §3.3, §5.11, §5.12 and §6.6 on iOS |
| Android Developers — string resources and quantity strings, notification channels, requesting runtime permissions, `contentDescription` | §5.11, §5.12, §6.2 and §6.6 on Android |
| Google developer documentation style guide — word list | "Touch & hold" and the other input verbs on Android (§4.3) |
| LVGL 9 documentation and headers (`lv_label.h`, `lv_textarea.h`, `lv_msgbox.h`, `lv_translation.h`, `lv_conf_template.h`) | §2.4's label long modes; §3.4's missing glyphs (`LV_USE_FONT_PLACEHOLDER`); §5.4's placeholder; §6.6's translation module and `LV_USE_BIDI` |
