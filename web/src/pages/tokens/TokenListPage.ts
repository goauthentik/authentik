import { gettext } from "django";
import { customElement, html, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../api/Client";
import { TablePage } from "../../elements/table/TablePage";

import "../../elements/buttons/ModalButton";
import "../../elements/buttons/Dropdown";
import "../../elements/buttons/TokenCopyButton";
import { TableColumn } from "../../elements/table/Table";
import { Token } from "../../api/Tokens";
import { PAGE_SIZE } from "../../constants";

@customElement("ak-token-list")
export class TokenListPage extends TablePage<Token> {
    searchEnabled(): boolean {
        return true;
    }
    pageTitle(): string {
        return gettext("Tokens");
    }
    pageDescription(): string {
        return gettext("Tokens are used throughout authentik for Email validation stages, Recovery keys and API access.");
    }
    pageIcon(): string {
        return gettext("pf-icon pf-icon-security");
    }

    @property()
    order = "expires";

    apiEndpoint(page: number): Promise<AKResponse<Token>> {
        return Token.list({
            ordering: this.order,
            page: page,
            page_size: PAGE_SIZE,
            search: this.search || "",
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn("Identifier", "identifier"),
            new TableColumn("User", "user"),
            new TableColumn("Expires?", "expiring"),
            new TableColumn("Expiry date", "expires"),
            new TableColumn(""),
        ];
    }

    row(item: Token): TemplateResult[] {
        return [
            html`${item.identifier}`,
            html`${item.user.username}`,
            html`${item.expiring ? "Yes" : "No"}`,
            html`${item.expiring ? new Date(item.expires * 1000).toLocaleString() : "-"}`,
            html`
            <ak-modal-button href="${Token.adminUrl(`${item.identifier}/delete/`)}">
                <ak-spinner-button slot="trigger" class="pf-m-danger">
                    ${gettext("Delete")}
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>
            <ak-token-copy-button identifier="${item.identifier}">
                ${gettext("Copy Key")}
            </ak-token-copy-button>
            `,
        ];
    }

}
