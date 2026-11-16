import type { StorybookConfig } from '@storybook/react-vite'

// Storybook documents every component in src/components/ui/ — a story per component, a docs page from its props and
// its stories — and vitest.config.ts runs each story as a test (REACT_VITE_SETUP §7).
const config: StorybookConfig = {
  stories: ['../src/**/*.mdx', '../src/**/*.stories.@(ts|tsx)'],
  addons: [
    '@storybook/addon-docs',
    '@storybook/addon-a11y',
    '@storybook/addon-vitest',
  ],
  framework: '@storybook/react-vite',
  // Serves public/ (the favicon), so a story logs no 404
  staticDirs: ['../public'],
}

export default config
