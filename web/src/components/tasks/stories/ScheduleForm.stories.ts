import "#components/tasks/ScheduleForm";
import { LastTaskStatusEnum, Schedule } from "@goauthentik/api";

import type { Meta, StoryObj } from "@storybook/web-components";

import { html } from "lit";

interface ScheduleFormArgs {
    schedule: Schedule;
}

const meta: Meta<ScheduleFormArgs> = {
    title: "Components / Tasks / Schedule Form",
    component: "ak-schedule-form",
    tags: ["autodocs"],
    parameters: {
        docs: {
            description: {
                component: "Edits a schedule's crontab and paused state.",
            },
        },
    },
    render: ({ schedule }) =>
        html`<ak-schedule-form
            .loadInstance=${() => Promise.resolve(schedule)}
            .instancePk=${schedule.id}
        ></ak-schedule-form>`,
};

export default meta;

type Story = StoryObj<ScheduleFormArgs>;

const base: Schedule = {
    id: "00000000-0000-4000-8000-000000000001",
    identifier: null,
    uid: "authentik.sources.ldap.tasks.ldap_sync:1",
    actorName: "authentik.sources.ldap.tasks.ldap_sync",
    description: "Sync LDAP source",
    crontab: "*/30 * * * *",
    paused: false,
    nextRun: new Date(),
    lastTaskStatus: LastTaskStatusEnum.Done,
    relObjAppLabel: "",
    relObjModel: "",
    relObjId: null,
};

export const Active: Story = { args: { schedule: base } };

export const Paused: Story = { args: { schedule: { ...base, paused: true } } };
