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

interface RolePermissionAssign {
    permissions: string[];
}

@customElement("ak-role-permission-form")
export class RolePermissionForm extends ModelForm<RolePermissionAssign, number> {
    @state()
    protected permissionsToAdd: Permission[] = [];

    @property({ type: String })
    public roleUuid: string | null = null;

    public override reset(): void {
        super.reset();

        this.permissionsToAdd = [];
    }

    loadInstance(): Promise<RolePermissionAssign> {
        throw new Error("Method not implemented.");
    }

    getSuccessMessage(): string {
        return msg("Successfully assigned permission.");
    }

    async send(data: RolePermissionAssign) {
        if (!this.roleUuid) {
            return;
        }
        await new RbacApi(DEFAULT_CONFIG).rbacPermissionsAssignedByRolesAssign({
            uuid: this.roleUuid,
            permissionAssignRequest: {
                permissions: data.permissions,
            },
        });
        this.permissionsToAdd = [];
    }

    protected override renderForm(): TemplateResult {
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
        "ak-role-permission-form": RolePermissionForm;
    }
}
