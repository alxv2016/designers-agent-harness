// The spec file's layout (PLAYWRIGHT §2). It ends in `.tpl` so an editor does not type-check it here. Copy it into
// the project's test folder as `<feature>.spec.ts` — without `.tpl` — rename the feature, the path, the tasks and
// the names, and keep the sections in this order. Delete these guide comments once it is filled in.
import AxeBuilder from '@axe-core/playwright'
import { expect, test } from '@playwright/test'

const WCAG = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']

test.describe('<feature>', () => {
  // 1. Setup — each test starts on its own (§5); what the project does not control is stubbed (§6).
  test.beforeEach(async ({ page }) => {
    await page.route('**/third-party.example/**', (route) =>
      route.fulfill({ json: { ok: true } }),
    )
    await page.goto('/<path>')
  })

  // 2. The task, named in the person's words — find by role and name (§3), assert what they see, awaited (§4).
  test('<does the task>', async ({ page }) => {
    await page.getByRole('textbox', { name: '<Field label>' }).fill('<value>')
    await page.getByRole('button', { name: '<Action>' }).click()
    await expect(page.getByRole('status')).toHaveText('<What the person is told>')
  })

  // 3. Its likely failure — stubbed at the network, so the error state is walked (§6).
  test('shows <the error> when <the cause>', async ({ page }) => {
    await page.route('**/api/<endpoint>', (route) => route.fulfill({ status: 500 }))
    await page.getByRole('button', { name: '<Action>' }).click()
    await expect(page.getByRole('alert')).toContainText('<What went wrong and what to do>')
  })

  // 4. The keyboard path (§7).
  test('works from the keyboard', async ({ page }) => {
    await page.getByRole('textbox', { name: '<Field label>' }).focus()
    await page.keyboard.type('<value>')
    await page.keyboard.press('Tab')
    await expect(page.getByRole('button', { name: '<Action>' })).toBeFocused()
    await page.keyboard.press('Enter')
    await expect(page.getByRole('status')).toHaveText('<What the person is told>')
  })

  // 5. The accessibility floors axe can find, in each theme (§7).
  for (const colorScheme of ['light', 'dark'] as const) {
    test(`has no WCAG A or AA violation axe can find, ${colorScheme}`, async ({ page }) => {
      await page.emulateMedia({ colorScheme })
      const results = await new AxeBuilder({ page }).withTags(WCAG).analyze()
      expect(results.violations).toEqual([])
    })
  }

  // 6. Reflow at 320 px wide, and a screenshot for the person (§7).
  test('reflows at 320 px wide', async ({ page }, testInfo) => {
    await page.setViewportSize({ width: 320, height: 640 })
    const width = await page.evaluate(() => document.documentElement.scrollWidth)
    expect(width).toBeLessThanOrEqual(320)
    await testInfo.attach('<feature> at 320 px', {
      body: await page.screenshot({ fullPage: true }),
      contentType: 'image/png',
    })
  })
})
