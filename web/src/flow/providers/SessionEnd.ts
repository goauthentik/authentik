import "#flow/FormStatic";
import "#flow/components/ak-flow-card";

import { globalAK } from "#common/global";

import { SlottedTemplateResult } from "#elements/types";

import { FlowUserDetails } from "#flow/FormStatic";
import { BaseStage } from "#flow/stages/base";

import { SessionEndChallenge } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { CSSResult, html, nothing } from "lit";
import { customElement } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-stage-session-end")
export class SessionEnd extends BaseStage<SessionEndChallenge, unknown> {
    static styles: CSSResult[] = [PFBase, PFLogin, PFForm, PFFormControl, PFTitle, PFButton];

    protected render(): SlottedTemplateResult {
        const { challenge } = this;

        if (!challenge) {
            return nothing;
        }

        return html`<ak-flow-card .challenge=${this.challenge}>
            <form class="pf-c-form">
                ${FlowUserDetails({ challenge: this.challenge })}

                <p>
                    ${msg(
                        str`You've logged out of ${challenge.applicationName}. You can go back to the overview to launch another application, or log out of your authentik account.`,
                    )}
                </p>
                <a href="${globalAK().api.base}" class="pf-c-button pf-m-primary">
                    ${msg("Go back to overview")}
                </a>
                ${challenge.invalidationFlowUrl
                    ? html`
                          <a
                              href="${challenge.invalidationFlowUrl}"
                              class="pf-c-button pf-m-secondary"
                              id="logout"
                          >
                              ${msg(str`Log out of ${challenge.brandName}`)}
                          </a>
                      `
                    : nothing}
                ${challenge.applicationLaunchUrl && challenge.applicationName
                    ? html`
                          <a
                              href="${challenge.applicationLaunchUrl}"
                              class="pf-c-button pf-m-secondary"
                          >
                              ${msg(str`Log back into ${challenge.applicationName}`)}
                          </a>
                      `
                    : nothing}
            </form>
        </ak-flow-card>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-session-end": SessionEnd;
    }
}
