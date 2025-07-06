import "@goauthentik/elements/EmptyState";
import "@goauthentik/flow/FormStatic";
import "@goauthentik/flow/components/ak-flow-card.js";
import { BaseStage } from "@goauthentik/flow/stages/base";

import { CSSResult, TemplateResult, css, html, nothing } from "lit";
import { customElement } from "lit/decorators.js";

import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { FrameChallenge, FrameChallengeResponseRequest } from "@goauthentik/api";

@customElement("xak-flow-frame")
export class FlowFrameStage extends BaseStage<FrameChallenge, FrameChallengeResponseRequest> {
    static styles: CSSResult[] = [PFBase, PFLogin, PFForm, PFFormControl, PFTitle];

    render(): TemplateResult {
        return html`<ak-flow-card .challenge=${this.challenge}>
            ${this.challenge.loadingOverlay
                ? html`<ak-empty-state loading
                      >${this.challenge.loadingText
                          ? html`<span>${this.challenge.loadingText}</span>`
                          : nothing}
                  </ak-empty-state>`
                : nothing}
            <iframe
                style=${this.challenge.loadingOverlay ? "width:0;height:0;position:absolute;" : ""}
                src=${this.challenge.url}
            ></iframe>
        </ak-flow-card>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "xak-flow-frame": FlowFrameStage;
    }
}
