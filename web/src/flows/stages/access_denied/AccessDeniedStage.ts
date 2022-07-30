import "@goauthentik/web/elements/EmptyState";
import "@goauthentik/web/flows/FormStatic";
import { BaseStage } from "@goauthentik/web/flows/stages/base";

import { t } from "@lingui/macro";

import { CSSResult, TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import AKGlobal from "@goauthentik/web/authentik.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFList from "@patternfly/patternfly/components/List/list.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { AccessDeniedChallenge, FlowChallengeResponseRequest } from "@goauthentik/api";

@customElement("ak-stage-access-denied")
export class AccessDeniedStage extends BaseStage<
    AccessDeniedChallenge,
    FlowChallengeResponseRequest
> {
    static get styles(): CSSResult[] {
        return [PFBase, PFLogin, PFForm, PFList, PFFormControl, PFTitle, AKGlobal];
    }

    render(): TemplateResult {
        if (!this.challenge) {
            return html`<ak-empty-state ?loading="${true}" header=${t`Loading`}> </ak-empty-state>`;
        }
        return html`<header class="pf-c-login__main-header">
                <h1 class="pf-c-title pf-m-3xl">${this.challenge.flowInfo?.title}</h1>
            </header>
            <div class="pf-c-login__main-body">
                <form class="pf-c-form">
                    <ak-form-static
                        class="pf-c-form__group"
                        userAvatar="${this.challenge.pendingUserAvatar}"
                        user=${this.challenge.pendingUser}
                    >
                        <div slot="link">
                            <a href="${ifDefined(this.challenge.flowInfo?.cancelUrl)}"
                                >${t`Not you?`}</a
                            >
                        </div>
                    </ak-form-static>
                    <div class="pf-c-form__group">
                        <p>
                            <i class="pf-icon pf-icon-error-circle-o"></i>
                            ${t`Request has been denied.`}
                        </p>
                        ${this.challenge?.errorMessage &&
                        html`<hr />
                            <p>${this.challenge.errorMessage}</p>`}
                    </div>
                </form>
            </div>
            <footer class="pf-c-login__main-footer">
                <ul class="pf-c-login__main-footer-links"></ul>
            </footer>`;
    }
}
