import { t } from "@lingui/macro";
import { customElement, html, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../api/Client";
import { Table, TableColumn } from "../table/Table";

import "../forms/DeleteForm";
import { PAGE_SIZE } from "../../constants";
import { ExpiringBaseGrantModel, Oauth2Api } from "authentik-api";
import { DEFAULT_CONFIG } from "../../api/Config";

@customElement("ak-user-oauth-code-list")
export class UserOAuthCodeList extends Table<ExpiringBaseGrantModel> {
    @property()
    userId?: string;

    apiEndpoint(page: number): Promise<AKResponse<ExpiringBaseGrantModel>> {
        return new Oauth2Api(DEFAULT_CONFIG).oauth2AuthorizationCodesList({
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
            new TableColumn(t`Expires`, "expires"),
            new TableColumn(t`Scopes`, "scope"),
            new TableColumn(""),
        ];
    }

    row(item: ExpiringBaseGrantModel): TemplateResult[] {
        return [
            html`<a href="#/core/providers/${item.provider?.pk}">
                ${item.provider?.name}
            </a>`,
            html`${item.expires?.toLocaleString()}`,
            html`${item.scope.join(", ")}`,
            html`
            <ak-forms-delete
                .obj=${item}
                objectLabel=${t`Authorization Code`}
                .delete=${() => {
                    return new Oauth2Api(DEFAULT_CONFIG).oauth2AuthorizationCodesDelete({
                        id: item.pk || 0,
                    });
                }}>
                <button slot="trigger" class="pf-c-button pf-m-danger">
                    ${t`Delete Authorization Code`}
                </button>
            </ak-forms-delete>`,
        ];
    }

}
