import "#flow/FormStatic";
import "#flow/components/ak-flow-card";

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

@customElement("ak-stage-session-end")
export class SessionEnd extends BaseStage<SessionEndChallenge, unknown> {
    static styles: CSSResult[] = [PFLogin, PFForm, PFFormControl, PFTitle, PFButton];

    getText(challenge: SessionEndChallenge) {
        if (challenge.overviewUrl && challenge.invalidationFlowUrl) {
            return msg(
                str`You've logged out of ${challenge.applicationName}. You can go back to the overview to launch another application, or log out of your authentik account.`,
            );
        } else if (challenge.invalidationFlowUrl) {
            return msg(
                str`You've logged out of ${challenge.applicationName}. You can log out of your authentik account.`,
            );
        }

        return msg(str`You've logged out of ${challenge.applicationName}.`);
    }

    protected render(): SlottedTemplateResult {
        const { challenge } = this;

        if (!challenge) {
            return nothing;
        }

        return html`<ak-flow-card .challenge=${challenge}>
            <form class="pf-c-form">
                ${FlowUserDetails({ challenge })}

                <p>${this.getText(challenge)}</p>
                ${challenge.overviewUrl
                    ? html`<a href="${challenge.overviewUrl}" class="pf-c-button pf-m-primary">
                          ${msg("Go back to overview")}
                      </a>`
                    : nothing}
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

export default SessionEnd;

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-session-end": SessionEnd;
    }
}
