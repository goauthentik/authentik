import "#elements/Tabs";
import "#components/events/ObjectChangelog";
import "#admin/rbac/ObjectPermissionsPage";
import "#admin/endpoints/connectors/agent/EnrollmentTokenListPage";
import "#admin/endpoints/connectors/agent/AgentConnectorSetup";

import { DEFAULT_CONFIG } from "#common/api/config";
import { APIError, parseAPIResponseError } from "#common/errors/network";

import { AKElement } from "#elements/Base";

import { setPageDetails } from "#components/ak-page-navbar";

import {
    AgentConnector,
    EndpointsApi,
    RbacPermissionsAssignedByUsersListModelEnum,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
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

    renderTabOverview() {
        return html`<div
            class="pf-c-page__main-section pf-m-no-padding-mobile pf-l-grid pf-m-gutter"
        >
            <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                <div class="pf-c-card__title">${msg("Setup")}</div>
                <ak-endpoints-connector-agent-setup
                    class="pf-c-card__body"
                    .connector=${this.connector}
                ></ak-endpoints-connector-agent-setup>
            </div>
            <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                <div class="pf-c-card__title">${msg("Enrollment Tokens")}</div>
                <ak-endpoints-agent-enrollment-token-list
                    .connector=${this.connector}
                ></ak-endpoints-agent-enrollment-token-list>
            </div>
        </div> `;
    }

    render() {
        if (!this.connector) {
            return nothing;
        }
        return html`<ak-tabs>
            <div
                role="tabpanel"
                tabindex="0"
                slot="page-overview"
                id="page-overview"
                aria-label="${msg("Overview")}"
            >
                ${this.renderTabOverview()}
            </div>
            <div
                role="tabpanel"
                tabindex="0"
                slot="page-changelog"
                id="page-changelog"
                aria-label="${msg("Changelog")}"
                class="pf-c-page__main-section pf-m-no-padding-mobile"
            >
                <div class="pf-c-card">
                    <div class="pf-c-card__body">
                        <ak-object-changelog
                            targetModelPk=${this.connector?.connectorUuid || ""}
                            targetModelName=${this.connector?.metaModelName || ""}
                        >
                        </ak-object-changelog>
                    </div>
                </div>
            </div>
            <ak-rbac-object-permission-page
                role="tabpanel"
                tabindex="0"
                slot="page-permissions"
                id="page-permissions"
                aria-label="${msg("Permissions")}"
                model=${RbacPermissionsAssignedByUsersListModelEnum.AuthentikEndpointsConnectorsAgentAgentconnector}
                objectPk=${this.connector.connectorUuid!}
            ></ak-rbac-object-permission-page>
        </ak-tabs> `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-endpoints-connector-agent-view": AgentConnectorViewPage;
    }
}
