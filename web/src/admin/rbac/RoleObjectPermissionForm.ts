import "#components/ak-toggle-group";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/Radio";
import "#elements/forms/SearchSelect/index";

import { DEFAULT_CONFIG } from "#common/api/config";
import { ActionName } from "#common/i18n/verbs";

import { ModelForm } from "#elements/forms/ModelForm";
import { SlottedTemplateResult } from "#elements/types";

import {
    ModelEnum,
    PaginatedPermissionList,
    RbacApi,
    RbacRolesListRequest,
    Role,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";

interface RoleAssignData {
    role: string;
    permissions: {
        [key: string]: boolean;
    };
}

@customElement("ak-rbac-role-object-permission-form")
export class RoleObjectPermissionForm extends ModelForm<RoleAssignData, number> {
    @property()
    model?: ModelEnum;

    @property()
    objectPk?: string;

    @state()
    modelPermissions?: PaginatedPermissionList;

    async load(): Promise<void> {
        const [appLabel, modelName] = (this.model || "").split(".");
        this.modelPermissions = await new RbacApi(DEFAULT_CONFIG).rbacPermissionsList({
            contentTypeModel: modelName,
            contentTypeAppLabel: appLabel,
            ordering: "codename",
        });
    }

    loadInstance(): Promise<RoleAssignData> {
        throw new Error("Method not implemented.");
    }

    protected override get actionName(): ActionName {
        return "assign";
    }

    protected override entityLabel = msg("Permission", { id: "entity.permission.singular" });

    send(data: RoleAssignData): Promise<unknown> {
        return new RbacApi(DEFAULT_CONFIG).rbacPermissionsAssignedByRolesAssign({
            uuid: data.role,
            permissionAssignRequest: {
                permissions: Object.keys(data.permissions).filter((key) => data.permissions[key]),
                model: this.model!,
                objectPk: this.objectPk,
            },
        });
    }

    renderForm(): SlottedTemplateResult {
        if (!this.modelPermissions) {
            return nothing;
        }
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal
                label=${msg("Role", {
                    id: "label.role.object.permission.role",
                    desc: "Label for role object permission role select",
                })}
                name="role"
            >
                <ak-search-select
                    .fetchObjects=${async (query?: string): Promise<Role[]> => {
                        const args: RbacRolesListRequest = {
                            ordering: "name",
                        };
                        if (query !== undefined) {
                            args.search = query;
                        }
                        const roles = await new RbacApi(DEFAULT_CONFIG).rbacRolesList(args);
                        return roles.results;
                    }}
                    .renderElement=${(role: Role): string => {
                        return role.name;
                    }}
                    .value=${(role: Role | undefined): string | undefined => {
                        return role?.pk;
                    }}
                >
                </ak-search-select>
            </ak-form-element-horizontal>
            ${this.modelPermissions?.results
                .filter((perm) => {
                    const [_app, model] = this.model?.split(".") || "";
                    return perm.codename !== `add_${model}`;
                })
                .map((perm) => {
                    return html` <ak-form-element-horizontal name="permissions.${perm.codename}">
                        <label class="pf-c-switch">
                            <input class="pf-c-switch__input" type="checkbox" />
                            <span class="pf-c-switch__toggle">
                                <span class="pf-c-switch__toggle-icon">
                                    <i class="fas fa-check" aria-hidden="true"></i>
                                </span>
                            </span>
                            <span class="pf-c-switch__label">${perm.name}</span>
                        </label>
                    </ak-form-element-horizontal>`;
                })}
        </form>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-rbac-role-object-permission-form": RoleObjectPermissionForm;
    }
}
