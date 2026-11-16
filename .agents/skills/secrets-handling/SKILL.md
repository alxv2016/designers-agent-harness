---
name: secrets-handling
description: How a product handles the secrets it holds for its users — API keys, account, session and refresh tokens, pairing keys, TLS private keys, signing keys — carried in the skill (references/secrets.md), with the principles for every platform and guidance labelled for the web, iOS, Android and embedded ESP-IDF firmware — every secret from the person at run time and none in the source, a build option, a header, a fixture or the shipped app (a bundle's public variables such as VITE_ and NEXT_PUBLIC_ are public); storage treated as readable unless the platform encrypts it (HttpOnly, Secure, SameSite cookies and never localStorage; the Keychain and its kSecAttrAccessible classes, never UserDefaults; the Android Keystore now that Jetpack Security's security-crypto is deprecated; NVS encryption by the HMAC or flash-encryption scheme, flash encryption in release mode, secure boot); at most a short prefix shown, and only where the person must tell two apart, otherwise length or state; a saved secret's field opening empty with its preview as placeholder; shape-checking a pasted token; wiping working copies; a flash write from a task with an internal-RAM stack; a console that accepts secrets kept out of shipped builds; logs, crash reports and screenshots; bench and CI credentials in ignored files, the home folder or the environment; a vendor's sample signing key never used; what to do after a leak (stop and tell, rotate first, re-enter, then clean up); plus secret_scan.py, which counts key-shaped strings in a change without printing them. Portable — the folder works in any repo. Use when touching how a token or key is entered, stored, shown, logged or sent; a settings field, a pairing or sign-in flow, a bench script or a console that takes a secret; .gitignore or .env files; before committing anything near credentials; or after a secret appears where it should not.
metadata:
  scope: portable
---

# Secrets handling

How a product's secrets enter, live in and leave it, and what never happens to them. The principles and their reasons
are kept in this skill at [references/secrets.md](references/secrets.md) (cited `SECRETS §n`); this page indexes them
in one-line rules and holds the steps: the review of a change near a secret, the scan, and the procedure after a leak.
**The project's inventory** — which secrets it holds, where each is stored, how much of each may be shown, which files
hold the bench's copies, which service issues each and how to rotate it — lives in the project's own docs; that wins
over the reference, and the reference over this page.

**Platforms.** The rules below hold on every platform. The reference labels how each is built — **Web**, **iOS**,
**Android**, **Embedded (ESP-IDF)**.

**Portable.** This folder is self-contained and links to nothing outside itself (it names the rest of a kit in
backticks): the reference and the scan ([scripts/secret_scan.py](scripts/secret_scan.py)). Copy it into any repo's
`.agents/skills/` (or `.claude/skills/`) and it works there: the scan reads `SECRET_PATTERNS` from
`.agents/project.py` when the repo has one, and uses only its common patterns when it does not. It needs git and
Python 3.9+.

**Builds on.** The agent's own safety — never reading a credential file or a `.env`, never committing a key-shaped
string or a secret file — is the agent-harness kit's guard and pre-commit hook; this skill does not restate them. It
covers what the product does with its users' secrets and what an agent writes into the product. In the kit,
`verify.py run` runs the scan.

## When to use

- Changing how a token or key is entered, stored, shown, logged or sent — a settings field, a sign-in or pairing flow,
  a provisioning step, a development console.
- Writing a bench script, a test or a log that runs against a real account.
- Editing `.gitignore`, a `.env.example`, a build configuration or a CI secret.
- Choosing where a server, an app or a firmware image keeps a secret.
- Before committing anything that ran against a real account.
- After a secret appears where it should not — a commit, a log, a screenshot, a prompt, a bug report.

## Rules

### Do

1. **Take every secret from the person at run time** — typed, paired, signed in, or read from the environment by a
   server or a bench tool (SECRETS §1).
2. **Keep a secret that belongs to the product on a server the product runs**; restrict any key that must ship in a
   client at the service, and treat it as public (SECRETS §1).
3. **Treat every store as readable unless the platform encrypts it, and say which in the project's docs** — an
   `HttpOnly`, `Secure`, `SameSite` cookie; the Keychain; a Keystore key; NVS encryption (SECRETS §2).
4. **Show at most a short prefix — 8 to 12 characters and `…` — and only where the person must tell two apart;
   otherwise length or state** (SECRETS §3).
5. **Open a saved secret's field empty, its preview as the placeholder** (SECRETS §4).
6. **Shape-check a pasted token on entry where its format is documented, and refuse a bad one at the field**
   (SECRETS §4).
7. **Wipe a working copy as soon as its use ends** — `mbedtls_platform_zeroize()` in C; the narrowest scope where a
   string cannot be wiped (SECRETS §5).
8. **Write a secret to storage from a context the store allows** — on ESP-IDF, a flash write from a task with an
   internal-RAM stack (SECRETS §6).
9. **Keep a console that accepts or reveals secrets off in source and in every shipped build, turned on by a build
   flag** (SECRETS §7).
10. **Keep bench credentials in files ignored by exact name, the home folder or the environment, and CI credentials in
    the CI's secret store; commit the `.env.example` beside them** (SECRETS §9).
11. **Generate the product's own release signing key and keep it outside the repo** (SECRETS §10).
12. **Scan a change for key-shaped strings with a tool that prints counts, never the match** (SECRETS §11).

### Never

- **Put a secret in a log, a screenshot, a crash report or a bug report** (SECRETS §8) — a prompt and a commit are
  the agent-harness kit's guard's and pre-commit hook's to refuse.
- **Log a secret whole, or past its prefix** (SECRETS §8).
- **Add a build option, a header constant, a public build variable or a test fixture holding a real secret**
  (SECRETS §1).
- **Store a secret in `localStorage`, `UserDefaults`, plain `SharedPreferences` or unencrypted NVS** (SECRETS §2).
- **Put a saved secret's value back into a widget** (SECRETS §4).
- **Sign anything shipped with a vendor's sample or development key** (SECRETS §10).
- **Rename an ignored bench file** — only the exact names are ignored (SECRETS §9).
- **Search for a leaked key with a command that prints the matching line** — `grep -n` and `git grep` show the key;
  use `grep -l`, `grep -c` or the scan (SECRETS §11).
- **Rewrite git history for the person** — it is theirs to decide, and it does not un-leak a pushed secret
  (SECRETS §12); burning a chip's eFuses is theirs too (SECRETS §2).

## Procedure

### Reviewing a change near a secret

1. **Read the project's inventory first** — the secret's display, its store, its rotation — and follow it; a secret
   the inventory does not list is added to it in the same change.
2. **Trace the secret from entry to store to use** against SECRETS §1–§8: where it comes from, where it lives, what
   shows it, what logs it, how long each copy lives.
3. **Run the scan** (Checks) and read each hit by file and pattern — never by printing the line.

### After a leak

The steps are a recommendation; the person confirms each account step with the service that issued the secret
(SECRETS §12).

1. **Stop and tell the person** which secret, where it appeared (a commit, a log, a screenshot, a prompt) and when.
2. **Rotate first** — revoke the secret with the service that issued it and make a new one; the project's docs say
   where for each of its secrets.
3. **Re-enter the new value** where the product takes it; for a leaked device token, unpair and pair again.
4. **Then clean up** — remove the secret from the file, log or screenshot. Rewriting git history is the person's call
   and does not un-leak a pushed secret.

## Checks

```sh
python3 .agents/skills/secrets-handling/scripts/secret_scan.py            # the change: git diff HEAD and new untracked files
python3 .agents/skills/secrets-handling/scripts/secret_scan.py <file> …   # whole files
python3 .agents/skills/secrets-handling/scripts/secret_scan.py --test     # the self-test
```

- [ ] (script) No key-shaped string in the change — 0 hits; it prints the file, the pattern and the line numbers,
  never the text
- [ ] Every new log line near a secret prints a prefix, a length or a state — never the value (Do 4)
- [ ] A new secret field opens empty with the preview as its placeholder (Do 5)
- [ ] Each secret's store is one the platform encrypts, or the project's docs say it is readable (Do 3)
- [ ] A console or debug route that takes secrets is off in the shipped build's configuration (Do 9)
- [ ] The project's inventory lists every secret the change touches

The scan reads the lines a change adds — `git diff HEAD` with `--text --no-textconv`, and every untracked file git does
not ignore — or the whole of each file named. Its patterns: a private key header; GitHub, AWS access key, Google API,
Slack, `sk-`, Stripe live, Hugging Face and npm tokens; a JSON Web Token; a URL carrying a password; and a name ending
in a credential word (`DB_PASSWORD`, `OPENAI_API_KEY`, `JWT_SECRET`, `apiKey`) assigned a value, quoted in code, JSON or
YAML or unquoted in `.env` style; plus the project's own from `SECRET_PATTERNS` in `.agents/project.py`, a list of
`(regex, what)` pairs. It does not count placeholders (`changeme`, `example`, `<…>`, `${…}`, a letters-only word under
16 characters such as a translated label) or a key ending in `EXAMPLE`; it skips a line carrying `secret-exception`
with its reason, and the files that hold patterns on purpose — itself and `SECRET_PATTERN_HOMES` or `PATTERN_HOMES` in
`.agents/project.py`. It prints only paths, pattern ids, counts and line numbers, never a file's text. It does not see
a secret with no fixed shape, one split across lines or encoded, a letters-only password under 16 characters, binary
files, or files over 5 MB (named as not read). Any hit exits 1; a file named that cannot be read, a
`.agents/project.py` that fails to load, or a project pattern that does not compile exits 2.

## Traps

- **A request fails later with no clear error** → a mistyped or truncated token was saved → shape-check on entry and
  trim whitespace (Do 6).
- **A shipped build still accepts secrets on its console** → the bench option stayed in an existing `sdkconfig`, which
  the defaults files do not override → build the release from a clean configuration and check which build the device
  runs (Do 9).
- **A key appears in the browser's network tab or the bundle** → it was read through a public build variable
  (`VITE_`, `NEXT_PUBLIC_`) → move it to the server (Do 2).
- **A token restored on a new phone cannot be decrypted** → its Keystore key stayed on the old device → exclude the
  encrypted secret from backup, or ask for it again (Do 3).
- **The device crashes when saving a token** → the write ran on a task whose stack is in PSRAM → write from a task with
  an internal-RAM stack (Do 8).
- **A search for a leaked key prints the key** → `grep -n` shows the matching line → `grep -l`, `grep -c` or the scan
  (Do 12).
- **A bench file is committed** → it was renamed, and only its exact name is ignored → keep the name, or move it to the
  home folder (Do 10).

## Sources

| Topic | Where |
| --- | --- |
| The principles, their reasons and the platform guidance | [references/secrets.md](references/secrets.md) |
| Cookies, local storage | MDN, `Set-Cookie`; OWASP, HTML5 Security Cheat Sheet |
| Public build variables, local env files | Vite, "Env Variables and Modes"; Next.js, "Environment Variables" |
| The Keychain, `UserDefaults` | Apple Developer, "Restricting keychain item accessibility", `UserDefaults` |
| The Keystore, API keys, logging, Jetpack Security | Android Developers, "Android Keystore system", "Security tips", Jetpack Security release notes |
| NVS, NVS encryption, flash encryption, secure boot, external RAM stacks, `sdkconfig` defaults | ESP-IDF Programming Guide |
| Removing a pushed secret | GitHub Docs, "Removing sensitive data from a repository" |
