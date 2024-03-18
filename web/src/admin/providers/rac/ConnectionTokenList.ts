import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { uiConfig } from "@goauthentik/common/ui/config";
import "@goauthentik/elements/buttons/SpinnerButton";
import "@goauthentik/elements/forms/DeleteBulkForm";
import "@goauthentik/elements/forms/ModalForm";
import { PaginatedResponse, Table } from "@goauthentik/elements/table/Table";
import { TableColumn } from "@goauthentik/elements/table/Table";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";

import { ConnectionToken, RACProvider, RacApi } from "@goauthentik/api";

@customElement("ak-rac-connection-token-list")
export class ConnectionTokenListPage extends Table<ConnectionToken> {
    checkbox = true;
    clearOnRefresh = true;

    searchEnabled(): boolean {
        return true;
    }

    @property()
    order = "name";

    @property({ attribute: false })
    provider?: RACProvider;

    @property({ type: Number })
    userId?: number;

    static get styles(): CSSResult[] {
        return super.styles.concat(PFDescriptionList);
    }

    async apiEndpoint(page: number): Promise<PaginatedResponse<ConnectionToken>> {
        return new RacApi(DEFAULT_CONFIG).racConnectionTokensList({
            ordering: this.order,
            page: page,
            pageSize: (await uiConfig()).pagination.perPage,
            search: this.search || "",
            provider: this.provider?.pk,
            sessionUser: this.userId,
        });
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${msg("Connection Token(s)")}
            .objects=${this.selectedElements}
            .metadata=${(item: ConnectionToken) => {
                return [
                    { key: msg("Endpoint"), value: item.endpointObj.name },
                    { key: msg("User"), value: item.user.username },
                ];
            }}
            .usedBy=${(item: ConnectionToken) => {
                return new RacApi(DEFAULT_CONFIG).racConnectionTokensUsedByList({
                    connectionTokenUuid: item.pk,
                });
            }}
            .delete=${(item: ConnectionToken) => {
                return new RacApi(DEFAULT_CONFIG).racConnectionTokensDestroy({
                    connectionTokenUuid: item.pk,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    columns(): TableColumn[] {
        if (this.provider) {
            return [
                new TableColumn(msg("Endpoint"), "endpoint__name"),
                new TableColumn(msg("User"), "session__user"),
            ];
        }
        return [
            new TableColumn(msg("Provider"), "provider__name"),
            new TableColumn(msg("Endpoint"), "endpoint__name"),
        ];
    }

    row(item: ConnectionToken): TemplateResult[] {
        if (this.provider) {
            return [html`${item.endpointObj.name}`, html`${item.user.username}`];
        }
        return [html`${item.providerObj.name}`, html`${item.endpointObj.name}`];
    }
}
