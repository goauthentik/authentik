import "@goauthentik/flow/FormStatic";
import "@goauthentik/flow/components/ak-flow-card.js";
import { BaseStage } from "@goauthentik/flow/stages/base";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html, nothing } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { AccessDeniedChallenge, FlowChallengeResponseRequest } from "@goauthentik/api";

@customElement("ak-stage-access-denied")
export class AccessDeniedStage extends BaseStage<
    AccessDeniedChallenge,
    FlowChallengeResponseRequest
> {
    static get styles(): CSSResult[] {
        return [PFBase, PFLogin, PFForm, PFTitle, PFFormControl];
    }

    render(): TemplateResult {
        return html`<ak-flow-card .challenge=${this.challenge}>
            <form class="pf-c-form">
                <ak-form-static
                    class="pf-c-form__group"
                    userAvatar="${this.challenge?.pendingUserAvatar}"
                    user=${this.challenge?.pendingUser}
                >
                    <div slot="link">
                        <a href="${ifDefined(this.challenge.flowInfo?.cancelUrl)}"
                            >${msg("Not you?")}</a
                        >
                    </div>
                </ak-form-static>
                <ak-empty-state icon="fa-times"
                    ><span>${msg("Request has been denied.")}</span>
                    ${this.challenge.errorMessage
                        ? html`
                              <div slot="body">
                                  <p>${this.challenge.errorMessage}</p>
                              </div>
                          `
                        : nothing}
                </ak-empty-state>
            </form>
        </ak-flow-card>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-access-denied": AccessDeniedStage;
    }
}
