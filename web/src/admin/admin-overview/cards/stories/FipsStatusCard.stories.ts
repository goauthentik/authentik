import "#admin/admin-overview/cards/FipsStatusCard";
import { SystemInfo } from "@goauthentik/api";

import type { Meta, StoryObj } from "@storybook/web-components";

import { html } from "lit";

interface FipsStatusCardArgs {
    fipsEnabled: boolean | null;
}

const meta: Meta<FipsStatusCardArgs> = {
    title: "Admin / Overview / FIPS Status Card",
    component: "ak-admin-fips-status-system",
};

export default meta;

type Story = StoryObj<FipsStatusCardArgs>;

const Template: Story = {
    render: ({ fipsEnabled }) =>
        html`<ak-admin-fips-status-system
            .getPrimaryValue=${() =>
                Promise.resolve({ runtime: { opensslFipsEnabled: fipsEnabled } } as SystemInfo)}
        ></ak-admin-fips-status-system>`,
};

export const Passing: Story = { ...Template, args: { fipsEnabled: true } };

export const Unverified: Story = { ...Template, args: { fipsEnabled: false } };
