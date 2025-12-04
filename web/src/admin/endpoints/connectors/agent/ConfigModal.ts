import "#elements/CodeMirror";
import "#elements/buttons/ActionButton/index";

import { DEFAULT_CONFIG } from "#common/api/config";
import { MessageLevel } from "#common/messages";

import { ModalButton } from "#elements/buttons/ModalButton";
import { CodeMirrorMode } from "#elements/CodeMirror";
import { showMessage } from "#elements/messages/MessageContainer";

import { EndpointsAgentsConnectorsMdmConfigCreateRequest, EndpointsApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-endpoints-agent-connector-config")
export class ConfigModal extends ModalButton {
    @property({ attribute: false })
    request?: EndpointsAgentsConnectorsMdmConfigCreateRequest;

    @state()
    config?: string;

    connectedCallback(): void {
        super.connectedCallback();
        this.addEventListener("ak-modal-show", (e) => {
            if (!this.request) return;
            new EndpointsApi(DEFAULT_CONFIG)
                .endpointsAgentsConnectorsMdmConfigCreate(this.request)
                .then((e) => {
                    this.config = e.config;
                })
                .catch((exc) => {
                    this.config = exc.toString();
                });
        });
    }
    renderModalInner() {
        return html`<div class="pf-c-modal-box__header">
                <h1 class="pf-c-title pf-m-2xl">${msg("Connector setup")}</h1>
            </div>
            <div class="pf-c-modal-box__body">
                <ak-codemirror
                    mode=${CodeMirrorMode.XML}
                    readonly
                    value="${ifDefined(this.config)}"
                ></ak-codemirror>
            </div>
            <footer class="pf-c-modal-box__footer pf-m-align-left">
                <ak-action-button
                    class="pf-m-secondary"
                    .apiRequest=${() => {
                        if (!navigator.clipboard) {
                            return Promise.resolve(
                                showMessage({
                                    level: MessageLevel.info,
                                    message: this.config || "",
                                }),
                            );
                        }
                        return navigator.clipboard.writeText(this.config || "");
                    }}
                >
                    ${msg("Copy")}
                </ak-action-button>
                &nbsp;
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
        "ak-endpoints-agent-connector-config": ConfigModal;
    }
}
