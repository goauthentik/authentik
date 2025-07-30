import "#flow/components/ak-flow-card";

import { AKFormErrors } from "#components/ak-field-errors";
import { AKLabel } from "#components/ak-label";

import { BaseDeviceStage } from "#flow/stages/authenticator_validate/base";
import { PasswordManagerPrefill } from "#flow/stages/identification/IdentificationStage";

import {
    AuthenticatorValidationChallenge,
    AuthenticatorValidationChallengeResponseRequest,
    DeviceClassesEnum,
} from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { css, CSSResult, html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-stage-authenticator-validate-code")
export class AuthenticatorValidateStageWebCode extends BaseDeviceStage<
    AuthenticatorValidationChallenge,
    AuthenticatorValidationChallengeResponseRequest
> {
    static styles: CSSResult[] = [
        ...super.styles,
        css`
            .icon-description {
                display: flex;
            }
            .icon-description i {
                font-size: 2em;
                padding: 0.25em;
                padding-right: 0.5em;
            }
        `,
    ];

    deviceMessage(): string {
        switch (this.deviceChallenge?.deviceClass) {
            case DeviceClassesEnum.Email: {
                const email = this.deviceChallenge.challenge?.email;
                return msg(str`A code has been sent to you via email${email ? ` ${email}` : ""}`);
            }
            case DeviceClassesEnum.Sms:
                return msg("A code has been sent to you via SMS.");
            case DeviceClassesEnum.Totp:
                return msg(
                    "Open your two-factor authenticator app to view your authentication code.",
                );
            case DeviceClassesEnum.Static:
                return msg("Enter a one-time recovery code for this user.");
        }

        return msg("Enter the code from your authenticator device.");
    }

    deviceIcon(): string {
        switch (this.deviceChallenge?.deviceClass) {
            case DeviceClassesEnum.Email:
                return "fa-envelope";
            case DeviceClassesEnum.Sms:
                return "fa-mobile-alt";
            case DeviceClassesEnum.Totp:
                return "fa-clock";
            case DeviceClassesEnum.Static:
                return "fa-key";
        }

        return "fa-mobile-alt";
    }

    render(): TemplateResult {
        return html`<form class="pf-c-form" @submit=${this.submitForm}>
            ${this.renderUserInfo()}
            <div class="icon-description">
                <i class="fa ${this.deviceIcon()}" aria-hidden="true"></i>
                <p>${this.deviceMessage()}</p>
            </div>
            <div class="pf-c-form__group">
                ${AKLabel(
                    { required: true, htmlFor: "validation-code-input" },
                    this.deviceChallenge?.deviceClass === DeviceClassesEnum.Static
                        ? msg("Static token")
                        : msg("Authentication code"),
                )}
                <input
                    id="validation-code-input"
                    type="text"
                    name="code"
                    inputmode="${this.deviceChallenge?.deviceClass === DeviceClassesEnum.Static
                        ? "text"
                        : "numeric"}"
                    pattern="${this.deviceChallenge?.deviceClass === DeviceClassesEnum.Static
                        ? "[0-9a-zA-Z]*"
                        : "[0-9]*"}"
                    placeholder="${msg("Please enter your code")}"
                    autofocus=""
                    autocomplete="one-time-code"
                    class="pf-c-form-control"
                    value="${PasswordManagerPrefill.totp || ""}"
                    required
                />
                ${AKFormErrors({ errors: this.challenge.responseErrors?.code })}
            </div>

            <div class="pf-c-form__group pf-m-action">
                <button type="submit" class="pf-c-button pf-m-primary pf-m-block">
                    ${msg("Continue")}
                </button>
                ${this.renderReturnToDevicePicker()}
            </div>
        </form>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-authenticator-validate-code": AuthenticatorValidateStageWebCode;
    }
}
