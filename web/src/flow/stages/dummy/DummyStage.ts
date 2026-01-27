import "#flow/FormStatic";
import "#flow/components/ak-flow-card";

import { BaseStage } from "#flow/stages/base";

import { DummyChallenge, DummyChallengeResponseRequest } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-stage-dummy")
export class DummyStage extends BaseStage<DummyChallenge, DummyChallengeResponseRequest> {
    static styles: CSSResult[] = [PFBase, PFLogin, PFForm, PFFormControl, PFTitle, PFButton];

    render(): TemplateResult {
        return html`<ak-flow-card .challenge=${this.challenge}>
            <form class="pf-c-form" @submit=${this.submitForm}>
                <p>${msg(str`Stage name: ${this.challenge?.name}`)}</p>
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
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-dummy": DummyStage;
    }
}
