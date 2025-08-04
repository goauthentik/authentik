import "#elements/forms/DeleteBulkForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";
import { groupBy } from "#common/utils";

import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";

import { ExtraRoleObjectPermission, ModelEnum, RbacApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-role-assigned-object-permissions-table")
export class RoleAssignedObjectPermissionTable extends Table<ExtraRoleObjectPermission> {
    @property()
    public roleUuid?: string;

    protected override searchEnabled(): boolean {
        return true;
    }

    public override checkbox = true;
    public override clearOnRefresh = true;

    protected async apiEndpoint(): Promise<PaginatedResponse<ExtraRoleObjectPermission>> {
        return new RbacApi(DEFAULT_CONFIG).rbacPermissionsRolesList({
            ...(await this.defaultEndpointConfig()),
            uuid: this.roleUuid || "",
        });
    }

    public override groupBy(
        items: ExtraRoleObjectPermission[],
    ): [string, ExtraRoleObjectPermission[]][] {
        return groupBy(items, (obj) => {
            return obj.appLabelVerbose;
        });
    }

    protected columns(): TableColumn[] {
        return [
            new TableColumn(msg("Model"), "model"),
            new TableColumn(msg("Permission"), ""),
            new TableColumn(msg("Object"), ""),
            new TableColumn(""),
        ];
    }

    protected override renderToolbarSelected(): TemplateResult {
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

    protected row(item: ExtraRoleObjectPermission): TemplateResult[] {
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
            html`<i class="fas fa-check pf-m-success"></i>`,
        ];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-role-assigned-object-permissions-table": RoleAssignedObjectPermissionTable;
    }
}
