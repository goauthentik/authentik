import "#admin/rbac/PermissionSelectModal";
import "#components/ak-toggle-group";
import "#elements/chips/Chip";
import "#elements/chips/ChipGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/Radio";
import "#elements/forms/SearchSelect/index";

import { DEFAULT_CONFIG } from "#common/api/config";

import { ModelForm } from "#elements/forms/ModelForm";

import { Permission, RbacApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

interface UserPermissionAssign {
    permissions: string[];
}

@customElement("ak-user-permission-form")
export class UserPermissionForm extends ModelForm<UserPermissionAssign, number> {
    @state()
    permissionsToAdd: Permission[] = [];

    @property({ type: Number })
    userId?: number;

    async load(): Promise<void> {}

    loadInstance(): Promise<UserPermissionAssign> {
        throw new Error("Method not implemented.");
    }

    getSuccessMessage(): string {
        return msg("Successfully assigned permission.");
    }

    async send(data: UserPermissionAssign) {
        await new RbacApi(DEFAULT_CONFIG).rbacPermissionsAssignedByUsersAssign({
            id: this.userId || 0,
            permissionAssignRequest: {
                permissions: data.permissions,
            },
        });
        this.permissionsToAdd = [];
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${msg("Permissions to add")} name="permissions">
                <div class="pf-c-input-group">
                    <ak-rbac-permission-select-table
                        .confirm=${(items: Permission[]) => {
                            this.permissionsToAdd = items;
                            this.requestUpdate();
                            return Promise.resolve();
                        }}
                    >
                        <button slot="trigger" class="pf-c-button pf-m-control" type="button">
                            <pf-tooltip position="top" content=${msg("Select permissions")}>
                                <i class="fas fa-plus" aria-hidden="true"></i>
                            </pf-tooltip>
                        </button>
                    </ak-rbac-permission-select-table>
                    <div class="pf-c-form-control">
                        <ak-chip-group>
                            ${this.permissionsToAdd.map((permission) => {
                                return html`<ak-chip
                                    removable
                                    value=${`${permission.appLabel}.${permission.codename}`}
                                    @remove=${() => {
                                        const idx = this.permissionsToAdd.indexOf(permission);
                                        this.permissionsToAdd.splice(idx, 1);
                                        this.requestUpdate();
                                    }}
                                >
                                    ${permission.name}
                                </ak-chip>`;
                            })}
                        </ak-chip-group>
                    </div>
                </div>
            </ak-form-element-horizontal>
        </form>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-permission-form": UserPermissionForm;
    }
}
