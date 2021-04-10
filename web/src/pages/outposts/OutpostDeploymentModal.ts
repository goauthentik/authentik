import { Outpost } from "authentik-api";
import { CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import { t } from "@lingui/macro";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFModalBox from "@patternfly/patternfly/components/ModalBox/modal-box.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import AKGlobal from "../../authentik.css";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../elements/buttons/TokenCopyButton";

@customElement("ak-outpost-deployment-modal")
export class OutpostDeploymentModal extends LitElement {

    @property({attribute: false})
    outpost?: Outpost;

    static get styles(): CSSResult[] {
        return [PFBase, PFTitle, PFButton, PFModalBox, PFForm, PFFormControl, AKGlobal];
    }

    render(): TemplateResult {
        return html`<div class="pf-c-modal-box__header">
                <h1 class="pf-c-title pf-m-2xl">${t`Outpost Deployment Info`}</h1>
            </div>
            <div class="pf-c-modal-box__body">
                <p><a target="_blank" href="https://goauthentik.io/docs/outposts/outposts/#deploy">${t`View deployment documentation`}</a></p>
                <form class="pf-c-form">
                    <div class="pf-c-form__group">
                        <label class="pf-c-form__label" for="help-text-simple-form-name">
                            <span class="pf-c-form__label-text">AUTHENTIK_HOST</span>
                        </label>
                        <input class="pf-c-form-control" readonly type="text" value="${document.location.origin}" />
                    </div>
                    <div class="pf-c-form__group">
                        <label class="pf-c-form__label" for="help-text-simple-form-name">
                            <span class="pf-c-form__label-text">AUTHENTIK_TOKEN</span>
                        </label>
                        <div>
                            <ak-token-copy-button identifier="${ifDefined(this.outpost?.tokenIdentifier)}">
                                ${t`Click to copy token`}
                            </ak-token-copy-button>
                        </div>
                    </div>
                    <h3>${t`If your authentik Instance is using a self-signed certificate, set this value.`}</h3>
                    <div class="pf-c-form__group">
                        <label class="pf-c-form__label" for="help-text-simple-form-name">
                            <span class="pf-c-form__label-text">AUTHENTIK_INSECURE</span>
                        </label>
                        <input class="pf-c-form-control" readonly type="text" value="true" />
                    </div>
                </form>
            </div>
            <footer class="pf-c-modal-box__footer pf-m-align-left">
                <a class="pf-c-button pf-m-primary">${t`Close`}</a>
            </footer>`;
    }

}
