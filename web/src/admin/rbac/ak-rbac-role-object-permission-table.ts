import "#admin/rbac/ak-rbac-role-object-permission-form";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "#admin/roles/ak-model-permissions-card";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";
import { aki } from "#common/api/client";
import { createPaginatedResponse } from "#common/api/responses";

import { ModalInvokerButton } from "#elements/dialogs";
import { toAdminInterface } from "#elements/router/core/interfaces";
import type { FilterOption } from "#elements/table/ak-table-filter-select";
import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { RoleObjectPermissionForm } from "#admin/rbac/ak-rbac-role-object-permission-form";

import {
    ModelEnum,
    PaginatedPermissionList,
    RbacApi,
    RoleAssignedObjectPermission,
} from "@goauthentik/api";

import { match } from "ts-pattern";

import { msg } from "@lit/localize";
import { css, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";

type PermissionDisplay = { name: string; kind: string | null };

const showOptions = [
    { label: msg("Active permissions", { id: "permissions.show.active-only" }), value: true },
    { label: msg("All permissions", { id: "permissions.show.all-permissions" }), value: false },
];

// prettier-ignore
const sortOptions = [
    { label: msg("Active permissions first", { id: "permissions,sort.active-first" }), value: true },
    { label: msg("Strict alphabetical order", { id: "permissions.sort.lexical" }), value: false },
];

const sortPermissions = (a: PermissionDisplay, b: PermissionDisplay) => {
    console.log(a.name, b.name);

    return a.name.toLowerCase().localeCompare(b.name.toLowerCase());
};

@customElement("ak-rbac-role-object-permission-table")
export class RoleAssignedObjectPermissionTable extends Table<RoleAssignedObjectPermission> {
    static readonly styles = [
        ...Table.styles,
        css`
            .pf-c-rbac-table-link {
                word-break: normal;
            }
        `,
    ];

    @property({ type: String })
    public model: ModelEnum | null = null;

    // TODO: Switch this to attribute-casing when we all the RBAC components are settled.
    @property({ type: String, attribute: "objectPk" })
    public objectPk: string | null = null;

    @property({ type: Boolean, attribute: "active-only", reflect: true })
    public showActiveOnly = false;

    @property({ type: Boolean, attribute: "active-first", reflect: true })
    public sortActiveFirst = false;

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

        const perms = await aki(RbacApi).rbacPermissionsAssignedByRolesList({
            ...(await this.defaultEndpointConfig()),
            model: this.model,
            objectPk: this.objectPk.toString(),
        });

        const [appLabel, modelName] = this.model.split(".");

        const modelPermissions = await aki(RbacApi).rbacPermissionsList({
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
        return [
            [msg("Role"), "role"],
            // We don't check pagination since models shouldn't need to have that many permissions?
            [msg("Permissions"), "permissions"],
        ];
    }

    protected override renderObjectCreate(): SlottedTemplateResult {
        return ModalInvokerButton(RoleObjectPermissionForm, {
            model: this.model,
            objectPk: this.objectPk,
        });
    }

    protected toggleShowActive = (ev: CustomEvent<FilterOption<boolean>>) => {
        this.showActiveOnly = ev.detail.value;
    };

    protected toggleSortActive = (ev: CustomEvent<FilterOption<boolean>>) => {
        this.sortActiveFirst = ev.detail.value;
    };

    renderToolbarAfter() {
        return html`<div class="pf-c-toolbar__group pf-m-filter-group">
            <div class="pf-c-toolbar__item pf-m-search-filter">
                <ak-table-filter-select
                    .options=${showOptions}
                    group=${msg("Show Active")}
                    .value=${this.showActiveOnly}
                    @change=${this.toggleShowActive}
                ></ak-table-filter-select>
            </div>
            <div class="pf-c-toolbar__item pf-m-search-filter">
                <ak-table-filter-select
                    .options=${sortOptions}
                    group=${msg("Active First")}
                    .value=${this.sortActiveFirst}
                    @change=${this.toggleSortActive}
                ></ak-table-filter-select>
            </div>
        </div>`;
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
                return aki(RbacApi).rbacPermissionsAssignedByRolesUnassignPartialUpdate({
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
        let permissions = this.modelPermissions?.results
            .map(({ name, codename }) => {
                const assignedToModel = item.modelPermissions.some(
                    (uPerm) => uPerm.codename === codename,
                );

                const assignedToObject = item.objectPermissions
                    .filter((uPerm) => uPerm.objectPk === this.objectPk)
                    .some((uPerm) => uPerm.codename === codename);

                const tooltip = match([assignedToModel, assignedToObject])
                    .with([true, true], () => msg("Global and object permission"))
                    .with([true, false], () => msg("Global permission"))
                    .with([false, true], () => msg("Object permission"))
                    .otherwise(() => null);

                return { name, kind: tooltip };
            })
            .toSorted(sortPermissions);

        if (!permissions) {
            return [];
        }

        if (this.showActiveOnly) {
            permissions = permissions.filter(({ kind }) => Boolean(kind));
        }

        if (this.sortActiveFirst && !this.showActiveOnly) {
            const activePermissions = permissions
                .filter(({ kind }) => Boolean(kind))
                .toSorted(sortPermissions);

            const inactivePermissions = permissions
                .filter(({ kind }) => !kind)
                .toSorted(sortPermissions);

            permissions = [...activePermissions, ...inactivePermissions];
        }

        return [
            html` <a
                class="pf-c-rbac-table-link"
                href=${toAdminInterface(`identity/roles/${item.rolePk}`)}
                >${item.name}</a
            >`,
            html` <ak-model-permissions-card .items=${permissions}></ak-model-permissions-card>`,
        ];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-rbac-role-object-permission-table": RoleAssignedObjectPermissionTable;
    }
}
