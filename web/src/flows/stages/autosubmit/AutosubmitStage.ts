import { t } from "@lingui/macro";

import { CSSResult, TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";

import AKGlobal from "../../../authentik.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { AutoSubmitChallengeResponseRequest, AutosubmitChallenge } from "@goauthentik/api";

import "../../../elements/EmptyState";
import { BaseStage } from "../base";

@customElement("ak-stage-autosubmit")
export class AutosubmitStage extends BaseStage<
    AutosubmitChallenge,
    AutoSubmitChallengeResponseRequest
> {
    static get styles(): CSSResult[] {
        return [PFBase, PFLogin, PFForm, PFFormControl, PFButton, PFTitle, AKGlobal];
    }

    updated(): void {
        this.shadowRoot?.querySelectorAll("form").forEach((form) => {
            form.submit();
        });
    }

    render(): TemplateResult {
        if (!this.challenge) {
            return html`<ak-empty-state ?loading="${true}" header=${t`Loading`}> </ak-empty-state>`;
        }
        let title = this.challenge.flowInfo?.title;
        if (this.challenge.title && this.challenge.title !== "") {
            title = this.challenge.title;
        }
        return html`<header class="pf-c-login__main-header">
                <h1 class="pf-c-title pf-m-3xl">${title}</h1>
            </header>
            <div class="pf-c-login__main-body">
                <form class="pf-c-form" action="${this.challenge.url}" method="POST">
                    ${Object.entries(this.challenge.attrs).map(([key, value]) => {
                        return html`<input
                            type="hidden"
                            name="${key as string}"
                            value="${value as string}"
                        />`;
                    })}
                    <ak-empty-state ?loading="${true}"> </ak-empty-state>
                    <div class="pf-c-form__group pf-m-action">
                        <button type="submit" class="pf-c-button pf-m-primary pf-m-block">
                            ${t`Continue`}
                        </button>
                    </div>
                </form>
            </div>
            <footer class="pf-c-login__main-footer">
                <ul class="pf-c-login__main-footer-links"></ul>
            </footer>`;
    }
}
