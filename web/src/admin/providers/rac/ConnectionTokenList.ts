import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { ConnectionToken, RacApi, RACProvider } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";

@customElement("ak-rac-connection-token-list")
export class ConnectionTokenListPage extends Table<ConnectionToken> {
    checkbox = true;
    clearOnRefresh = true;

    protected override searchEnabled = true;

    @property()
    order = "name";

    @property({ attribute: false })
    provider?: RACProvider;

    @property({ type: Number })
    userId?: number;

    static styles: CSSResult[] = [...super.styles, PFDescriptionList];

    async apiEndpoint(): Promise<PaginatedResponse<ConnectionToken>> {
        return new RacApi(DEFAULT_CONFIG).racConnectionTokensList({
            ...(await this.defaultEndpointConfig()),
            provider: this.provider?.pk,
            sessionUser: this.userId,
        });
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            object-label=${msg("Connection Token(s)")}
            .objects=${this.selectedElements}
            .metadata=${(item: ConnectionToken) => {
                return [
                    { key: msg("Endpoint"), value: item.endpointObj.name },
                    { key: msg("User"), value: item.user.username },
                ];
            }}
            .usedBy=${(item: ConnectionToken) => {
                return new RacApi(DEFAULT_CONFIG).racConnectionTokensUsedByList({
                    connectionTokenUuid: item.pk || "",
                });
            }}
            .delete=${(item: ConnectionToken) => {
                return new RacApi(DEFAULT_CONFIG).racConnectionTokensDestroy({
                    connectionTokenUuid: item.pk || "",
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    protected override rowLabel(item: ConnectionToken): string | null {
        if (this.provider) {
            return item.endpointObj.name ?? null;
        }
        return item.providerObj.name ?? null;
    }

    @state()
    protected get columns(): TableColumn[] {
        if (this.provider) {
            return [
                [msg("Endpoint"), "endpoint__name"],
                [msg("User"), "session__user"],
            ];
        }

        return [
            [msg("Provider"), "provider__name"],
            [msg("Endpoint"), "endpoint__name"],
        ];
    }

    row(item: ConnectionToken): SlottedTemplateResult[] {
        if (this.provider) {
            return [html`${item.endpointObj.name}`, html`${item.user.username}`];
        }
        return [html`${item.providerObj.name}`, html`${item.endpointObj.name}`];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-rac-connection-token-list": ConnectionTokenListPage;
    }
}
