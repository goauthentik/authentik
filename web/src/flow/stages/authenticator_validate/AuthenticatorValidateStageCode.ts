import "#flow/components/ak-flow-card";

import { formatDeviceChallengeMessage } from "#common/labels";

import { AKFormErrors } from "#components/ak-field-errors";
import { AKLabel } from "#components/ak-label";

import { BaseDeviceStage } from "#flow/stages/authenticator_validate/base";
import { PasswordManagerPrefill } from "#flow/stages/identification/IdentificationStage";

import {
    AuthenticatorValidationChallenge,
    AuthenticatorValidationChallengeResponseRequest,
    DeviceClassesEnum,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, LitElement, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-stage-authenticator-validate-code")
export class AuthenticatorValidateStageWebCode extends BaseDeviceStage<
    AuthenticatorValidationChallenge,
    AuthenticatorValidationChallengeResponseRequest
> {
    static shadowRootOptions = { ...LitElement.shadowRootOptions, delegatesFocus: true };

    render(): TemplateResult {
        const staticDevice = this.deviceChallenge?.deviceClass === DeviceClassesEnum.Static;

        return html`<form class="pf-c-form" @submit=${this.submitForm}>
            ${this.renderUserInfo()}
            <fieldset class="pf-c-form__group">
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

                ${AKFormErrors({ errors: this.challenge.responseErrors?.code })}
            </fieldset>

            <fieldset class="pf-c-form__group pf-m-action">
                <legend class="sr-only">${msg("Form actions")}</legend>
                <button name="continue" type="submit" class="pf-c-button pf-m-primary pf-m-block">
                    ${msg("Continue")}
                </button>
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
