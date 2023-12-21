import { docLink } from "@goauthentik/common/global";
import { ModalButton } from "@goauthentik/elements/buttons/ModalButton";
import "@goauthentik/elements/buttons/TokenCopyButton";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { Outpost, OutpostTypeEnum } from "@goauthentik/api";

@customElement("ak-outpost-deployment-modal")
export class OutpostDeploymentModal extends ModalButton {
    @property({ attribute: false })
    outpost?: Outpost;

    renderModalInner(): TemplateResult {
        return html`<div class="pf-c-modal-box__header">
                <h1 class="pf-c-title pf-m-2xl">${msg("Outpost Deployment Info")}</h1>
            </div>
            <div class="pf-c-modal-box__body">
                <p>
                    <a
                        target="_blank"
                        href="${docLink("/docs/outposts?utm_source=authentik#deploy")}"
                        >${msg("View deployment documentation")}</a
                    >
                </p>
                <form class="pf-c-form">
                    <div class="pf-c-form__group">
                        <label class="pf-c-form__label">
                            <span class="pf-c-form__label-text">AUTHENTIK_HOST</span>
                        </label>
                        <input
                            class="pf-c-form-control"
                            readonly
                            type="text"
                            value="${document.location.origin}"
                        />
                    </div>
                    <div class="pf-c-form__group">
                        <label class="pf-c-form__label">
                            <span class="pf-c-form__label-text">AUTHENTIK_TOKEN</span>
                        </label>
                        <div>
                            <ak-token-copy-button
                                class="pf-m-primary"
                                identifier="${ifDefined(this.outpost?.tokenIdentifier)}"
                            >
                                ${msg("Click to copy token")}
                            </ak-token-copy-button>
                        </div>
                    </div>
                    <h3>
                        ${msg(
                            "If your authentik Instance is using a self-signed certificate, set this value.",
                        )}
                    </h3>
                    <div class="pf-c-form__group">
                        <label class="pf-c-form__label">
                            <span class="pf-c-form__label-text">AUTHENTIK_INSECURE</span>
                        </label>
                        <input class="pf-c-form-control" readonly type="text" value="true" />
                    </div>
                    ${this.outpost?.type == OutpostTypeEnum.Proxy
                        ? html`
                              <h3>
                                  ${msg(
                                      "If your authentik_host setting does not match the URL you want to login with, add this setting.",
                                  )}
                              </h3>
                              <div class="pf-c-form__group">
                                  <label class="pf-c-form__label">
                                      <span class="pf-c-form__label-text"
                                          >AUTHENTIK_HOST_BROWSER</span
                                      >
                                  </label>
                                  <input
                                      class="pf-c-form-control"
                                      readonly
                                      type="text"
                                      value="${document.location.origin}"
                                  />
                              </div>
                          `
                        : html``}
                </form>
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
