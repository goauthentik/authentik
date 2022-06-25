import { AKResponse } from "@goauthentik/web/api/Client";
import { DEFAULT_CONFIG } from "@goauthentik/web/api/Config";
import { uiConfig } from "@goauthentik/web/common/config";
import { PFColor } from "@goauthentik/web/elements/Label";
import "@goauthentik/web/elements/buttons/SpinnerButton";
import { TableColumn } from "@goauthentik/web/elements/table/Table";
import { TableModal } from "@goauthentik/web/elements/table/TableModal";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { CoreApi, Group } from "@goauthentik/api";

@customElement("ak-user-group-select-table")
export class GroupSelectModal extends TableModal<Group> {
    checkbox = true;
    checkboxChip = true;

    searchEnabled(): boolean {
        return true;
    }

    @property()
    confirm!: (selectedItems: Group[]) => Promise<unknown>;

    order = "name";

    async apiEndpoint(page: number): Promise<AKResponse<Group>> {
        return new CoreApi(DEFAULT_CONFIG).coreGroupsList({
            ordering: this.order,
            page: page,
            pageSize: (await uiConfig()).pagination.perPage / 2,
            search: this.search || "",
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(t`Name`, "username"),
            new TableColumn(t`Superuser`, "is_superuser"),
            new TableColumn(t`Members`, ""),
        ];
    }

    row(item: Group): TemplateResult[] {
        return [
            html`<div>
                <div>${item.name}</div>
            </div>`,
            html` <ak-label color=${item.isSuperuser ? PFColor.Green : PFColor.Grey}>
                ${item.isSuperuser ? t`Yes` : t`No`}
            </ak-label>`,
            html`${item.users.length}`,
        ];
    }

    renderSelectedChip(item: Group): TemplateResult {
        return html`${item.name}`;
    }

    renderModalInner(): TemplateResult {
        return html`<section class="pf-c-modal-box__header pf-c-page__main-section pf-m-light">
                <div class="pf-c-content">
                    <h1 class="pf-c-title pf-m-2xl">${t`Select groups to add user to`}</h1>
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
