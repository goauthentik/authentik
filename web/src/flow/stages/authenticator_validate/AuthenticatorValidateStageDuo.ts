import "@goauthentik/elements/EmptyState";
import "@goauthentik/elements/forms/FormElement";
import "@goauthentik/flow/FormStatic";
import { AuthenticatorValidateStage } from "@goauthentik/flow/stages/authenticator_validate/AuthenticatorValidateStage";
import { BaseStage } from "@goauthentik/flow/stages/base";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import {
    AuthenticatorValidationChallenge,
    AuthenticatorValidationChallengeResponseRequest,
    DeviceChallenge,
} from "@goauthentik/api";

@customElement("ak-stage-authenticator-validate-duo")
export class AuthenticatorValidateStageWebDuo extends BaseStage<
    AuthenticatorValidationChallenge,
    AuthenticatorValidationChallengeResponseRequest
> {
    @property({ attribute: false })
    deviceChallenge?: DeviceChallenge;

    @property({ type: Boolean })
    showBackButton = false;

    static get styles(): CSSResult[] {
        return [PFBase, PFLogin, PFForm, PFFormControl, PFTitle, PFButton];
    }

    firstUpdated(): void {
        this.host?.submit({
            duo: this.deviceChallenge?.deviceUid,
        });
    }

    render(): TemplateResult {
        if (!this.challenge) {
            return html`<ak-empty-state ?loading="${true}" header=${msg("Loading")}>
            </ak-empty-state>`;
        }
        const errors = this.challenge.responseErrors?.duo || [];
        return html`<div class="pf-c-login__main-body">
                <form
                    class="pf-c-form"
                    @submit=${(e: Event) => {
                        this.submitForm(e);
                    }}
                >
                    <ak-form-static
                        class="pf-c-form__group"
                        userAvatar="${this.challenge.pendingUserAvatar}"
                        user=${this.challenge.pendingUser}
                    >
                        <div slot="link">
                            <a href="${ifDefined(this.challenge.flowInfo?.cancelUrl)}"
                                >${msg("Not you?")}</a
                            >
                        </div>
                    </ak-form-static>

                    ${errors.length > 0
                        ? errors.map((err) => {
                              if (err.code === "denied") {
                                  return html` <ak-stage-access-denied-icon
                                      errorMessage=${err.string}
                                  >
                                  </ak-stage-access-denied-icon>`;
                              }
                              return html`<p>${err.string}</p>`;
                          })
                        : html`${msg("Sending Duo push notification")}`}
                </form>
            </div>
            <footer class="pf-c-login__main-footer">
                <ul class="pf-c-login__main-footer-links">
                    ${this.showBackButton
                        ? html`<li class="pf-c-login__main-footer-links-item">
                              <button
                                  class="pf-c-button pf-m-secondary pf-m-block"
                                  @click=${() => {
                                      if (!this.host) return;
                                      (
                                          this.host as AuthenticatorValidateStage
                                      ).selectedDeviceChallenge = undefined;
                                  }}
                              >
                                  ${msg("Return to device picker")}
                              </button>
                          </li>`
                        : html``}
                </ul>
            </footer>`;
    }
}
