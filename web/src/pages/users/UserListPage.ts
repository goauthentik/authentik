import { t } from "@lingui/macro";
import { customElement, html, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../api/Client";
import { TablePage } from "../../elements/table/TablePage";

import "../../elements/forms/ModalForm";
import "../../elements/buttons/Dropdown";
import "../../elements/buttons/ActionButton";
import { TableColumn } from "../../elements/table/Table";
import { PAGE_SIZE } from "../../constants";
import { CoreApi, User } from "authentik-api";
import { DEFAULT_CONFIG, tenant } from "../../api/Config";
import "../../elements/forms/DeleteForm";
import "./UserActiveForm";
import "./UserForm";
import { showMessage } from "../../elements/messages/MessageContainer";
import { MessageLevel } from "../../elements/messages/Message";
import { first } from "../../utils";
import { until } from "lit-html/directives/until";

@customElement("ak-user-list")
export class UserListPage extends TablePage<User> {
    searchEnabled(): boolean {
        return true;
    }
    pageTitle(): string {
        return t`Users`;
    }
    pageDescription(): string {
        return "";
    }
    pageIcon(): string {
        return "pf-icon pf-icon-user";
    }

    @property()
    order = "last_login";

    @property({ type: Boolean })
    hideServiceAccounts = true;

    apiEndpoint(page: number): Promise<AKResponse<User>> {
        return new CoreApi(DEFAULT_CONFIG).coreUsersList({
            ordering: this.order,
            page: page,
            pageSize: PAGE_SIZE,
            search: this.search || "",
            attributes: this.hideServiceAccounts ? JSON.stringify({
                "goauthentik.io/user/service-account__isnull": "true"
            }) : undefined
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(t`Name`, "username"),
            new TableColumn(t`Active`, "active"),
            new TableColumn(t`Last login`, "last_login"),
            new TableColumn(""),
        ];
    }

    row(item: User): TemplateResult[] {
        return [
            html`<a href="#/identity/users/${item.pk}">
                <div>${item.username}</div>
                <small>${item.name}</small>
            </a>`,
            html`${item.isActive ? t`Yes` : t`No`}`,
            html`${first(item.lastLogin?.toLocaleString(), "-")}`,
            html`
            <ak-forms-modal>
                <span slot="submit">
                    ${t`Update`}
                </span>
                <span slot="header">
                    ${t`Update User`}
                </span>
                <ak-user-form slot="form" .instancePk=${item.pk}>
                </ak-user-form>
                <button slot="trigger" class="pf-m-secondary pf-c-button">
                    ${t`Edit`}
                </button>
            </ak-forms-modal>
            <ak-dropdown class="pf-c-dropdown">
                <button class="pf-m-primary pf-c-dropdown__toggle" type="button">
                    <span class="pf-c-dropdown__toggle-text">${item.isActive ? t`Disable` : t`Enable`}</span>
                    <i class="fas fa-caret-down pf-c-dropdown__toggle-icon" aria-hidden="true"></i>
                </button>
                <ul class="pf-c-dropdown__menu" hidden>
                    <li>
                        <ak-user-active-form
                            .obj=${item}
                            objectLabel=${t`User`}
                            .delete=${() => {
                                return new CoreApi(DEFAULT_CONFIG).coreUsersPartialUpdate({
                                    id: item.pk || 0,
                                    patchedUserRequest: {
                                        username: item.username,
                                        name: item.name,
                                        isActive: !item.isActive,
                                    }
                                });
                            }}>
                            <button slot="trigger" class="pf-c-dropdown__menu-item">
                                ${item.isActive ? t`Disable` : t`Enable`}
                            </button>
                        </ak-user-active-form>
                    </li>
                    <li class="pf-c-divider" role="separator"></li>
                    <li>
                        <ak-forms-delete
                            .obj=${item}
                            objectLabel=${t`User`}
                            .usedBy=${() => {
                                return new CoreApi(DEFAULT_CONFIG).coreUsersUsedByList({
                                    id: item.pk
                                });
                            }}
                            .delete=${() => {
                                return new CoreApi(DEFAULT_CONFIG).coreUsersDestroy({
                                    id: item.pk
                                });
                            }}>
                            <button slot="trigger" class="pf-c-dropdown__menu-item">
                                ${t`Delete`}
                            </button>
                        </ak-forms-delete>
                    </li>
                </ul>
            </ak-dropdown>
            ${until(tenant().then(te => {
                if (te.flowRecovery) {
                    return html`
                        <ak-action-button
                            .apiRequest=${() => {
                                return new CoreApi(DEFAULT_CONFIG).coreUsersRecoveryRetrieve({
                                    id: item.pk || 0,
                                }).then(rec => {
                                    showMessage({
                                        level: MessageLevel.success,
                                        message: t`Successfully generated recovery link`,
                                        description: rec.link
                                    });
                                }).catch((ex: Response) => {
                                    ex.json().then(() => {
                                        showMessage({
                                            level: MessageLevel.error,
                                            message: t`No recovery flow is configured.`,
                                        });
                                    });
                                });
                            }}>
                            ${t`Reset Password`}
                        </ak-action-button>`;
                }
                return html``;
            }))}
            <a class="pf-c-button pf-m-tertiary" href="${`/-/impersonation/${item.pk}/`}">
                ${t`Impersonate`}
            </a>`,
        ];
    }

    renderToolbar(): TemplateResult {
        return html`
        <ak-forms-modal>
            <span slot="submit">
                ${t`Create`}
            </span>
            <span slot="header">
                ${t`Create User`}
            </span>
            <ak-user-form slot="form">
            </ak-user-form>
            <button slot="trigger" class="pf-c-button pf-m-primary">
                ${t`Create`}
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
                        <input class="pf-c-check__input"
                            type="checkbox"
                            id="hide-service-accounts"
                            name="hide-service-accounts"
                            ?checked=${this.hideServiceAccounts}
                            @change=${() => {
                                this.hideServiceAccounts = !this.hideServiceAccounts;
                                this.page = 1;
                                this.fetch();
                            }} />
                        <label class="pf-c-check__label" for="hide-service-accounts">
                            ${t`Hide service-accounts`}
                        </label>
                    </div>
                </div>
            </div>
        </div>`;
    }

}
