import "#elements/buttons/ActionButton/ak-action-button";
import "#elements/forms/SearchSelect/ak-search-select";
import "#admin/endpoints/connectors/agent/ConfigModal";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFList from "@patternfly/patternfly/components/List/list.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";

import { aki } from "#common/api/client";
import { EVENT_REFRESH } from "#common/constants";

import { AKElement } from "#elements/Base";
import type { SearchSelect } from "#elements/forms/SearchSelect/ak-search-select";
import type { SearchSelectChangeEvent } from "#elements/forms/SearchSelect/events";
import { SearchSelectSource, withQuery } from "#elements/forms/SearchSelect/shared";

import {
    AgentConnector,
    DeviceFactsOSFamily,
    EndpointsApi,
    EnrollmentToken,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css, CSSResult, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { createRef, ref } from "lit/directives/ref.js";

@customElement("ak-endpoints-connector-agent-setup")
export class AgentConnectorSetup extends AKElement {
    @property({ attribute: false })
    connector?: AgentConnector;

    @state()
    token?: EnrollmentToken;

    #tokenSelectRef = createRef<SearchSelect<EnrollmentToken>>();

    #tokenSource: SearchSelectSource<EnrollmentToken> = {
        fetchObjects: (query) =>
            aki(EndpointsApi)
                .endpointsAgentsEnrollmentTokensList(
                    withQuery(query, {
                        ordering: "name",
                        connector: this.connector?.connectorUuid,
                    }),
                )
                .then(({ results }) => results),
        keyOf: (token) => token.tokenUuid,
        labelOf: (token) => token.name,
        describe: (token) => html`${token.name}`,
    };

    static styles: CSSResult[] = [
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

    public connectedCallback(): void {
        super.connectedCallback();
        this.#refreshHandler = this.#refreshHandler.bind(this);
        window.addEventListener(EVENT_REFRESH, this.#refreshHandler);
    }

    public disconnectedCallback(): void {
        super.disconnectedCallback();
        window.removeEventListener(EVENT_REFRESH, this.#refreshHandler);
    }

    #refreshHandler = () => {
        this.#tokenSelectRef.value?.refresh();
    };

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
                    <p>
                        ${msg(
                            "Next, download the configuration to deploy the authentik Agent via MDM",
                        )}
                    </p>
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
                        ${ref(this.#tokenSelectRef)}
                        .source=${this.#tokenSource}
                        @ak-change=${(event: SearchSelectChangeEvent<EnrollmentToken>) => {
                            this.token = event.detail.value ?? undefined;
                        }}
                    ></ak-search-select>
                </div>
                <div class="pf-l-grid__item pf-m-12-col">
                    <ul class="pf-c-list pf-m-inline">
                        <li>
                            <ak-endpoints-agent-connector-config
                                class="pf-m-secondary"
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
