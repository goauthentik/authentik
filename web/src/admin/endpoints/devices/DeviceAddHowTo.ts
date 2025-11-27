import "#admin/endpoints/connectors/agent/AgentConnectorSetup";
import "#elements/Tabs";

import { DEFAULT_CONFIG } from "#common/api/config";

import { ModalButton } from "#elements/buttons/ModalButton";

import { Connector, EndpointsApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, state } from "lit/decorators.js";

@customElement("ak-endpoints-device-add")
export class DeviceAddHowTo extends ModalButton {
    @state()
    connectors: Connector[] = [];

    connectedCallback(): void {
        super.connectedCallback();
        this.addEventListener("ak-modal-show", (e) => {
            new EndpointsApi(DEFAULT_CONFIG).endpointsConnectorsList().then((e) => {
                this.connectors = e.results;
            });
        });
    }

    renderSetup(connector: Connector) {
        switch (connector.component) {
            case "ak-endpoints-connector-agent-form":
                return html`<ak-endpoints-connector-agent-setup
                    .connector=${connector}
                ></ak-endpoints-connector-agent-setup>`;
        }
        return html`<p>${msg("Configured connector does not support setup.")}</p>`;
    }

    renderNone() {
        return html`<p>
            ${msg(
                "No connectors configured. Navigate to connectors in the sidebar and create a connector.",
            )}
        </p>`;
    }

    renderModalInner(): TemplateResult {
        return html`<div class="pf-c-modal-box__header">
                <h1 class="pf-c-title pf-m-2xl">${msg("Connector setup")}</h1>
            </div>
            <div class="pf-c-modal-box__body">
                ${this.connectors.length === 0
                    ? this.renderNone()
                    : html` <ak-tabs part="tabs" vertical>
                          ${this.connectors.map((c, idx) => {
                              return html`<div
                                  role="tabpanel"
                                  tabindex="0"
                                  slot="page-${c.connectorUuid}"
                                  id="page-${c.connectorUuid}"
                                  aria-label="${c.verboseName} ${c.name}"
                                  class="pf-c-page__main-section pf-m-no-padding-mobile"
                              >
                                  ${this.renderSetup(c)}
                              </div>`;
                          })}
                      </ak-tabs>`}
            </div>
            <footer class="pf-c-modal-box__footer pf-m-align-left">
                <button
                    class="pf-c-button pf-m-primary"
                    @click=${() => {
                        this.open = false;
                    }}
                >
                    ${msg("Close")}
                </button>
            </footer>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-endpoints-device-add": DeviceAddHowTo;
    }
}
