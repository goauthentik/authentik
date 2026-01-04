import "#admin/roles/RoleForm";
import "#admin/users/RoleSelectModal";
import "#components/ak-status-label";
import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/ModalForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { Form } from "#elements/forms/Form";
import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";
import { ifPresent } from "#elements/utils/attributes";

import { Group, RbacApi, Role, User } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html, nothing, PropertyValues, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

@customElement("ak-role-related-add")
export class RelatedRoleAdd extends Form<{ roles: string[] }> {
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
                return new RbacApi(DEFAULT_CONFIG).rbacRolesAddUserCreate({
                    uuid: role,
                    userAccountSerializerForRoleRequest: {
                        pk: this.user.pk,
                    },
                });
            }),
        );
        return data;
    }

    renderForm(): TemplateResult {
        return html`<ak-form-element-horizontal label=${msg("Roles to add")} name="roles">
            <div class="pf-c-input-group">
                <ak-user-role-select-table
                    .confirm=${(items: Role[]) => {
                        this.rolesToAdd = items;
                        return Promise.resolve();
                    }}
                >
                    <button slot="trigger" class="pf-c-button pf-m-control" type="button">
                        <pf-tooltip position="top" content=${msg("Add role")}>
                            <i class="fas fa-plus" aria-hidden="true"></i>
                        </pf-tooltip>
                    </button>
                </ak-user-role-select-table>
                <div class="pf-c-form-control">
                    <ak-chip-group>
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

@customElement("ak-role-related-list")
export class RelatedRoleList extends Table<Role> {
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

        // Handle group filtering
        if (this.targetGroup) {
            // Always fetch both direct and inherited roles
            const [directResponse, inheritedResponse] = await Promise.all([
                new RbacApi(DEFAULT_CONFIG).rbacRolesList({
                    ...config,
                    akGroups: [this.targetGroup.pk],
                }),
                new RbacApi(DEFAULT_CONFIG).rbacRolesList({
                    ...config,
                    inheritedGroupRoles: this.targetGroup.pk,
                }),
            ]);

            if (this.showInherited) {
                // Combine, deduplicate by pk, and sort alphabetically
                const allRoles = [...directResponse.results, ...inheritedResponse.results];
                const uniqueRoles = allRoles
                    .filter(
                        (role, index, self) => self.findIndex((r) => r.pk === role.pk) === index,
                    )
                    .sort((a, b) => a.name.localeCompare(b.name));
                return {
                    pagination: directResponse.pagination,
                    results: uniqueRoles,
                };
            }
            return directResponse;
        }

        // Handle user filtering - always fetch both direct and inherited roles
        const [directResponse, inheritedResponse] = await Promise.all([
            new RbacApi(DEFAULT_CONFIG).rbacRolesList({
                ...config,
                users: this.targetUser?.pk ? [this.targetUser.pk] : undefined,
            }),
            new RbacApi(DEFAULT_CONFIG).rbacRolesList({
                ...config,
                inheritedUserRoles: this.targetUser?.pk,
            }),
        ]);

        if (this.showInherited) {
            // Combine, deduplicate by pk, and sort alphabetically
            const allRoles = [...directResponse.results, ...inheritedResponse.results];
            const uniqueRoles = allRoles
                .filter((role, index, self) => self.findIndex((r) => r.pk === role.pk) === index)
                .sort((a, b) => a.name.localeCompare(b.name));
            return {
                pagination: directResponse.pagination,
                results: uniqueRoles,
            };
        }
        return directResponse;
    }

    get columns(): TableColumn[] {
        // Hide actions column in showInherited mode (view-only)
        if (this.showInherited) {
            return [[msg("Name"), "name"]];
        }
        return [
            [msg("Name"), "name"],
            [msg("Actions"), null, msg("Row Actions")],
        ];
    }

    renderToolbarSelected(): TemplateResult {
        // Don't render Remove button in showInherited mode (view-only)
        if (this.showInherited) {
            return nothing;
        }
        const disabled = !this.selectedElements.length;
        return html`<ak-forms-delete-bulk
            objectLabel=${msg("Role(s)")}
            actionLabel=${msg("Remove from Role(s)")}
            actionSubtext=${msg(
                str`Are you sure you want to remove user ${this.targetUser?.username} from the following roles?`,
            )}
            buttonLabel=${msg("Remove")}
            .objects=${this.selectedElements}
            .delete=${(item: Role) => {
                if (!this.targetUser) return;
                return new RbacApi(DEFAULT_CONFIG).rbacRolesRemoveUserCreate({
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

    isInherited(role: Role): boolean {
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

    row(item: Role): SlottedTemplateResult[] {
        const inherited = this.showInherited && this.isInherited(item);
        const inheritedTooltip = this.targetGroup
            ? msg("Inherited from parent group")
            : msg("Inherited from group");
        const nameCell = html`<a href="#/identity/roles/${item.pk}">${item.name}</a> ${inherited
                ? html`<pf-tooltip position="top" content=${inheritedTooltip}>
                      <span class="pf-c-label pf-m-outline pf-m-cyan" style="margin-left: 0.5rem;">
                          <span class="pf-c-label__content">${msg("Inherited")}</span>
                      </span>
                  </pf-tooltip>`
                : nothing}`;

        // Hide actions in showInherited mode (view-only)
        if (this.showInherited) {
            return [nameCell];
        }

        return [
            nameCell,
            html`<ak-forms-modal>
                <span slot="submit">${msg("Update")}</span>
                <span slot="header">${msg("Update Role")}</span>
                <ak-role-form slot="form" .instancePk=${item.pk}> </ak-role-form>
                <button slot="trigger" class="pf-c-button pf-m-plain">
                    <pf-tooltip position="top" content=${msg("Edit")}>
                        <i class="fas fa-edit" aria-hidden="true"></i>
                    </pf-tooltip>
                </button>
            </ak-forms-modal>`,
        ];
    }

    renderToolbar(): TemplateResult {
        // Hide add buttons in showInherited mode (view-only)
        if (this.showInherited || this.targetGroup) {
            return html`${super.renderToolbar()}`;
        }
        return html`
            ${this.targetUser
                ? html`<ak-forms-modal>
                      <span slot="submit">${msg("Add")}</span>
                      <span slot="header">${msg("Add Role")}</span>
                      <ak-role-related-add .user=${this.targetUser} slot="form">
                      </ak-role-related-add>
                      <button slot="trigger" class="pf-c-button pf-m-primary">
                          ${msg("Add to existing role")}
                      </button>
                  </ak-forms-modal>`
                : nothing}
            <ak-forms-modal>
                <span slot="submit">${msg("Create")}</span>
                <span slot="header">${msg("Create Role")}</span>
                <ak-role-form slot="form"> </ak-role-form>
                <button slot="trigger" class="pf-c-button pf-m-secondary">
                    ${msg("Add new role")}
                </button>
            </ak-forms-modal>
            ${super.renderToolbar()}
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-role-related-list": RelatedRoleList;
        "ak-role-related-add": RelatedRoleAdd;
    }
}
