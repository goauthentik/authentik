import { t } from "@lingui/macro";
import { CoreApi, User } from "authentik-api";
import { customElement, property } from "lit-element";
import { TemplateResult, html } from "lit-html";
import { AKResponse } from "../../api/Client";
import { DEFAULT_CONFIG } from "../../api/Config";
import { PAGE_SIZE } from "../../constants";
import { TableColumn } from "../../elements/table/Table";
import { TableModal } from "../../elements/table/TableModal";
import "../../elements/buttons/SpinnerButton";
import { first } from "../../utils";

@customElement("ak-group-member-select-table")
export class MemberSelectTable extends TableModal<User> {
    checkbox = true;

    searchEnabled(): boolean {
        return true;
    }

    @property()
    confirm!: (selectedItems: User[]) => Promise<unknown>;

    order = "username";

    apiEndpoint(page: number): Promise<AKResponse<User>> {
        return new CoreApi(DEFAULT_CONFIG).coreUsersList({
            ordering: this.order,
            page: page,
            pageSize: PAGE_SIZE / 2,
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
            html`${item.isActive ? t`Yes` : t`No`}`,
            html`${first(item.lastLogin?.toLocaleString(), "-")}`,
        ];
    }

    renderSelectedChip(item: User): TemplateResult {
        return html`${item.username}`;
    }

    renderModalInner(): TemplateResult {
        return html`<section class="pf-c-page__main-section pf-m-light">
                <div class="pf-c-content">
                    <h1 class="pf-c-title pf-m-2xl">${t`Select users to add`}</h1>
                </div>
            </section>
            <section class="pf-c-page__main-section pf-m-light">${this.renderTable()}</section>
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
