import type { Meta, StoryObj } from "@storybook/web-components";

import { html } from "lit";

import { LogLevelEnum, SyncStatus, SystemTaskStatusEnum } from "@goauthentik/api";

import "./SyncStatusCard";

const metadata: Meta<SyncStatus> = {
    title: "Elements/<ak-sync-status-card>",
    component: "ak-sync-status-card",
};

export default metadata;

export const Running: StoryObj = {
    args: {
        status: {
            isRunning: true,
            tasks: [],
        } as SyncStatus,
    },
    // @ts-ignore
    render: ({ status }: SyncStatus) => {
        return html` <div style="background-color: #f0f0f0; padding: 1rem;">
            <ak-sync-status-card
                .fetch=${async () => {
                    return status;
                }}
            ></ak-sync-status-card>
        </div>`;
    },
};

export const SingleTask: StoryObj = {
    args: {
        status: {
            isRunning: false,
            tasks: [
                {
                    uuid: "9ff42169-8249-4b67-ae3d-e455d822de2b",
                    name: "Single task",
                    fullName: "foo:bar:baz",
                    status: SystemTaskStatusEnum.Successful,
                    messages: [
                        {
                            logger: "foo",
                            event: "bar",
                            attributes: {
                                foo: "bar",
                            },
                            timestamp: new Date(),
                            logLevel: LogLevelEnum.Info,
                        },
                    ],
                    description: "foo",
                    startTimestamp: new Date(),
                    finishTimestamp: new Date(),
                    duration: 0,
                },
            ],
        } as SyncStatus,
    },
    // @ts-ignore
    render: ({ status }: SyncStatus) => {
        return html` <div style="background-color: #f0f0f0; padding: 1rem;">
            <ak-sync-status-card
                .fetch=${async () => {
                    return status;
                }}
            ></ak-sync-status-card>
        </div>`;
    },
};

export const MultipleTasks: StoryObj = {
    args: {
        status: {
            isRunning: false,
            tasks: [
                {
                    uuid: "9ff42169-8249-4b67-ae3d-e455d822de2b",
                    name: "Single task",
                    fullName: "foo:bar:baz",
                    status: SystemTaskStatusEnum.Successful,
                    messages: [
                        {
                            logger: "foo",
                            event: "bar",
                            attributes: {
                                foo: "bar",
                            },
                            timestamp: new Date(),
                            logLevel: LogLevelEnum.Info,
                        },
                    ],
                    description: "foo",
                    startTimestamp: new Date(),
                    finishTimestamp: new Date(),
                    duration: 0,
                },
                {
                    uuid: "9ff42169-8249-4b67-ae3d-e455d822de2b",
                    name: "Single task",
                    fullName: "foo:bar:baz",
                    status: SystemTaskStatusEnum.Successful,
                    messages: [
                        {
                            logger: "foo",
                            event: "bar",
                            attributes: {
                                foo: "bar",
                            },
                            timestamp: new Date(),
                            logLevel: LogLevelEnum.Info,
                        },
                    ],
                    description: "foo",
                    startTimestamp: new Date(),
                    finishTimestamp: new Date(),
                    duration: 0,
                },
                {
                    uuid: "9ff42169-8249-4b67-ae3d-e455d822de2b",
                    name: "Single task",
                    fullName: "foo:bar:baz",
                    status: SystemTaskStatusEnum.Successful,
                    messages: [
                        {
                            logger: "foo",
                            event: "bar",
                            attributes: {
                                foo: "bar",
                            },
                            timestamp: new Date(),
                            logLevel: LogLevelEnum.Info,
                        },
                    ],
                    description: "foo",
                    startTimestamp: new Date(),
                    finishTimestamp: new Date(),
                    duration: 0,
                },
            ],
        } as SyncStatus,
    },
    // @ts-ignore
    render: ({ status }: SyncStatus) => {
        return html` <div style="background-color: #f0f0f0; padding: 1rem;">
            <ak-sync-status-card
                .fetch=${async () => {
                    return status;
                }}
            ></ak-sync-status-card>
        </div>`;
    },
};
