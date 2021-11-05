import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { IPReputation, PoliciesApi } from "@goauthentik/api";

import { AKResponse } from "../../../api/Client";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { uiConfig } from "../../../common/config";
import "../../../elements/buttons/ModalButton";
import "../../../elements/buttons/SpinnerButton";
import "../../../elements/forms/DeleteBulkForm";
import "../../../elements/forms/ModalForm";
import { TableColumn } from "../../../elements/table/Table";
import { TablePage } from "../../../elements/table/TablePage";

@customElement("ak-policy-reputation-ip-list")
export class IPReputationListPage extends TablePage<IPReputation> {
    searchEnabled(): boolean {
        return true;
    }
    pageTitle(): string {
        return t`IP Reputation`;
    }
    pageDescription(): string {
        return t`Reputation for IPs. Scores are decreased for each failed login and increased for each successful login.`;
    }
    pageIcon(): string {
        return "fa fa-ban";
    }

    @property()
    order = "ip";

    checkbox = true;

    async apiEndpoint(page: number): Promise<AKResponse<IPReputation>> {
        return new PoliciesApi(DEFAULT_CONFIG).policiesReputationIpsList({
            ordering: this.order,
            page: page,
            pageSize: (await uiConfig()).pagination.perPage,
            search: this.search || "",
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(t`IP`, "ip"),
            new TableColumn(t`Score`, "score"),
            new TableColumn(t`Actions`),
        ];
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${t`IP Reputation`}
            .objects=${this.selectedElements}
            .usedBy=${(item: IPReputation) => {
                return new PoliciesApi(DEFAULT_CONFIG).policiesReputationIpsUsedByList({
                    id: item.pk,
                });
            }}
            .delete=${(item: IPReputation) => {
                return new PoliciesApi(DEFAULT_CONFIG).policiesReputationIpsDestroy({
                    id: item.pk,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${t`Delete`}
            </button>
        </ak-forms-delete-bulk>`;
    }

    row(item: IPReputation): TemplateResult[] {
        return [html`${item.ip}`, html`${item.score}`];
    }
}
