# Secrets

How a product handles the secrets it holds for its users — API keys, account and session tokens, refresh tokens,
pairing keys, TLS private keys, signing keys: where each comes from, where it lives, how much of it a screen, a field
or a log may show, how long a working copy lives, how a development console and bench credentials stay out of what
ships, how a repo is searched for one, and what to do after a leak. People read it to decide how a feature treats a
secret; coding agents read it, through the `secrets-handling` skill, before they touch one.

**Where it lives.** In the `secrets-handling` skill, beside the steps and the check that apply it —
[its SKILL.md](../SKILL.md). The skill folder is self-contained: copy it into any repo's `.agents/skills/` and this
reference and the scan come with it. **The project's inventory** — which secrets it holds, where each is stored, how
much of each may be shown, which files hold the bench's copies, which service issues each and how to rotate it — lives
in the project's own docs, never here.

**What it does not cover.** The agent's own safety — never reading a credential file or a `.env`, never committing a
key-shaped string — belongs to the agent-harness kit's guard and pre-commit hook. This doc covers what the product
does with its users' secrets; where it names the agent, it is only for what an agent writes into the product.

**Platforms.** Each principle is stated once, for every platform. How a platform builds it is labelled **Web**,
**iOS**, **Android** or **Embedded (ESP-IDF)**, in a bold lead or a table column. Embedded means firmware built with
ESP-IDF.

**Stability.** Cite this doc as `SECRETS §n`. Do not renumber; add new material under the next free number.

| § | Section | Look here for |
| --- | --- | --- |
| 1 | [Where a secret comes from](#1-where-a-secret-comes-from) | From the person at run time; never in the source, the build or the shipped app; public build-time variables |
| 2 | [Where a secret lives](#2-where-a-secret-lives) | Storage treated as readable; cookies, the Keychain, the Android Keystore, NVS encryption, flash encryption |
| 3 | [Showing a secret](#3-showing-a-secret) | A short prefix only to tell two apart, otherwise length or state; what shows nothing |
| 4 | [Entering a secret](#4-entering-a-secret) | The field opens empty with the preview as placeholder; shape-checking a pasted token; the password field |
| 5 | [Working copies](#5-working-copies) | Wiping a buffer, the narrowest scope, core dumps and crash reports |
| 6 | [Writing a secret to storage](#6-writing-a-secret-to-storage) | A context the store allows; flash writes and stacks in external RAM |
| 7 | [Development consoles and debug builds](#7-development-consoles-and-debug-builds) | A console that accepts secrets, off in source and in shipped builds; the build that runs on the target |
| 8 | [Logs, crash reports and support data](#8-logs-crash-reports-and-support-data) | Never past the prefix; who reads a log; screenshots and bug reports |
| 9 | [Bench and CI credentials](#9-bench-and-ci-credentials) | Ignored files by exact name, the home folder, the environment, a CI secret store; `.env.example` |
| 10 | [Signing keys](#10-signing-keys) | A vendor's sample key is public; where a release key lives |
| 11 | [Finding a secret in the repo](#11-finding-a-secret-in-the-repo) | Key-shaped strings, counting without printing, what a scan cannot see |
| 12 | [After a leak](#12-after-a-leak) | Stop and tell, rotate first, re-enter, then clean up; what rewriting history does not undo |

---

## 1. Where a secret comes from

**Every secret comes from the person at run time** — typed on the device or in the app, handed over by pairing or a
sign-in flow, or read from the environment by a server or a bench tool. None is in the source, a build option, a
header, a fixture or the shipped app.

- **A secret built into what ships is public** — everyone who has the bundle, the app or the firmware image has the
  secret, and it cannot be rotated without a new release.
- **A secret that belongs to the product, not the person** — a service key the app calls with — stays on a server the
  product runs; the app gets a short-lived token from that server, or calls through it.
- **A key that has to ship in a client** (a maps or analytics key meant to be public) is restricted at the service — to
  the app's signature, bundle ID or web origin — and treated as public.

| Platform | Where a secret comes from | What ships to everyone |
| --- | --- | --- |
| **Web** | The server's environment variables or a secret manager, read by server code only | Every file sent to the browser. A build tool's public variables are inlined into the bundle at build time: Vite's `VITE_` prefix, Next.js's `NEXT_PUBLIC_` |
| **iOS** | Sign-in, pairing or the person's entry, at run time | The app binary and its resources, `Info.plist` included |
| **Android** | Sign-in, pairing or the person's entry, at run time | The APK or bundle — resources, `BuildConfig` fields and native libraries included |
| **Embedded (ESP-IDF)** | Typed on the device, provisioning or pairing, at run time | The firmware image: string constants, `sdkconfig` values and any NVS partition image flashed with it |

Sources: Vite, "Env Variables and Modes"; Next.js, "Environment Variables"; Android Developers, "Security tips"
(API keys).

---

## 2. Where a secret lives

**Treat every place a secret is stored as readable, unless the platform itself encrypts it, and say in the project's
docs which it is.** Encrypt only with the platform's own encryption; a scheme the product invents holds its key next to
the data.

- **Why:** a settings file, unencrypted flash or a browser's storage can be read by anyone who holds the device, a
  backup of it, or a script running in the page.

| Platform | Store a secret in | Never in | What to know |
| --- | --- | --- | --- |
| **Web** | A session token in a cookie set by the server with `HttpOnly`, `Secure` and `SameSite`, under a `__Host-` name where the app allows; a server's secrets in its environment or a secret manager | `localStorage`, `sessionStorage`, IndexedDB or a cookie readable by script | One cross-site scripting flaw reads everything a script can reach. `HttpOnly` keeps a cookie from `document.cookie`; `Secure` sends it only over HTTPS; `SameSite` decides whether it goes with cross-site requests; `__Host-` requires `Secure`, `Path=/` and no `Domain` |
| **iOS** | The Keychain, with the most restrictive `kSecAttrAccessible` class the feature allows | `UserDefaults`, a plist or a file in the app's container | `UserDefaults` is stored on disk unencrypted. `kSecAttrAccessibleWhenUnlocked` is the default; `kSecAttrAccessibleAfterFirstUnlock` is for access in the background; `kSecAttrAccessibleWhenPasscodeSetThisDeviceOnly` for the most sensitive items. A class ending `ThisDeviceOnly` is not migrated to another device from a backup |
| **Android** | A key in the Android Keystore (StrongBox where the device has it and the threat model calls for it), and the secret encrypted with it — through the platform's `Cipher` or Tink — in the app's private storage | Plain `SharedPreferences`, a file, or external storage | Jetpack Security's `security-crypto` (`EncryptedSharedPreferences`, `EncryptedFile`, `MasterKey`) is deprecated in favour of the platform APIs and direct use of the Keystore. Keystore key material never enters the app's process. A Keystore key stays on its device, so a secret restored from a backup to another device cannot be decrypted: exclude it from backup, or ask for it again when decryption fails |
| **Embedded (ESP-IDF)** | NVS with NVS encryption on | NVS without encryption, a plain partition, or a file system on flash | Without NVS encryption, anyone with the flash chip can read, change, erase or add entries. NVS encryption has two schemes: the HMAC scheme (`CONFIG_NVS_SEC_KEY_PROTECT_USING_HMAC`) derives its keys from an eFuse key and needs no flash encryption, on chips with the HMAC peripheral; the flash-encryption scheme (`CONFIG_NVS_SEC_KEY_PROTECT_USING_FLASH_ENC`) keeps its keys in an `nvs_keys` partition that flash encryption protects. Flash encryption in development mode still lets new plaintext firmware be flashed, which can read the data back; a shipped device uses release mode, with secure boot so only signed firmware runs |

- **Encryption at rest does not stop erasure** — ESP-IDF's NVS encryption, for one, has no tamper resistance against
  erase; a product that must notice a wiped secret checks for it.
- **Burning eFuses is irreversible** — enabling flash encryption, secure boot or the HMAC key is a step the person
  takes, on a plan from the platform's docs, never an agent.

Sources: MDN, `Set-Cookie`; OWASP, HTML5 Security Cheat Sheet (local storage); Apple, `UserDefaults` and "Restricting
keychain item accessibility"; Android Developers, "Android Keystore system", "Security tips" and the Jetpack Security
release notes; ESP-IDF Programming Guide, "Non-Volatile Storage Library" (Security, Tampering, and Robustness), "NVS
Encryption", "Flash Encryption", "Secure Boot v2".

---

## 3. Showing a secret

**Show at most a short prefix — 8 to 12 characters, then `…` — and only where the person must recognise which secret
is saved; show any other secret by its length or its state only ("saved", "none").**

- **Why:** a prefix lets the person tell two keys apart; more of it narrows a guess, and every character shown lands in
  every screenshot and shared log.
- **A refresh token, a session token, a pairing key, a password and a private key show nothing of themselves** —
  nobody tells two of them apart by sight.
- **A prefix that a service fixes for every key tells nothing apart** — count only the characters after it toward
  what is useful, and stay within the 12.
- **The project's docs name each secret's display** — prefix length, length only, or state only — and every screen and
  log follows that one entry.

---

## 4. Entering a secret

**A saved secret's field opens empty, with the saved secret's preview (§3) as its placeholder; the saved value is
never put back into a widget.** Leaving it empty keeps the saved secret; typing replaces it.

- **Why:** a field filled with the value puts it in the view tree, the accessibility tree, screenshots and the
  clipboard's reach.
- **Shape-check a pasted token on entry where its format is documented** — length, character set, the service's fixed
  prefix — and refuse a bad one at the field with a clear message, so a mistyped token fails there, not later with no
  clear error.
- **Trim surrounding whitespace before the check** — a paste often carries a newline.
- **Use the platform's password field type for a secret** — `type="password"` on the web, secure text entry on iOS, a
  password input type on Android — with a control to reveal it while typing.
- **Embedded (ESP-IDF):** a secret typed on a device's screen is masked after each character; one handed over by
  pairing or provisioning travels over the encrypted channel that protocol defines.

---

## 5. Working copies

**Wipe a working copy as soon as its use ends** — a buffer a secret was copied into for one request is cleared after
it, and no copy lives longer than its use.

- **Why:** memory is read back by a crash dump, a core dump, a debugger or the next use of a reused buffer.
- **Embedded (ESP-IDF):** clear with `mbedtls_platform_zeroize()` (mbedTLS, bundled with ESP-IDF); a plain `memset`
  before `free` can be removed by the compiler. A core dump, when enabled, saves task stacks and registers to flash or
  the serial port — a secret on a stack goes with it.
- **Web, iOS, Android:** a string cannot be wiped in JavaScript, Swift or Kotlin. Keep the secret in the narrowest
  scope, hold it in a byte array (`Uint8Array`, `Data`, `ByteArray`) that can be filled with zeros where the API
  allows, and drop every reference after use.
- **Keep secrets out of crash and analytics payloads** — a crash reporter that captures memory, breadcrumbs or request
  bodies captures the secret with them (§8).

---

## 6. Writing a secret to storage

**Write a secret to storage from a context the store allows; on a platform where that is restricted, route the write
there.**

- **Embedded (ESP-IDF):** a flash write — NVS included — disables the cache, and external RAM is unreachable while it
  is off. A task whose stack is in external RAM (PSRAM) must not write to flash: write from a task with an internal-RAM
  stack, or route flash operations through the `espressif/esp_flash_dispatcher` component. Task stacks are in internal
  RAM by default; this applies once a project places stacks in PSRAM (`xTaskCreateWithCaps()` with
  `MALLOC_CAP_SPIRAM`, a static stack in PSRAM, or `CONFIG_FREERTOS_PLACE_TASK_STACKS_IN_EXT_RAM`).
- **Android:** Keystore operations can take time; run them off the main thread.
- **Web, iOS:** no restriction of this kind.

Sources: ESP-IDF Programming Guide, "Support for External RAM" (task stack placement); Android Developers, "Android
Keystore system".

---

## 7. Development consoles and debug builds

**A console, menu or endpoint that accepts or reveals secrets is off in source and in every shipped build; a build
flag turns it on for the bench, never an edit to the switch.**

- **Why:** a shipped image that takes a secret over its serial line or a debug endpoint hands it to anyone with a
  cable or a network path.
- **Embedded (ESP-IDF):** a Kconfig option with `default n`, turned on only in a bench defaults file layered in with
  `SDKCONFIG_DEFAULTS="sdkconfig.defaults;sdkconfig.bench"`. The defaults files apply only when `sdkconfig` is created
  or for an option it does not yet hold, so a project's existing `sdkconfig` keeps the bench value until it is
  regenerated — build a release from a clean configuration and check which build the device runs.
- **Web:** no debug route or verbose error page in the production build; a feature flag that exposes one is off in
  production configuration.
- **iOS, Android:** a debug menu is compiled only into debug builds (`#if DEBUG`, a debug build type or source set), not
  hidden behind a gesture in the release build.

---

## 8. Logs, crash reports and support data

**Never log a secret whole or past its prefix (§3); log its length or state instead.**

- **Why:** a log is shared, copied into bug reports and kept far longer than the secret's use.
- **Android:** the system log is a shared resource readable by any app with `READ_LOGS`; keep secrets and personal data
  out of it, and limit logging in release builds.
- **Embedded (ESP-IDF):** the serial log goes to whoever holds the cable and to every monitor capture.
- **Web:** server request logs, proxy logs and error trackers record headers and bodies — redact `Authorization`,
  cookies and secret fields before they are written.
- **A screenshot, a screen recording, a bug report and a support bundle follow the same rule** — a screen that shows a
  secret shows only what §3 allows.

Sources: Android Developers, "Security tips" (logging).

---

## 9. Bench and CI credentials

**A bench or test credential lives in a file the repo ignores by its exact name, in the person's home folder outside
the tree, or in an environment variable; a CI credential lives in the CI's secret store.** A bench tool takes it by a
flag or the environment and echoes none of it.

- **Why:** a file inside the tree is one `git add` from a commit.
- **Ignore by exact name and commit the template beside it** — `.env` ignored, `.env.example` committed with
  placeholder values, so a new clone knows which variables to set.
- **Never rename an ignored file** — only the names `.gitignore` lists are ignored; a renamed copy is committed with
  the next `git add`.
- **Web:** Vite's `.env.*.local` files are meant for local secrets; keep `*.local` in `.gitignore`.
- **Use test accounts with the least access the bench needs**, so a leaked bench credential reaches little.

Sources: Vite, "Env Variables and Modes"; Next.js, "Environment Variables".

---

## 10. Signing keys

**Never sign anything shipped with a vendor's sample or development key** — it is public and shared by everyone who
has the vendor's SDK.

- **Generate a release key for the product, keep it outside the repo** — in a hardware token, the platform's managed
  signing, or a secret store — and back it up where the person can recover it; a lost signing key can stop updates.
- **Embedded (ESP-IDF):** a secure boot signing key for production is generated with OpenSSL or another standard tool
  (ESP-IDF's `idf.py secure-generate-signing-key` takes its randomness from the host OS), and its path in `sdkconfig`
  points outside the tree or to an ignored file.
- **iOS, Android:** the release signing identity or upload key stays in the platform's signing service or the person's
  keychain, never in the repo.

Sources: ESP-IDF Programming Guide, "Secure Boot v2" (generating the signing key).

---

## 11. Finding a secret in the repo

**Search a change for key-shaped strings with a tool that prints counts and places, never the matching text.**

- **Why:** a search that prints the line puts the secret in the terminal, the agent's context and every log of the
  session — the leak repeats.
- **`grep -n` and `git grep` print the matching line**; `grep -l` and `grep -c` print only names and counts.
- **Nothing a file contains reaches the scan's output** — only paths, pattern ids, counts and line numbers; the place
  is opened in an editor.
- **A key-shaped pattern finds keys with a known shape** — a private key header, a cloud provider's or a service's
  token by its fixed prefix, a JSON Web Token, a URL carrying a password, and a name ending in a credential word
  (`DB_PASSWORD`, `OPENAI_API_KEY`, `JWT_SECRET`) assigned a value.
- **What a pattern scan does not see** — a secret with no fixed shape, a value split across lines or encoded, a
  letters-only password short enough to pass for a word, a binary file, and a file too large to read; a pass is a
  floor, never a review.
- **Placeholders are not secrets** — `changeme`, `example`, `<…>`, `${…}`, a translated label such as `"Passwort"`, and
  a vendor's documented example key ending in `EXAMPLE` are not counted, so a hit stays worth reading.
- **A sanctioned hit carries `secret-exception` on its line with the reason** — a vendor's published test value, say;
  the files that hold the scan's patterns on purpose are skipped whole.
- **Every project adds the shapes of its own secrets** — a service's token prefix and length — beside the common ones.

Steps: the `secrets-handling` skill's Checks ([its SKILL.md](../SKILL.md)).

---

## 12. After a leak

**Stop and tell the person, rotate the secret first, re-enter the new one, then clean up.** A secret that reached a
commit, a log, a screenshot, a prompt or a bug report is compromised from that moment.

| Step | What | Why |
| --- | --- | --- |
| 1. Stop and tell | Which secret, where it appeared, and when | The person owns the account and decides what follows |
| 2. Rotate first | Revoke the secret with the service that issued it and make a new one | Once revoked, the leaked copy opens nothing, wherever it is |
| 3. Re-enter | Put the new value where the product takes it; for a leaked device token, unpair and pair again | Whether the service revokes the old token on re-pairing is the service's to say |
| 4. Clean up | Remove the secret from the file, log or screenshot | Cleaning without rotating leaves the leaked copy valid |

- **Rewriting git history is the person's decision and does not un-leak a pushed secret** — clones and forks keep it,
  cached views and pull requests can still reach the commits, and anyone with an old clone can push it back; rewriting
  also changes every later commit's hash and drops signatures.
- **The steps are a recommendation; the person confirms each account step** with the service that issued the secret.

Sources: GitHub Docs, "Removing sensitive data from a repository".
