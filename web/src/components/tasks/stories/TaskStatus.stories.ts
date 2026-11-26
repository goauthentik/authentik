import "#components/tasks/TaskStatus";
import { TaskStatus } from "#components/tasks/TaskStatus";

import { LastTaskStatusEnum, TaskAggregatedStatusEnum } from "@goauthentik/api";

import type { Meta, StoryObj } from "@storybook/web-components";

import { html } from "lit";
import { map } from "lit/directives/map.js";

const meta: Meta<TaskStatus> = {
    title: "Components / Tasks / Task Status",
    component: "ak-task-status",
    tags: ["autodocs"],
    parameters: {
        docs: {
            description: {
                // I'm kinda annoyed that it's called "label." This is a chip.
                component:
                    "A label that maps a task's aggregated status, or a schedule's last task status, to a chip.",
            },
        },
    },
    argTypes: {
        status: {
            control: "select",
            options: [undefined, ...Object.values(TaskAggregatedStatusEnum)],
        },
    },
};

export default meta;

type Story = StoryObj<TaskStatus>;

export const Default: Story = {
    args: { status: TaskAggregatedStatusEnum.Running },
    render: ({ status }) => html`<ak-task-status status=${status ?? ""}></ak-task-status>`,
};

const grid = (statuses: string[]) =>
    html`<dl style="display: grid; grid-template-columns: 28ch 1fr; gap: 0.5rem;">
        ${map(
            statuses,
            (status) =>
                html`<dt><code>${status}</code></dt>
                    <dd><ak-task-status status=${status}></ak-task-status></dd>`,
        )}
        <dt><em>unset</em></dt>
        <dd><ak-task-status></ak-task-status></dd>
    </dl>`;

export const AllAggregatedStatuses: Story = {
    render: () => grid(Object.values(TaskAggregatedStatusEnum)),
};

export const AllLastTaskStatuses: Story = {
    render: () => grid(Object.values(LastTaskStatusEnum)),
};
