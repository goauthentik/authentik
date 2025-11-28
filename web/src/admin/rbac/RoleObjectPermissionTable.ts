import "#admin/rbac/RoleObjectPermissionForm";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

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

    async apiEndpoint(): Promise<PaginatedResponse<RoleAssignedObjectPermission>> {
        const perms = await new RbacApi(DEFAULT_CONFIG).rbacPermissionsAssignedByRolesList({
            ...(await this.defaultEndpointConfig()),
            // TODO: better default
            model: this.model || RbacPermissionsAssignedByRolesListModelEnum.AuthentikCoreUser,
            objectPk: this.objectPk?.toString(),
        });
        const [appLabel, modelName] = (this.model || "").split(".");
        const modelPermissions = await new RbacApi(DEFAULT_CONFIG).rbacPermissionsList({
            contentTypeModel: modelName,
            contentTypeAppLabel: appLabel,
            ordering: "codename",
        });
        modelPermissions.results = modelPermissions.results.filter((value) => {
            return value.codename !== `add_${this.model?.split(".")[1]}`;
        });
        this.modelPermissions = modelPermissions;
        this.requestUpdate("columns");
        return perms;
    }

    @state()
    protected get columns(): TableColumn[] {
        const permissions = this.modelPermissions?.results ?? [];

        return [
            [msg("User"), "user"],
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
                ${msg("Assign to new role")}
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
                        permissions: item.permissions.map((perm) => {
                            return `${perm.appLabel}.${perm.codename}`;
                        }),
                    },
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    row(item: RoleAssignedObjectPermission): SlottedTemplateResult[] {
        const baseRow = [html` <a href="#/identity/roles/${item.rolePk}">${item.name}</a>`];
        this.modelPermissions?.results.forEach((perm) => {
            const granted =
                item.permissions.filter((uperm) => uperm.codename === perm.codename).length > 0;
            baseRow.push(
                html`${granted
                    ? html`<pf-tooltip position="top" content=${msg("Directly assigned")}
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
