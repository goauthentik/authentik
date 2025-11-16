import "#admin/endpoints/connectors/agent/AgentConnectorViewPage";
import "#elements/EmptyState";
import "#elements/buttons/SpinnerButton/ak-spinner-button";

import { DEFAULT_CONFIG } from "#common/api/config";

import { AKElement } from "#elements/Base";

import { setPageDetails } from "#components/ak-page-navbar";

import { Connector, EndpointsApi } from "@goauthentik/api";

import { CSSResult, html, PropertyValues, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFPage from "@patternfly/patternfly/components/Page/page.css";

@customElement("ak-endpoints-connector-view")
export class ConnectorViewPage extends AKElement {
    @property({ type: String })
    set connectorID(value: string) {
        new EndpointsApi(DEFAULT_CONFIG)
            .endpointsConnectorsRetrieve({
                connectorUuid: value,
            })
            .then((conn) => (this.connector = conn));
    }

    @property({ attribute: false })
    connector?: Connector;

    static styles: CSSResult[] = [PFPage];

    render(): TemplateResult {
        if (!this.connector) {
            return html`<ak-empty-state loading full-height></ak-empty-state>`;
        }
        switch (this.connector?.component) {
            case "ak-endpoints-connector-agent-form":
                return html`<ak-endpoints-connector-agent-view
                    connectorID=${ifDefined(this.connector.connectorUuid)}
                ></ak-endpoints-connector-agent-view>`;
            default:
                return html`<p>Invalid connector type ${this.connector?.component}</p>`;
        }
    }

    updated(changed: PropertyValues<this>) {
        super.updated(changed);
        setPageDetails({
            icon: "pf-icon pf-icon-data-source",
            header: this.connector?.name,
            description: this.connector?.verboseName,
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-endpoints-connector-view": ConnectorViewPage;
    }
}
