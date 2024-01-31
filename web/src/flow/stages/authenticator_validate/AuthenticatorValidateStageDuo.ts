import { BaseDeviceStage } from "@goauthentik/app/flow/stages/authenticator_validate/base";
import "@goauthentik/elements/EmptyState";
import "@goauthentik/elements/forms/FormElement";
import "@goauthentik/flow/FormStatic";
import { AuthenticatorValidateStage } from "@goauthentik/flow/stages/authenticator_validate/AuthenticatorValidateStage";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { DuoDeviceChallengeRequest } from "@goauthentik/api";

@customElement("ak-stage-authenticator-validate-duo")
export class AuthenticatorValidateStageWebDuo extends BaseDeviceStage<
    DuoDeviceChallengeRequest,
    // Duo doesn't have a response challenge
    DuoDeviceChallengeRequest
> {
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
                        e.preventDefault();
                        this.submitDeviceChallenge();
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
