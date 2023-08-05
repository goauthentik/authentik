import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { uiConfig } from "@goauthentik/common/ui/config";
import { first } from "@goauthentik/common/utils";
import { PFColor } from "@goauthentik/elements/Label";
import "@goauthentik/elements/buttons/SpinnerButton";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import { TableColumn } from "@goauthentik/elements/table/Table";
import { TableModal } from "@goauthentik/elements/table/TableModal";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { CoreApi, User } from "@goauthentik/api";

@customElement("ak-group-member-select-table")
export class MemberSelectTable extends TableModal<User> {
    checkbox = true;
    checkboxChip = true;

    searchEnabled(): boolean {
        return true;
    }

    @property()
    confirm!: (selectedItems: User[]) => Promise<unknown>;

    order = "username";

    async apiEndpoint(page: number): Promise<PaginatedResponse<User>> {
        return new CoreApi(DEFAULT_CONFIG).coreUsersList({
            ordering: this.order,
            page: page,
            pageSize: (await uiConfig()).pagination.perPage,
            search: this.search || "",
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(msg("Name"), "username"),
            new TableColumn(msg("Active"), "is_active"),
            new TableColumn(msg("Last login"), "last_login"),
        ];
    }

    row(item: User): TemplateResult[] {
        return [
            html`<div>${item.username}</div>
                <small>${item.name}</small>`,
            html` <ak-label color=${item.isActive ? PFColor.Green : PFColor.Orange}>
                ${item.isActive ? msg("Yes") : msg("No")}
            </ak-label>`,
            html`${first(item.lastLogin?.toLocaleString(), msg("-"))}`,
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
