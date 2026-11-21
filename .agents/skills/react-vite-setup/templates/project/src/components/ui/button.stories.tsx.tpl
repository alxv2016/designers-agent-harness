import type { Meta, StoryObj } from '@storybook/react-vite'
import { expect, fn } from 'storybook/test'
import { Button } from './button'

// Every component in src/components/ui/ has a story file beside it (APP_ARCHITECTURE §2), laid out as the storybook
// skill's template: one concept per story, a summary on each, every prop covered, each theme pinned, a play function
// for what it does — shown on its docs page and run as a test, the a11y addon checking what it is.
const meta = {
  title: 'UI/Button',
  component: Button,
  args: { children: 'Save', onClick: fn() },
} satisfies Meta<typeof Button>

export default meta
type Story = StoryObj<typeof meta>

/** @summary the default: the action people take most often on a screen */
export const Default: Story = {
  play: async ({ args, canvas, userEvent }) => {
    await userEvent.click(canvas.getByRole('button', { name: 'Save' }))
    await expect(args.onClick).toHaveBeenCalledOnce()
  },
}

/** @summary an action that is not available yet, and takes no press */
export const Disabled: Story = {
  args: { disabled: true },
  play: async ({ args, canvas }) => {
    await expect(canvas.getByRole('button', { name: 'Save' })).toBeDisabled()
    await expect(args.onClick).not.toHaveBeenCalled()
  },
}
{{theme_stories}}
