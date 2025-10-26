import "#admin/endpoints/connectors/ConnectorWizard";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { Connector, EndpointsApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-endpoints-connectors-list")
export class ConnectorsListPage extends TablePage<Connector> {
    public pageIcon = "pf-icon pf-icon-data-source";
    public pageTitle = msg("Connectors");
    public pageDescription = msg("TODO");

    protected columns: TableColumn[] = [[msg("Name"), "name"], [msg("Type")]];

    async apiEndpoint(): Promise<PaginatedResponse<Connector>> {
        return new EndpointsApi(DEFAULT_CONFIG).endpointsConnectorsList(
            await this.defaultEndpointConfig(),
        );
    }

    row(item: Connector): SlottedTemplateResult[] {
        return [html`${item.name}`, html`${item.verboseName}`];
    }

    renderObjectCreate() {
        return html`<ak-endpoint-connector-wizard></ak-endpoint-connector-wizard> `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-endpoints-connectors-list": ConnectorsListPage;
    }
}
