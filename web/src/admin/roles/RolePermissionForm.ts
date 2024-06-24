import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/components/ak-toggle-group";
import "@goauthentik/elements/chips/Chip";
import "@goauthentik/elements/chips/ChipGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/forms/Radio";
import "@goauthentik/elements/forms/SearchSelect";
import "@goauthentik/elements/rbac/PermissionSelectModal";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import { Permission, RbacApi } from "@goauthentik/api";

interface RolePermissionAssign {
    permissions: string[];
}

@customElement("ak-role-permission-form")
export class RolePermissionForm extends ModelForm<RolePermissionAssign, number> {
    @state()
    permissionsToAdd: Permission[] = [];

    @property()
    roleUuid?: string;

    async load(): Promise<void> {}

    loadInstance(): Promise<RolePermissionAssign> {
        throw new Error("Method not implemented.");
    }

    getSuccessMessage(): string {
        return msg("Successfully assigned permission.");
    }

    async send(data: RolePermissionAssign) {
        await new RbacApi(DEFAULT_CONFIG).rbacPermissionsAssignedByRolesAssignCreate({
            uuid: this.roleUuid || "",
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
                                    .removable=${true}
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
