import "#admin/admin-overview/cards/WorkerStatusCard";
import { Worker } from "@goauthentik/api";

import type { Meta, StoryObj } from "@storybook/web-components";

import { html } from "lit";

interface WorkerStatusCardArgs {
    workers: Worker[];
}

const meta: Meta<WorkerStatusCardArgs> = {
    title: "Admin / Overview / Worker Status Card",
    component: "ak-admin-status-card-workers",
};

export default meta;

type Story = StoryObj<WorkerStatusCardArgs>;

const Template: Story = {
    render: ({ workers }) =>
        html`<ak-admin-status-card-workers
            .getPrimaryValue=${() => Promise.resolve(workers)}
        ></ak-admin-status-card-workers>`,
};

const makeWorker = (workerId: string, versionMatching = true): Worker => ({
    workerId: `worker-${workerId}`,
    version: versionMatching ? "2026.11.0" : "2026.8.2",
    versionMatching,
});

export const Healthy: Story = {
    ...Template,
    args: { workers: [makeWorker("1"), makeWorker("2"), makeWorker("3")] },
};

export const NoWorkers: Story = { ...Template, args: { workers: [] } };

export const VersionMismatch: Story = {
    ...Template,
    args: { workers: [makeWorker("1"), makeWorker("2", false)] },
};
