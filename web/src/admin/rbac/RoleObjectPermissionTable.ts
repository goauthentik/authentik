import "#admin/rbac/RoleObjectPermissionForm";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import type { Pagination } from "@goauthentik/api";
import {
    PaginatedPermissionList,
    RbacApi,
    RbacPermissionsAssignedByRolesListModelEnum,
    RoleAssignedObjectPermission,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

const FALLBACK_PAGINATED_RESPONSE: { pagination: Pagination; results: [] } = {
    pagination: {
        next: 0,
        previous: 0,
        count: 0,
        current: 1,
        totalPages: 1,
        startIndex: 0,
        endIndex: 0,
    },
    results: [],
};

@customElement("ak-rbac-role-object-permission-table")
export class RoleAssignedObjectPermissionTable extends Table<RoleAssignedObjectPermission> {
    @property()
    model?: RbacPermissionsAssignedByRolesListModelEnum;

    @property()
    objectPk?: string | number;

    @state()
    modelPermissions?: PaginatedPermissionList;

    checkbox = true;
    clearOnRefresh = true;

    protected override searchEnabled = true;

    async apiEndpoint(): Promise<PaginatedResponse<RoleAssignedObjectPermission>> {
        if (!this.objectPk || !this.model) {
            return FALLBACK_PAGINATED_RESPONSE;
        }
        const perms = await new RbacApi(DEFAULT_CONFIG).rbacPermissionsAssignedByRolesList({
            ...(await this.defaultEndpointConfig()),
            model: this.model,
            objectPk: this.objectPk.toString(),
        });
        const [appLabel, modelName] = this.model.split(".");
        const modelPermissions = await new RbacApi(DEFAULT_CONFIG).rbacPermissionsList({
            contentTypeModel: modelName,
            contentTypeAppLabel: appLabel,
            ordering: "codename",
        });
        modelPermissions.results = modelPermissions.results.filter((value) => {
            return value.codename !== `add_${modelName}`;
        });
        this.modelPermissions = modelPermissions;
        this.requestUpdate("columns");
        return perms;
    }

    @state()
    protected get columns(): TableColumn[] {
        const permissions = this.modelPermissions?.results ?? [];

        return [
            [msg("Role"), "role"],
            // We don't check pagination since models shouldn't need to have that many permissions?
            ...permissions.map(({ name, codename }): TableColumn => [name, codename]),
        ];
    }

    renderObjectCreate(): TemplateResult {
        return html`<ak-forms-modal>
            <span slot="submit">${msg("Assign")}</span>
            <span slot="header">${msg("Assign permission to role")}</span>
            <ak-rbac-role-object-permission-form
                model=${ifDefined(this.model)}
                objectPk=${ifDefined(this.objectPk)}
                slot="form"
            >
            </ak-rbac-role-object-permission-form>
            <button slot="trigger" class="pf-c-button pf-m-primary">
                ${msg("Assign role permissions")}
            </button>
        </ak-forms-modal>`;
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${msg("Permission(s)")}
            .objects=${this.selectedElements}
            .metadata=${(item: RoleAssignedObjectPermission) => {
                return [{ key: msg("Permission"), value: item.name }];
            }}
            .delete=${(item: RoleAssignedObjectPermission) => {
                return new RbacApi(
                    DEFAULT_CONFIG,
                ).rbacPermissionsAssignedByRolesUnassignPartialUpdate({
                    uuid: item.rolePk,
                    patchedPermissionAssignRequest: {
                        objectPk: this.objectPk?.toString(),
                        model: this.model,
                        permissions: item.objectPermissions.map((perm) => {
                            return `${perm.appLabel}.${perm.codename}`;
                        }),
                    },
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete Object Permission")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    row(item: RoleAssignedObjectPermission): SlottedTemplateResult[] {
        const baseRow = [html` <a href="#/identity/roles/${item.rolePk}">${item.name}</a>`];
        this.modelPermissions?.results.forEach((perm) => {
            const assignedToModel = item.modelPermissions.some(
                (uperm) => uperm.codename === perm.codename,
            );
            const assignedToObject = item.objectPermissions.some(
                (uperm) => uperm.codename === perm.codename,
            );

            let tooltip: string | null = null;
            if (assignedToModel && assignedToObject) {
                tooltip = msg("Global and object permission");
            } else if (assignedToModel) {
                tooltip = msg("Global permission");
            } else if (assignedToObject) {
                tooltip = msg("Object permission");
            }
            baseRow.push(
                html`${tooltip
                    ? html`<pf-tooltip position="top" content=${tooltip}
                          ><i class="fas fa-check pf-m-success" aria-hidden="true"></i
                      ></pf-tooltip>`
                    : html`<i class="fas fa-times pf-m-danger" aria-hidden="true"></i>`} `,
            );
        });
        return baseRow;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-rbac-role-object-permission-table": RoleAssignedObjectPermissionTable;
    }
}
