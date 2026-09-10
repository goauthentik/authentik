import "#admin/rbac/ObjectPermissionModal";
import "#admin/stages/authenticator_webauthn/WebAuthnRPConfigForm";
import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";

import { aki } from "#common/api/client";

import { IconEditButton, ModalInvokerButton } from "#elements/dialogs";
import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { WebAuthnRPConfigForm } from "#admin/stages/authenticator_webauthn/WebAuthnRPConfigForm";

import { ModelEnum, StagesApi, WebAuthnRPConfig } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-stage-authenticator-webauthn-rp-config-list")
export class WebAuthnRPConfigListPage extends TablePage<WebAuthnRPConfig> {
    protected override searchEnabled = true;
    public override searchPlaceholder = msg("Search by name or RP ID...", {
        id: "webauthn-rp-config.list.search.placeholder",
    });
    public pageTitle = msg("WebAuthn RP Configs", { id: "webauthn-rp-config.verbose-name-plural" });
    public pageDescription = msg(
        "Share WebAuthn credentials such as passkeys across brands by binding them to one fixed Relying Party ID with an explicit list of allowed origins.",
        { id: "webauthn-rp-config.list.description" },
    );
    public pageIcon = "pf-icon pf-icon-key";

    checkbox = true;
    clearOnRefresh = true;

    @property()
    order = "name";

    async apiEndpoint(): Promise<PaginatedResponse<WebAuthnRPConfig>> {
        return aki(StagesApi).stagesAuthenticatorWebauthnRpConfigsList(
            await this.defaultEndpointConfig(),
        );
    }

    protected override rowLabel(item: WebAuthnRPConfig): string | null {
        return item.name ?? null;
    }

    protected columns: TableColumn[] = [
        [msg("Name", { id: "webauthn-rp-config.form.name.label" }), "name"],
        [msg("RP ID", { id: "webauthn-rp-config.form.rp-id.label" }), "rp_id"],
        [msg("Origins", { id: "webauthn-rp-config.list.origins.label" }), null],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    protected override renderToolbarSelected(): SlottedTemplateResult {
        const disabled = this.selectedElements.length < 1;

        return html`<ak-forms-delete-bulk
            object-label=${msg("WebAuthn RP Config(s)", {
                id: "webauthn-rp-config.list.object-label",
            })}
            .objects=${this.selectedElements}
            .metadata=${(item: WebAuthnRPConfig) => {
                return [
                    {
                        key: msg("RP ID", { id: "webauthn-rp-config.form.rp-id.label" }),
                        value: item.rpId,
                    },
                ];
            }}
            .usedBy=${(item: WebAuthnRPConfig) => {
                return aki(StagesApi).stagesAuthenticatorWebauthnRpConfigsUsedByList({
                    rpConfigUuid: item.rpConfigUuid,
                });
            }}
            .delete=${(item: WebAuthnRPConfig) => {
                return aki(StagesApi).stagesAuthenticatorWebauthnRpConfigsDestroy({
                    rpConfigUuid: item.rpConfigUuid,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    protected override row(item: WebAuthnRPConfig): SlottedTemplateResult[] {
        return [
            item.name,
            item.rpId,
            html`${(item.origins ?? []).join(", ")}`,
            html`<div class="ak-c-table__actions">
                ${IconEditButton(WebAuthnRPConfigForm, item.rpConfigUuid, item.name)}

                <ak-rbac-object-permission-modal
                    model=${ModelEnum.AuthentikStagesAuthenticatorWebauthnWebauthnrpconfig}
                    objectPk=${item.rpConfigUuid}
                >
                </ak-rbac-object-permission-modal>
            </div>`,
        ];
    }

    protected override renderObjectCreate(): SlottedTemplateResult {
        return ModalInvokerButton(WebAuthnRPConfigForm);
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-authenticator-webauthn-rp-config-list": WebAuthnRPConfigListPage;
    }
}
