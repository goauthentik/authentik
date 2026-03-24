import "#flow/FormStatic";
import "#flow/components/ak-flow-card";

import { SlottedTemplateResult } from "#elements/types";

import { AKFormErrors } from "#components/ak-field-errors";
import { AKLabel } from "#components/ak-label";

import { FlowUserDetails } from "#flow/FormStatic";
import { BaseStage } from "#flow/stages/base";

import {
    AuthenticatorSMSChallenge,
    AuthenticatorSMSChallengeResponseRequest,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing } from "lit";
import { customElement } from "lit/decorators.js";

import PFAlert from "@patternfly/patternfly/components/Alert/alert.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFInputGroup from "@patternfly/patternfly/components/InputGroup/input-group.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";

@customElement("ak-stage-authenticator-sms")
export class AuthenticatorSMSStage extends BaseStage<
    AuthenticatorSMSChallenge,
    AuthenticatorSMSChallengeResponseRequest
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

    protected renderPhoneNumber(): SlottedTemplateResult {
        if (!this.challenge) {
            return nothing;
        }
        return html`<ak-flow-card .challenge=${this.challenge}>
            <form class="pf-c-form" @submit=${this.submitForm}>
                ${FlowUserDetails({ challenge: this.challenge })}

                <div class="pf-c-form__group">
                    ${AKLabel(
                        { required: true, htmlFor: "phone-number-input" },
                        msg("Phone number"),
                    )}

                    <input
                        type="tel"
                        name="phoneNumber"
                        placeholder="${msg("Please enter your Phone number.")}"
                        autofocus
                        autocomplete="tel"
                        class="pf-c-form-control"
                        required
                    />
                    ${AKFormErrors({ errors: this.challenge.responseErrors?.phone_number })}
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

    protected renderCode(): SlottedTemplateResult {
        if (!this.challenge) {
            return nothing;
        }

        return html`<ak-flow-card .challenge=${this.challenge}>
            <form class="pf-c-form" @submit=${this.submitForm}>
                ${FlowUserDetails({ challenge: this.challenge })}
                <div class="pf-c-form__group">
                    ${AKLabel({ required: true, htmlFor: "sms-code-input" }, msg("Code"))}
                    <input
                        id="sms-code-input"
                        type="text"
                        name="code"
                        inputmode="numeric"
                        pattern="[0-9]*"
                        placeholder="${msg("Please enter the code you received via SMS")}"
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

    render(): SlottedTemplateResult {
        if (this.challenge?.phoneNumberRequired) {
            return this.renderPhoneNumber();
        }

        return this.renderCode();
    }
}

export default AuthenticatorSMSStage;

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-authenticator-sms": AuthenticatorSMSStage;
    }
}
