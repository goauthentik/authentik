import "#elements/chips/Chip";
import "#elements/chips/ChipGroup";
import "#elements/forms/DeleteBulkForm";
import "#components/ak-status-label";

import { DEFAULT_CONFIG } from "#common/api/config";
import { formatElapsedTime } from "#common/temporal";

import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";

import { ExpiringBaseGrantModel, Oauth2Api, TokenModel } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFFlex from "@patternfly/patternfly/layouts/Flex/flex.css";

@customElement("ak-user-oauth-refresh-token-list")
export class UserOAuthRefreshTokenList extends Table<TokenModel> {
    expandable = true;

    @property({ type: Number })
    userId?: number;

    static get styles(): CSSResult[] {
        return super.styles.concat(PFFlex);
    }

    async apiEndpoint(): Promise<PaginatedResponse<TokenModel>> {
        return new Oauth2Api(DEFAULT_CONFIG).oauth2RefreshTokensList({
            ...(await this.defaultEndpointConfig()),
            user: this.userId,
        });
    }

    checkbox = true;
    clearOnRefresh = true;
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
            html`<ak-status-label
                type="warning"
                ?good=${!item.revoked}
                good-label=${msg("No")}
                bad-label=${msg("Yes")}
            ></ak-status-label>`,
            html`${item.expires
                ? html`<div>${formatElapsedTime(item.expires)}</div>
                      <small>${item.expires.toLocaleString()}</small>`
                : msg("-")}`,
            html`<ak-chip-group>
                ${item.scope.sort().map((scope) => {
                    return html`<ak-chip .removable=${false}>${scope}</ak-chip>`;
                })}
            </ak-chip-group>`,
        ];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-oauth-refresh-token-list": UserOAuthRefreshTokenList;
    }
}
