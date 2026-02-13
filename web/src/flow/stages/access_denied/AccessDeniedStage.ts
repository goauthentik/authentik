import "#flow/FormStatic";
import "#flow/components/ak-flow-card";

import { FlowUserDetails } from "#flow/FormStatic";
import { BaseStage } from "#flow/stages/base";

import { AccessDeniedChallenge, FlowChallengeResponseRequest } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";

@customElement("ak-stage-access-denied")
export class AccessDeniedStage extends BaseStage<
    AccessDeniedChallenge,
    FlowChallengeResponseRequest
> {
    static styles: CSSResult[] = [PFLogin, PFForm, PFTitle, PFFormControl, PFButton];

    render(): TemplateResult {
        return html`<ak-flow-card .challenge=${this.challenge}>
            <form class="pf-c-form">
                ${FlowUserDetails({ challenge: this.challenge })}
                <ak-empty-state icon="fa-times"
                    ><span>${msg("Request has been denied.")}</span>
                    ${this.challenge?.errorMessage
                        ? html`
                              <div slot="body">
                                  <p>${this.challenge?.errorMessage}</p>
                              </div>
                          `
                        : nothing}
                </ak-empty-state>
                ${this.challenge?.flowInfo?.cancelUrl
                    ? html`<fieldset class="pf-c-form__group pf-m-action">
                          <legend class="sr-only">${msg("Form actions")}</legend>
                          <a
                              class="pf-c-button pf-m-primary pf-m-block"
                              href=${this.challenge.flowInfo?.cancelUrl}
                          >
                              ${msg("Go back", {
                                  id: "flow.navigation.go-back",
                              })}
                          </a>
                      </fieldset>`
                    : nothing}
            </form>
        </ak-flow-card>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-access-denied": AccessDeniedStage;
    }
}
