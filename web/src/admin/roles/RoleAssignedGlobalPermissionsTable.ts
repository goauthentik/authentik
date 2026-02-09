import "#elements/forms/DeleteBulkForm";
import "#admin/roles/RolePermissionForm";
import "#elements/forms/ModalForm";

import { DEFAULT_CONFIG } from "#common/api/config";
import { groupBy } from "#common/utils";

import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { Permission, RbacApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-role-assigned-global-permissions-table")
export class RoleAssignedGlobalPermissionsTable extends Table<Permission> {
    @property()
    roleUuid?: string;

    protected override searchEnabled = true;

    checkbox = true;
    clearOnRefresh = true;

    order = "content_type__app_label,content_type__model";

    async apiEndpoint(): Promise<PaginatedResponse<Permission>> {
        return new RbacApi(DEFAULT_CONFIG).rbacPermissionsList({
            ...(await this.defaultEndpointConfig()),
            role: this.roleUuid,
        });
    }

    groupBy(items: Permission[]): [string, Permission[]][] {
        return groupBy(items, (obj) => {
            return obj.appLabelVerbose;
        });
    }

    protected columns: TableColumn[] = [
        // ---
        [msg("Model"), "model"],
        [msg("Permission"), ""],
        ["", null, msg("Assigned to role")],
    ];

    renderObjectCreate(): TemplateResult {
        return html`
            <ak-forms-modal>
                <span slot="submit">${msg("Assign")}</span>
                <span slot="header">${msg("Assign permission to role")}</span>
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
            object-label=${msg("Permission(s)")}
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

    row(item: Permission): SlottedTemplateResult[] {
        return [
            html`${item.modelVerbose}`,
            html`${item.name}`,
            html`<i class="fas fa-check pf-m-success" aria-hidden="true"></i>`,
        ];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-role-assigned-global-permissions-table": RoleAssignedGlobalPermissionsTable;
    }
}
