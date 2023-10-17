import { DEFAULT_CONFIG } from "@goauthentik/app/common/api/config";
import { PaginatedResponse, Table, TableColumn } from "@goauthentik/app/elements/table/Table";
import "@goauthentik/elements/forms/ModalForm";
import "@goauthentik/elements/rbac/RoleObjectPermissionForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import {
    PaginatedPermissionList,
    RbacApi,
    RbacPermissionsAssignedByRolesListModelEnum,
    RoleAssignedObjectPermission,
} from "@goauthentik/api";

@customElement("ak-rbac-role-object-permission-table")
export class RoleAssignedObjectPermissionTable extends Table<RoleAssignedObjectPermission> {
    @property()
    model?: RbacPermissionsAssignedByRolesListModelEnum;

    @property()
    objectPk?: string | number;

    @state()
    modelPermissions?: PaginatedPermissionList;

    async apiEndpoint(page: number): Promise<PaginatedResponse<RoleAssignedObjectPermission>> {
        const perms = await new RbacApi(DEFAULT_CONFIG).rbacPermissionsAssignedByRolesList({
            page: page,
            // TODO: better default
            model: this.model || RbacPermissionsAssignedByRolesListModelEnum.CoreUser,
            objectPk: this.objectPk?.toString(),
        });
        const [appLabel, modelName] = (this.model || "").split(".");
        const modelPermissions = await new RbacApi(DEFAULT_CONFIG).rbacPermissionsList({
            contentTypeModel: modelName,
            contentTypeAppLabel: appLabel,
            ordering: "codename",
        });
        modelPermissions.results = modelPermissions.results.filter((value) => {
            return !value.codename.startsWith("add_");
        });
        this.modelPermissions = modelPermissions;
        return perms;
    }

    columns(): TableColumn[] {
        const baseColumns = [new TableColumn("User", "user")];
        // We don't check pagination since models shouldn't need to have that many permissions?
        this.modelPermissions?.results.forEach((perm) => {
            baseColumns.push(new TableColumn(perm.name, perm.codename));
        });
        return baseColumns;
    }

    renderObjectCreate(): TemplateResult {
        return html`<ak-forms-modal>
            <span slot="submit"> ${msg("Assign")} </span>
            <span slot="header"> ${msg("Assign permission to role")} </span>
            <ak-rbac-role-object-permission-form
                model=${ifDefined(this.model)}
                objectPk=${ifDefined(this.objectPk)}
                slot="form"
            >
            </ak-rbac-role-object-permission-form>
            <button slot="trigger" class="pf-c-button pf-m-primary">
                ${msg("Assign to new role")}
            </button>
        </ak-forms-modal>`;
    }

    row(item: RoleAssignedObjectPermission): TemplateResult[] {
        const baseRow = [html` <a href="#/identity/roles/${item.rolePk}">${item.name}</a>`];
        this.modelPermissions?.results.forEach((perm) => {
            const granted =
                item.permissions.filter((uperm) => uperm.codename === perm.codename).length > 0;
            baseRow.push(html`
                <ak-action-button
                    .apiRequest=${async () => {
                        console.log(granted);
                    }}
                    class="pf-m-link"
                >
                    ${granted
                        ? html`<pf-tooltip position="top" content=${msg("Directly assigned")}
                              >✓</pf-tooltip
                          >`
                        : html`X`}
                </ak-action-button>
            `);
        });
        return baseRow;
    }
}
