import "#elements/buttons/ActionButton/ak-action-button";
import "#elements/forms/SearchSelect/index";
import "#admin/endpoints/connectors/agent/ConfigModal";

import { DEFAULT_CONFIG } from "#common/api/config";

import { AKElement } from "#elements/Base";

import {
    AgentConnector,
    DeviceFactsOSFamily,
    EndpointsAgentsEnrollmentTokensListRequest,
    EndpointsApi,
    EnrollmentToken,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css, CSSResult, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFList from "@patternfly/patternfly/components/List/list.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-endpoints-connector-agent-setup")
export class AgentConnectorSetup extends AKElement {
    @property({ attribute: false })
    connector?: AgentConnector;

    @state()
    token?: EnrollmentToken;

    static styles: CSSResult[] = [
        PFBase,
        PFGrid,
        PFButton,
        PFList,
        css`
            .pf-l-grid__item.pf-m-12-col {
                padding: 1rem 0;
                display: flex;
                flex-direction: row;
                align-items: center;
                width: 100%;
            }
        `,
    ];

    render() {
        return html`<div class="pf-l-grid pf-m-gutter">
            <div class="pf-l-grid__item pf-m-6-col pf-l-grid">
                <div class="pf-l-grid__item pf-m-12-col">
                    <p>${msg("Download the latest package from here:")}</p>
                </div>
                <div class="pf-l-grid__item pf-m-12-col">
                    <p>${msg("Afterwards, select the enrollment token you want to use:")}</p>
                </div>
                <div class="pf-l-grid__item pf-m-12-col">
                    <p>${msg("Then download the configuration to deploy the authentik Agent")}</p>
                </div>
            </div>
            <div class="pf-l-grid__item pf-m-6-col pf-l-grid">
                <div class="pf-l-grid__item pf-m-12-col">
                    <ul class="pf-c-list pf-m-inline">
                        <li>
                            <a
                                class="pf-c-button pf-m-secondary"
                                target="_blank"
                                href="https://pkg.goauthentik.io/packages/authentik_windows-2025_agent/agent_local/agent.msi"
                                >${msg("Windows")}</a
                            >
                        </li>
                        <li>
                            <a
                                class="pf-c-button pf-m-secondary"
                                target="_blank"
                                href="https://pkg.goauthentik.io/packages/authentik_macos-15_agent/agent_local/authentik%20agent%20installer.pkg"
                                >${msg("macOS")}</a
                            >
                        </li>
                        <li>
                            <a
                                class="pf-c-button pf-m-secondary"
                                target="_blank"
                                href="https://pkg.goauthentik.io/"
                                >${msg("Linux")}</a
                            >
                        </li>
                    </ul>
                </div>
                <div class="pf-l-grid__item pf-m-12-col">
                    <ak-search-select
                        .fetchObjects=${async (query?: string): Promise<EnrollmentToken[]> => {
                            const args: EndpointsAgentsEnrollmentTokensListRequest = {
                                ordering: "name",
                                connector: this.connector?.connectorUuid,
                            };
                            if (query !== undefined) {
                                args.search = query;
                            }
                            const token = await new EndpointsApi(
                                DEFAULT_CONFIG,
                            ).endpointsAgentsEnrollmentTokensList(args);
                            return token.results;
                        }}
                        .renderElement=${(token: EnrollmentToken): string => {
                            return token.name;
                        }}
                        .renderDescription=${(token: EnrollmentToken) => {
                            return html`${token.name}`;
                        }}
                        .value=${(token: EnrollmentToken | undefined): string | undefined => {
                            return token?.tokenUuid;
                        }}
                        @ak-change=${(ev: CustomEvent) => {
                            this.token = ev.detail.value;
                        }}
                    >
                    </ak-search-select>
                </div>
                <div class="pf-l-grid__item pf-m-12-col">
                    <ul class="pf-c-list pf-m-inline">
                        <li>
                            <ak-endpoints-agent-connector-config
                                class="pf-m-secondary"
                                label=${msg("Windows")}
                                .request=${{
                                    connectorUuid: this.connector?.connectorUuid || "",
                                    mDMConfigRequest: {
                                        platform: DeviceFactsOSFamily.Windows,
                                        enrollmentToken: this.token?.tokenUuid || "",
                                    },
                                }}
                            >
                                <button
                                    slot="trigger"
                                    class="pf-c-button pf-m-secondary"
                                    ?disabled=${!this.token}
                                >
                                    ${msg("Windows")}
                                </button>
                            </ak-endpoints-agent-connector-config>
                        </li>
                        <li>
                            <ak-endpoints-agent-connector-config
                                class="pf-m-link"
                                label=${msg("macOS")}
                                .request=${{
                                    connectorUuid: this.connector?.connectorUuid || "",
                                    mDMConfigRequest: {
                                        platform: DeviceFactsOSFamily.MacOs,
                                        enrollmentToken: this.token?.tokenUuid || "",
                                    },
                                }}
                            >
                                <button
                                    slot="trigger"
                                    class="pf-c-button pf-m-secondary"
                                    ?disabled=${!this.token}
                                >
                                    ${msg("macOS")}
                                </button>
                            </ak-endpoints-agent-connector-config>
                        </li>
                    </ul>
                </div>
            </div>
        </div> `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-endpoints-connector-agent-setup": AgentConnectorSetup;
    }
}
