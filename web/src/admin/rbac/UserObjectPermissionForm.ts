import "#components/ak-toggle-group";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/Radio";
import "#elements/forms/SearchSelect/index";

import { DEFAULT_CONFIG } from "#common/api/config";

import { ModelForm } from "#elements/forms/ModelForm";
import { SlottedTemplateResult } from "#elements/types";

import {
    CoreApi,
    CoreUsersListRequest,
    ModelEnum,
    PaginatedPermissionList,
    RbacApi,
    User,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

interface UserAssignData {
    user: number;
    permissions: {
        [key: string]: boolean;
    };
}

@customElement("ak-rbac-user-object-permission-form")
export class UserObjectPermissionForm extends ModelForm<UserAssignData, number> {
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

    loadInstance(): Promise<UserAssignData> {
        throw new Error("Method not implemented.");
    }

    getSuccessMessage(): string {
        return msg("Successfully assigned permission.");
    }

    send(data: UserAssignData): Promise<unknown> {
        return new RbacApi(DEFAULT_CONFIG).rbacPermissionsAssignedByUsersAssign({
            id: data.user,
            permissionAssignRequest: {
                permissions: Object.keys(data.permissions).filter((key) => data.permissions[key]),
                model: this.model!,
                objectPk: this.objectPk!,
            },
        });
    }

    renderForm(): SlottedTemplateResult {
        if (!this.modelPermissions) {
            return nothing;
        }
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${msg("User")} name="user">
                <ak-search-select
                    .fetchObjects=${async (query?: string): Promise<User[]> => {
                        const args: CoreUsersListRequest = {
                            ordering: "username",
                        };
                        if (query !== undefined) {
                            args.search = query;
                        }
                        const users = await new CoreApi(DEFAULT_CONFIG).coreUsersList(args);
                        return users.results;
                    }}
                    .renderElement=${(user: User): string => {
                        return user.username;
                    }}
                    .renderDescription=${(user: User): TemplateResult => {
                        return html`${user.name}`;
                    }}
                    .value=${(user: User | undefined): number | undefined => {
                        return user?.pk;
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
        "ak-rbac-user-object-permission-form": UserObjectPermissionForm;
    }
}
