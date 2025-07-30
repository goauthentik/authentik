import "#flow/FormStatic";
import "#flow/components/ak-flow-card";

import { BaseStage } from "#flow/stages/base";

import {
    AuthenticatorStaticChallenge,
    AuthenticatorStaticChallengeResponseRequest,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css, CSSResult, html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-stage-authenticator-static")
export class AuthenticatorStaticStage extends BaseStage<
    AuthenticatorStaticChallenge,
    AuthenticatorStaticChallengeResponseRequest
> {
    static styles: CSSResult[] = [
        PFBase,
        PFLogin,
        PFForm,
        PFFormControl,
        PFTitle,
        PFButton,
        css`
            /* Static OTP Tokens */
            ul {
                list-style: circle;
                columns: 2;
                -webkit-columns: 2;
                -moz-columns: 2;
                column-width: 1em;
                margin-left: var(--pf-global--spacer--xs);
            }
            ul li {
                font-size: var(--pf-global--FontSize--2xl);
                margin: 0 2rem;
            }
        `,
    ];

    render(): TemplateResult {
        return html`<ak-flow-card .challenge=${this.challenge}>
            <form class="pf-c-form" @submit=${this.submitForm}>
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
                <div class="pf-c-form__group">
                    <ul>
                        ${this.challenge.codes.map((token) => {
                            return html`<li class="pf-m-monospace">${token}</li>`;
                        })}
                    </ul>
                </div>
                <p>${msg("Make sure to keep these tokens in a safe place.")}</p>

                <div class="pf-c-form__group pf-m-action">
                    <button type="submit" class="pf-c-button pf-m-primary pf-m-block">
                        ${msg("Continue")}
                    </button>
                </div>
            </form>
        </ak-flow-card>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-authenticator-static": AuthenticatorStaticStage;
    }
}
