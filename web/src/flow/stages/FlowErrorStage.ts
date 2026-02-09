import "#elements/EmptyState";
import "#flow/FormStatic";
import "#flow/components/ak-flow-card";

import { SlottedTemplateResult } from "#elements/types";

import { BaseStage } from "#flow/stages/base";

import { FlowChallengeResponseRequest, FlowErrorChallenge } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css, CSSResult, html, nothing } from "lit";
import { customElement } from "lit/decorators.js";

import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";

@customElement("ak-stage-flow-error")
export class FlowErrorStage extends BaseStage<FlowErrorChallenge, FlowChallengeResponseRequest> {
    static styles: CSSResult[] = [
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

    protected render(): SlottedTemplateResult {
        if (!this.challenge) {
            return nothing;
        }

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
                        ${this.challenge.requestId
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
