#!/usr/bin/env python3
"""The playwright skill's check: patterns in Playwright test files that make a test flaky, slow, blind or pinned to
the markup, from references/playwright.md (cited `PLAYWRIGHT §n`). It finds what a line of a test shows; a run of the
tests, its traces and the person's review find the rest.

    python3 .agents/skills/playwright/scripts/e2e_check.py            # every Playwright file, against the baseline
    python3 .agents/skills/playwright/scripts/e2e_check.py FILE …     # some files, no baseline
    python3 .agents/skills/playwright/scripts/e2e_check.py --test     # the self-test

Which files: every tracked `.ts`, `.tsx`, `.js`, `.mjs` or `.cjs` file that imports `@playwright/test`, and every
`playwright.config.*`, outside vendored, generated and agent-kit folders. A line that carries `e2e-exception` is
skipped — write the reason beside it. Comment lines are skipped.

  PW1  a fixed wait — `waitForTimeout(…)`; wait for what the person would see instead             PLAYWRIGHT §4
  PW2  a CSS or XPath selector — `.locator('…')` with a string, `page.$(…)`, `page.$$(…)`              PLAYWRIGHT §3
  PW3  a manual assertion — `expect(await x.isVisible())` and the like, which neither waits nor retries  PLAYWRIGHT §4
  PW4  a web-first assertion with no `await` — `expect(locator).toBeVisible()` left floating             PLAYWRIGHT §4
  PW5  a focused test left in — `test.only`, `test.describe.only`                                      PLAYWRIGHT §10
  PW6  traces always on — `trace: 'on'` in the config; `'on-first-retry'` instead                      PLAYWRIGHT §9
  PW7  a visit to a site the project does not control — `page.goto('https://…')` off localhost         PLAYWRIGHT §6
  PW8  an action forced past its checks — `force: true`, which hides an element covered or disabled     PLAYWRIGHT §4

What it cannot see: whether a test checks what the person observes, whether tests share state, whether a third
party's request is stubbed, whether each page meets the accessibility floors, whether a test name says the task. Its
limits: PW2 flags every string selector, a `[data-testid]` one too — `getByTestId` reads the same; PW4 reads the
matcher after `expect(…)` and knows the web-first matchers by name; PW7 passes a relative path and the loopback
hosts. A pass is a floor, never a review.

Prints one line per hit — `file:line: PW<n> what — fix` — then a count and how many files it read. A whole-tree run
over BASELINE exits 1; a run on named files exits 1 on any hit. Python 3.9+, standard library only.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip()
            or ".")

# Hits sanctioned today, each with its reason. A new hit on a line you touched is yours to fix.
BASELINE = 0
EXT = {".ts", ".tsx", ".js", ".mjs", ".cjs"}
SKIP_DIRS = ("node_modules/", "vendor/", "third_party/", "build/", "dist/", "out/", "coverage/", ".cache/", ".venv/",
             "playwright-report/", "test-results/", "blob-report/", ".agents/", ".claude/", ".codex/", ".github/")
CONFIG = re.compile(r"(?:^|/)playwright\.config\.[cm]?[jt]s$")

WEB_FIRST = {"toBeAttached", "toBeChecked", "toBeDisabled", "toBeEditable", "toBeEmpty", "toBeEnabled", "toBeFocused",
             "toBeHidden", "toBeInViewport", "toBeVisible", "toContainText", "toHaveAccessibleDescription",
             "toHaveAccessibleErrorMessage", "toHaveAccessibleName", "toHaveAttribute", "toHaveClass", "toHaveCount",
             "toHaveCSS", "toHaveId", "toHaveJSProperty", "toHaveRole", "toHaveScreenshot", "toHaveText", "toHaveTitle",
             "toHaveURL", "toHaveValue", "toHaveValues", "toMatchAriaSnapshot", "toPass"}

PW1 = re.compile(r"\bwaitForTimeout\s*\(")
PW2 = re.compile(r"\.locator\s*\(\s*['\"`]|\bpage\.\$\$?\s*\(")
PW3 = re.compile(r"\bexpect\s*\(\s*await\b[^;\n]*?\.(?:isVisible|isHidden|isEnabled|isDisabled|isChecked|isEditable"
                 r"|textContent|innerText|innerHTML|inputValue|getAttribute|count)\s*\(")
EXPECT = re.compile(r"(?<![\w.])expect(?:\.soft)?\s*\(")
PW5 = re.compile(r"\b(?:test|it|describe)(?:\.describe)?\.only\s*\(")
PW6 = re.compile(r"\btrace\s*:\s*['\"]on['\"]")
PW7 = re.compile(r"\.goto\s*\(\s*['\"`]https?://(?!(?:localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\])(?:[:/'\"`]|$))")
PW8 = re.compile(r"\bforce\s*:\s*true\b")


def line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def blank_comments(text: str) -> str:
    """Comment lines replaced by blanks of the same length, so positions and line numbers hold."""
    out = []
    for line in text.split("\n"):
        s = line.lstrip()
        out.append(" " * len(line) if s.startswith(("//", "/*", "*")) else line)
    return "\n".join(out)


def unawaited(text: str):
    """Positions of a web-first assertion with no `await` (or `return`) before it on its statement."""
    for m in EXPECT.finditer(text):
        before = text[text.rfind("\n", 0, m.start()) + 1:m.start()]
        if re.search(r"\b(?:await|return)\s*$", before) or re.search(r"\b(?:await|return)\s*\($", before):
            continue
        depth, i = 0, m.end() - 1
        while i < len(text):
            if text[i] == "(":
                depth += 1
            elif text[i] == ")":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        matcher = re.match(r"\s*(?:\.not)?\s*\.(\w+)\s*\(", text[i + 1:])
        if matcher and matcher.group(1) in WEB_FIRST:
            yield m.start(), matcher.group(1)


def scan(name: str, text: str) -> list[tuple[int, str]]:
    """Every hit in one file's text: (line, message)."""
    code = blank_comments(text)
    found: list[tuple[int, str]] = []
    for m in PW1.finditer(code):
        found.append((m.start(), "PW1 a fixed wait — wait for what the person would see: a web-first assertion"))
    for m in PW2.finditer(code):
        found.append((m.start(), "PW2 a CSS or XPath selector — getByRole with its name, getByLabel or getByText"))
    for m in PW3.finditer(code):
        found.append((m.start(), "PW3 a manual assertion that does not wait — `await expect(locator).toBeVisible()` "
                                 "and the other web-first matchers"))
    for pos, matcher in unawaited(code):
        found.append((pos, f"PW4 `{matcher}` with no await — the assertion floats and never fails the test; "
                           "await it"))
    for m in PW5.finditer(code):
        found.append((m.start(), "PW5 a focused test left in — remove `.only`"))
    if CONFIG.search(name):
        for m in PW6.finditer(code):
            found.append((m.start(), "PW6 traces always on — `trace: 'on-first-retry'`"))
    for m in PW7.finditer(code):
        found.append((m.start(), "PW7 a site the project does not control — test your own app from baseURL, and "
                                 "stub the third party with page.route"))
    for m in PW8.finditer(code):
        found.append((m.start(), "PW8 an action forced past its checks — find why the element is covered, moving or "
                                 "disabled"))
    lines = text.split("\n")
    hits = []
    for pos, msg in found:
        n = line_of(text, pos)
        if not (0 < n <= len(lines) and "e2e-exception" in lines[n - 1]):
            hits.append((n, msg))
    return sorted(set(hits))


def playwright_files() -> list[str]:
    tracked = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=ROOT,
                             capture_output=True, text=True).stdout.splitlines()
    out = []
    for f in tracked:
        if f.startswith(SKIP_DIRS) or "/node_modules/" in f or Path(f).suffix not in EXT or not (ROOT / f).is_file():
            continue
        if CONFIG.search(f) or "@playwright/test" in (ROOT / f).read_text(errors="replace"):
            out.append(f)
    return out


def run(files: list, named: bool) -> tuple:
    out: list[str] = []
    hits: list[str] = []
    read = 0
    for f in files:
        if Path(f).suffix not in EXT:
            out.append(f"{f}: not a test or config file — skipped")
            continue
        try:
            text = (ROOT / f).read_text(errors="replace")
        except OSError:
            out.append(f"{f}: cannot be read — not checked")
            continue
        read += 1
        hits += [f"{f}:{n}: {msg}" for n, msg in scan(f, text)]
    out += hits
    limit = 0 if named else BASELINE
    out.append(f"PW1–PW8 Playwright patterns — {len(hits)} hits in {read} files"
               + ("" if named else f" (baseline {BASELINE})"))
    if not read:
        out.append("read no Playwright files — nothing was checked: "
                   + ("no named file is readable" if named else "no tracked file imports @playwright/test"))
    if len(hits) > limit:
        out.append("FAIL — fix each hit, or mark a sanctioned one `e2e-exception` with its reason")
        return out, 1
    return out, 0


GOOD = """import AxeBuilder from '@axe-core/playwright'
import { expect, test } from '@playwright/test'

test.describe('checkout', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('**/payments.example.com/**', (route) => route.fulfill({ json: { ok: true } }))
    await page.goto('/cart')
  })

  test('pays for the basket', async ({ page }) => {
    await page.getByRole('button', { name: 'Pay now' }).click()
    await expect(page.getByRole('status')).toHaveText('Paid')
    await expect.soft(page.getByRole('heading', { level: 1 })).toBeVisible()
    expect(await page.title()).toBe('Cart')
  })

  test('has no WCAG A or AA violation axe can find', async ({ page }) => {
    const results = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa']).analyze()
    expect(results.violations).toEqual([])
  })
})
"""

CONFIG_GOOD = "export default defineConfig({ use: { baseURL: 'http://localhost:5173', trace: 'on-first-retry' } })\n"


def self_test() -> int:
    failures = []

    def expect(what: str, got, want) -> None:
        if got != want:
            failures.append(f"{what}: got {got!r}, want {want!r}")

    def rules(text: str, name: str = "e2e/checkout.spec.ts") -> list[str]:
        return sorted(msg[:3] for _, msg in scan(name, text))

    expect("a spec in the layout is clean", rules(GOOD), [])
    expect("a config in the layout is clean", rules(CONFIG_GOOD, "playwright.config.ts"), [])
    expect("PW1 a fixed wait", rules(GOOD.replace("await page.goto('/cart')",
                                                  "await page.goto('/cart')\n    await page.waitForTimeout(500)")),
           ["PW1"])
    expect("PW2 a CSS selector", rules(GOOD.replace("page.getByRole('button', { name: 'Pay now' })",
                                                    "page.locator('button.pay')")), ["PW2"])
    expect("PW2 page.$", rules(GOOD.replace("page.getByRole('button', { name: 'Pay now' })", "page.$('#pay')")),
           ["PW2"])
    expect("PW2 a chained locator by role passes", rules(GOOD.replace(
        "page.getByRole('button', { name: 'Pay now' })",
        "page.getByRole('listitem').filter({ hasText: 'Socks' }).getByRole('button', { name: 'Pay now' })")), [])
    expect("PW3 a manual assertion", rules(GOOD.replace(
        "await expect(page.getByRole('status')).toHaveText('Paid')",
        "expect(await page.getByRole('status').isVisible()).toBe(true)")), ["PW3"])
    expect("PW4 an assertion left floating", rules(GOOD.replace(
        "await expect(page.getByRole('status')).toHaveText('Paid')",
        "expect(page.getByRole('status')).toHaveText('Paid')")), ["PW4"])
    expect("PW4 across lines and with .not", rules(GOOD.replace(
        "await expect(page.getByRole('status')).toHaveText('Paid')",
        "expect(\n      page.getByRole('status'),\n    ).not.toBeVisible()")), ["PW4"])
    expect("PW4 a value assertion needs no await", rules(GOOD.replace(
        "expect(results.violations).toEqual([])", "expect(results.violations.length).toBe(0)")), [])
    expect("PW5 test.only", rules(GOOD.replace("test('pays for the basket'", "test.only('pays for the basket'")),
           ["PW5"])
    expect("PW5 describe.only", rules(GOOD.replace("test.describe('checkout'", "test.describe.only('checkout'")),
           ["PW5"])
    expect("PW6 trace on", rules(CONFIG_GOOD.replace("'on-first-retry'", "'on'"), "playwright.config.ts"), ["PW6"])
    expect("PW6 only in a config", rules(CONFIG_GOOD.replace("'on-first-retry'", "'on'")), [])
    expect("PW7 a third-party site", rules(GOOD.replace("page.goto('/cart')", "page.goto('https://example.com/')")),
           ["PW7"])
    expect("PW7 localhost passes", rules(GOOD.replace("page.goto('/cart')", "page.goto('http://localhost:5173/')")),
           [])
    expect("PW7 a look-alike host is not localhost", rules(GOOD.replace(
        "page.goto('/cart')", "page.goto('https://localhost.example.com/')")), ["PW7"])
    expect("PW8 force", rules(GOOD.replace(".click()", ".click({ force: true })")), ["PW8"])
    expect("a comment is skipped", rules(GOOD.replace("await page.goto('/cart')",
                                                      "await page.goto('/cart')\n    // page.waitForTimeout(500)")),
           [])
    expect("e2e-exception skips its line", rules(GOOD.replace(
        ".click()", ".click({ force: true }) // e2e-exception: the canvas covers the button by design")), [])
    for f in failures:
        print(f"FAIL {f}")
    print(f"e2e_check self-test — {'FAIL' if failures else 'pass'} ({len(failures)} failures)")
    return 1 if failures else 0


def main(argv: list[str]) -> int:
    if argv[:1] == ["--test"]:
        return self_test()
    named = bool(argv)
    lines, code = run(argv if named else playwright_files(), named)
    for line in lines:
        print(line)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
