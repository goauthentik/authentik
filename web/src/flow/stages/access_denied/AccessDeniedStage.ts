import "#flow/FormStatic";
import "#flow/components/ak-flow-card";

import { BaseStage } from "#flow/stages/base";

import { AccessDeniedChallenge, FlowChallengeResponseRequest } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";

@customElement("ak-stage-access-denied")
export class AccessDeniedStage extends BaseStage<
    AccessDeniedChallenge,
    FlowChallengeResponseRequest
> {
    static styles: CSSResult[] = [PFLogin, PFForm, PFTitle, PFFormControl];

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
