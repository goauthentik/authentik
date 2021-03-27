import { Challenge } from "authentik-api";
import { CSSResult, customElement, html, property, TemplateResult } from "lit-element";
import { BaseStage } from "../stages/base";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFList from "@patternfly/patternfly/components/List/list.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import AKGlobal from "../../authentik.css";
import { gettext } from "django";

import "../../elements/EmptyState";

export interface AccessDeniedChallenge extends Challenge {
    error_message?: string;
}

@customElement("ak-stage-access-denied")
export class FlowAccessDenied extends BaseStage {

    @property({ attribute: false })
    challenge?: AccessDeniedChallenge;

    static get styles(): CSSResult[] {
        return [PFBase, PFLogin, PFForm, PFList, PFFormControl, PFTitle, AKGlobal];
    }

    render(): TemplateResult {
        if (!this.challenge) {
            return html`<ak-empty-state
                ?loading="${true}"
                header=${gettext("Loading")}>
            </ak-empty-state>`;
        }
        return html`<header class="pf-c-login__main-header">
                <h1 class="pf-c-title pf-m-3xl">
                    ${this.challenge.title}
                </h1>
            </header>
            <div class="pf-c-login__main-body">
                <form method="POST" class="pf-c-form">
                    <div class="pf-c-form__group">
                        <p>
                            <i class="pf-icon pf-icon-error-circle-o"></i>
                            ${gettext("Request has been denied.")}
                        </p>
                        ${this.challenge?.error_message &&
                            html`<hr>
                            <p>${this.challenge.error_message}</p>`}
                    </div>
                </form>
            </div>
            <footer class="pf-c-login__main-footer">
                <ul class="pf-c-login__main-footer-links">
                </ul>
            </footer>`;
    }

}
