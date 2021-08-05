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
    @property({ type: Number })
    userId?: number;

    apiEndpoint(page: number): Promise<AKResponse<ExpiringBaseGrantModel>> {
        return new Oauth2Api(DEFAULT_CONFIG).oauth2AuthorizationCodesList({
            user: this.userId,
            ordering: "expires",
            page: page,
            pageSize: PAGE_SIZE,
        });
    }

    checkbox = true;
    order = "-expires";

    columns(): TableColumn[] {
        return [
            new TableColumn(t`Provider`, "provider"),
            new TableColumn(t`Expires`, "expires"),
            new TableColumn(t`Scopes`, "scope"),
        ];
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length !== 1;
        const item = this.selectedElements[0];
        return html`<ak-forms-delete
            .obj=${item}
            objectLabel=${t`Authorization Code`}
            .usedBy=${() => {
                return new Oauth2Api(DEFAULT_CONFIG).oauth2AuthorizationCodesUsedByList({
                    id: item.pk,
                });
            }}
            .delete=${() => {
                return new Oauth2Api(DEFAULT_CONFIG).oauth2AuthorizationCodesDestroy({
                    id: item.pk,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${t`Delete`}
            </button>
        </ak-forms-delete>`;
    }

    row(item: ExpiringBaseGrantModel): TemplateResult[] {
        return [
            html`<a href="#/core/providers/${item.provider?.pk}"> ${item.provider?.name} </a>`,
            html`${item.expires?.toLocaleString()}`,
            html`${item.scope.join(", ")}`,
        ];
    }
}
