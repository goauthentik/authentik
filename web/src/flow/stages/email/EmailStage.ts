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
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-stage-email")
export class EmailStage extends BaseStage<EmailChallenge, EmailChallengeResponseRequest> {
    static styles: CSSResult[] = [PFBase, PFLogin, PFForm, PFFormControl, PFButton, PFTitle];

    render(): TemplateResult {
        return html`<ak-flow-card .challenge=${this.challenge}>
            <form
                class="pf-c-form"
                @submit=${(e: Event) => {
                    this.submitForm(e);
                }}
            >
                <div class="pf-c-form__group">
                    <p>${msg("Check your Inbox for a verification email.")}</p>
                </div>

                <div class="pf-c-form__group pf-m-action">
                    <button type="submit" class="pf-c-button pf-m-primary pf-m-block">
                        ${msg("Send Email again.")}
                    </button>
                </div>
            </form>
        </ak-flow-card>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-email": EmailStage;
    }
}
