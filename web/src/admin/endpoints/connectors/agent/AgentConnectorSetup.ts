import "#elements/buttons/ActionButton/ak-action-button";
import "#elements/forms/SearchSelect/index";

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
import { CSSResult, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFList from "@patternfly/patternfly/components/List/list.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-endpoints-connector-agent-setup")
export class AgentConnectorSetup extends AKElement {
    @property({ attribute: false })
    connector?: AgentConnector;

    @state()
    token?: EnrollmentToken;

    static styles: CSSResult[] = [PFBase, PFList];

    render() {
        return html`<h2>${msg("Download the latest package from here:")}</h2>
            <ul class="pf-c-list pf-m-inline">
                <li>
                    <a
                        href="https://pkg.goauthentik.io/packages/authentik_windows-2025_agent/agent_local/agent.msi"
                        >${msg("Windows")}</a
                    >
                </li>
                <li>
                    <a
                        href="https://pkg.goauthentik.io/packages/authentik_macos-15_agent/agent_local/authentik%20agent%20installer.pkg"
                        >${msg("macOS")}</a
                    >
                </li>
                <li><a href="https://pkg.goauthentik.io/">${msg("Linux")}</a></li>
            </ul>
            <h2>${msg("Afterwards, download the configuration for your MDM Software")}</h2>
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

            <ul class="pf-c-list pf-m-inline">
                <li>
                    <ak-action-button
                        class="pf-m-link"
                        label=${msg("Windows")}
                        .apiRequest=${() => {
                            return new EndpointsApi(
                                DEFAULT_CONFIG,
                            ).endpointsAgentsConnectorsMdmConfigCreate({
                                connectorUuid: this.connector?.connectorUuid || "",
                                mDMConfigRequest: {
                                    platform: DeviceFactsOSFamily.Windows,
                                    enrollmentToken: this.token?.tokenUuid || "",
                                },
                            });
                        }}
                    >
                        ${msg("Windows")}
                    </ak-action-button>
                </li>
                <li>
                    <ak-action-button
                        class="pf-m-link"
                        label=${msg("Windows")}
                        .apiRequest=${() => {
                            return new EndpointsApi(
                                DEFAULT_CONFIG,
                            ).endpointsAgentsConnectorsMdmConfigCreate({
                                connectorUuid: this.connector?.connectorUuid || "",
                                mDMConfigRequest: {
                                    platform: DeviceFactsOSFamily.MacOs,
                                    enrollmentToken: this.token?.tokenUuid || "",
                                },
                            });
                        }}
                    >
                        ${msg("macOS")}
                    </ak-action-button>
                </li>
            </ul>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-endpoints-connector-agent-setup": AgentConnectorSetup;
    }
}
