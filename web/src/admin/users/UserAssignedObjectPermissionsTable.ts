import "#elements/forms/DeleteBulkForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";
import { groupBy } from "#common/utils";

import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { ExtraUserObjectPermission, ModelEnum, RbacApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-user-assigned-object-permissions-table")
export class UserAssignedObjectPermissionsTable extends Table<ExtraUserObjectPermission> {
    @property({ type: Number })
    userId?: number;

    checkbox = true;
    clearOnRefresh = true;

    async apiEndpoint(): Promise<PaginatedResponse<ExtraUserObjectPermission>> {
        return new RbacApi(DEFAULT_CONFIG).rbacPermissionsUsersList({
            ...(await this.defaultEndpointConfig()),
            userId: this.userId || 0,
        });
    }

    groupBy(items: ExtraUserObjectPermission[]): [string, ExtraUserObjectPermission[]][] {
        return groupBy(items, (obj) => {
            return obj.appLabelVerbose;
        });
    }

    protected columns: TableColumn[] = [
        [msg("Model"), "model"],
        [msg("Permission"), ""],
        [msg("Object"), ""],
        [""],
    ];

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${msg("Permission(s)")}
            .objects=${this.selectedElements}
            .metadata=${(item: ExtraUserObjectPermission) => {
                return [
                    { key: msg("Permission"), value: item.name },
                    { key: msg("Object"), value: item.objectDescription || item.objectPk },
                ];
            }}
            .delete=${(item: ExtraUserObjectPermission) => {
                return new RbacApi(
                    DEFAULT_CONFIG,
                ).rbacPermissionsAssignedByUsersUnassignPartialUpdate({
                    id: this.userId || 0,
                    patchedPermissionAssignRequest: {
                        permissions: [`${item.appLabel}.${item.codename}`],
                        objectPk: item.objectPk,
                        model: `${item.appLabel}.${item.model}` as ModelEnum,
                    },
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    row(item: ExtraUserObjectPermission): SlottedTemplateResult[] {
        return [
            html`${item.modelVerbose}`,
            html`${item.name}`,
            html`${item.objectDescription
                ? html`${item.objectDescription}`
                : html`<pf-tooltip
                      position="top"
                      content=${msg(
                          "User doesn't have view permission so description cannot be retrieved.",
                      )}
                  >
                      <pre>${item.objectPk}</pre>
                  </pf-tooltip>`}`,
            html`<i class="fas fa-check pf-m-success" aria-hidden="true"></i>`,
        ];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-assigned-object-permissions-table": UserAssignedObjectPermissionsTable;
    }
}
