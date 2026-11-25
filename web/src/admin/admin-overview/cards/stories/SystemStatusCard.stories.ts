import "#admin/admin-overview/cards/SystemStatusCard";
import { SystemInfo } from "@goauthentik/api";

import type { Meta, StoryObj } from "@storybook/web-components";

import { html } from "lit";

type SystemStatusFields = Pick<
    SystemInfo,
    "embeddedOutpostDisabled" | "embeddedOutpostHost" | "httpIsSecure"
>;

interface SystemStatusCardArgs extends SystemStatusFields {
    clockSkew: number;
}

const meta: Meta<SystemStatusCardArgs> = {
    title: "Admin / Overview / System Status Card",
    component: "ak-admin-status-system",
};

export default meta;

type Story = StoryObj<SystemStatusCardArgs>;

const render = (getPrimaryValue: () => Promise<SystemInfo>) =>
    html`<ak-admin-status-system .getPrimaryValue=${getPrimaryValue}></ak-admin-status-system>`;

const Template: Story = {
    render: ({ clockSkew, ...fields }) =>
        render(() =>
            Promise.resolve({
                ...fields,
                serverTime: new Date(Date.now() + clockSkew),
            } as SystemInfo),
        ),
};

const healthy: SystemStatusCardArgs = {
    embeddedOutpostDisabled: false,
    embeddedOutpostHost: "https://authentik.example.com",
    httpIsSecure: true,
    clockSkew: 0,
};

export const Healthy: Story = { ...Template, args: healthy };

export const EmbeddedOutpostMisconfigured: Story = {
    ...Template,
    args: { ...healthy, embeddedOutpostHost: "" },
};

export const ClockSkew: Story = { ...Template, args: { ...healthy, clockSkew: 30_000 } };

// SystemStatusCard inherits from AdminStatusCard, so `loading` and `failed` are valid
// states.

export const Loading: Story = { render: () => render(() => new Promise(() => {})) };

export const Failed: Story = {
    render: () => render(() => Promise.reject(new Error("Connection refused"))),
};
