import type { Preview } from '@storybook/react-vite'
import '../src/styles/tokens.css'
import '../src/styles/global.css'

// Stories render with the app's own tokens and global styles, in each theme DESIGN.md gives. The toolbar sets
// data-theme on <html>, as the app does, so anything a component portals out switches too (REACT_VITE_SETUP §7).
const preview: Preview = {
  tags: ['autodocs'],
  globalTypes: {
    theme: {
      description: 'Theme',
      toolbar: {
        title: 'Theme',
        icon: 'mirror',
        dynamicTitle: true,
        items: [
{{theme_items}}
        ],
      },
    },
  },
  initialGlobals: { theme: '{{first_theme}}' },
  decorators: [
    (Story, context) => {
      document.documentElement.dataset.theme = context.globals.theme as string
      return <Story />
    },
  ],
  parameters: {
    a11y: {
      // 'error' fails a story's test on any axe violation: the accessibility floors hold from the first story
      test: 'error',
    },
  },
}

export default preview
