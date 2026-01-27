import "#flow/FormStatic";
import "#flow/components/ak-flow-card";

import { SlottedTemplateResult } from "#elements/types";

import { AKFormErrors } from "#components/ak-field-errors";
import { AKLabel } from "#components/ak-label";

import { FlowUserDetails } from "#flow/FormStatic";
import { BaseStage } from "#flow/stages/base";

import {
    AuthenticatorEmailChallenge,
    AuthenticatorEmailChallengeResponseRequest,
} from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

import PFAlert from "@patternfly/patternfly/components/Alert/alert.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFInputGroup from "@patternfly/patternfly/components/InputGroup/input-group.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-stage-authenticator-email")
export class AuthenticatorEmailStage extends BaseStage<
    AuthenticatorEmailChallenge,
    AuthenticatorEmailChallengeResponseRequest
> {
    static styles: CSSResult[] = [
        PFBase,
        PFAlert,
        PFLogin,
        PFForm,
        PFFormControl,
        PFInputGroup,
        PFTitle,
        PFButton,
    ];

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

    protected render(): SlottedTemplateResult {
        if (this.challenge?.emailRequired) {
            return this.renderEmailInput();
        }
        return this.renderEmailOTPInput();
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-authenticator-email": AuthenticatorEmailStage;
    }
}
