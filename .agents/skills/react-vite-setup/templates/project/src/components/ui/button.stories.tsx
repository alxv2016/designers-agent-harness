import type { Meta, StoryObj } from '@storybook/react-vite'
import { expect, fn } from 'storybook/test'
import { Button } from './button'

// Every component in src/components/ui/ has a story file beside it (APP_ARCHITECTURE §2): each state, shown on its
// docs page and run as a test — the play function checks what it does, the a11y addon what it is.
const meta = {
  title: 'UI/Button',
  component: Button,
  args: { children: 'Save', onClick: fn() },
} satisfies Meta<typeof Button>

export default meta
type Story = StoryObj<typeof meta>

export const Rest: Story = {
  play: async ({ args, canvas, userEvent }) => {
    await userEvent.click(canvas.getByRole('button', { name: 'Save' }))
    await expect(args.onClick).toHaveBeenCalledOnce()
  },
}

export const Disabled: Story = {
  args: { disabled: true },
  play: async ({ args, canvas }) => {
    await expect(canvas.getByRole('button', { name: 'Save' })).toBeDisabled()
    await expect(args.onClick).not.toHaveBeenCalled()
  },
}
