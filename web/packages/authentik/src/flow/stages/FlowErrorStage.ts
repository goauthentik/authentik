import "@goauthentik/elements/EmptyState";
import "@goauthentik/flow/FormStatic";
import { BaseStage } from "@goauthentik/flow/stages/base";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement } from "lit/decorators.js";

import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { FlowChallengeResponseRequest, FlowErrorChallenge } from "@goauthentik/api";

@customElement("ak-stage-flow-error")
export class FlowErrorStage extends BaseStage<FlowErrorChallenge, FlowChallengeResponseRequest> {
    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFLogin,
            PFForm,
            PFFormControl,
            PFTitle,
            css`
                pre {
                    overflow-x: scroll;
                    max-width: calc(
                        35rem - var(--pf-c-login__main-body--PaddingRight) - var(
                                --pf-c-login__main-body--PaddingRight
                            )
                    );
                }
            `,
        ];
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
                    <h3 class="pf-c-title pf-m-3xl">
                        ${this.challenge?.error
                            ? this.challenge.error
                            : msg("Something went wrong! Please try again later.")}
                    </h3>
                    ${this.challenge?.traceback
                        ? html`<div class="pf-c-form__group">
                              <pre class="ak-exception">${this.challenge.traceback}</pre>
                          </div>`
                        : html``}
                    ${this.challenge?.requestId
                        ? html`<div class="pf-c-form__group">
                              <p>${msg("Request ID")}</p>
                              <code>${this.challenge.requestId}</code>
                          </div>`
                        : html``}
                </form>
            </div>
            <footer class="pf-c-login__main-footer">
                <ul class="pf-c-login__main-footer-links"></ul>
            </footer>`;
    }
}
