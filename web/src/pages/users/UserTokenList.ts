import { gettext } from "django";
import { customElement, html, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../api/Client";

import "../../elements/forms/DeleteForm";
import "../../elements/buttons/ModalButton";
import "../../elements/buttons/Dropdown";
import "../../elements/buttons/TokenCopyButton";
import { Table, TableColumn } from "../../elements/table/Table";
import { PAGE_SIZE } from "../../constants";
import { CoreApi, Token } from "authentik-api";
import { DEFAULT_CONFIG } from "../../api/Config";
import { AdminURLManager } from "../../api/legacy";

@customElement("ak-user-token-list")
export class UserTokenList extends Table<Token> {
    searchEnabled(): boolean {
        return true;
    }

    expandable = true;

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
            new TableColumn(""),
        ];
    }

    renderToolbar(): TemplateResult {
        return html`
        <ak-modal-button href="/-/user/tokens/create/">
            <ak-spinner-button slot="trigger" class="pf-m-primary">
                ${gettext("Create")}
            </ak-spinner-button>
            <div slot="modal"></div>
        </ak-modal-button>
        ${super.renderToolbar()}
        `;
    }

    renderExpanded(item: Token): TemplateResult {
        return html`
        <td role="cell" colspan="3">
            <div class="pf-c-table__expandable-row-content">
                <dl class="pf-c-description-list pf-m-horizontal">
                    <div class="pf-c-description-list__group">
                        <dt class="pf-c-description-list__term">
                            <span class="pf-c-description-list__text">${gettext("User")}</span>
                        </dt>
                        <dd class="pf-c-description-list__description">
                            <div class="pf-c-description-list__text">${item.user.username}</div>
                        </dd>
                    </div>
                    <div class="pf-c-description-list__group">
                        <dt class="pf-c-description-list__term">
                            <span class="pf-c-description-list__text">${gettext("Expiring")}</span>
                        </dt>
                        <dd class="pf-c-description-list__description">
                            <div class="pf-c-description-list__text">${item.expiring ? "Yes" : "No"}</div>
                        </dd>
                    </div>
                    <div class="pf-c-description-list__group">
                        <dt class="pf-c-description-list__term">
                            <span class="pf-c-description-list__text">${gettext("Expiring")}</span>
                        </dt>
                        <dd class="pf-c-description-list__description">
                            <div class="pf-c-description-list__text">${item.expiring ? item.expires?.toLocaleString() : "-"}</div>
                        </dd>
                    </div>
                </dl>
            </div>
        </td>
        <td></td>`;
    }

    row(item: Token): TemplateResult[] {
        return [
            html`${item.identifier}`,
            html`
            <ak-modal-button href="${AdminURLManager.tokens(`${item.identifier}/update/`)}">
                <ak-spinner-button slot="trigger" class="pf-m-secondary">
                    ${gettext("Edit")}
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>
            <ak-forms-delete
                .obj=${item}
                objectLabel=${gettext("Token")}
                .delete=${() => {
                    return new CoreApi(DEFAULT_CONFIG).coreTokensDelete({
                        identifier: item.identifier
                    });
                }}>
                <button slot="trigger" class="pf-c-button pf-m-danger">
                    ${gettext("Delete")}
                </button>
            </ak-forms-delete>
            <ak-token-copy-button identifier="${item.identifier}">
                ${gettext("Copy Key")}
            </ak-token-copy-button>
            `,
        ];
    }

}
