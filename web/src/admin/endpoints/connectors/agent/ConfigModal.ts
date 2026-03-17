import "#elements/CodeMirror";
import "#elements/buttons/ActionButton/index";
import "#elements/Expand";

import { DEFAULT_CONFIG } from "#common/api/config";
import { downloadFile } from "#common/download";
import { parseAPIResponseError, pluckErrorDetail } from "#common/errors/network";
import { MessageLevel } from "#common/messages";

import { ModalButton } from "#elements/buttons/ModalButton";
import { showMessage } from "#elements/messages/MessageContainer";

import {
    EndpointsAgentsConnectorsMdmConfigCreateRequest,
    EndpointsApi,
    MDMConfigResponse,
} from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-endpoints-agent-connector-config")
export class ConfigModal extends ModalButton {
    @property({ attribute: false })
    request?: EndpointsAgentsConnectorsMdmConfigCreateRequest;

    @state()
    config?: MDMConfigResponse;

    #downloadConnectorConfig = async () => {
        if (!this.config) {
            return;
        }

        downloadFile({
            content: this.config.config,
            filename: this.config.filename,
            type: this.config.mimeType,
        });

        showMessage({
            level: MessageLevel.info,
            message: msg(str`Successfully downloaded ${this.config.filename}!`),
        });

        this.close();
    };

    connectedCallback(): void {
        super.connectedCallback();
        this.addEventListener("ak-modal-show", () => {
            if (!this.request) return;
            new EndpointsApi(DEFAULT_CONFIG)
                .endpointsAgentsConnectorsMdmConfigCreate(this.request)
                .then((e) => {
                    this.config = e;
                })
                .catch(async (error) => {
                    const parsedError = await parseAPIResponseError(error);

                    showMessage({
                        level: MessageLevel.error,
                        message: pluckErrorDetail(parsedError),
                    });
                });
        });
    }

    renderModalInner() {
        return html`<section class="pf-c-modal-box__header pf-c-page__main-section pf-m-light">
                <div class="pf-c-content">
                    <h1 id="modal-title" class="pf-c-title pf-m-2xl">${msg("Connector setup")}</h1>
                </div>
            </section>
            <div class="pf-c-modal-box__body">
                <ak-expand
                    text-closed=${msg("Show MDM configuration")}
                    text-open=${msg("Hide MDM configuration")}
                >
                    <ak-codemirror
                        mode="xml"
                        readonly
                        value="${ifDefined(this.config?.config)}"
                    ></ak-codemirror>
                </ak-expand>
            </div>
            <footer class="pf-c-modal-box__footer pf-m-align-left">
                <ak-action-button class="pf-m-primary" .apiRequest=${this.#downloadConnectorConfig}>
                    ${msg("Download")}
                </ak-action-button>
                &nbsp;
                <ak-action-button
                    class="pf-m-secondary"
                    .apiRequest=${() => {
                        if (!navigator.clipboard) {
                            return Promise.resolve(
                                showMessage({
                                    level: MessageLevel.info,
                                    message: this.config?.config || "",
                                }),
                            );
                        }
                        return navigator.clipboard.writeText(this.config?.config || "");
                    }}
                >
                    ${msg("Copy")}
                </ak-action-button>
                &nbsp;
                <button
                    class="pf-c-button pf-m-secondary"
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
