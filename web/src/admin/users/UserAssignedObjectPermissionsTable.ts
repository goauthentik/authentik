import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { groupBy } from "@goauthentik/common/utils";
import "@goauthentik/elements/forms/DeleteBulkForm";
import { PaginatedResponse, Table, TableColumn } from "@goauthentik/elements/table/Table";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { ExtraUserObjectPermission, ModelEnum, RbacApi } from "@goauthentik/api";

@customElement("ak-user-assigned-object-permissions-table")
export class UserAssignedObjectPermissionsTable extends Table<ExtraUserObjectPermission> {
    @property({ type: Number })
    userId?: number;

    checkbox = true;
    clearOnRefresh = true;

    apiEndpoint(page: number): Promise<PaginatedResponse<ExtraUserObjectPermission>> {
        return new RbacApi(DEFAULT_CONFIG).rbacPermissionsUsersList({
            userId: this.userId || 0,
            page: page,
            ordering: this.order,
            search: this.search,
        });
    }

    groupBy(items: ExtraUserObjectPermission[]): [string, ExtraUserObjectPermission[]][] {
        return groupBy(items, (obj) => {
            return obj.appLabelVerbose;
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn("Model", "model"),
            new TableColumn("Permission", ""),
            new TableColumn("Object", ""),
            new TableColumn(""),
        ];
    }

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

    row(item: ExtraUserObjectPermission): TemplateResult[] {
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
            html`✓`,
        ];
    }
}
