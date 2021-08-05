import { t } from "@lingui/macro";
import { customElement, html, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../../api/Client";
import { TablePage } from "../../../elements/table/TablePage";

import "../../../elements/buttons/ModalButton";
import "../../../elements/buttons/SpinnerButton";
import "../../../elements/forms/DeleteForm";
import "../../../elements/forms/ModalForm";
import { TableColumn } from "../../../elements/table/Table";
import { PAGE_SIZE } from "../../../constants";
import { IPReputation, PoliciesApi } from "authentik-api";
import { DEFAULT_CONFIG } from "../../../api/Config";

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

    apiEndpoint(page: number): Promise<AKResponse<IPReputation>> {
        return new PoliciesApi(DEFAULT_CONFIG).policiesReputationIpsList({
            ordering: this.order,
            page: page,
            pageSize: PAGE_SIZE,
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
        const disabled = this.selectedElements.length !== 1;
        const item = this.selectedElements[0];
        return html`<ak-forms-delete
            .obj=${item}
            objectLabel=${t`IP Reputation`}
            .usedBy=${() => {
                return new PoliciesApi(DEFAULT_CONFIG).policiesReputationIpsUsedByList({
                    id: item.pk,
                });
            }}
            .delete=${() => {
                return new PoliciesApi(DEFAULT_CONFIG).policiesReputationIpsDestroy({
                    id: item.pk,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${t`Delete`}
            </button>
        </ak-forms-delete>`;
    }

    row(item: IPReputation): TemplateResult[] {
        return [html`${item.ip}`, html`${item.score}`];
    }
}
