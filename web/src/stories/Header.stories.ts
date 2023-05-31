import type { Meta, StoryObj } from '@storybook/web-components';
import type { HeaderProps } from './Header';
import { Header } from './Header';

const meta = {
  title: 'Example/Header',
  // This component will have an automatically generated Autodocs entry: https://storybook.js.org/docs/web-components/writing-docs/autodocs
  tags: ['autodocs'],
  render: (args: HeaderProps) => Header(args),
} satisfies Meta<HeaderProps>;

export default meta;
type Story = StoryObj<HeaderProps>;

export const LoggedIn: Story = {
  args: {
    user: {
      name: 'Jane Doe',
    },
  },
};

export const LoggedOut: Story = {};
