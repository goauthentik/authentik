import "#flow/FormStatic";
import "#flow/components/ak-flow-card";

import { FlowUserDetails } from "#flow/FormStatic";
import { BaseStage } from "#flow/stages/base";

import {
    AuthenticatorStaticChallenge,
    AuthenticatorStaticChallengeResponseRequest,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css, CSSResult, html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFInputGroup from "@patternfly/patternfly/components/InputGroup/input-group.css";
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
        PFInputGroup,
        PFTitle,
        PFButton,
        css`
            /* Static OTP Tokens */
            .token-list {
                list-style: disc;
                padding-left: var(--pf-global--spacer--lg);
                margin: var(--pf-global--spacer--sm) 0;
            }
            .token-list li {
                font-family: var(--pf-global--FontFamily--monospace);
                font-size: var(--pf-global--FontSize--md);
                margin-bottom: var(--pf-global--spacer--xs);
                word-break: break-all;
            }
        `,
    ];

    render(): TemplateResult {
        return html`<ak-flow-card .challenge=${this.challenge}>
            <form class="pf-c-form" @submit=${this.submitForm}>
                ${FlowUserDetails({ challenge: this.challenge })}

                <ul class="pf-c-form__group token-list">
                    ${this.challenge.codes.map((token) => {
                        return html`<li>${token}</li>`;
                    })}
                </ul>
                <p>${msg("Make sure to keep these tokens in a safe place.")}</p>

                <fieldset class="pf-c-form__group pf-m-action">
                    <legend class="sr-only">${msg("Form actions")}</legend>
                    <button
                        name="continue"
                        type="submit"
                        class="pf-c-button pf-m-primary pf-m-block"
                    >
                        ${msg("Continue")}
                    </button>
                </fieldset>
            </form>
        </ak-flow-card>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-authenticator-static": AuthenticatorStaticStage;
    }
}
