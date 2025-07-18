import "./SyncStatusCard.js";

import { SyncStatus, TaskAggregatedStatusEnum } from "@goauthentik/api";

import type { Meta, StoryObj } from "@storybook/web-components";

import { html } from "lit";

const metadata: Meta<SyncStatus> = {
    title: "Elements/<ak-sync-status-card>",
    component: "ak-sync-status-card",
};

export default metadata;

export const Running: StoryObj = {
    args: {
        status: {
            isRunning: true,
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

export const LastSyncDone: StoryObj = {
    args: {
        status: {
            isRunning: false,
            lastSyncStatus: TaskAggregatedStatusEnum.Done,
        } as SyncStatus,
    },
    // @ts-ignore
    render: ({ status }: SyncStatus) => {
        return html`
            <ak-sync-status-card
                .fetch=${async () => {
                    return status;
                }}
            ></ak-sync-status-card>
        `;
    },
};

export const LastSyncError: StoryObj = {
    args: {
        status: {
            isRunning: false,
            lastSyncStatus: TaskAggregatedStatusEnum.Error,
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

export const LastSuccessfulSync: StoryObj = {
    args: {
        status: {
            isRunning: false,
            lastSuccessfulSync: new Date(),
        } as SyncStatus,
    },
    // @ts-ignore
    render: ({ status }: SyncStatus) => {
        return html`
            <ak-sync-status-card
                .fetch=${async () => {
                    return status;
                }}
            ></ak-sync-status-card>
        `;
    },
};
