import "#admin/rbac/ObjectPermissionModal";
import "#admin/tokens/TokenForm";
import "#components/ak-status-label";
import "#elements/buttons/Dropdown";
import "#elements/buttons/TokenCopyButton/index";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";
import { formatIntentLabel } from "#common/labels";

import { IconTokenCopyButton } from "#elements/buttons/IconTokenCopyButton";
import { IconEditButton, ModalInvokerButton } from "#elements/dialogs";
import { IconPermissionButton } from "#elements/dialogs/components/IconPermissionButton";
import { showAPIErrorMessage } from "#elements/messages/MessageContainer";
import { PaginatedResponse, Table, TableColumn, Timestamp } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { TokenForm } from "#admin/tokens/TokenForm";

import { CoreApi, IntentEnum, ModelEnum, Token, User } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing, PropertyValues } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-admin-user-token-list")
export class AdminUserTokenList extends Table<Token> {
    public static override verboseName = msg("Token");
    public static override verboseNamePlural = msg("Tokens");

    @property({ type: Number, attribute: "user-id", useDefault: true })
    public userID: number | null = null;

    @property({ attribute: false, useDefault: true })
    public user: User | null = null;

    protected override searchEnabled = true;

    protected override rowLabel(item: Token): string | null {
        return item.identifier;
    }

    public override checkbox = true;
    public override clearOnRefresh = true;
    public override order = "expires";

    //#region Lifecycle

    protected override async apiEndpoint(): Promise<PaginatedResponse<Token>> {
        if (!this.user) {
            await this.refresh();
        }

        if (!this.user) {
            throw new TypeError("User is not set, cannot fetch tokens.");
        }

        return new CoreApi(DEFAULT_CONFIG).coreTokensList({
            ...(await this.defaultEndpointConfig()),
            userUsername: this.user.username,
        });
    }

    public refresh = () => {
        if (!this.userID) {
            return;
        }

        return new CoreApi(DEFAULT_CONFIG)
            .coreUsersRetrieve({
                id: this.userID!,
            })
            .then((user) => {
                this.user = user;
            })
            .catch(showAPIErrorMessage);
    };

    protected override updated(changed: PropertyValues<this>) {
        super.updated(changed);

        if (changed.has("userID") && this.userID !== null) {
            this.refresh();
        }
    }

    //#region

    //#endregion

    //#region Rendering

    protected override renderObjectCreate(): SlottedTemplateResult {
        if (!this.user) {
            return null;
        }

        return ModalInvokerButton(TokenForm, { defaultUser: this.user });
    }

    protected columns: TableColumn[] = [
        [msg("Identifier"), "identifier"],
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

    protected override row(item: Token): SlottedTemplateResult[] {
        return [
            html`<div>${item.identifier}</div>
                ${item.managed
                    ? html`<small>${msg("Token is managed by authentik.")}</small>`
                    : nothing}`,
            html`<ak-status-label type="warning" ?good=${item.expiring}></ak-status-label>`,
            Timestamp(item.expires && item.expiring ? item.expires : null),
            html`${formatIntentLabel(item.intent ?? IntentEnum.Api)}`,
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
                ${IconTokenCopyButton(item)}
            </div>`,
        ];
    }

    //#endregion
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-admin-user-token-list": AdminUserTokenList;
    }
}
