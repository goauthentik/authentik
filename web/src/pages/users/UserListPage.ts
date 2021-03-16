import { gettext } from "django";
import { customElement, html, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../api/Client";
import { TablePage } from "../../elements/table/TablePage";

import "../../elements/buttons/ModalButton";
import "../../elements/buttons/Dropdown";
import "../../elements/buttons/ActionButton";
import { TableColumn } from "../../elements/table/Table";
import { PAGE_SIZE } from "../../constants";
import { CoreApi, User } from "authentik-api";
import { DEFAULT_CONFIG } from "../../api/Config";
import { AdminURLManager } from "../../api/legacy";

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
        return gettext("pf-icon pf-icon-user");
    }

    @property()
    order = "username";

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
            html`<div>
                <div>${item.username}</div>
                <small>${item.name}</small>
            </div>`,
            html`${item.isActive ? "Yes" : "No"}`,
            html`${item.lastLogin?.toLocaleString()}`,
            html`
            <ak-modal-button href="${AdminURLManager.users(`${item.pk}/update/`)}">
                <ak-spinner-button slot="trigger" class="pf-m-secondary">
                    ${gettext("Edit")}
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>
            <ak-dropdown class="pf-c-dropdown">
                <button class="pf-c-dropdown__toggle pf-m-primary" type="button">
                    <span class="pf-c-dropdown__toggle-text">${gettext(item.isActive ? "Disable" : "Enable")}</span>
                    <i class="fas fa-caret-down pf-c-dropdown__toggle-icon" aria-hidden="true"></i>
                </button>
                <ul class="pf-c-dropdown__menu" hidden>
                    <li>
                        ${item.isActive ?
                            html`<ak-modal-button href="${AdminURLManager.users(`${item.pk}/disable/`)}">
                                <button slot="trigger" class="pf-c-dropdown__menu-item">
                                    ${gettext("Disable")}
                                </button>
                                <div slot="modal"></div>
                            </ak-modal-button>`:
                            html`<ak-modal-button href="${AdminURLManager.users(`${item.pk}/enable/`)}">
                                <button slot="trigger" class="pf-c-dropdown__menu-item">
                                    ${gettext("Enable")}
                                </button>
                                <div slot="modal"></div>
                            </ak-modal-button>`}
                    </li>
                    <li class="pf-c-divider" role="separator"></li>
                    <li>
                        <ak-modal-button href="${AdminURLManager.users(`${item.pk}/delete/`)}">
                            <button slot="trigger" class="pf-c-dropdown__menu-item">
                                ${gettext("Delete")}
                            </button>
                            <div slot="modal"></div>
                        </ak-modal-button>
                    </li>
                </ul>
            </ak-dropdown>
            <ak-action-button method="GET" url="${AdminURLManager.users(`${item.pk}/reset/`)}">
                ${gettext("Reset Password")}
            </ak-action-button>
            <a class="pf-c-button pf-m-tertiary" href="${`-/impersonation/${item.pk}/`}">
                ${gettext("Impersonate")}
            </a>`,
        ];
    }

    renderToolbar(): TemplateResult {
        return html`
        <ak-modal-button href=${AdminURLManager.users("create/")}>
            <ak-spinner-button slot="trigger" class="pf-m-primary">
                ${gettext("Create")}
            </ak-spinner-button>
            <div slot="modal"></div>
        </ak-modal-button>
        ${super.renderToolbar()}
        `;
    }
}
