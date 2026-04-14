import "#admin/rbac/ObjectPermissionModal";
import "#admin/endpoints/connectors/agent/EnrollmentTokenForm";
import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";
import "#components/ak-status-label";

import { DEFAULT_CONFIG } from "#common/api/config";

import { IconEnrollmentTokenCopyButton } from "#elements/buttons/IconEnrollmentTokenCopyButton";
import { IconEditButton, ModalInvokerButton } from "#elements/dialogs";
import { IconPermissionButton } from "#elements/dialogs/components/IconPermissionButton";
import { PaginatedResponse, Table, TableColumn, Timestamp } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { EnrollmentTokenForm } from "#admin/endpoints/connectors/agent/EnrollmentTokenForm";

import { AgentConnector, EndpointsApi, EnrollmentToken, ModelEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-endpoints-agent-enrollment-token-list")
export class EnrollmentTokenListPage extends Table<EnrollmentToken> {
    #api = new EndpointsApi(DEFAULT_CONFIG);

    protected override searchEnabled = true;
    protected emptyStateMessage = msg("No enrollment tokens found for this connector.");

    public override checkbox = true;
    public override clearOnRefresh = true;

    public override searchPlaceholder = msg("Search for an enrollment token...");

    public override order = "name";

    @property({ attribute: false })
    public connector: AgentConnector | null = null;

    protected override async apiEndpoint(): Promise<PaginatedResponse<EnrollmentToken>> {
        return this.#api.endpointsAgentsEnrollmentTokensList({
            ...(await this.defaultEndpointConfig()),
            connector: this.connector?.connectorUuid,
        });
    }

    protected columns: TableColumn[] = [
        [msg("Name"), "name"],
        [msg("Group")],
        [msg("Expires?"), "expiring"],
        [msg("Expiry date"), "expires"],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    protected override renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;

        return html`<ak-forms-delete-bulk
            object-label=${msg("Enrollment Token(s)")}
            .objects=${this.selectedElements}
            .metadata=${(item: EnrollmentToken) => {
                return [
                    { key: msg("Name"), value: item.name },
                    { key: msg("Group"), value: item.deviceGroupObj?.name },
                ];
            }}
            .usedBy=${(item: EnrollmentToken) => {
                return this.#api.endpointsAgentsEnrollmentTokensUsedByList({
                    tokenUuid: item.tokenUuid,
                });
            }}
            .delete=${(item: EnrollmentToken) => {
                return this.#api.endpointsAgentsEnrollmentTokensDestroy({
                    tokenUuid: item.tokenUuid,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    protected override row(item: EnrollmentToken): SlottedTemplateResult[] {
        return [
            item.name,
            item.deviceGroupObj?.name || msg("-"),
            html`<ak-status-label type="warning" ?good=${item.expiring}></ak-status-label>`,
            Timestamp(item.expires && item.expiring ? item.expires : null),
            html`<div class="ak-c-table__actions">
                ${IconEditButton(EnrollmentTokenForm, item.tokenUuid, item.name)}
                ${IconPermissionButton(item.name, {
                    model: ModelEnum.AuthentikEndpointsConnectorsAgentEnrollmenttoken,
                    objectPk: item.tokenUuid,
                })}
                ${IconEnrollmentTokenCopyButton(item.tokenUuid)}
            </div>`,
        ];
    }

    protected override renderObjectCreate(): SlottedTemplateResult {
        return ModalInvokerButton(EnrollmentTokenForm, {
            connectorID: this.connector?.connectorUuid,
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-endpoints-agent-enrollment-token-list": EnrollmentTokenListPage;
    }
}
