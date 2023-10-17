import { DEFAULT_CONFIG } from "@goauthentik/app/common/api/config";
import { PaginatedResponse, Table, TableColumn } from "@goauthentik/app/elements/table/Table";
import "@goauthentik/elements/forms/ModalForm";
import "@goauthentik/elements/rbac/UserObjectPermissionForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import {
    PaginatedPermissionList,
    RbacApi,
    RbacPermissionsAssignedByUsersListModelEnum,
    UserAssignedObjectPermission,
} from "@goauthentik/api";

@customElement("ak-rbac-user-object-permission-table")
export class UserAssignedObjectPermissionTable extends Table<UserAssignedObjectPermission> {
    @property()
    model?: RbacPermissionsAssignedByUsersListModelEnum;

    @property()
    objectPk?: string | number;

    @state()
    modelPermissions?: PaginatedPermissionList;

    async apiEndpoint(page: number): Promise<PaginatedResponse<UserAssignedObjectPermission>> {
        const perms = await new RbacApi(DEFAULT_CONFIG).rbacPermissionsAssignedByUsersList({
            page: page,
            // TODO: better default
            model: this.model || RbacPermissionsAssignedByUsersListModelEnum.CoreUser,
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
            <span slot="header"> ${msg("Assign permission to user")} </span>
            <ak-rbac-user-object-permission-form
                model=${ifDefined(this.model)}
                objectPk=${ifDefined(this.objectPk)}
                slot="form"
            >
            </ak-rbac-user-object-permission-form>
            <button slot="trigger" class="pf-c-button pf-m-primary">
                ${msg("Assign to new user")}
            </button>
        </ak-forms-modal>`;
    }

    row(item: UserAssignedObjectPermission): TemplateResult[] {
        const baseRow = [html` <a href="#/identity/users/${item.pk}"> ${item.username} </a> `];
        this.modelPermissions?.results.forEach((perm) => {
            let cell = html`X`;
            if (item.permissions.filter((uperm) => uperm.codename === perm.codename).length > 0) {
                cell = html`<pf-tooltip position="top" content=${msg("Directly assigned")}
                    >✓</pf-tooltip
                >`;
            } else if (item.isSuperuser) {
                cell = html`<pf-tooltip position="top" content=${msg("Superuser")}>✓</pf-tooltip>`;
            }
            baseRow.push(cell);
        });
        return baseRow;
    }
}
