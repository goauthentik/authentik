import getUnicodeFlagIcon from "country-flag-icons/unicode";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { PoliciesApi, Reputation } from "@goauthentik/api";

import { AKResponse } from "../../../api/Client";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { uiConfig } from "../../../common/config";
import "../../../elements/buttons/ModalButton";
import "../../../elements/buttons/SpinnerButton";
import "../../../elements/forms/DeleteBulkForm";
import "../../../elements/forms/ModalForm";
import { TableColumn } from "../../../elements/table/Table";
import { TablePage } from "../../../elements/table/TablePage";

@customElement("ak-policy-reputation-list")
export class ReputationListPage extends TablePage<Reputation> {
    searchEnabled(): boolean {
        return true;
    }
    pageTitle(): string {
        return t`Reputation scores`;
    }
    pageDescription(): string {
        return t`Reputation for IP and user identifiers. Scores are decreased for each failed login and increased for each successful login.`;
    }
    pageIcon(): string {
        return "fa fa-ban";
    }

    @property()
    order = "identifier";

    checkbox = true;

    async apiEndpoint(page: number): Promise<AKResponse<Reputation>> {
        return new PoliciesApi(DEFAULT_CONFIG).policiesReputationScoresList({
            ordering: this.order,
            page: page,
            pageSize: (await uiConfig()).pagination.perPage,
            search: this.search || "",
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(t`Identifier`, "identifier"),
            new TableColumn(t`IP`, "ip"),
            new TableColumn(t`Score`, "score"),
            new TableColumn(t`Updated`, "updated"),
        ];
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${t`Reputation`}
            .objects=${this.selectedElements}
            .usedBy=${(item: Reputation) => {
                return new PoliciesApi(DEFAULT_CONFIG).policiesReputationScoresUsedByList({
                    reputationUuid: item.pk || "",
                });
            }}
            .delete=${(item: Reputation) => {
                return new PoliciesApi(DEFAULT_CONFIG).policiesReputationScoresDestroy({
                    reputationUuid: item.pk || "",
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${t`Delete`}
            </button>
        </ak-forms-delete-bulk>`;
    }

    row(item: Reputation): TemplateResult[] {
        return [
            html`${item.identifier}`,
            html`${item.ipGeoData?.country
                ? html` ${getUnicodeFlagIcon(item.ipGeoData.country)} `
                : html``}
            ${item.ip}`,
            html`${item.score}`,
            html`${item.updated.toLocaleString()}`,
        ];
    }
}
