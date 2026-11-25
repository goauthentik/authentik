import "#components/tasks/TaskList";
import { PaginatedResponse } from "#elements/table/Table";

import {
    GlobalTaskStatus,
    LogEvent,
    LogLevelEnum,
    Task,
    TaskAggregatedStatusEnum,
    TaskStatusEnum,
} from "@goauthentik/api";

import type { Meta, StoryObj } from "@storybook/web-components";

import { html } from "lit";

interface TaskListArgs {
    tasks: Task[];
    status?: GlobalTaskStatus;
    includeOverview: boolean;
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

const meta: Meta<TaskListArgs> = {
    title: "Components / Tasks / Task List",
    component: "ak-task-list",
    tags: ["autodocs"],
    parameters: {
        docs: {
            description: {
                component: "A table of background tasks.",
            },
        },
    },
    // `.status` is bound directly because the overview is normally fetched inside `apiEndpoint`.
    render: ({ tasks, status, includeOverview, relObjId }) =>
        html`<ak-task-list
            .apiEndpoint=${() => Promise.resolve(page(tasks))}
            .status=${status}
            .relObjId=${relObjId}
            ?include-overview=${includeOverview}
        ></ak-task-list>`,
};

export default meta;

type Story = StoryObj<TaskListArgs>;

const minutesAgo = (n: number) => new Date(Date.now() - n * 60_000);

const log = (n: number, logLevel: LogLevelEnum, event: string): LogEvent => ({
    timestamp: minutesAgo(n),
    logLevel,
    logger: "authentik.tasks",
    event,
    attributes: {},
});

const task = (
    n: number,
    actorName: string,
    description: string,
    aggregatedStatus: TaskAggregatedStatusEnum,
    state: TaskStatusEnum,
    extra: Partial<Task> = {},
): Task => ({
    messageId: `00000000-0000-4000-8000-${String(n).padStart(12, "0")}`,
    queueName: "default",
    actorName,
    description,
    state,
    aggregatedStatus,
    retries: 0,
    eta: null,
    mtime: minutesAgo(n),
    relObjAppLabel: "",
    relObjModel: "",
    relObjId: null,
    uid: `${actorName}:${n}`,
    logs: [log(n, LogLevelEnum.Info, "Task started")],
    previousLogs: [],
    ...extra,
});

const tasks: Task[] = [
    task(
        1,
        "authentik.outposts.tasks.outpost_controller",
        "Update outpost deployment",
        TaskAggregatedStatusEnum.Running,
        TaskStatusEnum.Running,
    ),
    task(
        3,
        "authentik.sources.ldap.tasks.ldap_sync",
        "Sync LDAP source",
        TaskAggregatedStatusEnum.Queued,
        TaskStatusEnum.Queued,
        { eta: new Date(Date.now() + 10 * 60_000) },
    ),
    task(
        8,
        "authentik.providers.scim.tasks.scim_sync",
        "Sync SCIM provider",
        TaskAggregatedStatusEnum.Warning,
        TaskStatusEnum.Done,
        {
            logs: [
                log(9, LogLevelEnum.Info, "Starting full sync"),
                log(8, LogLevelEnum.Warning, "Skipped 3 users without an email address"),
            ],
        },
    ),
    task(
        25,
        "authentik.events.tasks.event_notification_handler",
        "Send notification",
        TaskAggregatedStatusEnum.Rejected,
        TaskStatusEnum.Rejected,
        {
            retries: 5,
            logs: [log(25, LogLevelEnum.Error, "Connection refused: smtp.example.com:587")],
            previousLogs: [
                log(40, LogLevelEnum.Error, "Connection refused: smtp.example.com:587"),
                log(35, LogLevelEnum.Error, "Connection refused: smtp.example.com:587"),
            ],
        },
    ),
    task(
        60,
        "authentik.blueprints.v1.tasks.apply_blueprint",
        "Apply blueprint",
        TaskAggregatedStatusEnum.Done,
        TaskStatusEnum.Done,
    ),
];

export const Default: Story = {
    args: { tasks, includeOverview: false },
};

export const WithOverview: Story = {
    args: {
        tasks,
        includeOverview: true,
        status: {
            queued: 1,
            consumed: 0,
            preprocess: 0,
            running: 1,
            postprocess: 0,
            rejected: 1,
            done: 1,
            info: 0,
            warning: 1,
            error: 0,
        },
    },
};

export const ForObject: Story = {
    args: { tasks: tasks.slice(0, 2), includeOverview: false, relObjId: "1" },
};

export const Empty: Story = {
    args: { tasks: [], includeOverview: false },
};
