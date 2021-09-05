import { Outpost } from "@goauthentik/api";
import { customElement, html, property, TemplateResult } from "lit-element";
import { t } from "@lingui/macro";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../elements/buttons/TokenCopyButton";
import { ModalButton } from "../../elements/buttons/ModalButton";

@customElement("ak-outpost-deployment-modal")
export class OutpostDeploymentModal extends ModalButton {
    @property({ attribute: false })
    outpost?: Outpost;

    renderModalInner(): TemplateResult {
        return html`<div class="pf-c-modal-box__header">
                <h1 class="pf-c-title pf-m-2xl">${t`Outpost Deployment Info`}</h1>
            </div>
            <div class="pf-c-modal-box__body">
                <p>
                    <a target="_blank" href="https://goauthentik.io/docs/outposts/outposts/#deploy"
                        >${t`View deployment documentation`}</a
                    >
                </p>
                <form class="pf-c-form">
                    <div class="pf-c-form__group">
                        <label class="pf-c-form__label" for="help-text-simple-form-name">
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
                        <label class="pf-c-form__label" for="help-text-simple-form-name">
                            <span class="pf-c-form__label-text">AUTHENTIK_TOKEN</span>
                        </label>
                        <div>
                            <ak-token-copy-button
                                identifier="${ifDefined(this.outpost?.tokenIdentifier)}"
                            >
                                ${t`Click to copy token`}
                            </ak-token-copy-button>
                        </div>
                    </div>
                    <h3>
                        ${t`If your authentik Instance is using a self-signed certificate, set this value.`}
                    </h3>
                    <div class="pf-c-form__group">
                        <label class="pf-c-form__label" for="help-text-simple-form-name">
                            <span class="pf-c-form__label-text">AUTHENTIK_INSECURE</span>
                        </label>
                        <input class="pf-c-form-control" readonly type="text" value="true" />
                    </div>
                </form>
            </div>
            <footer class="pf-c-modal-box__footer pf-m-align-left">
                <button
                    class="pf-c-button pf-m-primary"
                    @click=${() => {
                        this.open = false;
                    }}
                >
                    ${t`Close`}
                </button>
            </footer>`;
    }
}
