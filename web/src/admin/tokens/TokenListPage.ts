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

import { PaginatedResponse, TableColumn, Timestamp } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import {
    CoreApi,
    IntentEnum,
    RbacPermissionsAssignedByRolesListModelEnum,
    Token,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-token-list")
export class TokenListPage extends TablePage<Token> {
    protected override searchEnabled = true;
    public pageTitle = msg("Tokens");
    public pageDescription = msg(
        "Tokens are used throughout authentik for Email validation stages, Recovery keys and API access.",
    );
    public pageIcon = "pf-icon pf-icon-security";

    protected override rowLabel(item: Token): string | null {
        return item.identifier;
    }

    checkbox = true;
    clearOnRefresh = true;

    @property()
    order = "expires";

    async apiEndpoint(): Promise<PaginatedResponse<Token>> {
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
                <span slot="submit">${msg("Create")}</span>
                <span slot="header">${msg("Create Token")}</span>
                <ak-token-form slot="form"> </ak-token-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">${msg("Create")}</button>
            </ak-forms-modal>
        `;
    }

    row(item: Token): SlottedTemplateResult[] {
        return [
            html`<div>${item.identifier}</div>
                ${item.managed
                    ? html`<small>${msg("Token is managed by authentik.")}</small>`
                    : nothing}`,
            html`<a href="#/identity/users/${item.userObj?.pk}">${item.userObj?.username}</a>`,
            html`<ak-status-label type="warning" ?good=${item.expiring}></ak-status-label>`,
            Timestamp(item.expires && item.expiring ? item.expires : null),
            html`${intentToLabel(item.intent ?? IntentEnum.Api)}`,
            html`
                ${!item.managed
                    ? html`<ak-forms-modal>
                          <span slot="submit">${msg("Update")}</span>
                          <span slot="header">${msg("Update Token")}</span>
                          <ak-token-form slot="form" .instancePk=${item.identifier}></ak-token-form>
                          <button slot="trigger" class="pf-c-button pf-m-plain">
                              <pf-tooltip position="top" content=${msg("Edit")}>
                                  <i class="fas fa-edit" aria-hidden="true"></i>
                              </pf-tooltip>
                          </button>
                      </ak-forms-modal>`
                    : html` <button class="pf-c-button pf-m-plain" disabled>
                          <pf-tooltip
                              position="top"
                              content=${msg("Editing is disabled for managed tokens")}
                          >
                              <i class="fas fa-edit" aria-hidden="true"></i>
                          </pf-tooltip>
                      </button>`}
                <ak-rbac-object-permission-modal
                    model=${RbacPermissionsAssignedByRolesListModelEnum.AuthentikCoreToken}
                    objectPk=${item.pk}
                >
                </ak-rbac-object-permission-modal>
                <ak-token-copy-button
                    class="pf-c-button pf-m-plain"
                    identifier="${item.identifier}"
                >
                    <pf-tooltip position="top" content=${msg("Copy token")}>
                        <i class="fas fa-copy" aria-hidden="true"></i>
                    </pf-tooltip>
                </ak-token-copy-button>
            `,
        ];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-token-list": TokenListPage;
    }
}
