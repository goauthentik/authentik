import { globalAK } from "@goauthentik/common/global.js";
import "@goauthentik/flow/FormStatic";
import { BaseStage } from "@goauthentik/flow/stages/base";

import { msg, str } from "@lit/localize";
import { CSSResult, TemplateResult, html, nothing } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

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
            return html`<ak-empty-state ?loading="${true}" header=${msg("Loading")}>
            </ak-empty-state>`;
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
                                >${msg("Not you?")}</a
                            >
                        </div>
                    </ak-form-static>
                    <p>
                        ${msg(
                            str`You've logged out of ${this.challenge.applicationName}. You can go back to the overview to launch another application, or log out of your authentik account.`,
                        )}
                    </p>
                    <a href="${globalAK().api.base}" class="pf-c-button pf-m-primary">
                        ${msg("Go back to overview")}
                    </a>
                    ${this.challenge.invalidationFlowUrl
                        ? html`
                              <a
                                  href="${this.challenge.invalidationFlowUrl}"
                                  class="pf-c-button pf-m-secondary"
                                  id="logout"
                              >
                                  ${msg(str`Log out of ${this.challenge.brandName}`)}
                              </a>
                          `
                        : nothing}
                    ${this.challenge.applicationLaunchUrl && this.challenge.applicationName
                        ? html`
                              <a
                                  href="${this.challenge.applicationLaunchUrl}"
                                  class="pf-c-button pf-m-secondary"
                              >
                                  ${msg(str`Log back into ${this.challenge.applicationName}`)}
                              </a>
                          `
                        : nothing}
                </form>
            </div>
            <footer class="pf-c-login__main-footer">
                <ul class="pf-c-login__main-footer-links"></ul>
            </footer>`;
    }
}
