import "#elements/forms/DeleteBulkForm";
import "#admin/roles/ak-role-permission-form";
import "#elements/forms/ModalForm";

import { DEFAULT_CONFIG } from "#common/api/config";
import { groupBy } from "#common/utils";

import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";
import { ifPresent } from "#elements/utils/attributes";

import { Permission, RbacApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-role-assigned-global-permissions-table")
export class RoleAssignedGlobalPermissionsTable extends Table<Permission> {
    @property({ type: String, attribute: "role-uuid" })
    public roleUuid: string | null = null;

    protected override searchEnabled = true;

    public override checkbox = true;
    public override clearOnRefresh = true;

    public override order = "content_type__app_label,content_type__model";

    protected override async apiEndpoint(): Promise<PaginatedResponse<Permission>> {
        return new RbacApi(DEFAULT_CONFIG).rbacPermissionsList({
            ...(await this.defaultEndpointConfig()),
            role: this.roleUuid ?? undefined,
        });
    }

    protected override groupBy(items: Permission[]): [string, Permission[]][] {
        return groupBy(items, (obj) => {
            return obj.appLabelVerbose;
        });
    }

    protected override columns: TableColumn[] = [
        // ---
        [msg("Model"), "model"],
        [msg("Permission"), ""],
        ["", null, msg("Assigned to role")],
    ];

    protected renderObjectCreate(): SlottedTemplateResult {
        return html`
            <ak-forms-modal>
                <span slot="submit">${msg("Assign")}</span>
                <span slot="header">${msg("Assign permission to role")}</span>
                <ak-role-permission-form role-uuid=${ifPresent(this.roleUuid)} slot="form">
                </ak-role-permission-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">
                    ${msg("Assign permission")}
                </button>
            </ak-forms-modal>
        `;
    }

    protected renderToolbarSelected(): SlottedTemplateResult {
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
