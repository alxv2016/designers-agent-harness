// The story file's layout (STORYBOOK §2). It ends in `.tpl` so an editor does not type-check its stand-in imports
// here. Copy it beside the component as `<component>.stories.tsx` — without `.tpl` — rename `Example` and
// `./example`, and keep the sections in this order. Delete these guide comments once it is filled in; keep the
// summaries. Every prop the component declares appears below (§3); every value on screen is a token (§6).
import type { Meta, StoryObj } from '@storybook/react-vite' // the project's framework package
import { expect, fn } from 'storybook/test'
import { Example } from './example'

// 1. Meta — names the component (§2) and holds what every story shares (§3).
const meta = {
  title: 'UI/Example', // the sidebar group, as the components folder is grouped
  component: Example,
  // The minimum to render it as people meet it: required props with the product's real words, a fn() per callback.
  args: {
    label: 'Save changes',
    onAction: fn(),
  },
  // Only where the inferred control is wrong: a union as a radio, a number's range, a pass-through prop hidden.
  argTypes: {
    variant: { control: 'inline-radio', options: ['primary', 'secondary'] },
    size: { control: 'select', options: ['small', 'medium', 'large'] },
  },
} satisfies Meta<typeof Example>

export default meta
type Story = StoryObj<typeof meta>

// 2. Default — the state people meet most often, with a play function for what it does (§7).

/** @summary the default: <when people reach for this component, in a line> */
export const Default: Story = {
  play: async ({ args, canvas, userEvent }) => {
    await userEvent.click(canvas.getByRole('button', { name: 'Save changes' }))
    await expect(args.onAction).toHaveBeenCalledOnce()
  },
}

// 3. One story per concept (§4): each variant, each state, each edge case — a summary saying why to use it (§5).

/** @summary <why to reach for the secondary variant> */
export const Secondary: Story = { args: { variant: 'secondary' } }

/** @summary <why sizes differ — one story, because size is one concept> */
export const Sizes: Story = {
  render: (args) => (
    <>
      <Example {...args} size="small" />
      <Example {...args} size="medium" />
      <Example {...args} size="large" />
    </>
  ),
}

/** @summary an action not available yet, which takes no press */
export const Disabled: Story = {
  args: { disabled: true },
  play: async ({ args, canvas }) => {
    await expect(canvas.getByRole('button', { name: 'Save changes' })).toBeDisabled()
    await expect(args.onAction).not.toHaveBeenCalled()
  },
}

/** @summary the longest label it must hold, as in the longest translation */
export const LongLabel: Story = { args: { label: 'Save changes and notify everyone on the project' } }

// 4. A story per theme past the first (§6): the default pinned with `globals`, kept out of the agents' manifest (§9).

/** The default in the dark theme, for the eye and the accessibility test */
export const Dark: Story = { globals: { theme: 'dark' }, tags: ['!manifest'] }
