import "#admin/rbac/ObjectPermissionModal";
import "#admin/tokens/TokenForm";
import "#components/ak-status-label";
import "#elements/buttons/Dropdown";
import "#elements/buttons/TokenCopyButton/index";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";
import { intentToLabel } from "#common/labels";

import { IconTokenCopyButton } from "#elements/buttons/IconTokenCopyButton";
import { IconEditButton, ModalInvokerButton } from "#elements/dialogs";
import { IconPermissionButton } from "#elements/dialogs/components/IconPermissionButton";
import { PaginatedResponse, TableColumn, Timestamp } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { TokenForm } from "#admin/tokens/TokenForm";

import { CoreApi, IntentEnum, ModelEnum, Token } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-token-list")
export class TokenListPage extends TablePage<Token> {
    protected override searchEnabled = true;
    public override pageTitle = msg("Tokens");
    public override pageDescription = msg(
        "Tokens are used throughout authentik for Email validation stages, Recovery keys and API access.",
    );
    public override pageIcon = "pf-icon pf-icon-security";
    public override searchPlaceholder = msg("Search for a token identifier, user, or intent...");

    protected override rowLabel(item: Token): string | null {
        return item.identifier;
    }

    public override checkbox = true;
    public override clearOnRefresh = true;
    public override order = "expires";

    protected override async apiEndpoint(): Promise<PaginatedResponse<Token>> {
        return new CoreApi(DEFAULT_CONFIG).coreTokensList(await this.defaultEndpointConfig());
    }

    protected columns: TableColumn[] = [
        [msg("Identifier"), "identifier"],
        [msg("User"), "user"],
        [msg("Expires?"), "expiring"],
        [msg("Expiry date"), "expires"],
        [msg("Intent"), "intent"],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    protected override renderToolbarSelected(): SlottedTemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            object-label=${msg("Token(s)")}
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

    protected override renderObjectCreate(): SlottedTemplateResult {
        return ModalInvokerButton(TokenForm);
    }

    protected override row(item: Token): SlottedTemplateResult[] {
        return [
            html`<div>${item.identifier}</div>
                ${item.managed
                    ? html`<small>${msg("Token is managed by authentik.")}</small>`
                    : nothing}`,
            html`<a href="#/identity/users/${item.userObj?.pk}">${item.userObj?.username}</a>`,
            html`<ak-status-label type="warning" ?good=${item.expiring}></ak-status-label>`,
            Timestamp(item.expires && item.expiring ? item.expires : null),
            html`${intentToLabel(item.intent ?? IntentEnum.Api)}`,
            html`<div class="ak-c-table__actions">
                ${!item.managed
                    ? IconEditButton(TokenForm, item.identifier, item.identifier)
                    : html`<button class="pf-c-button pf-m-plain" disabled type="button">
                          <pf-tooltip
                              position="top"
                              content=${msg("Editing is disabled for managed tokens")}
                          >
                              <i class="fas fa-edit" aria-hidden="true"></i>
                          </pf-tooltip>
                      </button>`}
                ${IconPermissionButton(item.identifier, {
                    model: ModelEnum.AuthentikCoreToken,
                    objectPk: item.pk,
                })}
                ${IconTokenCopyButton(item.identifier)}
            </div>`,
        ];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-token-list": TokenListPage;
    }
}
