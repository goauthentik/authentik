import { gettext } from "django";
import { css, CSSResult, customElement, html, property, TemplateResult } from "lit-element";
import { WithUserInfoChallenge } from "../../../api/Flows";
import { COMMON_STYLES } from "../../../common/styles";
import { BaseStage } from "../base";
import "../form";

export interface AuthenticatorStaticChallenge extends WithUserInfoChallenge {
    codes: number[];
}

@customElement("ak-stage-authenticator-static")
export class AuthenticatorStaticStage extends BaseStage {

    @property({ attribute: false })
    challenge?: AuthenticatorStaticChallenge;

    static get styles(): CSSResult[] {
        return COMMON_STYLES.concat(css`
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
        `);
    }

    render(): TemplateResult {
        if (!this.challenge) {
            return html`<ak-loading-state></ak-loading-state>`;
        }
        return html`<header class="pf-c-login__main-header">
                <h1 class="pf-c-title pf-m-3xl">
                    ${this.challenge.title}
                </h1>
            </header>
            <div class="pf-c-login__main-body">
                <form class="pf-c-form" @submit=${(e: Event) => { this.submitForm(e); }}>
                    <div class="pf-c-form__group">
                        <div class="form-control-static">
                            <div class="left">
                                <img class="pf-c-avatar" src="${this.challenge.pending_user_avatar}" alt="${gettext("User's avatar")}">
                                ${this.challenge.pending_user}
                            </div>
                            <div class="right">
                                <a href="/flows/-/cancel/">${gettext("Not you?")}</a>
                            </div>
                        </div>
                    </div>
                    <ak-form-element
                        label="${gettext("Tokens")}"
                        ?required="${true}"
                        class="pf-c-form__group">
                        <ul class="ak-otp-tokens">
                            ${this.challenge.codes.map((token) => {
                                return html`<li>${token}</li>`;
                            })}
                        </ul>
                    </ak-form-element>

                    <div class="pf-c-form__group pf-m-action">
                        <button type="submit" class="pf-c-button pf-m-primary pf-m-block">
                            ${gettext("Continue")}
                        </button>
                    </div>
                </form>
            </div>
            <footer class="pf-c-login__main-footer">
                <ul class="pf-c-login__main-footer-links">
                </ul>
            </footer>`;
    }

}
