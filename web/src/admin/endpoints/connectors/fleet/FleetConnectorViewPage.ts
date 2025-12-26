import "#elements/Tabs";
import "#components/events/ObjectChangelog";
import "#admin/rbac/ObjectPermissionsPage";
import "#elements/tasks/ScheduleList";
import "#elements/tasks/TaskList";

import { DEFAULT_CONFIG } from "#common/api/config";
import { APIError, parseAPIResponseError } from "#common/errors/network";

import { AKElement } from "#elements/Base";

import { setPageDetails } from "#components/ak-page-navbar";

import {
    EndpointsApi,
    FleetConnector,
    ModelEnum,
    RbacPermissionsAssignedByRolesListModelEnum,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing, PropertyValues } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";

const [FLEET_CONNECTOR_APP_LABEL, FLEET_CONNECTOR_MODEL_NAME] =
    ModelEnum.AuthentikEndpointsConnectorsFleetFleetconnector.split(".");

@customElement("ak-endpoints-connector-fleet-view")
export class FleetConnectorViewPage extends AKElement {
    @property({ type: String })
    public connectorId?: string;

    @state()
    protected connector?: FleetConnector;

    @state()
    protected error?: APIError;

    static styles: CSSResult[] = [PFCard, PFPage, PFGrid, PFButton, PFDescriptionList];

    protected fetchDevice(id: string) {
        new EndpointsApi(DEFAULT_CONFIG)
            .endpointsFleetConnectorsRetrieve({ connectorUuid: id })
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

    public override updated(changed: PropertyValues<this>) {
        super.updated(changed);
        setPageDetails({
            icon: "pf-icon pf-icon-data-source",
            header: this.connector?.name,
            description: this.connector?.verboseName,
        });
    }

    protected renderTabOverview() {
        return html`<div
            class="pf-c-page__main-section pf-m-no-padding-mobile pf-l-grid pf-m-gutter"
        >
            <div class="pf-l-grid__item pf-m-12-col pf-l-stack__item">
                <div class="pf-c-card">
                    <div class="pf-c-card__header">
                        <div class="pf-c-card__title">${msg("Schedules")}</div>
                    </div>
                    <div class="pf-c-card__body">
                        <ak-schedule-list
                            .relObjAppLabel=${FLEET_CONNECTOR_APP_LABEL}
                            .relObjModel=${FLEET_CONNECTOR_MODEL_NAME}
                            .relObjId="${this.connector?.connectorUuid}"
                        ></ak-schedule-list>
                    </div>
                </div>
            </div>
            <div class="pf-l-grid__item pf-m-12-col pf-l-stack__item">
                <div class="pf-c-card">
                    <div class="pf-c-card__header">
                        <div class="pf-c-card__title">${msg("Tasks")}</div>
                    </div>
                    <div class="pf-c-card__body">
                        <ak-task-list
                            .relObjAppLabel=${FLEET_CONNECTOR_APP_LABEL}
                            .relObjModel=${FLEET_CONNECTOR_MODEL_NAME}
                            .relObjId="${this.connector?.connectorUuid}"
                        ></ak-task-list>
                    </div>
                </div>
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
                aria-label=${msg("Permissions")}
                model=${RbacPermissionsAssignedByRolesListModelEnum.AuthentikEndpointsConnectorsFleetFleetconnector}
                objectPk=${this.connector.connectorUuid!}
            ></ak-rbac-object-permission-page>
        </ak-tabs> `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-endpoints-connector-fleet-view": FleetConnectorViewPage;
    }
}
