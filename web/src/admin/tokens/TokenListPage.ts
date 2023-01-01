import "@goauthentik/admin/tokens/TokenForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { uiConfig } from "@goauthentik/common/ui/config";
import { PFColor } from "@goauthentik/elements/Label";
import "@goauthentik/elements/buttons/Dropdown";
import "@goauthentik/elements/buttons/TokenCopyButton";
import "@goauthentik/elements/forms/DeleteBulkForm";
import "@goauthentik/elements/forms/ModalForm";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import { TableColumn } from "@goauthentik/elements/table/Table";
import { TablePage } from "@goauthentik/elements/table/TablePage";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { CoreApi, IntentEnum, Token } from "@goauthentik/api";

export function IntentToLabel(intent: IntentEnum): string {
    switch (intent) {
        case IntentEnum.Api:
            return t`API Access`;
        case IntentEnum.AppPassword:
            return t`App password`;
        case IntentEnum.Recovery:
            return t`Recovery`;
        case IntentEnum.Verification:
            return t`Verification`;
        case IntentEnum.UnknownDefaultOpenApi:
            return t`Unknown intent`;
    }
}

@customElement("ak-token-list")
export class TokenListPage extends TablePage<Token> {
    searchEnabled(): boolean {
        return true;
    }
    pageTitle(): string {
        return t`Tokens`;
    }
    pageDescription(): string {
        return t`Tokens are used throughout authentik for Email validation stages, Recovery keys and API access.`;
    }
    pageIcon(): string {
        return "pf-icon pf-icon-security";
    }

    checkbox = true;

    @property()
    order = "expires";

    async apiEndpoint(page: number): Promise<PaginatedResponse<Token>> {
        return new CoreApi(DEFAULT_CONFIG).coreTokensList({
            ordering: this.order,
            page: page,
            pageSize: (await uiConfig()).pagination.perPage,
            search: this.search || "",
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(t`Identifier`, "identifier"),
            new TableColumn(t`User`, "user"),
            new TableColumn(t`Expires?`, "expiring"),
            new TableColumn(t`Expiry date`, "expires"),
            new TableColumn(t`Intent`, "intent"),
            new TableColumn(t`Actions`),
        ];
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${t`Token(s)`}
            .objects=${this.selectedElements}
            .usedBy=${(item: Token) => {
                return new CoreApi(DEFAULT_CONFIG).coreTokensUsedByList({
                    identifier: item.identifier,
                });
            }}
            .delete=${(item: Token) => {
                return new CoreApi(DEFAULT_CONFIG).coreTokensDestroy({
                    identifier: item.identifier,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${t`Delete`}
            </button>
        </ak-forms-delete-bulk>`;
    }

    renderObjectCreate(): TemplateResult {
        return html`
            <ak-forms-modal>
                <span slot="submit"> ${t`Create`} </span>
                <span slot="header"> ${t`Create Token`} </span>
                <ak-token-form slot="form"> </ak-token-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">${t`Create`}</button>
            </ak-forms-modal>
        `;
    }

    row(item: Token): TemplateResult[] {
        return [
            html`<div>${item.identifier}</div>
                ${item.managed
                    ? html`<small>${t`Token is managed by authentik.`}</small>`
                    : html``}`,
            html`<a href="#/identity/users/${item.userObj?.pk}">${item.userObj?.username}</a>`,
            html` <ak-label color=${item.expiring ? PFColor.Green : PFColor.Orange}>
                ${item.expiring ? t`Yes` : t`No`}
            </ak-label>`,
            html`${item.expiring ? item.expires?.toLocaleString() : t`-`}`,
            html`${IntentToLabel(item.intent || IntentEnum.Api)}`,
            html`
                <ak-forms-modal>
                    <span slot="submit"> ${t`Update`} </span>
                    <span slot="header"> ${t`Update Token`} </span>
                    <ak-token-form slot="form" .instancePk=${item.identifier}></ak-token-form>
                    <button
                        ?disabled=${item.managed !== null}
                        slot="trigger"
                        class="pf-c-button pf-m-plain"
                    >
                        <i class="fas fa-edit"></i>
                    </button>
                </ak-forms-modal>
                <ak-token-copy-button
                    class="pf-c-button pf-m-plain"
                    identifier="${item.identifier}"
                >
                    <i class="fas fa-copy"></i>
                </ak-token-copy-button>
            `,
        ];
    }
}
