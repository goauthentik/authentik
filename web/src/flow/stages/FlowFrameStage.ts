import "@goauthentik/elements/EmptyState";
import "@goauthentik/flow/FormStatic";
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
    static get styles(): CSSResult[] {
        return [PFBase, PFLogin, PFForm, PFFormControl, PFTitle, css``];
    }

    render(): TemplateResult {
        if (!this.challenge) {
            return html`<ak-empty-state loading> </ak-empty-state>`;
        }
        return html` <header class="pf-c-login__main-header">
                <h1 class="pf-c-title pf-m-3xl">${this.challenge.flowInfo?.title}</h1>
            </header>
            <div class="pf-c-login__main-body">
                ${this.challenge.loadingOverlay
                    ? html`<ak-empty-state
                          loading
                          header=${this.challenge.loadingText ?? undefined}
                      >
                      </ak-empty-state>`
                    : nothing}
                <iframe
                    style=${this.challenge.loadingOverlay
                        ? "width:0;height:0;position:absolute;"
                        : ""}
                    src=${this.challenge.url}
                ></iframe>
            </div>
            <footer class="pf-c-login__main-footer">
                <ul class="pf-c-login__main-footer-links"></ul>
            </footer>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "xak-flow-frame": FlowFrameStage;
    }
}
