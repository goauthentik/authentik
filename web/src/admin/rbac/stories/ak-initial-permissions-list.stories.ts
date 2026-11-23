import "#admin/rbac/ak-initial-permissions-list";
import { createPaginatedResponse } from "#common/api/responses";

import { InitialPermissions } from "@goauthentik/api";

import type { Meta, StoryObj } from "@storybook/web-components";

import { html } from "lit";

interface InitialPermissionsListArgs {
    permissions: InitialPermissions[];
}

const meta: Meta<InitialPermissionsListArgs> = {
    title: "Admin / RBAC / Initial Permissions List",
    component: "ak-initial-permissions-list",
    render: ({ permissions }) =>
        html`<ak-initial-permissions-list
            .apiEndpoint=${() => Promise.resolve(createPaginatedResponse(permissions))}
        ></ak-initial-permissions-list>`,
};

export default meta;

type Story = StoryObj<InitialPermissionsListArgs>;

const initial = (pk: number, name: string): InitialPermissions => ({
    pk,
    name,
    role: "00000000-0000-4000-8000-000000000001",
    permissionsObj: [],
});

export const WithPermissions: Story = {
    args: {
        permissions: [
            initial(1, "Helpdesk: new users"),
            initial(2, "Platform team: new applications"),
            initial(3, "Security: new flows"),
        ],
    },
};

export const Empty: Story = { args: { permissions: [] } };
