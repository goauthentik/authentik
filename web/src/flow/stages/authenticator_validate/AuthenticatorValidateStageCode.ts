import "#flow/components/ak-flow-card";
import { formatDeviceChallengeMessage } from "#common/labels";

import { AKFormErrors } from "#components/ak-field-errors";
import { AKLabel } from "#components/ak-label";

import { BaseDeviceStage } from "#flow/stages/authenticator_validate/base";
import { PasswordManagerPrefill } from "#flow/stages/identification/IdentificationStage";
import { ResendFeedback } from "#flow/stages/resend-feedback";

import {
    AuthenticatorValidationChallenge,
    AuthenticatorValidationChallengeResponseRequest,
    DeviceClassesEnum,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, LitElement, nothing, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-stage-authenticator-validate-code")
export class AuthenticatorValidateStageWebCode extends BaseDeviceStage<
    AuthenticatorValidationChallenge,
    AuthenticatorValidationChallengeResponseRequest
> {
    static shadowRootOptions = {
        ...LitElement.shadowRootOptions,
        delegatesFocus: true,
    };

    #resendFeedback = new ResendFeedback(this);

    #resend = () =>
        this.#resendFeedback.run(
            () => this.host.resendSelectedChallenge?.() ?? Promise.resolve(false),
        );

    render(): TemplateResult {
        const staticDevice = this.deviceChallenge?.deviceClass === DeviceClassesEnum.Static;
        const emailDevice = this.deviceChallenge?.deviceClass === DeviceClassesEnum.Email;

        const emailSendLimited =
            emailDevice &&
            this.challenge?.responseErrors?.selected_challenge?.some(
                (error) => error.code === "throttled",
            );

        return html`<form class="pf-c-form" @submit=${this.submitForm}>
            ${this.renderUserInfo()}
            <fieldset class="ak-c-fieldset pf-c-form__group">
                <legend class="sr-only">${msg("Authentication code")}</legend>
                ${AKLabel(
                    {
                        required: true,
                        htmlFor: "validation-code-input",
                    },
                    staticDevice ? msg("Static token") : msg("Authentication code"),
                )}
                <input
                    ${this.primaryFocusTarget.toRef()}
                    id="validation-code-input"
                    aria-describedby="validation-code-help"
                    type="text"
                    name="code"
                    inputmode=${staticDevice ? "text" : "numeric"}
                    pattern=${staticDevice ? "[0-9a-zA-Z\\-\\s]*" : "[0-9]*"}
                    placeholder=${msg("Type an authentication code...")}
                    autofocus
                    spellcheck="false"
                    autocomplete="one-time-code"
                    class="pf-c-form-control pf-m-monospace"
                    value="${PasswordManagerPrefill.totp || ""}"
                    required
                />
                <div class="pf-c-form__helper-text" id="validation-code-help">
                    ${emailSendLimited ? nothing : formatDeviceChallengeMessage(this.deviceChallenge)}
                </div>
                ${
                    emailDevice
                        ? html`<div class="pf-c-form__helper-text">
                              ${msg(
                                  "Didn't get the code? It can take a moment and may land in your spam or junk folder. You can also resend it.",
                                  { id: "email-otp.resend.description" },
                              )}
                          </div>`
                        : nothing
                }
                ${AKFormErrors({
                    errors: this.challenge?.responseErrors?.code,
                })}
                ${AKFormErrors({
                    errors: this.challenge?.responseErrors?.selected_challenge,
                })}
            </fieldset>

            <fieldset class="ak-c-fieldset pf-c-form__group pf-m-action">
                <legend class="sr-only">${msg("Form actions")}</legend>
                <button name="continue" type="submit" class="pf-c-button pf-m-primary pf-m-block">
                    ${msg("Continue")}
                </button>
                ${
                    emailDevice
                        ? html`<button
                                  name="resend"
                                  type="button"
                                  class="pf-c-button pf-m-secondary pf-m-block"
                                  ?disabled=${this.#resendFeedback.state !== "idle"}
                                  aria-busy=${this.#resendFeedback.state === "sending"}
                                  @click=${this.#resend}
                              >
                                  ${this.#resendFeedback.label}
                              </button>
                              <span class="sr-only" role="status" aria-live="polite">
                                  ${this.#resendFeedback.state === "idle" ? nothing : this.#resendFeedback.label}
                              </span>`
                        : nothing
                }
                ${this.renderReturnToDevicePicker()}
            </fieldset>
        </form>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-authenticator-validate-code": AuthenticatorValidateStageWebCode;
    }
}
