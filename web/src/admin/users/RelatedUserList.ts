import "@goauthentik/admin/users/ServiceAccountForm";
import "@goauthentik/admin/users/UserActiveForm";
import "@goauthentik/admin/users/UserForm";
import "@goauthentik/admin/users/UserPasswordForm";
import "@goauthentik/admin/users/UserResetEmailForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { MessageLevel } from "@goauthentik/common/messages";
import { uiConfig } from "@goauthentik/common/ui/config";
import { first } from "@goauthentik/common/utils";
import { rootInterface } from "@goauthentik/elements/Base";
import { PFColor } from "@goauthentik/elements/Label";
import "@goauthentik/elements/buttons/ActionButton";
import "@goauthentik/elements/buttons/Dropdown";
import "@goauthentik/elements/forms/DeleteBulkForm";
import { Form } from "@goauthentik/elements/forms/Form";
import "@goauthentik/elements/forms/HorizontalFormElement";
import "@goauthentik/elements/forms/ModalForm";
import { showMessage } from "@goauthentik/elements/messages/MessageContainer";
import { getURLParam, updateURLParams } from "@goauthentik/elements/router/RouteMatch";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import { Table, TableColumn } from "@goauthentik/elements/table/Table";
import { UserOption } from "@goauthentik/elements/user/utils";

import { t } from "@lingui/macro";

import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFAlert from "@patternfly/patternfly/components/Alert/alert.css";
import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";

import { CapabilitiesEnum, CoreApi, Group, ResponseError, User } from "@goauthentik/api";

@customElement("ak-user-related-add")
export class RelatedUserAdd extends Form<{ users: number[] }> {
    @property({ attribute: false })
    group?: Group;

    @state()
    usersToAdd: User[] = [];

    getSuccessMessage(): string {
        return t`Successfully added user(s).`;
    }

    async send(data: { users: number[] }): Promise<{ users: number[] }> {
        await Promise.all(
            data.users.map((user) => {
                return new CoreApi(DEFAULT_CONFIG).coreGroupsAddUserCreate({
                    groupUuid: this.group?.pk || "",
                    userAccountRequest: {
                        pk: user,
                    },
                });
            }),
        );
        return data;
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            ${this.group?.isSuperuser ? html`` : html``}
            <ak-form-element-horizontal label=${t`Users to add`} name="users">
                <div class="pf-c-input-group">
                    <ak-group-member-select-table
                        .confirm=${(items: User[]) => {
                            this.usersToAdd = items;
                            this.requestUpdate();
                            return Promise.resolve();
                        }}
                    >
                        <button slot="trigger" class="pf-c-button pf-m-control" type="button">
                            <i class="fas fa-plus" aria-hidden="true"></i>
                        </button>
                    </ak-group-member-select-table>
                    <div class="pf-c-form-control">
                        <ak-chip-group>
                            ${this.usersToAdd.map((user) => {
                                return html`<ak-chip
                                    .removable=${true}
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
            </ak-form-element-horizontal>
        </form> `;
    }
}

@customElement("ak-user-related-list")
export class RelatedUserList extends Table<User> {
    expandable = true;
    checkbox = true;

    searchEnabled(): boolean {
        return true;
    }

    @property()
    targetGroup?: Group;

    @property()
    order = "last_login";

    @property({ type: Boolean })
    hideServiceAccounts = getURLParam<boolean>("hideServiceAccounts", true);

    static get styles(): CSSResult[] {
        return super.styles.concat(PFDescriptionList, PFAlert, PFBanner);
    }

    async apiEndpoint(page: number): Promise<PaginatedResponse<User>> {
        return new CoreApi(DEFAULT_CONFIG).coreUsersList({
            ordering: this.order,
            page: page,
            pageSize: (await uiConfig()).pagination.perPage,
            search: this.search || "",
            groupsByPk: this.targetGroup ? [this.targetGroup.pk] : [],
            attributes: this.hideServiceAccounts
                ? JSON.stringify({
                      "goauthentik.io/user/service-account__isnull": true,
                  })
                : undefined,
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(t`Name`, "username"),
            new TableColumn(t`Active`, "active"),
            new TableColumn(t`Last login`, "last_login"),
            new TableColumn(t`Actions`),
        ];
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${t`User(s)`}
            actionLabel=${t`Remove Users(s)`}
            actionSubtext=${t`Are you sure you want to remove the selected users from the group ${this.targetGroup?.name}?`}
            .objects=${this.selectedElements}
            .metadata=${(item: User) => {
                return [
                    { key: t`Username`, value: item.username },
                    { key: t`ID`, value: item.pk.toString() },
                    { key: t`UID`, value: item.uid },
                ];
            }}
            .delete=${(item: User) => {
                return new CoreApi(DEFAULT_CONFIG).coreGroupsRemoveUserCreate({
                    groupUuid: this.targetGroup?.pk || "",
                    userAccountRequest: {
                        pk: item.pk,
                    },
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${t`Remove`}
            </button>
        </ak-forms-delete-bulk>`;
    }

    row(item: User): TemplateResult[] {
        return [
            html`<a href="#/identity/users/${item.pk}">
                <div>${item.username}</div>
                <small>${item.name}</small>
            </a>`,
            html`<ak-label color=${item.isActive ? PFColor.Green : PFColor.Red}>
                ${item.isActive ? t`Yes` : t`No`}
            </ak-label>`,
            html`${first(item.lastLogin?.toLocaleString(), t`-`)}`,
            html`<ak-forms-modal>
                    <span slot="submit"> ${t`Update`} </span>
                    <span slot="header"> ${t`Update User`} </span>
                    <ak-user-form slot="form" .instancePk=${item.pk}> </ak-user-form>
                    <button slot="trigger" class="pf-c-button pf-m-plain">
                        <i class="fas fa-edit"></i>
                    </button>
                </ak-forms-modal>
                ${rootInterface()?.config?.capabilities.includes(CapabilitiesEnum.Impersonate)
                    ? html`
                          <a
                              class="pf-c-button pf-m-tertiary"
                              href="${`/-/impersonation/${item.pk}/`}"
                          >
                              ${t`Impersonate`}
                          </a>
                      `
                    : html``}`,
        ];
    }

    renderExpanded(item: User): TemplateResult {
        return html`<td role="cell" colspan="3">
                <div class="pf-c-table__expandable-row-content">
                    <dl class="pf-c-description-list pf-m-horizontal">
                        <div class="pf-c-description-list__group">
                            <dt class="pf-c-description-list__term">
                                <span class="pf-c-description-list__text">${t`User status`}</span>
                            </dt>
                            <dd class="pf-c-description-list__description">
                                <div class="pf-c-description-list__text">
                                    ${item.isActive ? t`Active` : t`Inactive`}
                                </div>
                                <div class="pf-c-description-list__text">
                                    ${item.isSuperuser ? t`Superuser` : t`Regular user`}
                                </div>
                            </dd>
                        </div>
                        <div class="pf-c-description-list__group">
                            <dt class="pf-c-description-list__term">
                                <span class="pf-c-description-list__text">${t`Change status`}</span>
                            </dt>
                            <dd class="pf-c-description-list__description">
                                <div class="pf-c-description-list__text">
                                    <ak-user-active-form
                                        .obj=${item}
                                        objectLabel=${t`User`}
                                        .delete=${() => {
                                            return new CoreApi(
                                                DEFAULT_CONFIG,
                                            ).coreUsersPartialUpdate({
                                                id: item.pk || 0,
                                                patchedUserRequest: {
                                                    isActive: !item.isActive,
                                                },
                                            });
                                        }}
                                    >
                                        <button slot="trigger" class="pf-c-button pf-m-warning">
                                            ${item.isActive ? t`Deactivate` : t`Activate`}
                                        </button>
                                    </ak-user-active-form>
                                </div>
                            </dd>
                        </div>
                        <div class="pf-c-description-list__group">
                            <dt class="pf-c-description-list__term">
                                <span class="pf-c-description-list__text">${t`Recovery`}</span>
                            </dt>
                            <dd class="pf-c-description-list__description">
                                <div class="pf-c-description-list__text">
                                    <ak-forms-modal>
                                        <span slot="submit">${t`Update password`}</span>
                                        <span slot="header">${t`Update password`}</span>
                                        <ak-user-password-form
                                            slot="form"
                                            .instancePk=${item.pk}
                                        ></ak-user-password-form>
                                        <button slot="trigger" class="pf-c-button pf-m-secondary">
                                            ${t`Set password`}
                                        </button>
                                    </ak-forms-modal>
                                    ${rootInterface()?.tenant?.flowRecovery
                                        ? html`
                                              <ak-action-button
                                                  class="pf-m-secondary"
                                                  .apiRequest=${() => {
                                                      return new CoreApi(DEFAULT_CONFIG)
                                                          .coreUsersRecoveryRetrieve({
                                                              id: item.pk,
                                                          })
                                                          .then((rec) => {
                                                              showMessage({
                                                                  level: MessageLevel.success,
                                                                  message: t`Successfully generated recovery link`,
                                                                  description: rec.link,
                                                              });
                                                          })
                                                          .catch((ex: ResponseError) => {
                                                              ex.response.json().then(() => {
                                                                  showMessage({
                                                                      level: MessageLevel.error,
                                                                      message: t`No recovery flow is configured.`,
                                                                  });
                                                              });
                                                          });
                                                  }}
                                              >
                                                  ${t`Copy recovery link`}
                                              </ak-action-button>
                                              ${item.email
                                                  ? html`<ak-forms-modal
                                                        .closeAfterSuccessfulSubmit=${false}
                                                    >
                                                        <span slot="submit"> ${t`Send link`} </span>
                                                        <span slot="header">
                                                            ${t`Send recovery link to user`}
                                                        </span>
                                                        <ak-user-reset-email-form
                                                            slot="form"
                                                            .user=${item}
                                                        >
                                                        </ak-user-reset-email-form>
                                                        <button
                                                            slot="trigger"
                                                            class="pf-c-button pf-m-secondary"
                                                        >
                                                            ${t`Email recovery link`}
                                                        </button>
                                                    </ak-forms-modal>`
                                                  : html`<span
                                                        >${t`Recovery link cannot be emailed, user has no email address saved.`}</span
                                                    >`}
                                          `
                                        : html` <p>
                                              ${t`To let a user directly reset a their password, configure a recovery flow on the currently active tenant.`}
                                          </p>`}
                                </div>
                            </dd>
                        </div>
                    </dl>
                </div>
            </td>
            <td></td>
            <td></td>`;
    }

    renderToolbar(): TemplateResult {
        return html`
            ${this.targetGroup
                ? html`<ak-forms-modal>
                      <span slot="submit"> ${t`Add`} </span>
                      <span slot="header"> ${t`Add User`} </span>
                      ${this.targetGroup.isSuperuser
                          ? html`
                                <div class="pf-c-banner pf-m-warning" slot="above-form">
                                    ${t`Warning: This group is configured with superuser access. Added users will have superuser access.`}
                                </div>
                            `
                          : html``}
                      <ak-user-related-add .group=${this.targetGroup} slot="form">
                      </ak-user-related-add>
                      <button slot="trigger" class="pf-c-button pf-m-primary">
                          ${t`Add existing user`}
                      </button>
                  </ak-forms-modal>`
                : html``}
            <ak-dropdown class="pf-c-dropdown">
                <button class="pf-m-secondary pf-c-dropdown__toggle" type="button">
                    <span class="pf-c-dropdown__toggle-text">${t`Create user`}</span>
                    <i class="fas fa-caret-down pf-c-dropdown__toggle-icon" aria-hidden="true"></i>
                </button>
                <ul class="pf-c-dropdown__menu" hidden>
                    <li>
                        <ak-forms-modal>
                            <span slot="submit"> ${t`Create`} </span>
                            <span slot="header"> ${t`Create User`} </span>
                            <ak-user-form slot="form"> </ak-user-form>
                            <a slot="trigger" class="pf-c-dropdown__menu-item">
                                ${t`Create user`}
                            </a>
                        </ak-forms-modal>
                    </li>
                    <li>
                        <ak-forms-modal
                            .closeAfterSuccessfulSubmit=${false}
                            .cancelText=${t`Close`}
                        >
                            <span slot="submit"> ${t`Create`} </span>
                            <span slot="header"> ${t`Create Service account`} </span>
                            <ak-user-service-account slot="form"> </ak-user-service-account>
                            <a slot="trigger" class="pf-c-dropdown__menu-item">
                                ${t`Create Service account`}
                            </a>
                        </ak-forms-modal>
                    </li>
                </ul>
            </ak-dropdown>
            ${super.renderToolbar()}
        `;
    }

    renderToolbarAfter(): TemplateResult {
        return html`&nbsp;
            <div class="pf-c-toolbar__group pf-m-filter-group">
                <div class="pf-c-toolbar__item pf-m-search-filter">
                    <div class="pf-c-input-group">
                        <label class="pf-c-switch">
                            <input
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
                            <span class="pf-c-switch__label">${t`Hide service-accounts`}</span>
                        </label>
                    </div>
                </div>
            </div>`;
    }
}
