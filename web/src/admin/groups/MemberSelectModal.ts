import "#components/ak-status-label";
import "#elements/buttons/SpinnerButton/index";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, TableColumn, Timestamp } from "#elements/table/Table";
import { TableModal } from "#elements/table/TableModal";
import { SlottedTemplateResult } from "#elements/types";

import { CoreApi, CoreUsersListRequest, User } from "@goauthentik/api";

import { match } from "ts-pattern";

import { msg } from "@lit/localize";
import { css, html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

// Leaving room in the future for a multi-state control if someone somehow needs to filter inactive
// users as well.
type UserListFilter = "active" | "all";
type UserListRequestFilter = Partial<Pick<CoreUsersListRequest, "isActive">>;

@customElement("ak-group-member-select-table")
export class MemberSelectTable extends TableModal<User> {
    public override searchPlaceholder = msg("Search for users by username or display name...");
    public override searchLabel = msg("Search Users");
    public override label = msg("Select Users");
    static styles = [
        ...super.styles,
        css`
            .show-disabled-toggle-group {
                margin-inline-start: 0.5rem;
            }

            [part="toolbar"] {
                gap: var(--pf-global--spacer--md);
            }
        `,
    ];
    public supportsQL = true;

    checkbox = true;
    checkboxChip = true;

    protected override searchEnabled = true;

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

    protected override rowLabel(item: User): string | null {
        return item.username ?? item.name ?? null;
    }

    protected columns: TableColumn[] = [
        [msg("Name"), "username"],
        [msg("Active"), "is_active"],
        [msg("Last login"), "last_login"],
    ];

    renderToolbarAfter() {
        const toggleShowDisabledUsers = () => {
            this.userListFilter = this.userListFilter === "all" ? "active" : "all";
            this.page = 1;
            this.fetch();
        };

        return html`<div class="pf-c-toolbar__group pf-m-filter-group">
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

    row(item: User): SlottedTemplateResult[] {
        return [
            html`<div>${item.username}</div>
                <small>${item.name}</small>`,
            html` <ak-status-label type="warning" ?good=${item.isActive}></ak-status-label>`,
            Timestamp(item.lastLogin),
        ];
    }

    renderSelectedChip(item: User): TemplateResult {
        return html`${item.username}`;
    }

    renderModalInner(): TemplateResult {
        return html`<div class="pf-c-modal-box__header pf-c-page__main-section pf-m-light">
                <div class="pf-c-content">
                    <h1 id="modal-title" class="pf-c-title pf-m-2xl">${msg("Select users")}</h1>
                </div>
            </div>
            <div class="pf-c-modal-box__body pf-m-light">${this.renderTable()}</div>
            <fieldset class="pf-c-modal-box__footer">
                <legend class="sr-only">${msg("Form actions")}</legend>
                <ak-spinner-button
                    .callAction=${() => {
                        return this.confirm(this.selectedElements).then(() => {
                            this.open = false;
                        });
                    }}
                    class="pf-m-primary"
                    >${msg("Confirm")}</ak-spinner-button
                >
                <ak-spinner-button
                    .callAction=${async () => {
                        this.open = false;
                    }}
                    class="pf-m-secondary"
                    >${msg("Cancel")}</ak-spinner-button
                >
            </fieldset>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-group-member-select-table": MemberSelectTable;
    }
}
