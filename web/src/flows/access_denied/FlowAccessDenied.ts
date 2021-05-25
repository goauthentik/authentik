import { AccessDeniedChallenge, FlowChallengeResponseRequest } from "authentik-api";
import { CSSResult, customElement, html, TemplateResult } from "lit-element";
import { BaseStage } from "../stages/base";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFList from "@patternfly/patternfly/components/List/list.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import AKGlobal from "../../authentik.css";
import { t } from "@lingui/macro";

import "../../elements/EmptyState";

@customElement("ak-stage-access-denied")
export class FlowAccessDenied extends BaseStage<AccessDeniedChallenge, FlowChallengeResponseRequest> {

    static get styles(): CSSResult[] {
        return [PFBase, PFLogin, PFForm, PFList, PFFormControl, PFTitle, AKGlobal];
    }

    render(): TemplateResult {
        if (!this.challenge) {
            return html`<ak-empty-state
                ?loading="${true}"
                header=${t`Loading`}>
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
                            ${t`Request has been denied.`}
                        </p>
                        ${this.challenge?.errorMessage &&
                            html`<hr>
                            <p>${this.challenge.errorMessage}</p>`}
                    </div>
                </form>
            </div>
            <footer class="pf-c-login__main-footer">
                <ul class="pf-c-login__main-footer-links">
                </ul>
            </footer>`;
    }

}
