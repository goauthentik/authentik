import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { uiConfig } from "@goauthentik/common/ui/config";
import { PFColor } from "@goauthentik/elements/Label";
import "@goauthentik/elements/forms/DeleteBulkForm";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import { Table, TableColumn } from "@goauthentik/elements/table/Table";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFFlex from "@patternfly/patternfly/layouts/Flex/flex.css";

import { ExpiringBaseGrantModel, Oauth2Api, TokenModel } from "@goauthentik/api";

@customElement("ak-user-oauth-refresh-list")
export class UserOAuthRefreshList extends Table<TokenModel> {
    expandable = true;

    @property({ type: Number })
    userId?: number;

    static get styles(): CSSResult[] {
        return super.styles.concat(PFFlex);
    }

    async apiEndpoint(page: number): Promise<PaginatedResponse<TokenModel>> {
        return new Oauth2Api(DEFAULT_CONFIG).oauth2RefreshTokensList({
            user: this.userId,
            ordering: "expires",
            page: page,
            pageSize: (await uiConfig()).pagination.perPage,
        });
    }

    checkbox = true;
    order = "-expires";

    columns(): TableColumn[] {
        return [
            new TableColumn(msg("Provider"), "provider"),
            new TableColumn(msg("Revoked?"), "revoked"),
            new TableColumn(msg("Expires"), "expires"),
            new TableColumn(msg("Scopes"), "scope"),
        ];
    }

    renderExpanded(item: TokenModel): TemplateResult {
        return html` <td role="cell" colspan="4">
                <div class="pf-c-table__expandable-row-content">
                    <div class="pf-l-flex">
                        <div class="pf-l-flex__item">
                            <h3>${msg("ID Token")}</h3>
                            <pre>${item.idToken}</pre>
                        </div>
                    </div>
                </div>
            </td>
            <td></td>
            <td></td>`;
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${msg("Refresh Tokens(s)")}
            .objects=${this.selectedElements}
            .usedBy=${(item: ExpiringBaseGrantModel) => {
                return new Oauth2Api(DEFAULT_CONFIG).oauth2RefreshTokensUsedByList({
                    id: item.pk,
                });
            }}
            .delete=${(item: ExpiringBaseGrantModel) => {
                return new Oauth2Api(DEFAULT_CONFIG).oauth2RefreshTokensDestroy({
                    id: item.pk,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    row(item: TokenModel): TemplateResult[] {
        return [
            html`<a href="#/core/providers/${item.provider?.pk}"> ${item.provider?.name} </a>`,
            html`<ak-label color=${item.revoked ? PFColor.Orange : PFColor.Green}>
                ${item.revoked ? msg("Yes") : msg("No")}
            </ak-label>`,
            html`${item.expires?.toLocaleString()}`,
            html`${item.scope.join(", ")}`,
        ];
    }
}
