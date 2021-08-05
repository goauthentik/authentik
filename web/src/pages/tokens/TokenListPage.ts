import { t } from "@lingui/macro";
import { customElement, html, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../api/Client";
import { TablePage } from "../../elements/table/TablePage";

import "../../elements/buttons/Dropdown";
import "../../elements/buttons/TokenCopyButton";
import "../../elements/forms/DeleteForm";
import { TableColumn } from "../../elements/table/Table";
import { PAGE_SIZE } from "../../constants";
import { CoreApi, Token } from "authentik-api";
import { DEFAULT_CONFIG } from "../../api/Config";

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
            new TableColumn(t`Actions`),
        ];
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length !== 1;
        const item = this.selectedElements[0];
        return html`<ak-forms-delete
            .obj=${item}
            objectLabel=${t`Token`}
            .usedBy=${() => {
                return new CoreApi(DEFAULT_CONFIG).coreTokensUsedByList({
                    identifier: item.identifier,
                });
            }}
            .delete=${() => {
                return new CoreApi(DEFAULT_CONFIG).coreTokensDestroy({
                    identifier: item.identifier,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${t`Delete`}
            </button>
        </ak-forms-delete>`;
    }

    row(item: Token): TemplateResult[] {
        return [
            html`${item.identifier}`,
            html`${item.user?.username}`,
            html`${item.expiring ? t`Yes` : t`No`}`,
            html`${item.expiring ? item.expires?.toLocaleString() : "-"}`,
            html`
                <ak-token-copy-button identifier="${item.identifier}">
                    ${t`Copy Key`}
                </ak-token-copy-button>
            `,
        ];
    }
}
