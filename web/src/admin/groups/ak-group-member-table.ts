import "#components/ak-status-label";
import "#elements/buttons/SpinnerButton/index";
import "#elements/table/ak-table-filter-select";

import { aki } from "#common/api/client";

import { FilterOption } from "#elements/table/ak-table-filter-select";
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

@customElement("ak-group-member-table")
export class GroupMemberSelectTable extends Table<User> {
    static styles = [
        ...super.styles,
        css`
            [part="toolbar"] {
                gap: var(--pf-global--spacer--md);
            }
        `,
    ];

    public override searchPlaceholder = msg("Search for users by username or display name...");
    public override searchLabel = msg("Search Users");
    public override label = msg("Select Users");
    public override supportsQL = true;

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

        return aki(CoreApi).coreUsersList({
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
        return html`<div class="pf-c-toolbar__group pf-m-filter-group">
            <div class="pf-c-toolbar__item pf-m-search-filter">
                <ak-table-filter-select
                    .options=${[
                        { label: msg("Active"), value: "active" as const },
                        { label: msg("All"), value: "all" as const },
                    ]}
                    group=${msg("User status")}
                    .value=${this.userListFilter}
                    @change=${(ev: CustomEvent<FilterOption<UserListFilter>>) => {
                        this.userListFilter = ev.detail.value;
                        this.page = 1;
                        this.fetch();
                    }}
                ></ak-table-filter-select>
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
        "ak-group-member-table": GroupMemberSelectTable;
    }
}
