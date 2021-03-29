import { gettext } from "django";
import { customElement, html, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../api/Client";
import { TablePage } from "../../elements/table/TablePage";

import "../../elements/forms/ModalForm";
import "../../elements/buttons/Dropdown";
import "../../elements/buttons/ActionButton";
import { TableColumn } from "../../elements/table/Table";
import { PAGE_SIZE } from "../../constants";
import { CoreApi, User } from "authentik-api";
import { DEFAULT_CONFIG } from "../../api/Config";
import "../../elements/forms/DeleteForm";
import "./UserActiveForm";
import "./UserForm";
import { showMessage } from "../../elements/messages/MessageContainer";
import { MessageLevel } from "../../elements/messages/Message";

@customElement("ak-user-list")
export class UserListPage extends TablePage<User> {
    searchEnabled(): boolean {
        return true;
    }
    pageTitle(): string {
        return gettext("Users");
    }
    pageDescription(): string {
        return "";
    }
    pageIcon(): string {
        return "pf-icon pf-icon-user";
    }

    @property()
    order = "last_login";

    apiEndpoint(page: number): Promise<AKResponse<User>> {
        return new CoreApi(DEFAULT_CONFIG).coreUsersList({
            ordering: this.order,
            page: page,
            pageSize: PAGE_SIZE,
            search: this.search || "",
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn("Name", "username"),
            new TableColumn("Active", "active"),
            new TableColumn("Last login", "last_login"),
            new TableColumn(""),
        ];
    }

    row(item: User): TemplateResult[] {
        return [
            html`<a href="#/identity/users/${item.pk}">
                <div>${item.username}</div>
                <small>${item.name}</small>
            </a>`,
            html`${item.isActive ? "Yes" : "No"}`,
            html`${item.lastLogin?.toLocaleString()}`,
            html`
            <ak-forms-modal>
                <span slot="submit">
                    ${gettext("Update")}
                </span>
                <span slot="header">
                    ${gettext("Update User")}
                </span>
                <ak-user-form slot="form" .user=${item}>
                </ak-user-form>
                <button slot="trigger" class="pf-m-secondary pf-c-button">
                    ${gettext("Edit")}
                </button>
            </ak-forms-modal>
            <ak-dropdown class="pf-c-dropdown">
                <button class="pf-c-dropdown__toggle pf-m-primary" type="button">
                    <span class="pf-c-dropdown__toggle-text">${gettext(item.isActive ? "Disable" : "Enable")}</span>
                    <i class="fas fa-caret-down pf-c-dropdown__toggle-icon" aria-hidden="true"></i>
                </button>
                <ul class="pf-c-dropdown__menu" hidden>
                    <li>
                        <ak-user-active-form
                            .obj=${item}
                            objectLabel=${gettext("User")}
                            .delete=${() => {
                                return new CoreApi(DEFAULT_CONFIG).coreUsersPartialUpdate({
                                    id: item.pk || 0,
                                    data: {
                                        username: item.username,
                                        name: item.name,
                                        isActive: !item.isActive,
                                    }
                                });
                            }}>
                            <button slot="trigger" class="pf-c-dropdown__menu-item">
                                ${item.isActive ? gettext("Disable") : gettext("Enable")}
                            </button>
                        </ak-user-active-form>
                    </li>
                    <li class="pf-c-divider" role="separator"></li>
                    <li>
                        <ak-forms-delete
                            .obj=${item}
                            objectLabel=${gettext("User")}
                            .delete=${() => {
                                return new CoreApi(DEFAULT_CONFIG).coreUsersDelete({
                                    id: item.pk || 0
                                });
                            }}>
                            <button slot="trigger" class="pf-c-dropdown__menu-item">
                                ${gettext("Delete")}
                            </button>
                        </ak-forms-delete>
                    </li>
                </ul>
            </ak-dropdown>
            <ak-action-button
                .apiRequest=${() => {
                    return new CoreApi(DEFAULT_CONFIG).coreUsersRecovery({
                        id: item.pk || 0,
                    }).then(rec => {
                        showMessage({
                            level: MessageLevel.success,
                            message: gettext("Successfully generated recovery link"),
                            description: rec.link
                        });
                    });
                }}>
                ${gettext("Reset Password")}
            </ak-action-button>
            <a class="pf-c-button pf-m-tertiary" href="${`/-/impersonation/${item.pk}/`}">
                ${gettext("Impersonate")}
            </a>`,
        ];
    }

    renderToolbar(): TemplateResult {
        return html`
        <ak-forms-modal>
            <span slot="submit">
                ${gettext("Create")}
            </span>
            <span slot="header">
                ${gettext("Create User")}
            </span>
            <ak-user-form slot="form">
            </ak-user-form>
            <button slot="trigger" class="pf-c-button pf-m-primary">
                ${gettext("Create")}
            </button>
        </ak-forms-modal>
        ${super.renderToolbar()}
        `;
    }

}
