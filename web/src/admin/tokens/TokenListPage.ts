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
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { CoreApi, IntentEnum, Token } from "@goauthentik/api";

export function IntentToLabel(intent: IntentEnum): string {
    switch (intent) {
        case IntentEnum.Api:
            return msg("API Access");
        case IntentEnum.AppPassword:
            return msg("App password");
        case IntentEnum.Recovery:
            return msg("Recovery");
        case IntentEnum.Verification:
            return msg("Verification");
        case IntentEnum.UnknownDefaultOpenApi:
            return msg("Unknown intent");
    }
}

@customElement("ak-token-list")
export class TokenListPage extends TablePage<Token> {
    searchEnabled(): boolean {
        return true;
    }
    pageTitle(): string {
        return msg("Tokens");
    }
    pageDescription(): string {
        return msg(
            "Tokens are used throughout authentik for Email validation stages, Recovery keys and API access.",
        );
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
            new TableColumn(msg("Identifier"), "identifier"),
            new TableColumn(msg("User"), "user"),
            new TableColumn(msg("Expires?"), "expiring"),
            new TableColumn(msg("Expiry date"), "expires"),
            new TableColumn(msg("Intent"), "intent"),
            new TableColumn(msg("Actions")),
        ];
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${msg("Token(s)")}
            .objects=${this.selectedElements}
            .metadata=${(item: Token) => {
                return [{ key: msg("Identifier"), value: item.identifier }];
            }}
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
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    renderObjectCreate(): TemplateResult {
        return html`
            <ak-forms-modal>
                <span slot="submit"> ${msg("Create")} </span>
                <span slot="header"> ${msg("Create Token")} </span>
                <ak-token-form slot="form"> </ak-token-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">${msg("Create")}</button>
            </ak-forms-modal>
        `;
    }

    row(item: Token): TemplateResult[] {
        return [
            html`<div>${item.identifier}</div>
                ${item.managed
                    ? html`<small>${msg("Token is managed by authentik.")}</small>`
                    : html``}`,
            html`<a href="#/identity/users/${item.userObj?.pk}">${item.userObj?.username}</a>`,
            html` <ak-label color=${item.expiring ? PFColor.Green : PFColor.Orange}>
                ${item.expiring ? msg("Yes") : msg("No")}
            </ak-label>`,
            html`${item.expiring ? item.expires?.toLocaleString() : msg("-")}`,
            html`${IntentToLabel(item.intent || IntentEnum.Api)}`,
            html`
                ${!item.managed
                    ? html`<ak-forms-modal>
                          <span slot="submit"> ${msg("Update")} </span>
                          <span slot="header"> ${msg("Update Token")} </span>
                          <ak-token-form slot="form" .instancePk=${item.identifier}></ak-token-form>
                          <button slot="trigger" class="pf-c-button pf-m-plain">
                              <pf-tooltip position="top" content=${msg("Edit")}>
                                  <i class="fas fa-edit"></i>
                              </pf-tooltip>
                          </button>
                      </ak-forms-modal>`
                    : html``}
                <ak-token-copy-button
                    class="pf-c-button pf-m-plain"
                    identifier="${item.identifier}"
                >
                    <pf-tooltip position="top" content=${msg("Copy token")}>
                        <i class="fas fa-copy"></i>
                    </pf-tooltip>
                </ak-token-copy-button>
            `,
        ];
    }
}
