import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { storybookTest } from '@storybook/addon-vitest/vitest-plugin'
import react from '@vitejs/plugin-react'
import { playwright } from '@vitest/browser-playwright'
import { defineConfig } from 'vitest/config'

const dirname = path.dirname(fileURLToPath(import.meta.url))

// Two projects in one config. `unit` runs src/**/*.test.ts(x) in Node: fast, no browser. `storybook` runs every
// story as a test in a real Chromium through Playwright — its render, its play function and the a11y addon's checks
// (REACT_VITE_SETUP §6). It is apart from vite.config.ts so the tests never take the dev server's fixed port.
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { '@': path.join(dirname, 'src') },
  },
  test: {
    projects: [
      {
        extends: true,
        test: {
          name: 'unit',
          include: ['src/**/*.test.{ts,tsx}'],
          environment: 'node',
        },
      },
      {
        extends: true,
        plugins: [
          storybookTest({ configDir: path.join(dirname, '.storybook') }),
        ],
        test: {
          name: 'storybook',
          browser: {
            enabled: true,
            headless: true,
            provider: playwright(),
            instances: [{ browser: 'chromium' }],
          },
        },
      },
    ],
  },
})
