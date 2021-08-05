import { t } from "@lingui/macro";
import { CSSResult, customElement, html, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../api/Client";
import { Table, TableColumn } from "../table/Table";
import PFFlex from "@patternfly/patternfly/layouts/Flex/flex.css";

import "../forms/DeleteForm";
import { PAGE_SIZE } from "../../constants";
import { RefreshTokenModel, Oauth2Api } from "authentik-api";
import { DEFAULT_CONFIG } from "../../api/Config";

@customElement("ak-user-oauth-refresh-list")
export class UserOAuthRefreshList extends Table<RefreshTokenModel> {
    expandable = true;

    @property({ type: Number })
    userId?: number;

    static get styles(): CSSResult[] {
        return super.styles.concat(PFFlex);
    }

    apiEndpoint(page: number): Promise<AKResponse<RefreshTokenModel>> {
        return new Oauth2Api(DEFAULT_CONFIG).oauth2RefreshTokensList({
            user: this.userId,
            ordering: "expires",
            page: page,
            pageSize: PAGE_SIZE,
        });
    }

    order = "-expires";

    columns(): TableColumn[] {
        return [
            new TableColumn(t`Provider`, "provider"),
            new TableColumn(t`Revoked?`, "revoked"),
            new TableColumn(t`Expires`, "expires"),
            new TableColumn(t`Scopes`, "scope"),
            new TableColumn("Actions"),
        ];
    }

    renderExpanded(item: RefreshTokenModel): TemplateResult {
        return html` <td role="cell" colspan="4">
                <div class="pf-c-table__expandable-row-content">
                    <div class="pf-l-flex">
                        <div class="pf-l-flex__item">
                            <h3>${t`ID Token`}</h3>
                            <pre>${item.idToken}</pre>
                        </div>
                    </div>
                </div>
            </td>
            <td></td>
            <td></td>
            <td></td>`;
    }

    row(item: RefreshTokenModel): TemplateResult[] {
        return [
            html`<a href="#/core/providers/${item.provider?.pk}"> ${item.provider?.name} </a>`,
            html`${item.revoked ? t`Yes` : t`No`}`,
            html`${item.expires?.toLocaleString()}`,
            html`${item.scope.join(", ")}`,
            html` <ak-forms-delete
                .obj=${item}
                objectLabel=${t`Refresh Code`}
                .usedBy=${() => {
                    return new Oauth2Api(DEFAULT_CONFIG).oauth2RefreshTokensUsedByList({
                        id: item.pk,
                    });
                }}
                .delete=${() => {
                    return new Oauth2Api(DEFAULT_CONFIG).oauth2RefreshTokensDestroy({
                        id: item.pk,
                    });
                }}
            >
                <button slot="trigger" class="pf-c-button pf-m-danger">
                    ${t`Delete Refresh Code`}
                </button>
            </ak-forms-delete>`,
        ];
    }
}
