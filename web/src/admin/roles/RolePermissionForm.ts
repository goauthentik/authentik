import "#admin/rbac/PermissionSelectForm";
import "#components/ak-toggle-group";
import "#elements/chips/Chip";
import "#elements/chips/ChipGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/Radio";
import "#elements/forms/SearchSelect/index";

import { DEFAULT_CONFIG } from "#common/api/config";

import { AKFormSubmitEvent } from "#elements/forms/Form";
import { ModelForm } from "#elements/forms/ModelForm";
import { renderModal } from "#elements/modals/utils";

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

    protected openSelectPermissionsModal = () => {
        return renderModal(html`
            <ak-form
                headline=${msg("Select permissions to assign")}
                action-label=${msg("Confirm")}
                @submit=${(event: AKFormSubmitEvent<Permission[]>) => {
                    this.permissionsToAdd = event.target.toJSON();
                }}
                ><ak-rbac-permission-select-form></ak-rbac-permission-select-form>
            </ak-form>
        `);
    };

    protected override renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${msg("Permissions to add")} name="permissions">
                <div class="pf-c-input-group">
                    <button
                        class="pf-c-button pf-m-control"
                        type="button"
                        @click=${this.openSelectPermissionsModal}
                    >
                        <pf-tooltip position="top" content=${msg("Select permissions")}>
                            <i class="fas fa-plus" aria-hidden="true"></i>
                        </pf-tooltip>
                    </button>

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
