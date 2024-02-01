import { BaseDeviceStage } from "@goauthentik/app/flow/stages/authenticator_validate/base";
import "@goauthentik/elements/EmptyState";
import "@goauthentik/elements/forms/FormElement";
import "@goauthentik/flow/FormStatic";
import { PasswordManagerPrefill } from "@goauthentik/flow/stages/identification/IdentificationStage";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { TOTPDeviceChallenge, TOTPDeviceChallengeResponseRequest } from "@goauthentik/api";

@customElement("ak-stage-authenticator-validate-code")
export class AuthenticatorValidateStageWebCode extends BaseDeviceStage<
    // Technically this stage also supports `static` and `sms` devices
    // however they all have the same serializer
    TOTPDeviceChallenge,
    TOTPDeviceChallengeResponseRequest
> {
    static get styles(): CSSResult[] {
        return super.styles.concat(css`
            .icon-description {
                display: flex;
            }
            .icon-description i {
                font-size: 2em;
                padding: 0.25em;
                padding-right: 0.5em;
            }
        `);
    }

    render(): TemplateResult {
        if (!this.challenge) {
            return html`<ak-empty-state ?loading="${true}" header=${msg("Loading")}>
            </ak-empty-state>`;
        }
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
                    <div class="icon-description">
                        <i
                            class="fa ${this.deviceChallenge?.component ==
                            "ak-stage-authenticator-validate-device-sms"
                                ? "fa-key"
                                : "fa-mobile-alt"}"
                            aria-hidden="true"
                        ></i>
                        ${this.deviceChallenge?.component ==
                        "ak-stage-authenticator-validate-device-sms"
                            ? html`<p>${msg("A code has been sent to you via SMS.")}</p>`
                            : html`<p>
                                  ${msg(
                                      "Open your two-factor authenticator app to view your authentication code.",
                                  )}
                              </p>`}
                    </div>
                    <ak-form-element
                        label="${this.deviceChallenge?.component ===
                        "ak-stage-authenticator-validate-device-static"
                            ? msg("Static token")
                            : msg("Authentication code")}"
                        ?required="${true}"
                        class="pf-c-form__group"
                        .errors=${(this.challenge?.responseErrors || {})["code"]}
                    >
                        <!-- @ts-ignore -->
                        <input
                            type="text"
                            name="code"
                            inputmode="${this.deviceChallenge?.component ===
                            "ak-stage-authenticator-validate-device-static"
                                ? "text"
                                : "numeric"}"
                            pattern="${this.deviceChallenge?.component ===
                            "ak-stage-authenticator-validate-device-static"
                                ? "[0-9a-zA-Z]*"
                                : "[0-9]*"}"
                            placeholder="${msg("Please enter your code")}"
                            autofocus=""
                            autocomplete="one-time-code"
                            class="pf-c-form-control"
                            value="${PasswordManagerPrefill.totp || ""}"
                            required
                        />
                    </ak-form-element>

                    <div class="pf-c-form__group pf-m-action">
                        <button type="submit" class="pf-c-button pf-m-primary pf-m-block">
                            ${msg("Continue")}
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
                            : html``}
                    </div>
                </form>
            </div>
            <footer class="pf-c-login__main-footer">
                <ul class="pf-c-login__main-footer-links"></ul>
            </footer>`;
    }
}
