import "#elements/forms/DeleteBulkForm";

import { DEFAULT_CONFIG } from "#common/api/config";
import { formatElapsedTime } from "#common/temporal";

import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";

import { PoliciesApi, Reputation } from "@goauthentik/api";

import getUnicodeFlagIcon from "country-flag-icons/unicode";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-user-reputation-list")
export class UserReputationList extends Table<Reputation> {
    @property()
    targetUsername!: string;

    @property()
    targetEmail!: string | undefined;

    async apiEndpoint(): Promise<PaginatedResponse<Reputation>> {
        const identifiers = [this.targetUsername];
        if (this.targetEmail !== undefined) {
            identifiers.push(this.targetEmail);
        }
        return new PoliciesApi(DEFAULT_CONFIG).policiesReputationScoresList({
            ...(await this.defaultEndpointConfig()),
            identifierIn: identifiers,
        });
    }

    checkbox = true;
    clearOnRefresh = true;
    order = "identifier";

    columns(): TableColumn[] {
        return [
            new TableColumn(msg("Identifier"), "identifier"),
            new TableColumn(msg("IP"), "ip"),
            new TableColumn(msg("Score"), "score"),
            new TableColumn(msg("Updated"), "updated"),
        ];
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${msg("Reputation score(s)")}
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
                ${msg("Delete")}
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
            html`<div>${formatElapsedTime(item.updated)}</div>
                <small>${item.updated.toLocaleString()}</small>`,
        ];
    }
}
