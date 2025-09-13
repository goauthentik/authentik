import "#flow/components/ak-flow-card";

import { isActiveElement } from "#elements/utils/focus";

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
import { createRef, ref, Ref } from "lit/directives/ref.js";

@customElement("ak-stage-authenticator-validate-code")
export class AuthenticatorValidateStageWebCode extends BaseDeviceStage<
    AuthenticatorValidationChallenge,
    AuthenticatorValidationChallengeResponseRequest
> {
    //#region Refs

    inputRef: Ref<HTMLInputElement> = createRef();
    //#endregion

    static styles: CSSResult[] = [
        ...super.styles,
        css`
            .icon-description {
                display: flex;
                align-items: center;
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

    //#region Lifecycle

    /**
     * Interval ID for the focus observer.
     *
     * @see {@linkcode observeInputFocus}
     */
    inputFocusIntervalID?: ReturnType<typeof setInterval>;

    /**
     * Periodically attempt to focus the input field until it is focused.
     *
     * This is some-what of a crude way to get autofocus, but in most cases
     * the `autofocus` attribute isn't enough, due to timing within shadow doms and such.
     */
    observeInputFocus(): void {
        this.inputFocusIntervalID = setInterval(() => {
            const input = this.inputRef.value;

            if (!input) return;

            if (isActiveElement(input, document.activeElement)) {
                console.debug(
                    "authentik/stages/authenticator-validate-code: cleared focus observer",
                );
                clearInterval(this.inputFocusIntervalID);
            }

            input.focus();
        }, 10);

        console.debug("authentik/stages/authenticator-validate-code: started focus observer");
    }

    connectedCallback() {
        super.connectedCallback();
        this.observeInputFocus();
    }

    disconnectedCallback() {
        if (this.inputFocusIntervalID) {
            clearInterval(this.inputFocusIntervalID);
        }

        super.disconnectedCallback();
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
                    ${ref(this.inputRef)}
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
