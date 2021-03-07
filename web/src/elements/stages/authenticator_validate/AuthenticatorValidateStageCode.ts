import { gettext } from "django";
import { CSSResult, customElement, html, property, TemplateResult } from "lit-element";
import { COMMON_STYLES } from "../../../common/styles";
import { BaseStage } from "../base";
import { AuthenticatorValidateStage, AuthenticatorValidateStageChallenge, DeviceChallenge } from "./AuthenticatorValidateStage";
import "../form";

@customElement("ak-stage-authenticator-validate-code")
export class AuthenticatorValidateStageWebCode extends BaseStage {

    @property({ attribute: false })
    challenge?: AuthenticatorValidateStageChallenge;

    @property({ attribute: false })
    deviceChallenge?: DeviceChallenge;

    @property({ type: Boolean })
    showBackButton = false;

    static get styles(): CSSResult[] {
        return COMMON_STYLES;
    }

    render(): TemplateResult {
        if (!this.challenge) {
            return html`<ak-loading-state></ak-loading-state>`;
        }
        return html`<div class="pf-c-login__main-body">
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
                    label="${gettext("Code")}"
                    ?required="${true}"
                    class="pf-c-form__group"
                    .errors=${(this.challenge?.responseErrors || {})["code"]}>
                    <!-- @ts-ignore -->
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
                ${this.showBackButton ?
                    html`<li class="pf-c-login__main-footer-links-item">
                        <button class="pf-c-button pf-m-secondary pf-m-block" @click=${() => {
                            if (!this.host) return;
                            (this.host as AuthenticatorValidateStage).selectedDeviceChallenge = undefined;
                        }}>
                            ${gettext("Return to device picker")}
                        </button>
                    </li>`:
                    html``}
            </ul>
        </footer>`;
    }

}
