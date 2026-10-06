import "#admin/rbac/ak-rbac-role-object-permission-form";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "#admin/rbac/ak-rbac-model-permission-list";
import { aki } from "#common/api/client";
import { createPaginatedResponse } from "#common/api/responses";

import { ModalInvokerButton } from "#elements/dialogs";
import { toAdminInterface } from "#elements/router/core/interfaces";
import type { FilterOption } from "#elements/table/ak-table-filter-select";
import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import type { PermissionDisplay } from "#admin/rbac/ak-rbac-model-permission-list";
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

const byName = (a: PermissionDisplay, b: PermissionDisplay) =>
    a.name.localeCompare(b.name, undefined, { sensitivity: "base" });

const activeFirst = (a: PermissionDisplay, b: PermissionDisplay) =>
    Number(b.active) - Number(a.active) || byName(a, b);

const permissionSorting = ["default", "activefirst", "activeonly"] as const;

type PermissionSorting = (typeof permissionSorting)[number];

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

    @property({ attribute: "sort-filter", reflect: true })
    public sortFilter: PermissionSorting = "default";

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

        const [permsResult, modelPermissionsResult] = await Promise.allSettled([
            permsPromise,
            modelPermissionsPromise,
        ]);

        if (permsResult.status !== "fulfilled" || modelPermissionsResult.status !== "fulfilled") {
            this.modelPermissions = undefined;

            return createPaginatedResponse([]);
        }

        const modelPermissions = modelPermissionsResult.value;
        const addModelName = `add_${modelName}`;

        modelPermissions.results = modelPermissions.results.filter(
            ({ codename }) => codename !== addModelName,
        );

        this.modelPermissions = modelPermissions;

        return permsResult.value;
    }

    @state()
    protected get columns(): TableColumn[] {
        return [
            [msg("Role", { id: "permissions.table-column.role" }), "role"],
            // We don't check pagination since models shouldn't need to have that many permissions?
            [msg("Permissions", { id: "permissions.table-column.permissions" }), "permissions"],
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

    renderToolbarAfter() {
        // prettier-ignore
        const sortOptions: { label: string, value: PermissionSorting }[] = [
            { label: msg("By name", { id: "permission.sort.default" }), value: "default" },
            { label: msg("Active first", { id: "permissions.sort.active-first" }), value: "activefirst" },
            { label: msg("Active only", { id: "permissions.sort.active-only" }), value: "activeonly" },
        ];

        return html`<div class="pf-c-toolbar__group pf-m-filter-group">
            <div class="pf-c-toolbar__item pf-m-search-filter">
                <ak-table-filter-select
                    .options=${sortOptions}
                    group=${msg("Sort and filter", { id: "permissions.filter.show-active" })}
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

            const tooltip = match([assignedToModel, assignedToObject])
                .with([true, true], () =>
                    msg("Global and object permission", { id: "permissions.kind.universal" }),
                )
                .with([true, false], () =>
                    msg("Global permission", { id: "permissions.kind.global" }),
                )
                .with([false, true], () =>
                    msg("Object permission", { id: "permissions.kind.object" }),
                )
                .otherwise(() => null);

            return { name, kind: tooltip, active: Boolean(tooltip) };
        });

        console.log(this.sortFilter);

        permissions = match(this.sortFilter)
            .with("default", () => permissions)
            .with("activefirst", () => permissions.toSorted(activeFirst))
            .with("activeonly", () => permissions.filter(({ active }) => active))
            .exhaustive();

        return [
            html` <a
                class="pf-c-rbac-table-link"
                href=${toAdminInterface(`identity/roles/${item.rolePk}`)}
                >${item.name}</a
            >`,
            html` <ak-rbac-model-permission-list
                .items=${permissions}
            ></ak-rbac-model-permission-list>`,
        ];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-rbac-role-object-permission-table": RoleAssignedObjectPermissionTable;
    }
}
