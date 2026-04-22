import "#admin/groups/ak-group-member-table";
import "#admin/users/ServiceAccountForm";
import "#admin/users/UserActiveForm";
import "#admin/users/UserForm";
import "#admin/users/UserImpersonateForm";
import "#admin/users/UserPasswordForm";
import "#admin/users/UserResetEmailForm";
import "#components/ak-status-label";
import "#elements/buttons/ActionButton/index";
import "#elements/buttons/Dropdown";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/ModalForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";
import { formatDisambiguatedUserDisplayName } from "#common/users";

import { IconEditButton, renderModal } from "#elements/dialogs";
import { AKFormSubmitEvent, Form } from "#elements/forms/Form";
import { WithBrandConfig } from "#elements/mixins/branding";
import { WithCapabilitiesConfig } from "#elements/mixins/capabilities";
import { getURLParam, updateURLParams } from "#elements/router/RouteMatch";
import { PaginatedResponse, Table, TableColumn, Timestamp } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { AKLabel } from "#components/ak-label";

import { RecoveryButtons } from "#admin/users/recovery";
import { ToggleUserActivationButton } from "#admin/users/UserActiveForm";
import { UserForm } from "#admin/users/UserForm";
import { UserImpersonateForm } from "#admin/users/UserImpersonateForm";

import {
    CapabilitiesEnum,
    CoreApi,
    Group,
    RbacApi,
    Role,
    User,
    UserTypeEnum,
} from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFAlert from "@patternfly/patternfly/components/Alert/alert.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";

@customElement("ak-add-related-user-form")
export class AddRelatedUserForm extends Form<{ users: number[] }> {
    public override headline = msg("Assign Additional Users");
    public override submitLabel = msg("Assign");

    @property({ attribute: false })
    public targetGroup: Group | null = null;

    @property({ attribute: false })
    public targetRole: Role | null = null;

    @state()
    usersToAdd: User[] = [];

    public override getSuccessMessage(): string {
        return msg("Successfully added user(s).");
    }

    async send(data: { users: number[] }): Promise<{ users: number[] }> {
        await Promise.all(
            data.users.map((userPk) => {
                if (this.targetGroup) {
                    return new CoreApi(DEFAULT_CONFIG).coreGroupsAddUserCreate({
                        groupUuid: this.targetGroup.pk,
                        userAccountRequest: {
                            pk: userPk,
                        },
                    });
                } else if (this.targetRole) {
                    return new RbacApi(DEFAULT_CONFIG).rbacRolesAddUserCreate({
                        uuid: this.targetRole.pk,
                        // TODO: Rename this.
                        userAccountSerializerForRoleRequest: {
                            pk: userPk,
                        },
                    });
                }
                return Promise.resolve();
            }),
        );
        return data;
    }

    protected openUserSelectionModal = (event?: Event) => {
        if (event?.defaultPrevented) {
            return;
        }

        return renderModal(html`
            <ak-form
                headline=${msg("Select users")}
                submit-label=${msg("Confirm")}
                @submit=${(event: AKFormSubmitEvent<User[]>) => {
                    this.usersToAdd = event.target.toJSON();
                }}
                ><ak-group-member-table></ak-group-member-table>
            </ak-form>
        `);
    };

    //#region Rendering

    protected override renderForm(): TemplateResult {
        // TODO: The `form-control-sibling` container is a workaround to get the
        // table to allow the table to appear as an inline-block element next to the input group.
        // This should be fixed by moving the `@container` query off `:host`.

        return html`<ak-form-element-horizontal name="users">
            ${AKLabel(
                {
                    slot: "label",
                    className: "pf-c-form__group-label",
                    htmlFor: "assign-users-button",
                },
                msg("Users"),
            )}
            <div class="pf-c-input-group">
                <div class="form-control-sibling">
                    <button
                        class="pf-c-button pf-m-control"
                        type="button"
                        id="assign-users-button"
                        aria-haspopup="dialog"
                        aria-label=${msg("Open user selection dialog")}
                        @click=${this.openUserSelectionModal}
                    >
                        <pf-tooltip position="right" content=${msg("Add users")}>
                            <i class="fas fa-plus" aria-hidden="true"></i>
                        </pf-tooltip>
                    </button>
                </div>
                <div class="pf-c-form-control">
                    <ak-chip-group
                        @click=${this.openUserSelectionModal}
                        placeholder=${msg("Select one or more users to assign...")}
                        >${this.usersToAdd.map((user) => {
                            return html`<ak-chip
                                removable
                                value=${ifDefined(user.pk)}
                                @remove=${() => {
                                    const idx = this.usersToAdd.indexOf(user);
                                    this.usersToAdd.splice(idx, 1);
                                    this.requestUpdate();
                                }}
                            >
                                ${formatDisambiguatedUserDisplayName(user)}
                            </ak-chip>`;
                        })}</ak-chip-group
                    >
                </div>
            </div>
        </ak-form-element-horizontal>`;
    }
}

@customElement("ak-user-related-list")
export class RelatedUserList extends WithBrandConfig(WithCapabilitiesConfig(Table<User>)) {
    public static styles: CSSResult[] = [...Table.styles, PFDescriptionList, PFAlert];

    public override searchPlaceholder = msg("Search for users by username or display name...");
    public override searchLabel = msg("User Search");
    public override label = msg("Users");

    public override expandable = true;
    public override checkbox = true;
    public override clearOnRefresh = true;

    protected override searchEnabled = true;

    @property({ attribute: false })
    public targetGroup: Group | null = null;

    @property({ attribute: false })
    public targetRole: Role | null = null;

    public override order = "last_login";

    @property({ type: Boolean })
    public hideServiceAccounts = getURLParam<boolean>("hideServiceAccounts", true);

    protected canImpersonate = false;

    public override connectedCallback(): void {
        super.connectedCallback();

        this.canImpersonate = this.can(CapabilitiesEnum.CanImpersonate);
    }

    protected async apiEndpoint(): Promise<PaginatedResponse<User>> {
        const users = await new CoreApi(DEFAULT_CONFIG).coreUsersList({
            ...(await this.defaultEndpointConfig()),
            ...(this.targetGroup && { groupsByPk: [this.targetGroup.pk] }),
            ...(this.targetRole && { rolesByPk: [this.targetRole.pk] }),
            type: this.hideServiceAccounts
                ? [UserTypeEnum.External, UserTypeEnum.Internal]
                : undefined,
            includeGroups: false,
            includeRoles: false,
        });

        return users;
    }

    protected override rowLabel(item: User): string | null {
        return item.username ?? item.name ?? null;
    }

    protected columns: TableColumn[] = [
        [msg("Name"), "username"],
        [msg("Active"), "is_active"],
        [msg("Last login"), "last_login"],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    protected override renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        const targetLabel = this.targetGroup?.name || this.targetRole?.name;

        return html`<ak-forms-delete-bulk
            object-label=${msg("User(s)")}
            submit-label=${msg("Remove User(s)")}
            action=${msg("removed")}
            action-subtext=${targetLabel
                ? msg(str`Are you sure you want to remove the selected users from ${targetLabel}?`)
                : msg("Are you sure you want to remove the selected users?")}
            .objects=${this.selectedElements}
            .metadata=${(item: User) => {
                return [
                    { key: msg("Username"), value: item.username },
                    { key: msg("ID"), value: item.pk.toString() },
                    { key: msg("UID"), value: item.uid },
                ];
            }}
            .delete=${(item: User) => {
                if (this.targetGroup) {
                    return new CoreApi(DEFAULT_CONFIG).coreGroupsRemoveUserCreate({
                        groupUuid: this.targetGroup.pk,
                        userAccountRequest: {
                            pk: item.pk,
                        },
                    });
                }
                if (this.targetRole) {
                    return new RbacApi(DEFAULT_CONFIG).rbacRolesRemoveUserCreate({
                        uuid: this.targetRole.pk,
                        userAccountSerializerForRoleRequest: {
                            pk: item.pk,
                        },
                    });
                }
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Remove")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    protected override row(item: User): SlottedTemplateResult[] {
        const showImpersonate = this.canImpersonate && item.pk !== this.currentUser?.pk;

        return [
            html`<a href="#/identity/users/${item.pk}">
                <div>${item.username}</div>
                <small>${item.name}</small>
            </a>`,
            html`<ak-status-label ?good=${item.isActive}></ak-status-label>`,
            Timestamp(item.lastLogin),

            html`<div class="ak-c-table__actions">
                ${IconEditButton(UserForm, item.pk)}
                ${showImpersonate
                    ? html`<button
                          class="pf-c-button pf-m-tertiary"
                          ${UserImpersonateForm.asInstanceInvoker(item.pk)}
                      >
                          <pf-tooltip
                              position="top"
                              content=${msg("Temporarily assume the identity of this user")}
                          >
                              <span>${msg("Impersonate")}</span>
                          </pf-tooltip>
                      </button>`
                    : null}
            </div>`,
        ];
    }

    protected override renderExpanded(item: User): TemplateResult {
        return html`<dl class="pf-c-description-list pf-m-horizontal">
            <div class="pf-c-description-list__group">
                <dt class="pf-c-description-list__term">
                    <span class="pf-c-description-list__text">${msg("User status")}</span>
                </dt>
                <dd class="pf-c-description-list__description">
                    <div class="pf-c-description-list__text">
                        ${item.isActive ? msg("Active") : msg("Inactive")}
                    </div>
                    <div class="pf-c-description-list__text">
                        ${item.isSuperuser ? msg("Superuser") : msg("Regular user")}
                    </div>
                </dd>
            </div>
            <div class="pf-c-description-list__group">
                <dt class="pf-c-description-list__term">
                    <span class="pf-c-description-list__text">${msg("Change status")}</span>
                </dt>
                <dd class="pf-c-description-list__description">
                    <div class="pf-c-description-list__text">
                        ${ToggleUserActivationButton(item)}
                    </div>
                </dd>
            </div>
            <div class="pf-c-description-list__group">
                <dt class="pf-c-description-list__term">
                    <span class="pf-c-description-list__text">${msg("Recovery")}</span>
                </dt>
                <dd class="pf-c-description-list__description">
                    <div class="pf-c-description-list__text">
                        ${RecoveryButtons({
                            user: item,
                            brandHasRecoveryFlow: Boolean(this.brand.flowRecovery),
                        })}
                    </div>
                </dd>
            </div>
        </dl>`;
    }

    protected openAddUserToTargetGroupModal = () => {
        const banner = this.targetGroup?.isSuperuser
            ? html`<div class="pf-c-banner pf-m-warning" slot="before-body">
                  ${msg(
                      "Warning: This group is configured with superuser access. Added users will have superuser access.",
                  )}
              </div>`
            : nothing;

        return renderModal(
            html`${banner}<ak-add-related-user-form .targetGroup=${this.targetGroup}>
                </ak-add-related-user-form>`,
        );
    };

    protected openAddUserToTargetRoleModal = () => {
        return renderModal(
            html`<ak-add-related-user-form .targetRole=${this.targetRole}>
            </ak-add-related-user-form>`,
        );
    };

    protected openNewUserToTargetGroupModal = () => {
        const banner = this.targetGroup
            ? html`<div class="pf-c-banner pf-m-info" slot="before-body">
                  ${msg(str`This user will be added to the group "${this.targetGroup.name}".`)}
              </div>`
            : nothing;

        return renderModal(
            html`${banner}<ak-user-form
                    .targetGroup=${this.targetGroup}
                    headline=${msg("New Group User")}
                ></ak-user-form>`,
        );
    };

    protected openNewUserToTargetRoleModal = () => {
        const banner = this.targetRole
            ? html`<div class="pf-c-banner pf-m-info" slot="before-body">
                  ${msg(str`This user will be added to the role "${this.targetRole.name}".`)}
              </div>`
            : nothing;

        return renderModal(
            html`${banner}<ak-user-form
                    .targetRole=${this.targetRole}
                    headline=${msg("New Role User")}
                ></ak-user-form>`,
        );
    };

    protected openNewServiceUserToTargetGroupModal = () => {
        const banner = this.targetGroup
            ? html`<div class="pf-c-banner pf-m-info" slot="before-body">
                  ${msg(str`This user will be added to the group "${this.targetGroup.name}".`)}
              </div>`
            : nothing;

        return renderModal(
            html`${banner}<ak-user-service-account-form
                    .targetGroup=${this.targetGroup}
                ></ak-user-service-account-form>`,
            {
                closedBy: "none",
            },
        );
    };

    protected override renderToolbar(): TemplateResult {
        return html`
            ${this.targetGroup
                ? html`<button
                      class="pf-c-button pf-m-primary"
                      @click=${this.openAddUserToTargetGroupModal}
                  >
                      ${msg("Add Existing User")}
                  </button>`
                : null}
            ${this.targetRole
                ? html`<button
                      class="pf-c-button pf-m-primary"
                      @click=${this.openAddUserToTargetRoleModal}
                  >
                      ${msg("Add Existing User")}
                  </button>`
                : null}

            <ak-dropdown class="pf-c-dropdown">
                <button
                    class="pf-c-button pf-m-secondary pf-c-dropdown__toggle"
                    type="button"
                    id="add-user-toggle"
                    aria-haspopup="menu"
                    aria-controls="add-user-menu"
                    tabindex="0"
                >
                    <span class="pf-c-dropdown__toggle-text">${msg("Add New User")}</span>
                    <i class="fas fa-caret-down pf-c-dropdown__toggle-icon" aria-hidden="true"></i>
                </button>
                <menu
                    class="pf-c-dropdown__menu"
                    hidden
                    id="add-user-menu"
                    aria-labelledby="add-user-toggle"
                    tabindex="-1"
                >
                    ${this.targetGroup
                        ? html`<li role="presentation">
                              <button
                                  type="button"
                                  role="menuitem"
                                  class="pf-c-dropdown__menu-item"
                                  @click=${this.openNewUserToTargetGroupModal}
                              >
                                  ${msg("New Group User...")}
                              </button>
                          </li>`
                        : null}
                    ${this.targetRole
                        ? html`<li role="presentation">
                              <button
                                  type="button"
                                  role="menuitem"
                                  class="pf-c-dropdown__menu-item"
                                  @click=${this.openNewUserToTargetRoleModal}
                              >
                                  ${msg("New Role User...")}
                              </button>
                          </li>`
                        : null}

                    <li role="presentation">
                        <button
                            type="button"
                            role="menuitem"
                            class="pf-c-dropdown__menu-item"
                            @click=${this.openNewServiceUserToTargetGroupModal}
                        >
                            ${msg("New Service Account...")}
                        </button>
                    </li>
                </menu>
            </ak-dropdown>
            ${super.renderToolbar()}
        `;
    }

    protected override renderToolbarAfter(): TemplateResult {
        return html`<div class="pf-c-toolbar__group pf-m-filter-group">
            <div class="pf-c-toolbar__item pf-m-search-filter">
                <div class="pf-c-input-group">
                    <label class="pf-c-switch" id="hide-service-accounts-label">
                        <input
                            id="hide-service-accounts"
                            class="pf-c-switch__input"
                            type="checkbox"
                            ?checked=${this.hideServiceAccounts}
                            @change=${() => {
                                this.hideServiceAccounts = !this.hideServiceAccounts;
                                this.page = 1;
                                this.fetch();
                                updateURLParams({
                                    hideServiceAccounts: this.hideServiceAccounts,
                                });
                            }}
                        />
                        <span class="pf-c-switch__toggle">
                            <span class="pf-c-switch__toggle-icon">
                                <i class="fas fa-check" aria-hidden="true"></i>
                            </span>
                        </span>
                        <span class="pf-c-switch__label">${msg("Hide service-accounts")}</span>
                    </label>
                </div>
            </div>
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-related-list": RelatedUserList;
        "ak-add-related-user-form": AddRelatedUserForm;
    }
}
