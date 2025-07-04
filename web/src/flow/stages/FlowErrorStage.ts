import "@goauthentik/elements/EmptyState";
import "@goauthentik/flow/FormStatic";
import "@goauthentik/flow/components/ak-flow-card.js";
import { BaseStage } from "@goauthentik/flow/stages/base";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, css, html, nothing } from "lit";
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
        return html`<ak-flow-card .challenge=${this.challenge}>
            <form class="pf-c-form">
                <ak-empty-state icon="fa-times"
                    ><span>
                        ${this.challenge.error
                            ? this.challenge.error
                            : msg("Something went wrong! Please try again later.")}</span
                    >
                    <div slot="body">
                        ${this.challenge?.traceback
                            ? html`<div class="pf-c-form__group">
                                  <pre class="ak-exception">${this.challenge.traceback}</pre>
                              </div>`
                            : nothing}
                        ${this.challenge?.requestId
                            ? html`<div class="pf-c-form__group">
                                  <p>${msg("Request ID")}</p>
                                  <code>${this.challenge.requestId}</code>
                              </div>`
                            : nothing}
                    </div>
                </ak-empty-state>
            </form>
        </ak-flow-card>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-flow-error": FlowErrorStage;
    }
}
