/**
 * @file Storybook stories for ak-schedule-form
 */

import "#elements/messages/MessageContainer";
import "../ScheduleForm.js";
import { LastTaskStatusEnum, type Schedule } from "@goauthentik/api";

import { Meta, StoryObj } from "@storybook/web-components";

import { html } from "lit";

interface ScheduleFormProps {
    instance?: Schedule;
}

const meta: Meta<ScheduleFormProps> = {
    title: "Components / Tasks / Schedule Form",
    component: "ak-schedule-form",
    tags: ["autodocs"],
    parameters: {
        docs: {
            description: {
                component: `Edits the crontab and paused state of an existing schedule.`,
            },
        },
    },
};

export default meta;

type Story = StoryObj<ScheduleFormProps>;

const schedule = (overrides: Partial<Schedule> = {}): Schedule => ({
    id: "0b6f3c1e-2f1a-4b7e-9d1c-1a2b3c4d5e6f",
    identifier: null,
    uid: "authentik.outposts.tasks.outpost_send_update:4c8f",
    actorName: "authentik.outposts.tasks.outpost_send_update",
    relObjAppLabel: "authentik_outposts",
    relObjModel: "outpost",
    relObjId: "4c8f",
    crontab: "*/5 9-17 * * 1-5",
    paused: false,
    nextRun: new Date(),
    description: "Send outpost update",
    lastTaskStatus: LastTaskStatusEnum.Done,
    ...overrides,
});

const container = (instance: Schedule) =>
    html`<ak-message-container></ak-message-container>
        <div style="padding: 2rem; background: var(--pf-global--BackgroundColor--100)">
            <ak-schedule-form .instance=${instance}></ak-schedule-form>
        </div>`;

export const Default: Story = {
    render: () => container(schedule()),
};

export const InvalidCrontab: Story = {
    parameters: {
        docs: { description: { story: "A stored crontab that does not parse." } },
    },
    render: () => container(schedule({ crontab: "not a cron" })),
};
