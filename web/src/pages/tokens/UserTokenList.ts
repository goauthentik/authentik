import { gettext } from "django";
import { customElement, html, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../api/Client";

import "../../elements/buttons/ModalButton";
import "../../elements/buttons/Dropdown";
import "../../elements/buttons/TokenCopyButton";
import { Table, TableColumn } from "../../elements/table/Table";
import { PAGE_SIZE } from "../../constants";
import { CoreApi, Token } from "../../api";
import { DEFAULT_CONFIG } from "../../api/Config";
import { AdminURLManager } from "../../api/legacy";

@customElement("ak-token-user-list")
export class UserTokenList extends Table<Token> {
    searchEnabled(): boolean {
        return true;
    }

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
            new TableColumn("Identifier", "identifier"),
            new TableColumn("User", "user"),
            new TableColumn("Expires?", "expiring"),
            new TableColumn("Expiry date", "expires"),
            new TableColumn(""),
        ];
    }

    renderToolbar(): TemplateResult {
        return html`
        <ak-modal-button href="-/user/tokens/create/">
            <ak-spinner-button slot="trigger" class="pf-m-primary">
                ${gettext("Create")}
            </ak-spinner-button>
            <div slot="modal"></div>
        </ak-modal-button>
        ${super.renderToolbar()}
        `;
    }

    row(item: Token): TemplateResult[] {
        return [
            html`${item.identifier}`,
            html`${item.user.username}`,
            html`${item.expiring ? "Yes" : "No"}`,
            html`${item.expiring ? item.expires?.toLocaleString() : "-"}`,
            html`
            <ak-modal-button href="${AdminURLManager.tokens(`${item.identifier}/update/`)}">
                <ak-spinner-button slot="trigger" class="pf-m-secondary">
                    ${gettext("Edit")}
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>
            <ak-modal-button href="${AdminURLManager.tokens(`${item.identifier}/delete/`)}">
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
