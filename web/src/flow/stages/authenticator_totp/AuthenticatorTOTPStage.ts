import "#elements/forms/FormElement";
import "#flow/FormStatic";
import "#flow/components/ak-flow-card";
import "webcomponent-qr-code";

import { MessageLevel } from "#common/messages";

import { showMessage } from "#elements/messages/MessageContainer";

import { BaseStage } from "#flow/stages/base";

import {
    AuthenticatorTOTPChallenge,
    AuthenticatorTOTPChallengeResponseRequest,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css, CSSResult, html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-stage-authenticator-totp")
export class AuthenticatorTOTPStage extends BaseStage<
    AuthenticatorTOTPChallenge,
    AuthenticatorTOTPChallengeResponseRequest
> {
    public static override styles: CSSResult[] = [
        PFBase,
        PFLogin,
        PFForm,
        PFFormControl,
        PFTitle,
        PFButton,
        css`
            .qr-container {
                display: flex;
                flex-direction: column;
                place-items: center;
            }
        `,
    ];

    public override render(): TemplateResult {
        return html`<ak-flow-card .challenge=${this.challenge}>
            <form class="pf-c-form" @submit=${this.submitForm}>
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
                <input type="hidden" name="otp_uri" value=${this.challenge.configUrl} />
                <ak-form-element>
                    <div class="qr-container">
                        <qr-code data="${this.challenge.configUrl}"></qr-code>
                        <button
                            type="button"
                            class="pf-c-button pf-m-secondary pf-m-progress pf-m-in-progress"
                            @click=${(e: Event) => {
                                e.preventDefault();
                                if (!this.challenge?.configUrl) return;
                                if (!navigator.clipboard) {
                                    showMessage({
                                        level: MessageLevel.info,
                                        message: this.challenge?.configUrl,
                                    });
                                    return;
                                }
                                navigator.clipboard
                                    .writeText(this.challenge?.configUrl)
                                    .then(() => {
                                        showMessage({
                                            level: MessageLevel.success,
                                            message: msg("Successfully copied TOTP Config."),
                                        });
                                    });
                            }}
                        >
                            <span class="pf-c-button__progress"><i class="fas fa-copy"></i></span>
                            ${msg("Copy")}
                        </button>
                    </div>
                </ak-form-element>
                <p>
                    ${msg(
                        "Please scan the QR code above using the Microsoft Authenticator, Google Authenticator, or other authenticator apps on your device, and enter the code the device displays below to finish setting up the MFA device.",
                    )}
                </p>
                <ak-form-element
                    label="${msg("Code")}"
                    required
                    class="pf-c-form__group"
                    .errors=${(this.challenge?.responseErrors || {}).code}
                >
                    <!-- @ts-ignore -->
                    <input
                        type="text"
                        name="code"
                        inputmode="numeric"
                        pattern="[0-9]*"
                        placeholder="${msg("Please enter your TOTP Code")}"
                        autofocus=""
                        autocomplete="one-time-code"
                        class="pf-c-form-control pf-m-monospace"
                        spellcheck="false"
                        required
                    />
                </ak-form-element>

                <div class="pf-c-form__group pf-m-action">
                    <button type="submit" class="pf-c-button pf-m-primary pf-m-block">
                        ${msg("Continue")}
                    </button>
                </div>
            </form>
        </ak-flow-card>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-authenticator-totp": AuthenticatorTOTPStage;
    }
}
