import "#elements/utils/TimeDeltaHelp";
import type { TimeDeltaHelp } from "#elements/utils/TimeDeltaHelp";

import type { Meta, StoryObj } from "@storybook/web-components";

import { html } from "lit";

const metadata: Meta<TimeDeltaHelp> = {
    title: "Elements/<ak-utils-time-delta-help>",
    component: "ak-utils-time-delta-help",
    tags: ["autodocs"],
    parameters: {
        docs: {
            description: {
                component: /* md */ `Explains the timedelta format to users.`,
            },
        },
    },
    argTypes: {
        negative: { control: "boolean" },
    },
    args: {
        negative: false,
    },
    render: ({ negative }) =>
        html`<ak-utils-time-delta-help ?negative=${negative}></ak-utils-time-delta-help>`,
};

export default metadata;

type Story = StoryObj<TimeDeltaHelp>;

export const Default: Story = {};

export const Negative: Story = {
    args: { negative: true },
};
