import { InitialPermissionsModeToLabel } from "@goauthentik/admin/rbac/utils";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/elements/ak-dual-select/ak-dual-select-provider";
import { DataProvision, DualSelectPair } from "@goauthentik/elements/ak-dual-select/types";
import "@goauthentik/elements/chips/Chip";
import "@goauthentik/elements/chips/ChipGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/forms/SearchSelect";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import {
    InitialPermissions,
    InitialPermissionsModeEnum,
    Permission,
    RbacApi,
    RbacRolesListRequest,
    Role,
} from "@goauthentik/api";

export function rbacPermissionPair(item: Permission): DualSelectPair {
    return [item.id.toString(), html`<div class="selection-main">${item.name}</div>`, item.name];
}

@customElement("ak-initial-permissions-form")
export class InitialPermissionsForm extends ModelForm<InitialPermissions, string> {
    loadInstance(pk: string): Promise<InitialPermissions> {
        return new RbacApi(DEFAULT_CONFIG).rbacInitialPermissionsRetrieve({
            id: Number(pk),
        });
    }

    getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated initial permissions.")
            : msg("Successfully created initial permissions.");
    }

    async send(data: InitialPermissions): Promise<InitialPermissions> {
        if (this.instance?.pk) {
            return new RbacApi(DEFAULT_CONFIG).rbacInitialPermissionsPartialUpdate({
                id: this.instance.pk,
                patchedInitialPermissionsRequest: data,
            });
        }
        return new RbacApi(DEFAULT_CONFIG).rbacInitialPermissionsCreate({
            initialPermissionsRequest: data,
        });
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${msg("Name")} required name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Role")} required name="role">
                <ak-search-select
                    .fetchObjects=${async (query?: string): Promise<Role[]> => {
                        const args: RbacRolesListRequest = {
                            ordering: "name",
                        };
                        if (query !== undefined) {
                            args.search = query;
                        }
                        const users = await new RbacApi(DEFAULT_CONFIG).rbacRolesList(args);
                        return users.results;
                    }}
                    .renderElement=${(role: Role): string => {
                        return role.name;
                    }}
                    .renderDescription=${(role: Role): TemplateResult => {
                        return html`${role.name}`;
                    }}
                    .value=${(role: Role | undefined): string | undefined => {
                        return role?.pk;
                    }}
                    .selected=${(role: Role): boolean => {
                        return this.instance?.role === role.pk;
                    }}
                >
                </ak-search-select>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "When a user with the selected Role creates an object, the Initial Permissions will be applied to that object.",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Mode")} required name="mode">
                <select class="pf-c-form-control">
                    <option
                        value=${InitialPermissionsModeEnum.User}
                        ?selected=${this.instance?.mode === InitialPermissionsModeEnum.User}
                    >
                        ${InitialPermissionsModeToLabel(InitialPermissionsModeEnum.User)}
                    </option>
                    <option
                        value=${InitialPermissionsModeEnum.Role}
                        ?selected=${this.instance?.mode === InitialPermissionsModeEnum.Role}
                    >
                        ${InitialPermissionsModeToLabel(InitialPermissionsModeEnum.Role)}
                    </option>
                </select>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "The Initial Permissions can either be placed on the User creating the object, or the Role selected in the previous field.",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Permissions")} name="permissions">
                <ak-dual-select-provider
                    .provider=${(page: number, search?: string): Promise<DataProvision> => {
                        return new RbacApi(DEFAULT_CONFIG)
                            .rbacPermissionsList({
                                page: page,
                                search: search,
                            })
                            .then((results) => {
                                return {
                                    pagination: results.pagination,
                                    options: results.results.map(rbacPermissionPair),
                                };
                            });
                    }}
                    .selected=${(this.instance?.permissionsObj ?? []).map(rbacPermissionPair)}
                    available-label="${msg("Available Permissions")}"
                    selected-label="${msg("Selected Permissions")}"
                ></ak-dual-select-provider>
                <p class="pf-c-form__helper-text">
                    ${msg("Permissions to grant when a new object is created.")}
                </p>
            </ak-form-element-horizontal>
        </form>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-initial-permissions-form": InitialPermissionsForm;
    }
}
