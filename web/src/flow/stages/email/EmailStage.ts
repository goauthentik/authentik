import "#flow/components/ak-flow-card";

import { BaseStage } from "#flow/stages/base";

import { EmailChallenge, EmailChallengeResponseRequest } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";

@customElement("ak-stage-email")
export class EmailStage extends BaseStage<EmailChallenge, EmailChallengeResponseRequest> {
    static styles: CSSResult[] = [PFLogin, PFForm, PFFormControl, PFButton, PFTitle];

    render(): TemplateResult {
        return html`<ak-flow-card .challenge=${this.challenge}>
            <form class="pf-c-form" @submit=${this.submitForm}>
                <div class="pf-c-form__group">
                    <p>${msg("Check your Inbox for a verification email.")}</p>
                </div>

                <fieldset class="pf-c-form__group pf-m-action">
                    <legend class="sr-only">${msg("Form actions")}</legend>
                    <button
                        name="continue"
                        type="submit"
                        class="pf-c-button pf-m-primary pf-m-block"
                    >
                        ${msg("Send Email again.")}
                    </button>
                </fieldset>
            </form>
        </ak-flow-card>`;
    }
}

export default EmailStage;

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-email": EmailStage;
    }
}
