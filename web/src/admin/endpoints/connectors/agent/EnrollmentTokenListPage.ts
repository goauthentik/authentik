import "#admin/rbac/ObjectPermissionModal";
import "#admin/endpoints/connectors/agent/EnrollmentTokenForm";
import "#admin/endpoints/connectors/agent/ak-enrollment-token-copy-button";
import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";
import "#components/ak-status-label";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, Table, TableColumn, Timestamp } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import {
    AgentConnector,
    EndpointsApi,
    EnrollmentToken,
    RbacPermissionsAssignedByUsersListModelEnum,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-endpoints-agent-enrollment-token-list")
export class EnrollmentTokenListPage extends Table<EnrollmentToken> {
    checkbox = true;
    clearOnRefresh = true;

    protected override searchEnabled = true;

    @property()
    order = "name";

    @property({ attribute: false })
    connector?: AgentConnector;

    async apiEndpoint(): Promise<PaginatedResponse<EnrollmentToken>> {
        return new EndpointsApi(DEFAULT_CONFIG).endpointsAgentsEnrollmentTokensList({
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

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${msg("Enrollment Token(s)")}
            .objects=${this.selectedElements}
            .metadata=${(item: EnrollmentToken) => {
                return [
                    { key: msg("Name"), value: item.name },
                    { key: msg("Group"), value: item.deviceGroupObj?.name },
                ];
            }}
            .usedBy=${(item: EnrollmentToken) => {
                return new EndpointsApi(DEFAULT_CONFIG).endpointsAgentsEnrollmentTokensUsedByList({
                    tokenUuid: item.tokenUuid,
                });
            }}
            .delete=${(item: EnrollmentToken) => {
                return new EndpointsApi(DEFAULT_CONFIG).endpointsAgentsEnrollmentTokensDestroy({
                    tokenUuid: item.tokenUuid,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    row(item: EnrollmentToken): SlottedTemplateResult[] {
        return [
            html`${item.name}`,
            html`${item.deviceGroupObj?.name || "-"}`,
            html`<ak-status-label type="warning" ?good=${item.expiring}></ak-status-label>`,
            Timestamp(item.expires && item.expiring ? item.expires : null),
            html`<div>
                <ak-forms-modal>
                    <span slot="submit">${msg("Update")}</span>
                    <span slot="header">${msg("Update Endpoint")}</span>
                    <ak-endpoints-agent-enrollment-token-form
                        slot="form"
                        .instancePk=${item.tokenUuid}
                    >
                    </ak-endpoints-agent-enrollment-token-form>
                    <button slot="trigger" class="pf-c-button pf-m-plain">
                        <pf-tooltip position="top" content=${msg("Edit")}>
                            <i class="fas fa-edit" aria-hidden="true"></i>
                        </pf-tooltip>
                    </button>
                </ak-forms-modal>
                <ak-rbac-object-permission-modal
                    model=${RbacPermissionsAssignedByUsersListModelEnum.AuthentikEndpointsConnectorsAgentEnrollmenttoken}
                    objectPk=${item.tokenUuid}
                >
                </ak-rbac-object-permission-modal>
                <ak-enrollment-token-copy-button .identifier=${item.tokenUuid}>
                    <pf-tooltip position="top" content=${msg("Copy token")}>
                        <i class="fas fa-copy" aria-hidden="true"></i>
                    </pf-tooltip>
                </ak-enrollment-token-copy-button>
            </div>`,
        ];
    }

    renderObjectCreate(): TemplateResult {
        return html`
            <ak-forms-modal>
                <span slot="submit">${msg("Create")}</span>
                <span slot="header">${msg("Create Enrollment Token")}</span>
                <ak-endpoints-agent-enrollment-token-form
                    slot="form"
                    .connectorID=${this.connector?.connectorUuid}
                >
                </ak-endpoints-agent-enrollment-token-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">${msg("Create")}</button>
            </ak-forms-modal>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-endpoints-agent-enrollment-token-list": EnrollmentTokenListPage;
    }
}
