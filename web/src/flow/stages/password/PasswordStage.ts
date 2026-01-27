import "#flow/FormStatic";
import "#flow/components/ak-flow-card";
import "#flow/components/ak-flow-password-input";

import { ErrorProp } from "#components/ak-field-errors";

import { FlowUserDetails } from "#flow/FormStatic";
import { BaseStage } from "#flow/stages/base";
import { PasswordManagerPrefill } from "#flow/stages/identification/IdentificationStage";

import { PasswordChallenge, PasswordChallengeResponseRequest } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFInputGroup from "@patternfly/patternfly/components/InputGroup/input-group.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-stage-password")
export class PasswordStage extends BaseStage<PasswordChallenge, PasswordChallengeResponseRequest> {
    static styles: CSSResult[] = [
        PFBase,
        PFLogin,
        PFInputGroup,
        PFForm,
        PFFormControl,
        PFButton,
        PFTitle,
    ];

    #errors(field: string): ErrorProp[] | undefined {
        const errors = this.challenge?.responseErrors?.[field];

        return errors;
    }

    render(): TemplateResult {
        return html`<ak-flow-card .challenge=${this.challenge}>
            <form class="pf-c-form" @submit=${this.submitForm}>
                ${FlowUserDetails({ challenge: this.challenge })}

                <input
                    name="username"
                    type="text"
                    autocomplete="username"
                    hidden
                    readonly
                    value="${this.challenge?.pendingUser ?? ""}"
                />
                <ak-flow-input-password
                    label=${msg("Password")}
                    required
                    grab-focus
                    class="pf-c-form__group"
                    .errors=${this.#errors("password")}
                    ?allow-show-password=${!!this.challenge?.allowShowPassword}
                    prefill=${PasswordManagerPrefill.password ?? ""}
                ></ak-flow-input-password>
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
            ${this.challenge?.recoveryUrl
                ? html`<fieldset
                      slot="footer-band"
                      part="additional-actions"
                      class="pf-c-login__main-footer-band"
                  >
                      <legend class="sr-only">${msg("Additional actions")}</legend>
                      <div class="pf-c-login__main-footer-band-item">
                          <a name="forgot-password" href="${this.challenge.recoveryUrl}"
                              >${msg("Forgot password?")}</a
                          >
                      </div>
                  </fieldset>`
                : null}
        </ak-flow-card>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-password": PasswordStage;
    }
}
