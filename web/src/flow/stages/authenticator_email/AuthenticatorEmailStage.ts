import "#flow/FormStatic";
import "#flow/components/ak-flow-card";

import { SlottedTemplateResult } from "#elements/types";

import { AKFormErrors } from "#components/ak-field-errors";
import { AKLabel } from "#components/ak-label";

import { FlowUserDetails } from "#flow/FormStatic";
import { BaseStage } from "#flow/stages/base";
import { RESEND_COOLDOWN_SECONDS, startResendCooldown } from "#flow/stages/resend-cooldown";

import {
    AuthenticatorEmailChallenge,
    AuthenticatorEmailChallengeResponseRequest,
} from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement, state } from "lit/decorators.js";

import PFAlert from "@patternfly/patternfly/components/Alert/alert.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFInputGroup from "@patternfly/patternfly/components/InputGroup/input-group.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";

@customElement("ak-stage-authenticator-email")
export class AuthenticatorEmailStage extends BaseStage<
    AuthenticatorEmailChallenge,
    AuthenticatorEmailChallengeResponseRequest
> {
    static styles: CSSResult[] = [
        PFAlert,
        PFLogin,
        PFForm,
        PFFormControl,
        PFInputGroup,
        PFTitle,
        PFButton,
    ];

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
        // Submit with neither code nor email; the backend treats this as a resend request and
        // re-sends a fresh code to the same address. Only start the visible cooldown once the
        // submit resolves successfully, so a failed resend doesn't disable the button for nothing.
        this.host
            ?.submit(
                {
                    component: "ak-stage-authenticator-email",
                } as AuthenticatorEmailChallengeResponseRequest,
                { invisible: true },
            )
            ?.then((ok) => {
                if (ok) {
                    this.#beginCooldown();
                }
            })
            .catch(() => undefined);
    };

    protected override willUpdate(): void {
        // The OTP screen is only reached once a code has been mailed out, so start counting from
        // there rather than from the first click.
        if (!this.#cooldownStarted && this.challenge && !this.challenge.emailRequired) {
            this.#cooldownStarted = true;
            this.#beginCooldown();
        }
    }

    override disconnectedCallback(): void {
        this.#cancelCooldown?.();
        super.disconnectedCallback();
    }

    renderEmailInput(): TemplateResult {
        return html`<ak-flow-card .challenge=${this.challenge}>
            <form class="pf-c-form" @submit=${this.submitForm}>
                ${FlowUserDetails({ challenge: this.challenge })}

                <div class="pf-c-form__group">
                    ${AKLabel(
                        { required: true, htmlFor: "email-input" },
                        msg("Configure your email"),
                    )}
                    <input
                        id="email-input"
                        type="email"
                        name="email"
                        placeholder="${msg("Please enter your email address.")}"
                        autofocus
                        autocomplete="email"
                        class="pf-c-form-control"
                        required
                    />
                    ${AKFormErrors({ errors: this.challenge?.responseErrors?.email })}
                </div>
                ${this.renderNonFieldErrors()}
                <fieldset class="ak-c-fieldset pf-c-form__group pf-m-action">
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

    protected renderEmailOTPInput(): SlottedTemplateResult {
        if (!this.challenge) {
            return nothing;
        }

        const { email } = this.challenge;

        return html`<ak-flow-card .challenge=${this.challenge}>
            ${FlowUserDetails({ challenge: this.challenge })}

            <p>
                ${email
                    ? msg(
                          str`A verification token has been sent to your configured email address: ${email}`,
                          {
                              id: "stage.authenticator.email.sent-to-address",
                              desc: "Displayed when a verification token has been sent to the user's configured email address.",
                          },
                      )
                    : msg("A verification token has been sent to your email address.", {
                          id: "stage.authenticator.email.sent",
                          desc: "Displayed when a verification token has been sent to the user's email address.",
                      })}
            </p>
            <form class="pf-c-form" @submit=${this.submitForm}>
                <div class="pf-c-form__group">
                    ${AKLabel({ required: true, htmlFor: "code-input" }, msg("Code"))}
                    <input
                        id="code-input"
                        type="text"
                        name="code"
                        inputmode="numeric"
                        pattern="[0-9]*"
                        placeholder="${msg("Please enter the code you received via email")}"
                        autofocus
                        autocomplete="one-time-code"
                        class="pf-c-form-control pf-m-monospace"
                        required
                    />
                    ${AKFormErrors({ errors: this.challenge.responseErrors?.code })}
                </div>
                ${this.renderNonFieldErrors()}
                <div class="pf-c-form__helper-text">
                    ${this.resendCooldown > 0
                        ? msg(
                              str`Didn't get the code? It can take a moment and may land in your spam or junk folder. You can request a new code in ${this.resendCooldown} seconds.`,
                          )
                        : msg(
                              "Didn't get the code? It can take a moment and may land in your spam or junk folder. You can also resend it.",
                          )}
                </div>
                <fieldset class="ak-c-fieldset pf-c-form__group pf-m-action">
                    <legend class="sr-only">${msg("Form actions")}</legend>
                    <button
                        name="continue"
                        type="submit"
                        class="pf-c-button pf-m-primary pf-m-block"
                    >
                        ${msg("Continue")}
                    </button>
                    <button
                        name="resend"
                        type="button"
                        class="pf-c-button pf-m-secondary pf-m-block"
                        ?disabled=${this.resendCooldown > 0}
                        @click=${this.#resend}
                    >
                        ${this.resendCooldown > 0
                            ? msg(str`Resend code (${this.resendCooldown}s)`)
                            : msg("Resend code")}
                    </button>
                </fieldset>
            </form>
        </ak-flow-card>`;
    }

    protected render(): SlottedTemplateResult {
        if (this.challenge?.emailRequired) {
            return this.renderEmailInput();
        }
        return this.renderEmailOTPInput();
    }
}

export default AuthenticatorEmailStage;

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-authenticator-email": AuthenticatorEmailStage;
    }
}
