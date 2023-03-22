import { rootInterface } from "@goauthentik/elements/Base";
import { BaseStage } from "@goauthentik/flow/stages/base";

import { t } from "@lingui/macro";

import { CSSResult, TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { SessionEndChallenge } from "@goauthentik/api";

@customElement("ak-stage-session-end")
export class SessionEnd extends BaseStage<SessionEndChallenge, unknown> {
    static get styles(): CSSResult[] {
        return [PFBase, PFLogin, PFForm, PFFormControl, PFTitle, PFButton];
    }

    render(): TemplateResult {
        if (!this.challenge) {
            return html`<ak-empty-state ?loading="${true}" header=${t`Loading`}> </ak-empty-state>`;
        }
        const tenant = rootInterface()?.tenant;
        return html`<header class="pf-c-login__main-header">
                <h1 class="pf-c-title pf-m-3xl">${this.challenge.flowInfo?.title}</h1>
            </header>
            <div class="pf-c-login__main-body">
                <form class="pf-c-form">
                    <p>
                        ${t`You've logged out of ${this.challenge.applicationName}. You can go back to the overview to launch another application, or log out of your authentik account.`}
                    </p>
                    <a href="/" class="pf-c-button pf-m-primary"> ${t`Go back to overview`} </a>
                    ${tenant && tenant.flowInvalidation
                        ? html`
                              <!-- TODO: don't construct URL here -->
                              <a
                                  href="/if/flow/${tenant.flowInvalidation}/"
                                  class="pf-c-button pf-m-secondary"
                              >
                                  ${t`Log out of ${tenant.brandingTitle}`}
                              </a>
                          `
                        : html``}
                    ${this.challenge.applicationLaunchUrl
                        ? html`
                              <a
                                  href="${this.challenge.applicationLaunchUrl}"
                                  class="pf-c-button pf-m-secondary"
                              >
                                  ${t`Log back into ${this.challenge.applicationName}`}
                              </a>
                          `
                        : html``}
                </form>
            </div>`;
    }
}
