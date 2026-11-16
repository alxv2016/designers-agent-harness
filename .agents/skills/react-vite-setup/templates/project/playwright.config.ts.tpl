import { defineConfig, devices } from '@playwright/test'

// End-to-end tests drive the app in real browsers. Locally they use the dev server — one already running on the
// port is reused; in CI they build the app and test the production preview, so a build-only failure shows too.
// The browsers and the sizes are the web app spec's ({{spec_facts}}): one project for each pair (REACT_VITE_SETUP §6).
const ci = !!process.env.CI
const port = ci ? {{preview_port}} : {{dev_port}}
const baseURL = `http://localhost:${port}`

export default defineConfig({
  testDir: 'e2e',
  fullyParallel: true,
  forbidOnly: ci,
  retries: ci ? 2 : 0,
  reporter: [[ci ? 'github' : 'list'], ['html', { open: 'never' }]],
  use: {
    baseURL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
{{playwright_projects}}
  ],
  webServer: {
    command: ci ? 'npm run build && npm run preview' : 'npm run dev',
    url: baseURL,
    reuseExistingServer: !ci,
  },
})
