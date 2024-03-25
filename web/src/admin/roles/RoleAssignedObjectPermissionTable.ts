import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { groupBy } from "@goauthentik/common/utils";
import "@goauthentik/elements/forms/DeleteBulkForm";
import { PaginatedResponse, Table, TableColumn } from "@goauthentik/elements/table/Table";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { ExtraRoleObjectPermission, ModelEnum, RbacApi } from "@goauthentik/api";

@customElement("ak-role-assigned-object-permissions-table")
export class RoleAssignedObjectPermissionTable extends Table<ExtraRoleObjectPermission> {
    @property()
    roleUuid?: string;

    searchEnabled(): boolean {
        return true;
    }

    checkbox = true;
    clearOnRefresh = true;

    apiEndpoint(page: number): Promise<PaginatedResponse<ExtraRoleObjectPermission>> {
        return new RbacApi(DEFAULT_CONFIG).rbacPermissionsRolesList({
            uuid: this.roleUuid || "",
            page: page,
            ordering: this.order,
            search: this.search,
        });
    }

    groupBy(items: ExtraRoleObjectPermission[]): [string, ExtraRoleObjectPermission[]][] {
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
            .metadata=${(item: ExtraRoleObjectPermission) => {
                return [
                    { key: msg("Permission"), value: item.name },
                    { key: msg("Object"), value: item.objectDescription || item.objectPk },
                ];
            }}
            .delete=${(item: ExtraRoleObjectPermission) => {
                return new RbacApi(
                    DEFAULT_CONFIG,
                ).rbacPermissionsAssignedByRolesUnassignPartialUpdate({
                    uuid: this.roleUuid || "",
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

    row(item: ExtraRoleObjectPermission): TemplateResult[] {
        return [
            html`${item.modelVerbose}`,
            html`${item.name}`,
            html`${item.objectDescription
                ? html`${item.objectDescription}`
                : html`<pf-tooltip
                      position="top"
                      content=${msg(
                          "Role doesn't have view permission so description cannot be retrieved.",
                      )}
                  >
                      <pre>${item.objectPk}</pre>
                  </pf-tooltip>`}`,
            html`✓`,
        ];
    }
}
