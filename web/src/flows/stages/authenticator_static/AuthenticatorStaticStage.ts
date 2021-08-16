import { t } from "@lingui/macro";
import { css, CSSResult, customElement, html, TemplateResult } from "lit-element";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import AKGlobal from "../../../authentik.css";
import { BaseStage } from "../base";
import "../../../elements/forms/FormElement";
import "../../../elements/EmptyState";
import "../../FormStatic";
import {
    AuthenticatorStaticChallenge,
    AuthenticatorStaticChallengeResponseRequest,
} from "authentik-api";
import { ifDefined } from "lit-html/directives/if-defined";

export const STATIC_TOKEN_STYLE = css`
    /* Static OTP Tokens */
    .ak-otp-tokens {
        list-style: circle;
        columns: 2;
        -webkit-columns: 2;
        -moz-columns: 2;
        margin-left: var(--pf-global--spacer--xs);
    }
    .ak-otp-tokens li {
        font-size: var(--pf-global--FontSize--2xl);
        font-family: monospace;
    }
`;

@customElement("ak-stage-authenticator-static")
export class AuthenticatorStaticStage extends BaseStage<
    AuthenticatorStaticChallenge,
    AuthenticatorStaticChallengeResponseRequest
> {
    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFLogin,
            PFForm,
            PFFormControl,
            PFTitle,
            PFButton,
            AKGlobal,
            STATIC_TOKEN_STYLE,
        ];
    }

    render(): TemplateResult {
        if (!this.challenge) {
            return html`<ak-empty-state ?loading="${true}" header=${t`Loading`}> </ak-empty-state>`;
        }
        return html`<header class="pf-c-login__main-header">
                <h1 class="pf-c-title pf-m-3xl">${this.challenge.flowInfo?.title}</h1>
            </header>
            <div class="pf-c-login__main-body">
                <form
                    class="pf-c-form"
                    @submit=${(e: Event) => {
                        this.submitForm(e);
                    }}
                >
                    <ak-form-static
                        class="pf-c-form__group"
                        userAvatar="${this.challenge.pendingUserAvatar}"
                        user=${this.challenge.pendingUser}
                    >
                        <div slot="link">
                            <a href="${ifDefined(this.challenge.flowInfo?.cancelUrl)}"
                                >${t`Not you?`}</a
                            >
                        </div>
                    </ak-form-static>
                    <ak-form-element
                        label="${t`Tokens`}"
                        ?required="${true}"
                        class="pf-c-form__group"
                    >
                        <ul class="ak-otp-tokens">
                            ${this.challenge.codes.map((token) => {
                                return html`<li>${token}</li>`;
                            })}
                        </ul>
                    </ak-form-element>

                    <div class="pf-c-form__group pf-m-action">
                        <button type="submit" class="pf-c-button pf-m-primary pf-m-block">
                            ${t`Continue`}
                        </button>
                    </div>
                </form>
            </div>
            <footer class="pf-c-login__main-footer">
                <ul class="pf-c-login__main-footer-links"></ul>
            </footer>`;
    }
}
