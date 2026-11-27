import "#components/tasks/ScheduleList";
import { PaginatedResponse } from "#elements/table/Table";

import { LastTaskStatusEnum, Schedule } from "@goauthentik/api";

import type { Meta, StoryObj } from "@storybook/web-components";

import { html } from "lit";

interface ScheduleListArgs {
    schedules: Schedule[];
    relObjId?: string;
}

const page = <T>(results: T[]): PaginatedResponse<T> => ({
    pagination: {
        next: 0,
        previous: 0,
        count: results.length,
        current: 1,
        totalPages: 1,
        startIndex: results.length ? 1 : 0,
        endIndex: results.length,
    },
    results,
});

const meta: Meta<ScheduleListArgs> = {
    title: "Components / Tasks / Schedule List",
    component: "ak-schedule-list",
    tags: ["autodocs"],
    parameters: {
        docs: {
            description: {
                component: "A table of scheduled tasks.",
            },
        },
    },
    // Today I learned that Lit's property syntax works even without the `@property()` decorator;
    // the decorator only ensures that changes to the property are tracked.
    render: ({ schedules, relObjId }) =>
        html`<ak-schedule-list
            .apiEndpoint=${() => Promise.resolve(page(schedules))}
            .relObjId=${relObjId}
        ></ak-schedule-list>`,
};

export default meta;

type Story = StoryObj<ScheduleListArgs>;

const schedule = (
    n: number,
    actorName: string,
    description: string,
    crontab: string,
    lastTaskStatus: LastTaskStatusEnum | null,
    paused = false,
): Schedule => ({
    id: `00000000-0000-4000-8000-${String(n).padStart(12, "0")}`,
    identifier: null,
    uid: `${actorName}:${n}`,
    actorName,
    description,
    crontab,
    paused,
    nextRun: new Date(Date.now() + n * 3_600_000),
    lastTaskStatus,
    relObjAppLabel: "",
    relObjModel: "",
    relObjId: null,
});

const schedules: Schedule[] = [
    schedule(
        1,
        "authentik.sources.ldap.tasks.ldap_sync",
        "Sync LDAP source",
        "*/30 * * * *",
        LastTaskStatusEnum.Done,
    ),
    schedule(
        2,
        "authentik.outposts.tasks.outpost_controller_all",
        "Update all outposts",
        "0 */4 * * *",
        LastTaskStatusEnum.Warning,
    ),
    schedule(
        6,
        "authentik.crypto.tasks.certificate_discovery",
        "Discover certificates",
        "0 3 * * *",
        LastTaskStatusEnum.Error,
    ),
    schedule(
        12,
        "authentik.admin.tasks.update_latest_version",
        "Check for updates",
        "0 0 * * 1",
        null,
        true,
    ),
];

export const Default: Story = { args: { schedules } };

/** Scoped to a single object: the "standalone" filter is hidden. */
export const ForObject: Story = { args: { schedules: schedules.slice(0, 1), relObjId: "1" } };

export const Empty: Story = { args: { schedules: [] } };
