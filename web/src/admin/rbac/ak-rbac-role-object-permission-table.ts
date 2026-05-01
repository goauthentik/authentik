import "#admin/rbac/ak-rbac-role-object-permission-form";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";
import { createPaginatedResponse } from "#common/api/responses";

import { ModalInvokerButton } from "#elements/dialogs";
import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { RoleObjectPermissionForm } from "#admin/rbac/ak-rbac-role-object-permission-form";

import {
    ModelEnum,
    PaginatedPermissionList,
    RbacApi,
    RoleAssignedObjectPermission,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property, state } from "lit/decorators.js";

@customElement("ak-rbac-role-object-permission-table")
export class RoleAssignedObjectPermissionTable extends Table<RoleAssignedObjectPermission> {
    @property({ type: String })
    public model: ModelEnum | null = null;

    // TODO: Switch this to attribute-casing when we all the RBAC components are settled.
    @property({ type: String, attribute: "objectPk" })
    public objectPk: string | null = null;

    @state()
    protected modelPermissions?: PaginatedPermissionList;

    public override checkbox = true;
    public override clearOnRefresh = true;

    protected override searchEnabled = true;

    protected override async apiEndpoint(): Promise<
        PaginatedResponse<RoleAssignedObjectPermission>
    > {
        if (!this.objectPk || !this.model) {
            return createPaginatedResponse([]);
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

    protected override renderObjectCreate(): SlottedTemplateResult {
        return ModalInvokerButton(RoleObjectPermissionForm, {
            model: this.model,
            objectPk: this.objectPk,
        });
    }

    protected override renderToolbarSelected(): SlottedTemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            object-label=${msg("Permission(s)")}
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
                        model: this.model || undefined,
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

    protected override row(item: RoleAssignedObjectPermission): SlottedTemplateResult[] {
        const baseRow = [html` <a href="#/identity/roles/${item.rolePk}">${item.name}</a>`];
        this.modelPermissions?.results.forEach((perm) => {
            const assignedToModel = item.modelPermissions.some(
                (uperm) => uperm.codename === perm.codename,
            );
            const assignedToObject = item.objectPermissions
                .filter((uPerm) => uPerm.objectPk === this.objectPk)
                .some((uPerm) => uPerm.codename === perm.codename);

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
