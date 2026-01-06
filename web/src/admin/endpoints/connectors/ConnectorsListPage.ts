import "#admin/endpoints/connectors/ConnectorWizard";
import "#admin/endpoints/connectors/agent/AgentConnectorForm";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ProxyForm";
import "#elements/forms/ModalForm";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { Connector, EndpointsApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-endpoints-connectors-list")
export class ConnectorsListPage extends TablePage<Connector> {
    public pageIcon = "pf-icon pf-icon-data-source";
    public pageTitle = msg("Connectors");
    public pageDescription = msg(
        "Configure how devices connect with authentik and ingest external device data.",
    );

    protected searchEnabled: boolean = true;
    protected columns: TableColumn[] = [
        [msg("Name"), "name"],
        [msg("Type")],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    checkbox = true;

    async apiEndpoint(): Promise<PaginatedResponse<Connector>> {
        return new EndpointsApi(DEFAULT_CONFIG).endpointsConnectorsList(
            await this.defaultEndpointConfig(),
        );
    }

    row(item: Connector): SlottedTemplateResult[] {
        return [
            html`<a href="#/endpoints/connectors/${item.connectorUuid}">${item.name}</a>`,
            html`${item.verboseName}`,
            html`<div>
                <ak-forms-modal>
                    <span slot="submit">${msg("Update")}</span>
                    <span slot="header">${msg("Update Connector")}</span>
                    <ak-proxy-form
                        slot="form"
                        .args=${{
                            instancePk: item.connectorUuid,
                        }}
                        type=${ifDefined(item.component)}
                    >
                    </ak-proxy-form>
                    <button slot="trigger" class="pf-c-button pf-m-plain">
                        <pf-tooltip position="top" content=${msg("Edit")}>
                            <i class="fas fa-edit" aria-hidden="true"></i>
                        </pf-tooltip>
                    </button>
                </ak-forms-modal>
            </div>`,
        ];
    }

    renderObjectCreate() {
        return html`<ak-endpoint-connector-wizard></ak-endpoint-connector-wizard> `;
    }

    renderToolbarSelected() {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${msg("Connector(s)")}
            .objects=${this.selectedElements}
            .metadata=${(item: Connector) => {
                return [{ key: msg("Name"), value: item.name }];
            }}
            .usedBy=${(item: Connector) => {
                return new EndpointsApi(DEFAULT_CONFIG).endpointsConnectorsUsedByList({
                    connectorUuid: item.connectorUuid!,
                });
            }}
            .delete=${(item: Connector) => {
                return new EndpointsApi(DEFAULT_CONFIG).endpointsConnectorsDestroy({
                    connectorUuid: item.connectorUuid!,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-endpoints-connectors-list": ConnectorsListPage;
    }
}
