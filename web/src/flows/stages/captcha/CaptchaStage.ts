import { gettext } from "django";
import { CSSResult, customElement, html, property, TemplateResult } from "lit-element";
import { WithUserInfoChallenge } from "../../../api/Flows";
import { COMMON_STYLES } from "../../../common/styles";
import { SpinnerSize } from "../../../elements/Spinner";
import { BaseStage } from "../base";
import "../../../elements/forms/FormElement";
import "../../../elements/utils/LoadingState";

export interface CaptchaChallenge extends WithUserInfoChallenge {
    site_key: string;
}

@customElement("ak-stage-captcha")
export class CaptchaStage extends BaseStage {

    @property({ attribute: false })
    challenge?: CaptchaChallenge;

    static get styles(): CSSResult[] {
        return COMMON_STYLES;
    }

    submitFormAlt(token: string): void {
        const form = new FormData();
        form.set("token", token);
        this.host?.submit(form);
    }

    firstUpdated(): void {
        const script = document.createElement("script");
        script.src = "https://www.google.com/recaptcha/api.js";//?render=${this.challenge?.site_key}`;
        script.async = true;
        script.defer = true;
        const captchaContainer = document.createElement("div");
        document.body.appendChild(captchaContainer);
        script.onload = () => {
            console.debug("authentik/stages/captcha: script loaded");
            grecaptcha.ready(() => {
                if (!this.challenge?.site_key) return;
                console.debug("authentik/stages/captcha: ready");
                const captchaId = grecaptcha.render(captchaContainer, {
                    sitekey: this.challenge.site_key,
                    callback: (token) => {
                        this.submitFormAlt(token);
                    },
                    size: "invisible",
                });
                grecaptcha.execute(captchaId);
            });
        };
        document.head.appendChild(script);
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
                <form class="pf-c-form">
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
                    <div class="ak-loading">
                        <ak-spinner size=${SpinnerSize.XLarge}></ak-spinner>
                    </div>
                </form>
            </div>
            <footer class="pf-c-login__main-footer">
                <ul class="pf-c-login__main-footer-links">
                </ul>
            </footer>`;
    }

}
