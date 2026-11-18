/**
 * @file Storybook stories for ak-task-status-summary
 */

import "../TaskStatusSummary.js";
import type { GlobalTaskStatus } from "@goauthentik/api";

import { Meta, StoryObj } from "@storybook/web-components";

import { html } from "lit";

interface TaskStatusSummaryProps {
    status?: GlobalTaskStatus;
}

const meta: Meta<TaskStatusSummaryProps> = {
    title: "Components / Tasks / Task Status Summary",
    component: "ak-task-status-summary",
    tags: ["autodocs"],
    parameters: {
        docs: {
            description: {
                component: `Four aggregate cards summarizing global task counts. Running, queued,
successful, and error cards each sum several underlying statuses. Shows spinners until \`status\`
is set.`,
            },
        },
    },
};

export default meta;

type Story = StoryObj<TaskStatusSummaryProps>;

const summary = (status?: GlobalTaskStatus) =>
    html`<ak-task-status-summary .status=${status}></ak-task-status-summary>`;

export const Loading: Story = {
    render: () => summary(),
};

export const Retrieved: Story = {
    parameters: {
        docs: {
            description: {
                story: "Running = 3 + 1 + 1, Queued = 4 + 2, Successful = 120 + 8 + 5, Error = 2 + 1.",
            },
        },
    },
    render: () =>
        summary({
            queued: 4,
            consumed: 2,
            preprocess: 1,
            running: 3,
            postprocess: 1,
            rejected: 1,
            done: 120,
            info: 8,
            warning: 5,
            error: 2,
        }),
};
