import "#components/ak-status-label";
import "#admin/endpoints/devices/BoundDeviceUsersList";

import { DEFAULT_CONFIG } from "#common/api/config";
import { APIError, parseAPIResponseError } from "#common/errors/network";

import { AKElement } from "#elements/Base";
import { Timestamp } from "#elements/table/shared";

import { setPageDetails } from "#components/ak-page-navbar";
import renderDescriptionList from "#components/DescriptionList";

import { AgentConnector, Disk, EndpointDevice, EndpointsApi } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { CSSResult, html, nothing, PropertyValues } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-endpoints-connector-agent-view")
export class AgentConnectorViewPage extends AKElement {
    @property({ type: String })
    public connectorId?: string;

    @state()
    protected connector?: AgentConnector;

    @state()
    protected error?: APIError;

    static styles: CSSResult[] = [PFBase, PFCard, PFPage, PFGrid, PFButton, PFDescriptionList];

    protected fetchDevice(id: string) {
        new EndpointsApi(DEFAULT_CONFIG)
            .endpointsAgentsConnectorsRetrieve({ connectorUuid: id })
            .then((conn) => {
                this.connector = conn;
            })
            .catch(async (error) => {
                this.error = await parseAPIResponseError(error);
            });
    }

    public override willUpdate(changedProperties: PropertyValues<this>) {
        if (changedProperties.has("connectorId") && this.connectorId) {
            this.fetchDevice(this.connectorId);
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

    render() {
        if (!this.connector) {
            return nothing;
        }
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-endpoints-connector-agent-view": AgentConnectorViewPage;
    }
}
