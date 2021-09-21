import { t } from "@lingui/macro";

import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators";

import { ExpiringBaseGrantModel, Oauth2Api } from "@goauthentik/api";

import { AKResponse } from "../../api/Client";
import { DEFAULT_CONFIG } from "../../api/Config";
import { PAGE_SIZE } from "../../constants";
import "../forms/DeleteBulkForm";
import { Table, TableColumn } from "../table/Table";

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
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${t`Authorization Code(s)`}
            .objects=${this.selectedElements}
            .usedBy=${(item: ExpiringBaseGrantModel) => {
                return new Oauth2Api(DEFAULT_CONFIG).oauth2AuthorizationCodesUsedByList({
                    id: item.pk,
                });
            }}
            .delete=${(item: ExpiringBaseGrantModel) => {
                return new Oauth2Api(DEFAULT_CONFIG).oauth2AuthorizationCodesDestroy({
                    id: item.pk,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${t`Delete`}
            </button>
        </ak-forms-delete-bulk>`;
    }

    row(item: ExpiringBaseGrantModel): TemplateResult[] {
        return [
            html`<a href="#/core/providers/${item.provider?.pk}"> ${item.provider?.name} </a>`,
            html`${item.expires?.toLocaleString()}`,
            html`${item.scope.join(", ")}`,
        ];
    }
}
