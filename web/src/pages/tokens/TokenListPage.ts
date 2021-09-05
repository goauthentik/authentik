import { t } from "@lingui/macro";
import { customElement, html, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../api/Client";
import { TablePage } from "../../elements/table/TablePage";

import "../../elements/buttons/Dropdown";
import "../../elements/buttons/TokenCopyButton";
import "../../elements/forms/DeleteBulkForm";
import "../../elements/forms/ModalForm";
import "./TokenForm";
import { TableColumn } from "../../elements/table/Table";
import { PAGE_SIZE } from "../../constants";
import { CoreApi, IntentEnum, Token } from "@goauthentik/api";
import { DEFAULT_CONFIG } from "../../api/Config";

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

    apiEndpoint(page: number): Promise<AKResponse<Token>> {
        return new CoreApi(DEFAULT_CONFIG).coreTokensList({
            ordering: this.order,
            page: page,
            pageSize: PAGE_SIZE,
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

    renderToolbar(): TemplateResult {
        return html`
            <ak-forms-modal>
                <span slot="submit"> ${t`Create`} </span>
                <span slot="header"> ${t`Create Token`} </span>
                <ak-token-form slot="form"> </ak-token-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">${t`Create`}</button>
            </ak-forms-modal>
            ${super.renderToolbar()}
        `;
    }

    row(item: Token): TemplateResult[] {
        return [
            html`${item.identifier}`,
            html`<a href="#/identity/users/${item.userObj?.pk}">${item.userObj?.username}</a>`,
            html`${item.expiring ? t`Yes` : t`No`}`,
            html`${item.expiring ? item.expires?.toLocaleString() : "-"}`,
            html`${IntentToLabel(item.intent || IntentEnum.Api)}`,
            html`
                ${item.managed
                    ? html``
                    : html`<ak-forms-modal>
                          <span slot="submit"> ${t`Update`} </span>
                          <span slot="header"> ${t`Update Token`} </span>
                          <ak-token-form slot="form" .instancePk=${item.identifier}></ak-token-form>
                          <button slot="trigger" class="pf-c-button pf-m-plain">
                              <i class="fas fa-edit"></i>
                          </button>
                      </ak-forms-modal>`}
                <ak-token-copy-button identifier="${item.identifier}">
                    <i class="fas fa-copy"></i>
                </ak-token-copy-button>
            `,
        ];
    }
}
