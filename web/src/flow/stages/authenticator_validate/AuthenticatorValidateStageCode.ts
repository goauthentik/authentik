import "#flow/components/ak-flow-card";

import { formatDeviceChallengeMessage } from "#common/labels";

import { AKFormErrors } from "#components/ak-field-errors";
import { AKLabel } from "#components/ak-label";

import { BaseDeviceStage } from "#flow/stages/authenticator_validate/base";
import { PasswordManagerPrefill } from "#flow/stages/identification/IdentificationStage";
import { RESEND_COOLDOWN_SECONDS, startResendCooldown } from "#flow/stages/resend-cooldown";

import {
    AuthenticatorValidationChallenge,
    AuthenticatorValidationChallengeResponseRequest,
    DeviceClassesEnum,
} from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html, LitElement, nothing, TemplateResult } from "lit";
import { customElement, state } from "lit/decorators.js";

@customElement("ak-stage-authenticator-validate-code")
export class AuthenticatorValidateStageWebCode extends BaseDeviceStage<
    AuthenticatorValidationChallenge,
    AuthenticatorValidationChallengeResponseRequest
> {
    static shadowRootOptions = { ...LitElement.shadowRootOptions, delegatesFocus: true };

    @state()
    protected resendCooldown = 0;

    #cancelCooldown?: () => void;
    #cooldownStarted = false;

    #beginCooldown() {
        this.#cancelCooldown?.();
        this.#cancelCooldown = startResendCooldown(RESEND_COOLDOWN_SECONDS, (remaining) => {
            this.resendCooldown = remaining;
        });
    }

    #resend = () => {
        if (this.resendCooldown > 0) {
            return;
        }
        // Only start the visible cooldown once the resend request actually succeeds, so a failed
        // request does not leave the button disabled with no code on its way.
        this.host
            ?.resendSelectedChallenge?.()
            ?.then(() => this.#beginCooldown())
            .catch(() => undefined);
    };

    protected override willUpdate(): void {
        // Reaching this stage means a code was just mailed out, so the cooldown starts here
        // rather than on the first click.
        if (!this.#cooldownStarted && this.deviceChallenge?.deviceClass === DeviceClassesEnum.Email) {
            this.#cooldownStarted = true;
            this.#beginCooldown();
        }
    }

    override disconnectedCallback(): void {
        this.#cancelCooldown?.();
        super.disconnectedCallback();
    }

    render(): TemplateResult {
        const staticDevice = this.deviceChallenge?.deviceClass === DeviceClassesEnum.Static;
        const emailDevice = this.deviceChallenge?.deviceClass === DeviceClassesEnum.Email;

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
                    ${this.autofocusTarget.toRef()}
                    id="validation-code-input"
                    aria-describedby="validation-code-help"
                    type="text"
                    name="code"
                    inputmode=${staticDevice ? "text" : "numeric"}
                    pattern=${staticDevice ? "[0-9a-zA-Z]*" : "[0-9]*"}
                    placeholder=${msg("Type an authentication code...")}
                    autofocus
                    spellcheck="false"
                    autocomplete="one-time-code"
                    class="pf-c-form-control pf-m-monospace"
                    value="${PasswordManagerPrefill.totp || ""}"
                    required
                />
                <div class="pf-c-form__helper-text" id="validation-code-help">
                    ${formatDeviceChallengeMessage(this.deviceChallenge)}
                </div>
                ${emailDevice
                    ? html`<div class="pf-c-form__helper-text">
                          ${this.resendCooldown > 0
                              ? msg(
                                    str`Didn't get the code? It can take a moment and may land in your spam or junk folder. You can request a new code in ${this.resendCooldown} seconds.`,
                                )
                              : msg(
                                    "Didn't get the code? It can take a moment and may land in your spam or junk folder. You can also resend it.",
                                )}
                      </div>`
                    : nothing}

                ${AKFormErrors({ errors: this.challenge?.responseErrors?.code })}
            </fieldset>

            <fieldset class="ak-c-fieldset pf-c-form__group pf-m-action">
                <legend class="sr-only">${msg("Form actions")}</legend>
                <button name="continue" type="submit" class="pf-c-button pf-m-primary pf-m-block">
                    ${msg("Continue")}
                </button>
                ${emailDevice
                    ? html`<button
                          name="resend"
                          type="button"
                          class="pf-c-button pf-m-secondary pf-m-block"
                          ?disabled=${this.resendCooldown > 0}
                          @click=${this.#resend}
                      >
                          ${this.resendCooldown > 0
                              ? msg(str`Resend code (${this.resendCooldown}s)`)
                              : msg("Resend code")}
                      </button>`
                    : nothing}
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
