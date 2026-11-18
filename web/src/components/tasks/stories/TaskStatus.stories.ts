/**
 * @file Storybook stories for ak-task-status
 */

import "../TaskStatus.js";
import { LastTaskStatusEnum, TaskAggregatedStatusEnum } from "@goauthentik/api";

import { Meta, StoryObj } from "@storybook/web-components";

import { html } from "lit";

interface TaskStatusProps {
    status?: TaskAggregatedStatusEnum | LastTaskStatusEnum;
}

const meta: Meta<TaskStatusProps> = {
    title: "Components / Tasks / Task Status",
    component: "ak-task-status",
    tags: ["autodocs"],
    parameters: {
        docs: {
            description: {
                component: `A chip (color coded) for a task or schedule status.`,
            },
        },
    },
    argTypes: {
        status: {
            control: "select",
            options: Object.values(TaskAggregatedStatusEnum),
        },
    },
};

export default meta;

type Story = StoryObj<TaskStatusProps>;

export const Default: Story = {
    parameters: {
        docs: {
            description: {
                story: "Every aggregated status value, plus an unset and an unrecognized value.",
            },
        },
    },
    render: () =>
        html`<style>
                dl {
                    display: grid;
                    grid-template-columns: 28ch 1fr;
                    gap: 0.5rem;
                }
            </style>
            <dl>
                ${Object.values(TaskAggregatedStatusEnum).map(
                    (status) =>
                        html`<dt><code>${status}</code></dt>
                            <dd><ak-task-status status=${status}></ak-task-status></dd>`,
                )}
                <dt>(unset)</dt>
                <dd><ak-task-status></ak-task-status></dd>
                <dt><code>not_a_status</code></dt>
                <dd><ak-task-status status="not_a_status"></ak-task-status></dd>
            </dl>`,
};
