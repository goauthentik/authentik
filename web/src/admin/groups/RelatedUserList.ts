import "#admin/groups/MemberSelectModal";
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
import { PFSize } from "#common/enums";
import { parseAPIResponseError, pluckErrorDetail } from "#common/errors/network";
import { MessageLevel } from "#common/messages";

import { Form } from "#elements/forms/Form";
import { showMessage } from "#elements/messages/MessageContainer";
import { WithBrandConfig } from "#elements/mixins/branding";
import { CapabilitiesEnum, WithCapabilitiesConfig } from "#elements/mixins/capabilities";
import { getURLParam, updateURLParams } from "#elements/router/RouteMatch";
import { PaginatedResponse, Table, TableColumn, Timestamp } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";
import { UserOption } from "#elements/user/utils";

import { AKLabel } from "#components/ak-label";

import { CoreApi, CoreUsersListTypeEnum, Group, RbacApi, Role, User } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFAlert from "@patternfly/patternfly/components/Alert/alert.css";
import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";

@customElement("ak-user-related-add")
export class RelatedUserAdd extends Form<{ users: number[] }> {
    @property({ attribute: false })
    public targetGroup: Group | null = null;

    @property({ attribute: false })
    public targetRole: Role | null = null;

    @state()
    usersToAdd: User[] = [];

    getSuccessMessage(): string {
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

    protected override renderForm(): TemplateResult {
        // TODO: The `form-control-sibling` container is a workaround to get the
        // table to allow the table to appear as an inline-block element next to the input group.
        // This should be fixed by moving the `@container` query off `:host`.

        return html` <ak-form-element-horizontal name="users">
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
                    <ak-group-member-select-table
                        .confirm=${(items: User[]) => {
                            this.usersToAdd = items;
                            this.requestUpdate();
                            return Promise.resolve();
                        }}
                    >
                        <button
                            slot="trigger"
                            class="pf-c-button pf-m-control"
                            type="button"
                            id="assign-users-button"
                            aria-haspopup="dialog"
                            aria-label=${msg("Open user selection dialog")}
                        >
                            <pf-tooltip position="top" content=${msg("Add users")}>
                                <i class="fas fa-plus" aria-hidden="true"></i>
                            </pf-tooltip>
                        </button>
                    </ak-group-member-select-table>
                </div>
                <div class="pf-c-form-control">
                    <ak-chip-group>
                        ${this.usersToAdd.map((user) => {
                            return html`<ak-chip
                                removable
                                value=${ifDefined(user.pk)}
                                @remove=${() => {
                                    const idx = this.usersToAdd.indexOf(user);
                                    this.usersToAdd.splice(idx, 1);
                                    this.requestUpdate();
                                }}
                            >
                                ${UserOption(user)}
                            </ak-chip>`;
                        })}
                    </ak-chip-group>
                </div>
            </div>
        </ak-form-element-horizontal>`;
    }
}

@customElement("ak-user-related-list")
export class RelatedUserList extends WithBrandConfig(WithCapabilitiesConfig(Table<User>)) {
    public override searchPlaceholder = msg("Search for users by username or display name...");
    public override searchLabel = msg("User Search");
    public override label = msg("Users");

    expandable = true;
    checkbox = true;
    clearOnRefresh = true;

    protected override searchEnabled = true;

    @property({ attribute: false })
    targetGroup?: Group;

    @property({ attribute: false })
    targetRole?: Role;

    @property()
    order = "last_login";

    @property({ type: Boolean })
    hideServiceAccounts = getURLParam<boolean>("hideServiceAccounts", true);

    static styles: CSSResult[] = [...Table.styles, PFDescriptionList, PFAlert, PFBanner];

    async apiEndpoint(): Promise<PaginatedResponse<User>> {
        const users = await new CoreApi(DEFAULT_CONFIG).coreUsersList({
            ...(await this.defaultEndpointConfig()),
            ...(this.targetGroup && { groupsByPk: [this.targetGroup.pk] }),
            ...(this.targetRole && { rolesByPk: [this.targetRole.pk] }),
            type: this.hideServiceAccounts
                ? [CoreUsersListTypeEnum.External, CoreUsersListTypeEnum.Internal]
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

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        const targetLabel = this.targetGroup?.name || this.targetRole?.name;
        return html`<ak-forms-delete-bulk
            objectLabel=${msg("User(s)")}
            actionLabel=${msg("Remove User(s)")}
            action=${msg("removed")}
            actionSubtext=${targetLabel
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

    row(item: User): SlottedTemplateResult[] {
        const canImpersonate =
            this.can(CapabilitiesEnum.CanImpersonate) && item.pk !== this.currentUser?.pk;
        return [
            html`<a href="#/identity/users/${item.pk}">
                <div>${item.username}</div>
                <small>${item.name}</small>
            </a>`,
            html`<ak-status-label ?good=${item.isActive}></ak-status-label>`,
            Timestamp(item.lastLogin),

            html`<div>
                <ak-forms-modal>
                    <span slot="submit">${msg("Update")}</span>
                    <span slot="header">${msg("Update User")}</span>
                    <ak-user-form slot="form" .instancePk=${item.pk}> </ak-user-form>
                    <button slot="trigger" class="pf-c-button pf-m-plain">
                        <pf-tooltip position="top" content=${msg("Edit")}>
                            <i class="fas fa-edit" aria-hidden="true"></i>
                        </pf-tooltip>
                    </button>
                </ak-forms-modal>
                ${canImpersonate
                    ? html`
                          <ak-forms-modal size=${PFSize.Medium} id="impersonate-request">
                              <span slot="submit">${msg("Impersonate")}</span>
                              <span slot="header">${msg("Impersonate")} ${item.username}</span>
                              <ak-user-impersonate-form
                                  slot="form"
                                  .instancePk=${item.pk}
                              ></ak-user-impersonate-form>
                              <button slot="trigger" class="pf-c-button pf-m-tertiary">
                                  <pf-tooltip
                                      position="top"
                                      content=${msg("Temporarily assume the identity of this user")}
                                  >
                                      <span>${msg("Impersonate")}</span>
                                  </pf-tooltip>
                              </button>
                          </ak-forms-modal>
                      `
                    : nothing}
            </div>`,
        ];
    }

    renderExpanded(item: User): TemplateResult {
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
                        <ak-user-active-form
                            .obj=${item}
                            objectLabel=${msg("User")}
                            .delete=${() => {
                                return new CoreApi(DEFAULT_CONFIG).coreUsersPartialUpdate({
                                    id: item.pk || 0,
                                    patchedUserRequest: {
                                        isActive: !item.isActive,
                                    },
                                });
                            }}
                        >
                            <button slot="trigger" class="pf-c-button pf-m-warning">
                                ${item.isActive ? msg("Deactivate") : msg("Activate")}
                            </button>
                        </ak-user-active-form>
                    </div>
                </dd>
            </div>
            <div class="pf-c-description-list__group">
                <dt class="pf-c-description-list__term">
                    <span class="pf-c-description-list__text">${msg("Recovery")}</span>
                </dt>
                <dd class="pf-c-description-list__description">
                    <div class="pf-c-description-list__text">
                        <ak-forms-modal>
                            <span slot="submit">${msg("Update password")}</span>
                            <span slot="header">
                                ${msg(str`Update ${item.name || item.username}'s password`)}
                            </span>
                            <ak-user-password-form
                                username=${item.username}
                                email=${ifDefined(item.email)}
                                slot="form"
                                .instancePk=${item.pk}
                            ></ak-user-password-form>
                            <button slot="trigger" class="pf-c-button pf-m-secondary">
                                ${msg("Set password")}
                            </button>
                        </ak-forms-modal>
                        ${this.brand.flowRecovery
                            ? html`
                                  <ak-action-button
                                      class="pf-m-secondary"
                                      .apiRequest=${() => {
                                          return new CoreApi(DEFAULT_CONFIG)
                                              .coreUsersRecoveryCreate({
                                                  id: item.pk,
                                              })
                                              .then((rec) => {
                                                  showMessage({
                                                      level: MessageLevel.success,
                                                      message: msg(
                                                          "Successfully generated recovery link",
                                                      ),
                                                      description: rec.link,
                                                  });
                                              })
                                              .catch(async (error: unknown) => {
                                                  const parsedError =
                                                      await parseAPIResponseError(error);

                                                  showMessage({
                                                      level: MessageLevel.error,
                                                      message: pluckErrorDetail(parsedError),
                                                  });
                                              });
                                      }}
                                  >
                                      ${msg("Copy recovery link")}
                                  </ak-action-button>
                                  ${item.email
                                      ? html`<ak-forms-modal .closeAfterSuccessfulSubmit=${false}>
                                            <span slot="submit"> ${msg("Send link")} </span>
                                            <span slot="header">
                                                ${msg("Send recovery link to user")}
                                            </span>
                                            <ak-user-reset-email-form slot="form" .user=${item}>
                                            </ak-user-reset-email-form>
                                            <button
                                                slot="trigger"
                                                class="pf-c-button pf-m-secondary"
                                            >
                                                ${msg("Email recovery link")}
                                            </button>
                                        </ak-forms-modal>`
                                      : html`<span
                                            >${msg(
                                                "Recovery link cannot be emailed, user has no email address saved.",
                                            )}</span
                                        >`}
                              `
                            : html` <p>
                                  ${msg(
                                      "To let a user directly reset a their password, configure a recovery flow on the currently active brand.",
                                  )}
                              </p>`}
                    </div>
                </dd>
            </div>
        </dl>`;
    }

    renderToolbar(): TemplateResult {
        return html`
            ${this.targetGroup
                ? html`<ak-forms-modal>
                      <span slot="submit">${msg("Assign")}</span>
                      <span slot="header">${msg("Assign Additional Users")}</span>
                      ${this.targetGroup.isSuperuser
                          ? html`
                                <div class="pf-c-banner pf-m-warning" slot="above-form">
                                    ${msg(
                                        "Warning: This group is configured with superuser access. Added users will have superuser access.",
                                    )}
                                </div>
                            `
                          : nothing}
                      <ak-user-related-add .targetGroup=${this.targetGroup} slot="form">
                      </ak-user-related-add>
                      <button slot="trigger" class="pf-c-button pf-m-primary">
                          ${msg("Add existing user")}
                      </button>
                  </ak-forms-modal>`
                : nothing}
            ${this.targetRole
                ? html`<ak-forms-modal>
                      <span slot="submit">${msg("Assign")}</span>
                      <span slot="header">${msg("Assign Additional Users")}</span>
                      <ak-user-related-add .targetRole=${this.targetRole} slot="form">
                      </ak-user-related-add>
                      <button slot="trigger" class="pf-c-button pf-m-primary">
                          ${msg("Add existing user")}
                      </button>
                  </ak-forms-modal>`
                : nothing}
            <ak-dropdown class="pf-c-dropdown">
                <button
                    class="pf-m-secondary pf-c-dropdown__toggle"
                    type="button"
                    id="add-user-toggle"
                    aria-haspopup="menu"
                    aria-controls="add-user-menu"
                    tabindex="0"
                >
                    <span class="pf-c-dropdown__toggle-text">${msg("Add new user")}</span>
                    <i class="fas fa-caret-down pf-c-dropdown__toggle-icon" aria-hidden="true"></i>
                </button>
                <ul
                    class="pf-c-dropdown__menu"
                    hidden
                    role="menu"
                    id="add-user-menu"
                    aria-labelledby="add-user-toggle"
                    tabindex="-1"
                >
                    <li role="presentation">
                        <ak-forms-modal>
                            <span slot="submit">${msg("Create User")}</span>
                            <span slot="header">${msg("New User")}</span>
                            ${this.targetGroup
                                ? html`
                                      <div class="pf-c-banner pf-m-info" slot="above-form">
                                          ${msg(
                                              str`This user will be added to the group "${this.targetGroup.name}".`,
                                          )}
                                      </div>
                                      <ak-user-form .targetGroup=${this.targetGroup} slot="form">
                                      </ak-user-form>
                                  `
                                : nothing}
                            ${this.targetRole
                                ? html`
                                      <div class="pf-c-banner pf-m-info" slot="above-form">
                                          ${msg(
                                              str`This user will be added to the role "${this.targetRole.name}".`,
                                          )}
                                      </div>
                                      <ak-user-form .targetRole=${this.targetRole} slot="form">
                                      </ak-user-form>
                                  `
                                : nothing}
                            <a role="menuitem" slot="trigger" class="pf-c-dropdown__menu-item">
                                ${msg("New user...")}
                            </a>
                        </ak-forms-modal>
                    </li>
                    <li role="presentation">
                        <ak-forms-modal
                            .closeAfterSuccessfulSubmit=${false}
                            .cancelText=${msg("Close")}
                        >
                            <span slot="submit">${msg("Create Service Account")}</span>
                            <span slot="header">${msg("New Service Account")}</span>
                            ${this.targetGroup
                                ? html`
                                      <div class="pf-c-banner pf-m-info" slot="above-form">
                                          ${msg(
                                              str`This user will be added to the group "${this.targetGroup.name}".`,
                                          )}
                                      </div>
                                      <ak-user-service-account-form
                                          .targetGroup=${this.targetGroup}
                                          slot="form"
                                      ></ak-user-service-account-form>
                                  `
                                : nothing}
                            ${this.targetRole
                                ? html`
                                      <div class="pf-c-banner pf-m-info" slot="above-form">
                                          ${msg(
                                              str`This user will be added to the role "${this.targetRole.name}".`,
                                          )}
                                      </div>
                                      <ak-user-service-account-form
                                          .targetRole=${this.targetRole}
                                          slot="form"
                                      ></ak-user-service-account-form>
                                  `
                                : nothing}
                            <a role="menuitem" slot="trigger" class="pf-c-dropdown__menu-item">
                                ${msg("New service account...")}
                            </a>
                        </ak-forms-modal>
                    </li>
                </ul>
            </ak-dropdown>
            ${super.renderToolbar()}
        `;
    }

    renderToolbarAfter(): TemplateResult {
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
        "ak-user-related-add": RelatedUserAdd;
    }
}
