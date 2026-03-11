import "#flow/FormStatic";
import "#flow/components/ak-flow-card";

import { FlowUserDetails } from "#flow/FormStatic";
import { BaseStage } from "#flow/stages/base";

import { UserLoginChallenge, UserLoginChallengeResponseRequest } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFSpacing from "@patternfly/patternfly/utilities/Spacing/spacing.css";

@customElement("ak-stage-user-login")
export class PasswordStage extends BaseStage<
    UserLoginChallenge,
    UserLoginChallengeResponseRequest
> {
    static styles: CSSResult[] = [PFLogin, PFForm, PFFormControl, PFSpacing, PFButton, PFTitle];

    render(): TemplateResult {
        return html`<ak-flow-card .challenge=${this.challenge}>
            <form
                class="pf-c-form"
                @submit=${(event: SubmitEvent) => {
                    event.preventDefault();

                    const submitter =
                        event.submitter instanceof HTMLButtonElement ? event.submitter : null;

                    this.submitForm(event, {
                        rememberMe: submitter?.name === "remember-me",
                    });
                }}
            >
                ${FlowUserDetails({ challenge: this.challenge })}

                <div class="pf-c-form__group">
                    <h3 data-test-id="stage-heading" class="pf-c-title pf-m-xl pf-u-mb-xl">
                        ${msg("Stay signed in?")}
                    </h3>
                    <p class="pf-u-mb-sm">
                        ${msg("Select Yes to reduce the number of times you're asked to sign in.")}
                    </p>
                </div>

                <fieldset class="pf-c-form__group pf-m-action">
                    <legend class="sr-only">${msg("Form actions")}</legend>
                    <button name="remember-me" type="submit" class="pf-c-button pf-m-primary">
                        ${msg("Yes")}
                    </button>
                    <button name="forget-me" type="submit" class="pf-c-button pf-m-secondary">
                        ${msg("No")}
                    </button>
                </fieldset>
            </form>
        </ak-flow-card>`;
    }
}

export default PasswordStage;

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-user-login": PasswordStage;
    }
}
