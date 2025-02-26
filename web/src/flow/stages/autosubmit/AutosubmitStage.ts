import "@goauthentik/elements/EmptyState";
import { BaseStage } from "@goauthentik/flow/stages/base";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, query } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { AutoSubmitChallengeResponseRequest, AutosubmitChallenge } from "@goauthentik/api";

@customElement("ak-stage-autosubmit")
export class AutosubmitStage extends BaseStage<
    AutosubmitChallenge,
    AutoSubmitChallengeResponseRequest
> {
    @query("form")
    private form?: HTMLFormElement;

    static get styles(): CSSResult[] {
        return [PFBase, PFLogin, PFForm, PFFormControl, PFButton, PFTitle];
    }

    updated(): void {
        this.form?.submit();
    }

    render(): TemplateResult {
        if (!this.challenge) {
            return html`<ak-empty-state loading> </ak-empty-state>`;
        }
        let title = this.challenge.flowInfo?.title;
        if (this.challenge.title && this.challenge.title !== "") {
            title = this.challenge.title;
        }
        if (!title) {
            title = msg("Loading");
        }
        return html`<form class="pf-c-form" action="${this.challenge.url}" method="POST">
            ${Object.entries(this.challenge.attrs).map(([key, value]) => {
                return html`<input
                    type="hidden"
                    name="${key as string}"
                    value="${value as string}"
                />`;
            })}
            <ak-empty-state loading title=${title}> </ak-empty-state>
        </form>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-autosubmit": AutosubmitStage;
    }
}
