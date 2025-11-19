import "#admin/users/UserPermissionForm";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";
import { groupBy } from "#common/utils";

import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { Permission, RbacApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-user-assigned-global-permissions-table")
export class UserAssignedGlobalPermissionsTable extends Table<Permission> {
    @property({ type: Number })
    userId?: number;

    checkbox = true;
    clearOnRefresh = true;

    async apiEndpoint(): Promise<PaginatedResponse<Permission>> {
        return new RbacApi(DEFAULT_CONFIG).rbacPermissionsList({
            ...(await this.defaultEndpointConfig()),
            user: this.userId || 0,
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
        ["", null, msg("Assigned to user")],
    ];

    renderObjectCreate(): TemplateResult {
        return html`
            <ak-forms-modal>
                <span slot="submit">${msg("Assign")}</span>
                <span slot="header">${msg("Assign permission to user")}</span>
                <ak-user-permission-form userId=${ifDefined(this.userId)} slot="form">
                </ak-user-permission-form>
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
            .metadata=${(item: Permission) => {
                return [{ key: msg("Permission"), value: item.name }];
            }}
            .delete=${(item: Permission) => {
                return new RbacApi(
                    DEFAULT_CONFIG,
                ).rbacPermissionsAssignedByUsersUnassignPartialUpdate({
                    id: this.userId || 0,
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
        "ak-user-assigned-global-permissions-table": UserAssignedGlobalPermissionsTable;
    }
}
