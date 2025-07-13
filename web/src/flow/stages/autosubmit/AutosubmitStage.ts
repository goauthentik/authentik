import "#elements/EmptyState";
import "#flow/components/ak-flow-card";

import { BaseStage } from "#flow/stages/base";

import { AutosubmitChallenge, AutoSubmitChallengeResponseRequest } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement, query } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-stage-autosubmit")
export class AutosubmitStage extends BaseStage<
    AutosubmitChallenge,
    AutoSubmitChallengeResponseRequest
> {
    @query("form")
    private form?: HTMLFormElement;

    static styles: CSSResult[] = [PFBase, PFLogin, PFForm, PFFormControl, PFButton, PFTitle];

    updated(): void {
        if (this.challenge.url !== undefined) {
            this.form?.submit();
        }
    }

    render(): TemplateResult {
        let title = msg("Loading");
        if (this.challenge.title && this.challenge.title !== "") {
            title = this.challenge.title;
        }
        return html`<ak-flow-card .challenge=${this.challenge}>
            <form class="pf-c-form" action="${this.challenge.url}" method="post">
                ${Object.entries(this.challenge.attrs).map(([key, value]) => {
                    return html`<input
                        type="hidden"
                        name="${key as string}"
                        value="${value as string}"
                    />`;
                })}
                <ak-empty-state loading default-label></ak-empty-state>
            </form>
        </ak-flow-card>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-autosubmit": AutosubmitStage;
    }
}
