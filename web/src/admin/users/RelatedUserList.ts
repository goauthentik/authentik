import "@goauthentik/admin/users/ServiceAccountForm";
import "@goauthentik/admin/users/UserActiveForm";
import "@goauthentik/admin/users/UserForm";
import "@goauthentik/admin/users/UserPasswordForm";
import "@goauthentik/admin/users/UserResetEmailForm";
import { DEFAULT_CONFIG, config, tenant } from "@goauthentik/common/api/config";
import { MessageLevel } from "@goauthentik/common/messages";
import { uiConfig } from "@goauthentik/common/ui/config";
import { me } from "@goauthentik/common/users";
import { first } from "@goauthentik/common/utils";
import { PFColor } from "@goauthentik/elements/Label";
import "@goauthentik/elements/buttons/ActionButton";
import "@goauthentik/elements/forms/DeleteBulkForm";
import "@goauthentik/elements/forms/ModalForm";
import { showMessage } from "@goauthentik/elements/messages/MessageContainer";
import { getURLParam, updateURLParams } from "@goauthentik/elements/router/RouteMatch";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import { Table, TableColumn } from "@goauthentik/elements/table/Table";

import { msg, str } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { until } from "lit/directives/until.js";

import PFAlert from "@patternfly/patternfly/components/Alert/alert.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";

import { CapabilitiesEnum, CoreApi, ResponseError, User } from "@goauthentik/api";

@customElement("ak-user-related-list")
export class RelatedUserList extends Table<User> {
    expandable = true;
    checkbox = true;

    searchEnabled(): boolean {
        return true;
    }

    @property()
    groupUuid?: string;

    @property()
    order = "last_login";

    @property({ type: Boolean })
    hideServiceAccounts = getURLParam<boolean>("hideServiceAccounts", true);

    static get styles(): CSSResult[] {
        return super.styles.concat(PFDescriptionList, PFAlert);
    }

    async apiEndpoint(page: number): Promise<PaginatedResponse<User>> {
        return new CoreApi(DEFAULT_CONFIG).coreUsersList({
            ordering: this.order,
            page: page,
            pageSize: (await uiConfig()).pagination.perPage,
            search: this.search || "",
            groupsByPk: this.groupUuid ? [this.groupUuid] : [],
            attributes: this.hideServiceAccounts
                ? JSON.stringify({
                      "goauthentik.io/user/service-account__isnull": true,
                  })
                : undefined,
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(msg("Name"), "username"),
            new TableColumn(msg("Active"), "active"),
            new TableColumn(msg("Last login"), "last_login"),
            new TableColumn(msg("Actions")),
        ];
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${msg("User(s)")}
            .objects=${this.selectedElements}
            .metadata=${(item: User) => {
                return [
                    { key: msg("Username"), value: item.username },
                    { key: msg("ID"), value: item.pk.toString() },
                    { key: msg("UID"), value: item.uid },
                ];
            }}
            .usedBy=${(item: User) => {
                return new CoreApi(DEFAULT_CONFIG).coreUsersUsedByList({
                    id: item.pk,
                });
            }}
            .delete=${(item: User) => {
                return new CoreApi(DEFAULT_CONFIG).coreUsersDestroy({
                    id: item.pk,
                });
            }}
        >
            ${until(
                me().then((user) => {
                    const shouldShowWarning = this.selectedElements.find((el) => {
                        return el.pk === user.user.pk || el.pk == user.original?.pk;
                    });
                    if (shouldShowWarning) {
                        return html`
                            <div slot="notice" class="pf-c-form__alert">
                                <div class="pf-c-alert pf-m-inline pf-m-warning">
                                    <div class="pf-c-alert__icon">
                                        <i class="fas fa-exclamation-circle"></i>
                                    </div>
                                    <h4 class="pf-c-alert__title">
                                        ${msg(
                                            str`Warning: You're about to delete the user you're logged in as (${shouldShowWarning.username}). Proceed at your own risk.`,
                                        )}
                                    </h4>
                                </div>
                            </div>
                        `;
                    }
                    return html``;
                }),
            )}
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
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
                ${item.isActive ? msg("Yes") : msg("No")}
            </ak-label>`,
            html`${first(item.lastLogin?.toLocaleString(), msg("-"))}`,
            html`<ak-forms-modal>
                    <span slot="submit"> ${msg("Update")} </span>
                    <span slot="header"> ${msg("Update User")} </span>
                    <ak-user-form slot="form" .instancePk=${item.pk}> </ak-user-form>
                    <button slot="trigger" class="pf-c-button pf-m-plain">
                        <i class="fas fa-edit"></i>
                    </button>
                </ak-forms-modal>
                ${until(
                    config().then((config) => {
                        if (config.capabilities.includes(CapabilitiesEnum.Impersonate)) {
                            return html`<a
                                class="pf-c-button pf-m-tertiary"
                                href="${`/-/impersonation/${item.pk}/`}"
                            >
                                ${msg("Impersonate")}
                            </a>`;
                        }
                        return html``;
                    }),
                )}`,
        ];
    }

    renderExpanded(item: User): TemplateResult {
        return html`<td role="cell" colspan="3">
                <div class="pf-c-table__expandable-row-content">
                    <dl class="pf-c-description-list pf-m-horizontal">
                        <div class="pf-c-description-list__group">
                            <dt class="pf-c-description-list__term">
                                <span class="pf-c-description-list__text"
                                    >${msg("User status")}</span
                                >
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
                                <span class="pf-c-description-list__text"
                                    >${msg("Change status")}</span
                                >
                            </dt>
                            <dd class="pf-c-description-list__description">
                                <div class="pf-c-description-list__text">
                                    <ak-user-active-form
                                        .obj=${item}
                                        objectLabel=${msg("User")}
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
                                        <span slot="header">${msg("Update password")}</span>
                                        <ak-user-password-form
                                            slot="form"
                                            .instancePk=${item.pk}
                                        ></ak-user-password-form>
                                        <button slot="trigger" class="pf-c-button pf-m-secondary">
                                            ${msg("Set password")}
                                        </button>
                                    </ak-forms-modal>
                                    ${until(
                                        tenant().then((tenant) => {
                                            if (!tenant.flowRecovery) {
                                                return html`
                                                    <p>
                                                        ${msg(
                                                            "To let a user directly reset a their password, configure a recovery flow on the currently active tenant.",
                                                        )}
                                                    </p>
                                                `;
                                            }
                                            return html`
                                                <ak-action-button
                                                    class="pf-m-secondary"
                                                    .apiRequest=${() => {
                                                        return new CoreApi(DEFAULT_CONFIG)
                                                            .coreUsersRecoveryRetrieve({
                                                                id: item.pk || 0,
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
                                                            .catch((ex: ResponseError) => {
                                                                ex.response.json().then(() => {
                                                                    showMessage({
                                                                        level: MessageLevel.error,
                                                                        message: msg(
                                                                            "No recovery flow is configured.",
                                                                        ),
                                                                    });
                                                                });
                                                            });
                                                    }}
                                                >
                                                    ${msg("Copy recovery link")}
                                                </ak-action-button>
                                                ${item.email
                                                    ? html`<ak-forms-modal
                                                          .closeAfterSuccessfulSubmit=${false}
                                                      >
                                                          <span slot="submit">
                                                              ${msg("Send link")}
                                                          </span>
                                                          <span slot="header">
                                                              ${msg("Send recovery link to user")}
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
                                                              ${msg("Email recovery link")}
                                                          </button>
                                                      </ak-forms-modal>`
                                                    : html`<span
                                                          >${msg(
                                                              "Recovery link cannot be emailed, user has no email address saved.",
                                                          )}</span
                                                      >`}
                                            `;
                                        }),
                                    )}
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
            <ak-forms-modal>
                <span slot="submit"> ${msg("Create")} </span>
                <span slot="header"> ${msg("Create User")} </span>
                <ak-user-form slot="form"> </ak-user-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">${msg("Create")}</button>
            </ak-forms-modal>
            <ak-forms-modal .closeAfterSuccessfulSubmit=${false} .cancelText=${msg("Close")}>
                <span slot="submit"> ${msg("Create")} </span>
                <span slot="header"> ${msg("Create Service account")} </span>
                <ak-user-service-account slot="form"> </ak-user-service-account>
                <button slot="trigger" class="pf-c-button pf-m-secondary">
                    ${msg("Create Service account")}
                </button>
            </ak-forms-modal>
            ${super.renderToolbar()}
        `;
    }

    renderToolbarAfter(): TemplateResult {
        return html`&nbsp;
            <div class="pf-c-toolbar__group pf-m-filter-group">
                <div class="pf-c-toolbar__item pf-m-search-filter">
                    <div class="pf-c-input-group">
                        <div class="pf-c-check">
                            <input
                                class="pf-c-check__input"
                                type="checkbox"
                                id="hide-service-accounts"
                                name="hide-service-accounts"
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
                            <label class="pf-c-check__label" for="hide-service-accounts">
                                ${msg("Hide service-accounts")}
                            </label>
                        </div>
                    </div>
                </div>
            </div>`;
    }
}
