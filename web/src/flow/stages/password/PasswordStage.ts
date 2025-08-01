import "#flow/FormStatic";
import "#flow/components/ak-flow-card";
import "#flow/components/ak-flow-password-input";

import { BaseStage } from "#flow/stages/base";
import { PasswordManagerPrefill } from "#flow/stages/identification/IdentificationStage";

import { PasswordChallenge, PasswordChallengeResponseRequest } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

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

    hasError(field: string): boolean {
        const errors = (this.challenge?.responseErrors || {})[field];
        return (errors || []).length > 0;
    }

    render(): TemplateResult {
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
                <input
                    name="username"
                    type="text"
                    autocomplete="username"
                    hidden
                    readonly
                    value="${this.challenge.pendingUser}"
                />
                <ak-flow-input-password
                    label=${msg("Password")}
                    required
                    grab-focus
                    class="pf-c-form__group"
                    .errors=${(this.challenge?.responseErrors || {}).password}
                    ?allow-show-password=${this.challenge.allowShowPassword}
                    invalid=${this.hasError("password").toString()}
                    prefill=${PasswordManagerPrefill.password ?? ""}
                ></ak-flow-input-password>
                <div class="pf-c-form__group pf-m-action">
                    <button type="submit" class="pf-c-button pf-m-primary pf-m-block">
                        ${msg("Continue")}
                    </button>
                </div>
            </form>
            ${this.challenge.recoveryUrl
                ? html`<div slot="footer-band" class="pf-c-login__main-footer-band">
                      <p class="pf-c-login__main-footer-band-item">
                          <a href="${this.challenge.recoveryUrl}"> ${msg("Forgot password?")}</a>
                      </p>
                  </div>`
                : nothing}
        </ak-flow-card>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-password": PasswordStage;
    }
}
