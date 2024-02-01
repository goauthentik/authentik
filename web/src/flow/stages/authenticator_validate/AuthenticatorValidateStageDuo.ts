import { BaseDeviceStage } from "@goauthentik/app/flow/stages/authenticator_validate/base";
import "@goauthentik/elements/EmptyState";
import "@goauthentik/elements/forms/FormElement";
import "@goauthentik/flow/FormStatic";

import { msg } from "@lit/localize";
import { TemplateResult, html, nothing } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { DuoDeviceChallenge, DuoDeviceChallengeResponseRequest } from "@goauthentik/api";

@customElement("ak-stage-authenticator-validate-duo")
export class AuthenticatorValidateStageWebDuo extends BaseDeviceStage<
    DuoDeviceChallenge,
    DuoDeviceChallengeResponseRequest
> {
    firstUpdated(): void {
        this.submitDeviceChallenge(undefined, false);
    }

    render(): TemplateResult {
        if (!this.challenge) {
            return html`<ak-empty-state ?loading="${true}" header=${msg("Loading")}>
            </ak-empty-state>`;
        }
        const errors = this.challenge.responseErrors?.selected_challenge_uid || [];
        return html`<div class="pf-c-login__main-body">
            <form class="pf-c-form">
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
                              return html`<ak-stage-access-denied-icon
                                  errorTitle=${msg("Duo denied authentication")}
                                  errorMessage=${err.string}
                              >
                              </ak-stage-access-denied-icon>`;
                          }
                          return html`<p>${err.string}</p>`;
                      })
                    : html`<ak-empty-state
                          ?loading=${true}
                          header=${msg("Sending Duo push notification")}
                      >
                      </ak-empty-state>`}
                <div class="pf-c-form__group pf-m-action">
                    <button
                        class="pf-c-button pf-m-primary pf-m-block"
                        @click=${() => {
                            this.firstUpdated();
                        }}
                    >
                        ${msg("Retry authentication")}
                    </button>
                    ${this.showBackButton
                        ? html`<button
                              class="pf-c-button pf-m-secondary pf-m-block"
                              @click=${() => {
                                  this.returnToDevicePicker();
                              }}
                          >
                              ${msg("Return to device picker")}
                          </button>`
                        : nothing}
                </div>
            </form>
        </div>`;
    }
}
