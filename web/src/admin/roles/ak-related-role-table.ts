import "#admin/roles/ak-role-form";
import "#admin/users/ak-user-role-table";
import "#components/ak-status-label";
import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/ModalForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { renderModal } from "#elements/dialogs";
import { AKFormSubmitEvent, Form } from "#elements/forms/Form";
import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";
import { ifPresent } from "#elements/utils/attributes";

import { RoleForm } from "#admin/roles/ak-role-form";

import { Group, RbacApi, Role, User } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html, nothing, PropertyValues, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

//#region Related Role Form

@customElement("ak-add-related-role-form")
export class AddRelatedRoleForm extends Form<{ roles: string[] }> {
    public static override verboseName = msg("Role");
    public static override verboseNamePlural = msg("Roles");

    #api = new RbacApi(DEFAULT_CONFIG);

    @property({ attribute: false })
    public user: User | null = null;

    @state()
    protected rolesToAdd: Role[] = [];

    getSuccessMessage(): string {
        return msg("Successfully added user to role(s).");
    }

    async send(data: { roles: string[] }): Promise<unknown> {
        await Promise.all(
            data.roles.map((role) => {
                if (!this.user) return Promise.resolve();
                return this.#api.rbacRolesAddUserCreate({
                    uuid: role,
                    userAccountSerializerForRoleRequest: {
                        pk: this.user.pk,
                    },
                });
            }),
        );
        return data;
    }

    protected openRolesSelectionModal = () => {
        return renderModal(html`
            <ak-form
                headline=${msg("Assign Additional Roles")}
                submit-label=${msg("Confirm")}
                @submit=${(event: AKFormSubmitEvent<Role[]>) => {
                    this.rolesToAdd = event.target.toJSON();
                }}
                ><ak-user-role-table></ak-user-role-table>
            </ak-form>
        `);
    };

    protected override renderForm(): TemplateResult {
        return html`<ak-form-element-horizontal label=${msg("Roles to add")} name="roles">
            <div class="pf-c-input-group">
                <button
                    class="pf-c-button pf-m-control"
                    type="button"
                    @click=${this.openRolesSelectionModal}
                >
                    <pf-tooltip position="top" content=${msg("Add role")}>
                        <i class="fas fa-plus" aria-hidden="true"></i>
                    </pf-tooltip>
                </button>
                <div class="pf-c-form-control">
                    <ak-chip-group
                        @click=${this.openRolesSelectionModal}
                        placeholder=${msg("Select one or more roles...")}
                    >
                        ${this.rolesToAdd.map((role) => {
                            return html`<ak-chip
                                removable
                                value=${ifPresent(role.pk)}
                                @remove=${() => {
                                    this.rolesToAdd = this.rolesToAdd.filter(
                                        ($role) => $role === role,
                                    );
                                }}
                            >
                                ${role.name}
                            </ak-chip>`;
                        })}
                    </ak-chip-group>
                </div>
            </div>
        </ak-form-element-horizontal>`;
    }
}

//#endregion

//#region Related Role List

@customElement("ak-related-role-table")
export class RelatedRoleTable extends Table<Role> {
    #api = new RbacApi(DEFAULT_CONFIG);

    checkbox = true;
    clearOnRefresh = true;
    protected override searchEnabled = true;

    @property({ type: String })
    public order = "name";

    @property({ attribute: false })
    public targetUser: User | null = null;

    @property({ attribute: false })
    public targetGroup: Group | null = null;

    @property({ type: Boolean })
    public showInherited = false;

    willUpdate(changedProperties: PropertyValues<this>) {
        super.willUpdate(changedProperties);
        if (changedProperties.has("showInherited")) {
            // Disable checkboxes in showInherited mode (view-only)
            this.checkbox = !this.showInherited;
        }
    }

    async apiEndpoint(): Promise<PaginatedResponse<Role>> {
        const config = await this.defaultEndpointConfig();

        if (this.targetGroup) {
            return this.#api.rbacRolesList({
                ...config,
                groups: this.targetGroup.pk,
                inherited: this.showInherited,
            });
        }

        return this.#api.rbacRolesList({
            ...config,
            users: this.targetUser?.pk,
            inherited: this.showInherited,
        });
    }

    protected get columns(): TableColumn[] {
        // Hide actions column in showInherited mode (view-only)
        if (this.showInherited) {
            return [[msg("Name"), "name"]];
        }
        return [
            [msg("Name"), "name"],
            [msg("Actions"), null, msg("Row Actions")],
        ];
    }

    protected openAddExistingRoleModal = () => {
        if (!this.targetUser) return;

        return renderModal(
            html`<ak-add-related-role-form .user=${this.targetUser}></ak-add-related-role-form>`,
        );
    };

    renderToolbarSelected(): SlottedTemplateResult {
        // Don't render Remove button in showInherited mode (view-only)
        if (this.showInherited) {
            return nothing;
        }
        const disabled = !this.selectedElements.length;
        return html`<ak-forms-delete-bulk
            object-label=${msg("Role(s)")}
            submit-label=${msg("Remove from Role(s)")}
            action-subtext=${msg(
                str`Are you sure you want to remove user ${this.targetUser?.username} from the following roles?`,
            )}
            button-label=${msg("Remove")}
            .objects=${this.selectedElements}
            .delete=${(item: Role) => {
                if (!this.targetUser) return;
                return this.#api.rbacRolesRemoveUserCreate({
                    uuid: item.pk,
                    userAccountSerializerForRoleRequest: {
                        pk: this.targetUser.pk,
                    },
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Remove")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    protected isInherited(role: Role): boolean {
        if (this.targetGroup) {
            // For groups, check if role is in direct roles
            if (!this.targetGroup.roles) return false;

            return !this.targetGroup.roles.includes(role.pk);
        }

        if (this.targetUser) {
            // For users, check if role is in direct roles

            if (!this.targetUser.roles) return false;

            return !this.targetUser.roles.includes(role.pk);
        }

        return false;
    }

    protected row(item: Role): SlottedTemplateResult[] {
        const inherited = this.showInherited && this.isInherited(item);
        const inheritedTooltip = this.targetGroup
            ? msg("Inherited from parent group")
            : msg("Inherited from group");
        const nameCell = html`<a href="#/identity/roles/${item.pk}">${item.name}</a> ${inherited
                ? html`<pf-tooltip position="top" content=${inheritedTooltip}>
                      <span class="pf-c-label pf-m-outline pf-m-cyan">
                          <span class="pf-c-label__content">&nbsp;${msg("Inherited")}</span>
                      </span>
                  </pf-tooltip>`
                : nothing}`;

        // Hide actions in showInherited mode (view-only)
        if (this.showInherited) {
            return [nameCell];
        }

        return [
            nameCell,
            html`<button
                class="pf-c-button pf-m-plain"
                type="button"
                ${RoleForm.asInstanceInvoker(item.pk)}
            >
                <pf-tooltip position="top" content=${msg("Edit")}>
                    <i class="fas fa-edit" aria-hidden="true"></i>
                </pf-tooltip>
            </button>`,
        ];
    }

    renderToolbar(): SlottedTemplateResult {
        // Hide add buttons in showInherited mode (view-only)
        if (this.showInherited || this.targetGroup) {
            return super.renderToolbar();
        }

        return [
            this.targetUser
                ? html`<button
                      type="button"
                      class="pf-c-button pf-m-primary"
                      @click=${this.openAddExistingRoleModal}
                  >
                      ${msg("Add to existing role")}
                  </button>`
                : nothing,
            html` <button
                type="button"
                class="pf-c-button pf-m-secondary"
                ${RoleForm.asModalInvoker()}
            >
                ${msg("Add new role")}
            </button>`,
            super.renderToolbar(),
        ];
    }
}

//#endregion

declare global {
    interface HTMLElementTagNameMap {
        "ak-related-role-table": RelatedRoleTable;
        "ak-add-related-role-form": AddRelatedRoleForm;
    }
}
