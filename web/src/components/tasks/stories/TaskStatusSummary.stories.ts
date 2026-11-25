import "#components/tasks/TaskStatusSummary";
import { GlobalTaskStatus } from "@goauthentik/api";

import type { Meta, StoryObj } from "@storybook/web-components";

import { html } from "lit";

interface SummaryArgs {
    status?: GlobalTaskStatus;
}

const meta: Meta<SummaryArgs> = {
    title: "Components / Tasks / Task Status Summary",
    component: "ak-task-status-summary",
    tags: ["autodocs"],
    render: ({ status }) =>
        html`<ak-task-status-summary .status=${status}></ak-task-status-summary>`,
};

export default meta;

type Story = StoryObj<SummaryArgs>;

const zero: GlobalTaskStatus = {
    queued: 0,
    consumed: 0,
    preprocess: 0,
    running: 0,
    postprocess: 0,
    rejected: 0,
    done: 0,
    info: 0,
    warning: 0,
    error: 0,
};

export const Loaded: Story = {
    args: {
        status: {
            ...zero,
            queued: 4,
            consumed: 1,
            preprocess: 1,
            running: 3,
            postprocess: 1,
            done: 1280,
            info: 12,
            warning: 7,
            error: 2,
            rejected: 1,
        },
    },
};

export const AllZero: Story = { args: { status: zero } };

export const Loading: Story = { args: {} };
