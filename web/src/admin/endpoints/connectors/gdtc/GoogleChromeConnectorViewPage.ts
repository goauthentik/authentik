import "#elements/Tabs";
import "#admin/events/ObjectChangelog";
import "#admin/rbac/ak-rbac-object-permission-page";
import "#admin/rbac/ObjectPermissionModal";
import "#elements/tasks/ScheduleList";
import "#elements/tasks/TaskList";

import { DEFAULT_CONFIG } from "#common/api/config";
import { APIError, parseAPIResponseError } from "#common/errors/network";

import { AKElement } from "#elements/Base";

import { setPageDetails } from "#components/ak-page-navbar";

import { EndpointsApi, GoogleChromeConnector, ModelEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing, PropertyValues } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";

@customElement("ak-endpoints-connector-google-chrome-view")
export class GoogleChromeConnectorViewPage extends AKElement {
    @property({ type: String })
    public connectorId?: string;

    @state()
    protected connector?: GoogleChromeConnector;

    @state()
    protected error?: APIError;

    static styles: CSSResult[] = [PFCard, PFPage, PFGrid, PFButton, PFDescriptionList];

    protected fetchDevice(id: string) {
        new EndpointsApi(DEFAULT_CONFIG)
            .endpointsGoogleChromeConnectorsRetrieve({ connectorUuid: id })
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
                class="pf-c-page__main-section pf-m-no-padding-mobile"
            >
                <div class="pf-c-card">
                    <ak-object-changelog
                        targetModelPk=${this.connector?.connectorUuid || ""}
                        targetModelName=${this.connector?.metaModelName || ""}
                    >
                    </ak-object-changelog>
                </div>
            </div>
            <ak-rbac-object-permission-page
                role="tabpanel"
                tabindex="0"
                slot="page-permissions"
                id="page-permissions"
                aria-label=${msg("Permissions")}
                model=${ModelEnum.AuthentikEndpointsConnectorsGoogleChromeGooglechromeconnector}
                objectPk=${this.connector.connectorUuid!}
            ></ak-rbac-object-permission-page>
        </ak-tabs> `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-endpoints-connector-google-chrome-view": GoogleChromeConnectorViewPage;
    }
}
