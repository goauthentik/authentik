import { AKResponse } from "@goauthentik/web/api/Client";
import { DEFAULT_CONFIG } from "@goauthentik/web/api/Config";
import { uiConfig } from "@goauthentik/web/common/config";
import { PFColor } from "@goauthentik/web/elements/Label";
import "@goauthentik/web/elements/buttons/SpinnerButton";
import { TableColumn } from "@goauthentik/web/elements/table/Table";
import { TableModal } from "@goauthentik/web/elements/table/TableModal";
import { first } from "@goauthentik/web/utils";

import { t } from "@lingui/macro";

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

    async apiEndpoint(page: number): Promise<AKResponse<User>> {
        return new CoreApi(DEFAULT_CONFIG).coreUsersList({
            ordering: this.order,
            page: page,
            pageSize: (await uiConfig()).pagination.perPage,
            search: this.search || "",
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(t`Name`, "username"),
            new TableColumn(t`Active`, "active"),
            new TableColumn(t`Last login`, "last_login"),
        ];
    }

    row(item: User): TemplateResult[] {
        return [
            html`<div>
                <div>${item.username}</div>
                <small>${item.name}</small>
            </div>`,
            html` <ak-label color=${item.isActive ? PFColor.Green : PFColor.Orange}>
                ${item.isActive ? t`Yes` : t`No`}
            </ak-label>`,
            html`${first(item.lastLogin?.toLocaleString(), t`-`)}`,
        ];
    }

    renderSelectedChip(item: User): TemplateResult {
        return html`${item.username}`;
    }

    renderModalInner(): TemplateResult {
        return html`<section class="pf-c-modal-box__header pf-c-page__main-section pf-m-light">
                <div class="pf-c-content">
                    <h1 class="pf-c-title pf-m-2xl">${t`Select users to add`}</h1>
                </div>
            </section>
            <section class="pf-c-modal-box__body pf-c-page__main-section pf-m-light">
                ${this.renderTable()}
            </section>
            <footer class="pf-c-modal-box__footer">
                <ak-spinner-button
                    .callAction=${() => {
                        return this.confirm(this.selectedElements).then(() => {
                            this.open = false;
                        });
                    }}
                    class="pf-m-primary"
                >
                    ${t`Add`} </ak-spinner-button
                >&nbsp;
                <ak-spinner-button
                    .callAction=${async () => {
                        this.open = false;
                    }}
                    class="pf-m-secondary"
                >
                    ${t`Cancel`}
                </ak-spinner-button>
            </footer>`;
    }
}
