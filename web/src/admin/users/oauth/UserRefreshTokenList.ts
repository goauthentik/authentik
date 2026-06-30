import "#components/ak-status-label";
import "#elements/chips/Chip";
import "#elements/chips/ChipGroup";
import "#elements/forms/DeleteBulkForm";

import { aki } from "#common/api/client";

import { PaginatedResponse, Table, TableColumn, Timestamp } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { ExpiringBaseGrantModel, Oauth2Api, TokenModel } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFFlex from "@patternfly/patternfly/layouts/Flex/flex.css";

@customElement("ak-user-oauth-refresh-token-list")
export class UserOAuthRefreshTokenList extends Table<TokenModel> {
    public static override verboseName = msg("Refresh Token");
    public static override verboseNamePlural = msg("Refresh Tokens");

    expandable = true;

    @property({ type: Number })
    userId?: number;

    static styles: CSSResult[] = [...super.styles, PFFlex];

    async apiEndpoint(): Promise<PaginatedResponse<TokenModel>> {
        return aki(Oauth2Api).oauth2RefreshTokensList({
            ...(await this.defaultEndpointConfig()),
            user: this.userId,
        });
    }

    checkbox = true;
    clearOnRefresh = true;
    order = "-expires";

    protected override rowLabel(item: TokenModel): string | null {
        return item.provider?.name ?? null;
    }

    protected columns: TableColumn[] = [
        [msg("Provider"), "provider"],
        [msg("Revoked?"), "revoked"],
        [msg("Expires"), "expires"],
        [msg("Scopes"), "scope"],
    ];

    renderExpanded(item: TokenModel): TemplateResult {
        return html`<div class="pf-l-flex">
            <div class="pf-l-flex__item">
                <h3>${msg("ID Token")}</h3>
                <pre>${item.idToken}</pre>
            </div>
        </div>`;
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;

        return html`<ak-forms-delete-bulk
            object-label=${msg("Refresh Tokens(s)")}
            .objects=${this.selectedElements}
            .usedBy=${(item: ExpiringBaseGrantModel) => {
                return aki(Oauth2Api).oauth2RefreshTokensUsedByList({
                    id: item.pk,
                });
            }}
            .delete=${(item: ExpiringBaseGrantModel) => {
                return aki(Oauth2Api).oauth2RefreshTokensDestroy({
                    id: item.pk,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    row(item: TokenModel): SlottedTemplateResult[] {
        return [
            html`<a href="#/core/providers/${item.provider?.pk}"> ${item.provider?.name} </a>`,
            html`<ak-status-label
                type="warning"
                ?good=${!item.revoked}
                good-label=${msg("No")}
                bad-label=${msg("Yes")}
            ></ak-status-label>`,
            Timestamp(item.expires),
            html`<ak-chip-group>
                ${item.scope.sort().map((scope) => {
                    return html`<ak-chip>${scope}</ak-chip>`;
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
