import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";

import { ConnectionToken, RacApi, RACProvider } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";

@customElement("ak-rac-connection-token-list")
export class ConnectionTokenListPage extends Table<ConnectionToken> {
    public override checkbox = true;
    public override clearOnRefresh = true;

    protected override searchEnabled(): boolean {
        return true;
    }

    @property()
    public override order = "name";

    @property({ attribute: false })
    public provider?: RACProvider;

    @property({ type: Number })
    public userId?: number;

    public static override styles: CSSResult[] = [...super.styles, PFDescriptionList];

    protected async apiEndpoint(): Promise<PaginatedResponse<ConnectionToken>> {
        return new RacApi(DEFAULT_CONFIG).racConnectionTokensList({
            ...(await this.defaultEndpointConfig()),
            provider: this.provider?.pk,
            sessionUser: this.userId,
        });
    }

    protected override renderToolbarSelected(): TemplateResult {
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

    protected columns(): TableColumn[] {
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

    protected row(item: ConnectionToken): TemplateResult[] {
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
