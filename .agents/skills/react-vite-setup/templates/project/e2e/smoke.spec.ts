import AxeBuilder from '@axe-core/playwright'
import { expect, test, type Page } from '@playwright/test'

// The smoke test every page starts from, run in each browser and size the spec names: the page loads with no error,
// its main heading shows, axe finds no WCAG A or AA violation, nothing scrolls sideways at 320 px wide, and a
// screenshot of it goes into the report (REACT_VITE_SETUP §6). The lines naming "Hello world" and "Add one" change
// when the hello feature goes.

function collectErrors(page: Page): string[] {
  const errors: string[] = []
  page.on('pageerror', (error) => errors.push(error.message))
  page.on('console', (message) => {
    if (message.type() === 'error') errors.push(message.text())
  })
  page.on('requestfailed', (request) =>
    errors.push(`${request.url()} ${request.failure()?.errorText ?? ''}`),
  )
  return errors
}

test.describe('home', () => {
  test('loads with no error', async ({ page }) => {
    const errors = collectErrors(page)
    await page.goto('/')
    await expect(
      page.getByRole('heading', { level: 1, name: 'Hello world' }),
    ).toBeVisible()
    expect(errors).toEqual([])
  })

  test('counts each press', async ({ page }) => {
    await page.goto('/')
    await page.getByRole('button', { name: 'Add one' }).click()
    await expect(page.getByRole('status')).toHaveText('Count: 1')
  })

  test('has no WCAG A or AA violation axe can find', async ({ page }) => {
    await page.goto('/')
    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
      .analyze()
    expect(results.violations).toEqual([])
  })

  test('reflows at 320 px wide', async ({ page }) => {
    await page.setViewportSize({ width: 320, height: 640 })
    await page.goto('/')
    const width = await page.evaluate(
      () => document.documentElement.scrollWidth,
    )
    expect(width).toBeLessThanOrEqual(320)
  })

  test('screenshot', async ({ page }, testInfo) => {
    await page.goto('/')
    await testInfo.attach('home', {
      body: await page.screenshot({ fullPage: true }),
      contentType: 'image/png',
    })
  })
})
