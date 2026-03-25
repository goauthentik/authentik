import "#components/ak-status-label";
import "#elements/buttons/SpinnerButton/index";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, Table, TableColumn, Timestamp } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { CoreApi, CoreUsersListRequest, User } from "@goauthentik/api";

import { match } from "ts-pattern";

import { msg } from "@lit/localize";
import { css, html } from "lit";
import { customElement } from "lit/decorators.js";

// Leaving room in the future for a multi-state control if someone somehow needs to filter inactive
// users as well.
type UserListFilter = "active" | "all";
type UserListRequestFilter = Partial<Pick<CoreUsersListRequest, "isActive">>;

@customElement("ak-group-member-select-form")
export class MemberSelectForm extends Table<User> {
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

    public override searchPlaceholder = msg("Search for users by username or display name...");
    public override searchLabel = msg("Search Users");
    public override label = msg("Select Users");
    public overridesupportsQL = true;

    public override checkbox = true;
    public override checkboxChip = true;

    protected override searchEnabled = true;

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

    renderSelectedChip(item: User): SlottedTemplateResult {
        return item.username;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-group-member-select-form": MemberSelectForm;
    }
}
