import "@goauthentik/admin/roles/RolePermissionForm";
import { DEFAULT_CONFIG } from "@goauthentik/app/common/api/config";
import { groupBy } from "@goauthentik/app/common/utils";
import { PaginatedResponse, Table, TableColumn } from "@goauthentik/app/elements/table/Table";
import "@goauthentik/elements/forms/ModalForm";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { Permission, RbacApi } from "@goauthentik/api";

@customElement("ak-role-permissions-global-table")
export class RolePermissionGlobalTable extends Table<Permission> {
    @property()
    roleUuid?: string;

    searchEnabled(): boolean {
        return true;
    }

    checkbox = true;

    order = "content_type__app_label,content_type__model";

    apiEndpoint(page: number): Promise<PaginatedResponse<Permission>> {
        return new RbacApi(DEFAULT_CONFIG).rbacPermissionsList({
            role: this.roleUuid,
            page: page,
            ordering: this.order,
            search: this.search,
        });
    }

    groupBy(items: Permission[]): [string, Permission[]][] {
        return groupBy(items, (obj) => {
            return obj.appLabelVerbose;
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn("Model", "model"),
            new TableColumn("Permission", ""),
            new TableColumn(""),
        ];
    }

    renderObjectCreate(): TemplateResult {
        return html`
            <ak-forms-modal>
                <span slot="submit"> ${msg("Assign")} </span>
                <span slot="header"> ${msg("Assign permission to role")} </span>
                <ak-role-permission-form roleUuid=${ifDefined(this.roleUuid)} slot="form">
                </ak-role-permission-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">
                    ${msg("Assign permission")}
                </button>
            </ak-forms-modal>
        `;
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${msg("Permission(s)")}
            .objects=${this.selectedElements}
            .delete=${(item: Permission) => {
                return new RbacApi(
                    DEFAULT_CONFIG,
                ).rbacPermissionsAssignedByRolesUnassignPartialUpdate({
                    uuid: this.roleUuid || "",
                    patchedPermissionAssignRequest: {
                        permissions: [`${item.appLabel}.${item.codename}`],
                    },
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    row(item: Permission): TemplateResult[] {
        return [html`${item.modelVerbose}`, html`${item.name}`, html`✓`];
    }
}
