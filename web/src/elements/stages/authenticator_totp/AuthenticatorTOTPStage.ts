import { gettext } from "django";
import { CSSResult, customElement, html, property, TemplateResult } from "lit-element";
import { WithUserInfoChallenge } from "../../../api/Flows";
import { COMMON_STYLES } from "../../../common/styles";
import { BaseStage } from "../base";
import 'webcomponent-qr-code'

export interface AuthenticatorTOTPChallenge extends WithUserInfoChallenge {
    config_url: string;
}

@customElement("ak-stage-authenticator-totp")
export class AuthenticatorTOTPStage extends BaseStage {

    @property({ attribute: false })
    challenge?: AuthenticatorTOTPChallenge;

    static get styles(): CSSResult[] {
        return COMMON_STYLES;
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
                <form class="pf-c-form" @submit=${(e: Event) => { this.submit(e); }}>
                    <div class="pf-c-form__group">
                        <div class="form-control-static">
                            <div class="left">
                                <img class="pf-c-avatar" src="${this.challenge.pending_user_avatar}" alt="${gettext("User's avatar")}">
                                ${this.challenge.pending_user}
                            </div>
                            <div class="right">
                                <a href="/-/cancel/">${gettext("Not you?")}</a>
                            </div>
                        </div>
                    </div>
                    <ak-form-element>
                        <qr-code data="${this.challenge.config_url}"></qr-code>
                    </ak-form-element>
                    <ak-form-element
                        label="${gettext("Code")}"
                        ?required="${true}"
                        class="pf-c-form__group"
                        .errors=${(this.challenge?.response_errors || {})["code"]}>
                        <input type="text"
                            name="code"
                            inputmode="numeric"
                            pattern="[0-9]*"
                            placeholder="${gettext("Please enter your TOTP Code")}"
                            autofocus=""
                            autocomplete="one-time-code"
                            class="pf-c-form-control"
                            required="">
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
