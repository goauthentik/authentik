import { DEFAULT_CONFIG } from "@goauthentik/common/api/config.js";
import { getRelativeTime } from "@goauthentik/common/utils.js";
import "@goauthentik/components/ak-status-label";
import "@goauthentik/elements/buttons/SpinnerButton";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import { TableColumn } from "@goauthentik/elements/table/Table";
import { TableModal } from "@goauthentik/elements/table/TableModal";
import { match } from "ts-pattern";

import { msg } from "@lit/localize";
import { TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { CoreApi, CoreUsersListRequest, User } from "@goauthentik/api";

// Leaving room in the future for a multi-state control if someone somehow needs to filter inactive
// users as well.
type UserListFilter = "active" | "all";
type UserListRequestFilter = Partial<Pick<CoreUsersListRequest, "isActive">>;

@customElement("ak-group-member-select-table")
export class MemberSelectTable extends TableModal<User> {
    static get styles() {
        return [
            ...super.styles,
            css`
                .show-disabled-toggle-group {
                    margin-inline-start: 0.5rem;
                }
            `,
        ];
    }

    checkbox = true;
    checkboxChip = true;

    searchEnabled(): boolean {
        return true;
    }

    @property()
    confirm!: (selectedItems: User[]) => Promise<unknown>;

    userListFilter: UserListFilter = "active";

    order = "username";

    // The `userListRequestFilter` clause is necessary because the back-end for searches is
    // tri-state: `isActive: true` will only show active users, `isActive: false` will show only
    // inactive users; only when it's _missing_ will you get all users.
    async apiEndpoint(): Promise<PaginatedResponse<User>> {
        const userListRequestFilter: UserListRequestFilter = match(this.userListFilter)
            .with("all", () => ({}))
            .with("active", () => ({ isActive: true }))
            .exhaustive();

        return new CoreApi(DEFAULT_CONFIG).coreUsersList({
            ...(await this.defaultEndpointConfig()),
            ...userListRequestFilter,
            includeGroups: false,
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(msg("Name"), "username"),
            new TableColumn(msg("Active"), "is_active"),
            new TableColumn(msg("Last login"), "last_login"),
        ];
    }

    renderToolbarAfter() {
        const toggleShowDisabledUsers = () => {
            this.userListFilter = this.userListFilter === "all" ? "active" : "all";
            this.page = 1;
            this.fetch();
        };

        return html`&nbsp;
            <div class="pf-c-toolbar__group pf-m-filter-group">
                <div class="pf-c-toolbar__item pf-m-search-filter">
                    <div class="pf-c-input-group show-disabled-toggle-group">
                        <label class="pf-c-switch">
                            <input
                                class="pf-c-switch__input"
                                type="checkbox"
                                ?checked=${this.userListFilter === "all"}
                                @change=${toggleShowDisabledUsers}
                            />
                            <span class="pf-c-switch__toggle">
                                <span class="pf-c-switch__toggle-icon">
                                    <i class="fas fa-check" aria-hidden="true"></i>
                                </span>
                            </span>
                            <span class="pf-c-switch__label">${msg("Show inactive users")}</span>
                        </label>
                    </div>
                </div>
            </div>`;
    }

    row(item: User): TemplateResult[] {
        return [
            html`<div>${item.username}</div>
                <small>${item.name}</small>`,
            html` <ak-status-label type="warning" ?good=${item.isActive}></ak-status-label>`,
            html`${item.lastLogin
                ? html`<div>${getRelativeTime(item.lastLogin)}</div>
                      <small>${item.lastLogin.toLocaleString()}</small>`
                : msg("-")}`,
        ];
    }

    renderSelectedChip(item: User): TemplateResult {
        return html`${item.username}`;
    }

    renderModalInner(): TemplateResult {
        return html`<section class="pf-c-modal-box__header pf-c-page__main-section pf-m-light">
                <div class="pf-c-content">
                    <h1 class="pf-c-title pf-m-2xl">${msg("Select users to add")}</h1>
                </div>
            </section>
            <section class="pf-c-modal-box__body pf-m-light">${this.renderTable()}</section>
            <footer class="pf-c-modal-box__footer">
                <ak-spinner-button
                    .callAction=${() => {
                        return this.confirm(this.selectedElements).then(() => {
                            this.open = false;
                        });
                    }}
                    class="pf-m-primary"
                >
                    ${msg("Add")} </ak-spinner-button
                >&nbsp;
                <ak-spinner-button
                    .callAction=${async () => {
                        this.open = false;
                    }}
                    class="pf-m-secondary"
                >
                    ${msg("Cancel")}
                </ak-spinner-button>
            </footer>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-group-member-select-table": MemberSelectTable;
    }
}
