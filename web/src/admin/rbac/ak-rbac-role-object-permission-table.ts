import "#admin/rbac/ak-rbac-role-object-permission-form";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "#admin/rbac/ak-rbac-model-permissions-list";
import { aki } from "#common/api/client";
import { createPaginatedResponse } from "#common/api/responses";

import { ModalInvokerButton } from "#elements/dialogs";
import { toAdminInterface } from "#elements/router/core/interfaces";
import type { FilterOption } from "#elements/table/ak-table-filter-select";
import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import type { PermissionDisplay } from "#admin/rbac/ak-rbac-model-permissions-list";
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

const permissionSorting = ["by-name", "assignedfirst", "assignedonly"] as const;

type PermissionSorting = (typeof permissionSorting)[number];

const byName = (a: PermissionDisplay, b: PermissionDisplay) =>
    a.name.localeCompare(b.name, undefined, { sensitivity: "base" });

const assignedFirst = (a: PermissionDisplay, b: PermissionDisplay) =>
    Number(Boolean(b.scope)) - Number(Boolean(a.scope)) || byName(a, b);

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

    @property({ attribute: "sort-filter", reflect: true })
    public sortFilter: PermissionSorting = "by-name";

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

        const permsPromise = aki(RbacApi).rbacPermissionsAssignedByRolesList({
            ...(await this.defaultEndpointConfig()),
            model: this.model,
            objectPk: this.objectPk.toString(),
        });

        const [appLabel, modelName] = this.model.split(".");

        const modelPermissionsPromise = aki(RbacApi).rbacPermissionsList({
            contentTypeModel: modelName,
            contentTypeAppLabel: appLabel,
            ordering: "name",
        });

        const [permsResult, modelPermissions] = await Promise.all([
            permsPromise,
            modelPermissionsPromise,
        ]);

        const addModelName = `add_${modelName}`;

        modelPermissions.results = modelPermissions.results.filter(
            ({ codename }) => codename !== addModelName,
        );

        this.modelPermissions = modelPermissions;

        return permsResult;
    }

    @state()
    protected get columns(): TableColumn[] {
        return [
            [msg("Role", { id: "permissions.table-column.role" }), "name"],
            // We don't check pagination since models shouldn't need to have that many permissions?
            [msg("Permissions", { id: "permissions.table-column.permissions" })],
        ];
    }

    protected override renderObjectCreate(): SlottedTemplateResult {
        return ModalInvokerButton(RoleObjectPermissionForm, {
            model: this.model,
            objectPk: this.objectPk,
        });
    }

    protected onSortChange = (ev: CustomEvent<FilterOption<PermissionSorting>>) => {
        this.sortFilter = ev.detail.value;
    };

    protected override renderToolbarAfter(): SlottedTemplateResult {
        // prettier-ignore
        const sortOptions: { label: string, value: PermissionSorting }[] = [
            { label: msg("By name", { id: "permission.sort.by-name" }), value: "by-name" },
            { label: msg("Assigned first", { id: "permissions.sort.assigned-first" }), value: "assignedfirst" },
            { label: msg("Assigned only", { id: "permissions.sort.assigned-only" }), value: "assignedonly" },
        ];

        return html`<div class="pf-c-toolbar__group pf-m-filter-group">
            <div class="pf-c-toolbar__item pf-m-search-filter">
                <ak-table-filter-select
                    .options=${sortOptions}
                    group=${msg("Sort and filter", { id: "permissions.filter.show-assigned" })}
                    .value=${this.sortFilter}
                    @change=${this.onSortChange}
                ></ak-table-filter-select>
            </div>
        </div>`;
    }

    protected override renderToolbarSelected(): SlottedTemplateResult {
        const disabled = this.selectedElements.length < 1;

        return html`<ak-forms-delete-bulk
            object-label=${msg("Permission(s)", { id: "permissions.delete.label" })}
            .objects=${this.selectedElements}
            .metadata=${(item: RoleAssignedObjectPermission) => [
                {
                    key: msg("Permission", { id: "permissions.delete.meta-data" }),
                    value: item.name,
                },
            ]}
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
                ${msg("Delete object permission", { id: "permissions.delete.button" })}
            </button>
        </ak-forms-delete-bulk>`;
    }

    protected override row(item: RoleAssignedObjectPermission): SlottedTemplateResult[] {
        const allPermissions = this.modelPermissions?.results ?? [];
        const { objectPk } = this;
        const modelPermissions = new Set(item.modelPermissions.map(({ codename }) => codename));

        const objectPermissions = new Set(
            item.objectPermissions
                .filter(({ objectPk: pk }) => pk === objectPk)
                .map(({ codename }) => codename),
        );

        let permissions = allPermissions.map(({ name, codename }) => {
            const assignedToModel = modelPermissions.has(codename);
            const assignedToObject = objectPermissions.has(codename);

            const scope = match([assignedToModel, assignedToObject])
                .with([true, true], () => "both")
                .with([true, false], () => "global")
                .with([false, true], () => "object")
                .otherwise(() => null);

            return { name, scope };
        });

        permissions = match(this.sortFilter)
            .with("by-name", () => permissions)
            .with("assignedfirst", () => permissions.toSorted(assignedFirst))
            .with("assignedonly", () => permissions.filter(({ scope }) => !!scope))
            .exhaustive();

        return [
            html` <a
                class="pf-c-rbac-table-link"
                href=${toAdminInterface(`identity/roles/${item.rolePk}`)}
                >${item.name}</a
            >`,
            html` <ak-rbac-model-permissions-list
                .items=${permissions}
            ></ak-rbac-model-permissions-list>`,
        ];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-rbac-role-object-permission-table": RoleAssignedObjectPermissionTable;
    }
}
