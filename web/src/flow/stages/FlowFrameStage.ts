import "#elements/EmptyState";
import "#flow/FormStatic";
import "#flow/components/ak-flow-card";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";

import { SlottedTemplateResult } from "#elements/types";

import { BaseStage } from "#flow/stages/base";

import { FrameChallenge, FrameChallengeResponseRequest } from "@goauthentik/api";

import { CSSResult, html, nothing } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("xak-flow-frame")
export class FlowFrameStage extends BaseStage<FrameChallenge, FrameChallengeResponseRequest> {
    static styles: CSSResult[] = [PFLogin, PFForm, PFFormControl, PFTitle];

    protected render(): SlottedTemplateResult {
        if (!this.challenge) {
            return nothing;
        }

        // The frame loads authentik's own device verification views from this origin. They need the
        // session, and they run a script that tells the flow to continue.
        /* oxlint-disable goauthentik/iframe-sandbox */
        return html`<ak-flow-card .challenge=${this.challenge}>
            ${
                this.challenge.loadingOverlay
                    ? html`<ak-empty-state loading
                          >${
                              this.challenge.loadingText
                                  ? html`<span>${this.challenge.loadingText}</span>`
                                  : nothing
                          }
                      </ak-empty-state>`
                    : nothing
            }
            <iframe
                style=${this.challenge.loadingOverlay ? "width:0;height:0;position:absolute;" : ""}
                src=${this.challenge.url}
            ></iframe>
        </ak-flow-card>`;
        /* oxlint-enable goauthentik/iframe-sandbox */
    }
}

export default FlowFrameStage;

declare global {
    interface HTMLElementTagNameMap {
        "xak-flow-frame": FlowFrameStage;
    }
}
