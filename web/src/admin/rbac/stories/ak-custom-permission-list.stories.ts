import "#admin/rbac/ak-custom-permission-list";
import { createPaginatedResponse } from "#common/api/responses";

import { CustomPermission } from "@goauthentik/api";

import type { Meta, StoryObj } from "@storybook/web-components";

import { html } from "lit";

interface CustomPermissionArgs {
    permissions: CustomPermission[];
}

const meta: Meta<CustomPermissionArgs> = {
    title: "Admin / RBAC / Custom Permission List",
    component: "ak-custom-permission-list",
    render: ({ permissions }) =>
        html`<ak-custom-permission-list
            .apiEndpoint=${() => Promise.resolve(createPaginatedResponse(permissions))}
        ></ak-custom-permission-list>`,
};

export default meta;

type Story = StoryObj<CustomPermissionArgs>;

const permission = (pk: number, codename: string, name: string): CustomPermission => ({
    pk,
    codename,
    name,
    model: "authentik_rbac.systempermission",
    permission: `authentik_rbac.${codename}`,
});

export const WithPermissions: Story = {
    args: {
        permissions: [
            permission(1, "access_reports", "Can access reports"),
            permission(2, "approve_enrollments", "Can approve enrollments"),
            permission(3, "view_audit_trail", "Can view audit trail"),
        ],
    },
};

export const Empty: Story = { args: { permissions: [] } };
