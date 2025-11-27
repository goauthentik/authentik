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

import { RbacApi, Role, User } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html, nothing, TemplateResult } from "lit";
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
                if (!this.user) return;
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

    async apiEndpoint(): Promise<PaginatedResponse<Role>> {
        return new RbacApi(DEFAULT_CONFIG).rbacRolesList({
            ...(await this.defaultEndpointConfig()),
            users: this.targetUser ? [this.targetUser.pk] : [],
        });
    }

    protected columns: TableColumn[] = [
        [msg("Name"), "name"],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    renderToolbarSelected(): TemplateResult {
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

    row(item: Role): SlottedTemplateResult[] {
        return [
            html`<a href="#/identity/roles/${item.pk}">${item.name}</a>`,
            html` <ak-forms-modal>
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
