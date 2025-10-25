import "#admin/rbac/UserObjectPermissionForm";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import {
    PaginatedPermissionList,
    RbacApi,
    RbacPermissionsAssignedByUsersListModelEnum,
    UserAssignedObjectPermission,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-rbac-user-object-permission-table")
export class UserAssignedObjectPermissionTable extends Table<UserAssignedObjectPermission> {
    @property()
    model?: RbacPermissionsAssignedByUsersListModelEnum;

    @property()
    objectPk?: string | number;

    @state()
    modelPermissions?: PaginatedPermissionList;

    checkbox = true;
    clearOnRefresh = true;

    async apiEndpoint(): Promise<PaginatedResponse<UserAssignedObjectPermission>> {
        const perms = await new RbacApi(DEFAULT_CONFIG).rbacPermissionsAssignedByUsersList({
            ...(await this.defaultEndpointConfig()),
            // TODO: better default
            model: this.model || RbacPermissionsAssignedByUsersListModelEnum.AuthentikCoreUser,
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
            <span slot="header">${msg("Assign permission to user")}</span>
            <ak-rbac-user-object-permission-form
                model=${ifDefined(this.model)}
                objectPk=${ifDefined(this.objectPk)}
                slot="form"
            >
            </ak-rbac-user-object-permission-form>
            <button slot="trigger" class="pf-c-button pf-m-primary">
                ${msg("Assign to new user")}
            </button>
        </ak-forms-modal>`;
    }

    renderToolbarSelected(): TemplateResult {
        const disabled =
            this.selectedElements.length < 1 ||
            this.selectedElements.filter((item) => item.isSuperuser).length > 0;
        return html`<ak-forms-delete-bulk
            objectLabel=${msg("Permission(s)")}
            .objects=${this.selectedElements.filter((item) => !item.isSuperuser)}
            .metadata=${(item: UserAssignedObjectPermission) => {
                return [{ key: msg("Permission"), value: item.name }];
            }}
            .delete=${(item: UserAssignedObjectPermission) => {
                if (item.isSuperuser) {
                    return Promise.resolve();
                }
                return new RbacApi(
                    DEFAULT_CONFIG,
                ).rbacPermissionsAssignedByUsersUnassignPartialUpdate({
                    id: item.pk,
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

    row(item: UserAssignedObjectPermission): SlottedTemplateResult[] {
        const baseRow = [html` <a href="#/identity/users/${item.pk}"> ${item.username} </a> `];
        this.modelPermissions?.results.forEach((perm) => {
            let cell = html`<i class="fas fa-times pf-m-danger" aria-hidden="true"></i>`;
            if (item.permissions.filter((uperm) => uperm.codename === perm.codename).length > 0) {
                cell = html`<pf-tooltip position="top" content=${msg("Directly assigned")}
                    ><i class="fas fa-check pf-m-success" aria-hidden="true"></i
                ></pf-tooltip>`;
            } else if (item.isSuperuser) {
                cell = html`<pf-tooltip position="top" content=${msg("Superuser")}
                    ><i class="fas fa-check pf-m-success" aria-hidden="true"></i
                ></pf-tooltip>`;
            }
            baseRow.push(cell);
        });
        return baseRow;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-rbac-user-object-permission-table": UserAssignedObjectPermissionTable;
    }
}
