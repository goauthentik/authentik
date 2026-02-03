import "#flow/FormStatic";
import "#flow/components/ak-flow-card";
import "webcomponent-qr-code";
import "#types/qr-code";

import { MessageLevel } from "#common/messages";

import { showMessage } from "#elements/messages/MessageContainer";
import { SlottedTemplateResult } from "#elements/types";

import { AKFormErrors } from "#components/ak-field-errors";
import { AKLabel } from "#components/ak-label";

import { FlowUserDetails } from "#flow/FormStatic";
import { BaseStage } from "#flow/stages/base";

import {
    AuthenticatorTOTPChallenge,
    AuthenticatorTOTPChallengeResponseRequest,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css, CSSResult, html, nothing } from "lit";
import { customElement } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFInputGroup from "@patternfly/patternfly/components/InputGroup/input-group.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";

/**
 * Copies a value to the clipboard and notifies the user about the result.
 */
function copyToClipboard(value: string, successMessage: string): Promise<void> {
    if (!navigator.clipboard) {
        showMessage({
            level: MessageLevel.info,
            message: value,
        });

        return Promise.resolve();
    }

    return navigator.clipboard.writeText(value).then(() => {
        showMessage(
            {
                level: MessageLevel.success,
                message: successMessage,
            },
            true,
        );
    });
}

@customElement("ak-stage-authenticator-totp")
export class AuthenticatorTOTPStage extends BaseStage<
    AuthenticatorTOTPChallenge,
    AuthenticatorTOTPChallengeResponseRequest
> {
    static styles: CSSResult[] = [
        PFLogin,
        PFForm,
        PFFormControl,
        PFInputGroup,
        PFTitle,
        PFButton,
        css`
            .qr-container {
                display: flex;
                flex-direction: column;
                place-items: center;
            }
            .qr-buttons {
                display: flex;
                gap: 0.5rem;
                flex-wrap: wrap;
                justify-content: center;
                margin-top: 1rem;
            }
        `,
    ];

    #copyTOTPToClipboard = (event: Event): void => {
        event.preventDefault();

        const configUrl = this.challenge?.configUrl;
        if (!configUrl) return;

        copyToClipboard(configUrl, msg("Successfully copied TOTP Config."));
    };

    #copySecretToClipboard = (event: Event): void => {
        event.preventDefault();

        const secret = this.#secretParam;
        if (!secret) return;

        copyToClipboard(secret, msg("Successfully copied TOTP Secret."));
    };

    get #secretParam(): string | null {
        const configUrl = this.challenge?.configUrl;
        if (!configUrl || !URL.canParse(configUrl)) return null;

        const url = new URL(configUrl);

        return url.searchParams.get("secret");
    }

    protected render(): SlottedTemplateResult {
        if (!this.challenge) {
            return nothing;
        }

        return html`<ak-flow-card .challenge=${this.challenge}>
            <form class="pf-c-form" @submit=${this.submitForm}>
                ${FlowUserDetails({ challenge: this.challenge })}

                <input type="hidden" name="otp_uri" value=${this.challenge.configUrl} />

                <div class="pf-c-form__group">
                    <div class="qr-container">
                        <qr-code
                            role="img"
                            aria-label=${msg("QR-Code to setup a time-based one-time password")}
                            format="svg"
                            data="${this.challenge.configUrl}"
                        ></qr-code>
                        <div class="qr-buttons">
                            <button
                                type="button"
                                class="pf-c-button pf-m-secondary pf-m-progress pf-m-in-progress"
                                aria-label=${msg("Copy time-based one-time password configuration")}
                                @click=${this.#copyTOTPToClipboard}
                            >
                                <span class="pf-c-button__progress"
                                    ><i class="fas fa-copy" aria-hidden="true"></i
                                ></span>
                                ${msg("Copy TOTP Config")}
                            </button>
                            <button
                                type="button"
                                class="pf-c-button pf-m-secondary pf-m-progress pf-m-in-progress"
                                aria-label=${msg("Copy time-based one-time password secret")}
                                @click=${this.#copySecretToClipboard}
                            >
                                <span class="pf-c-button__progress"
                                    ><i class="fas fa-key" aria-hidden="true"></i
                                ></span>
                                ${msg("Copy Secret")}
                            </button>
                        </div>
                    </div>
                </div>
                <p>
                    ${msg(
                        "Please scan the QR code above using the Microsoft Authenticator, Google Authenticator, or other authenticator apps on your device, and enter the code the device displays below to finish setting up the MFA device.",
                    )}
                </p>
                <div class="pf-c-form__group">
                    ${AKLabel(
                        {
                            "required": true,
                            "htmlFor": "totp-code-input",
                            "aria-label": msg("Time-based one-time password"),
                        },
                        msg("TOTP Code"),
                    )}
                    <input
                        id="totp-code-input"
                        type="text"
                        name="code"
                        inputmode="numeric"
                        pattern="[0-9]*"
                        placeholder="${msg("Type your TOTP code...")}"
                        aria-placeholder=${msg("Type your time-based one-time password code.")}
                        autocomplete="one-time-code"
                        class="pf-c-form-control pf-m-monospace"
                        spellcheck="false"
                        required
                    />
                    ${AKFormErrors({ errors: this.challenge.responseErrors?.code })}
                </div>

                <fieldset class="pf-c-form__group pf-m-action">
                    <legend class="sr-only">${msg("Form actions")}</legend>
                    <button
                        name="continue"
                        type="submit"
                        class="pf-c-button pf-m-primary pf-m-block"
                    >
                        ${msg("Continue")}
                    </button>
                </fieldset>
            </form>
        </ak-flow-card>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-authenticator-totp": AuthenticatorTOTPStage;
    }
}
