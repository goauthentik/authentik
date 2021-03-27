import { gettext } from "django";
import { CSSResult, customElement, html, property, TemplateResult } from "lit-element";
import { WithUserInfoChallenge } from "../../../api/Flows";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import AKGlobal from "../../../authentik.css";
import { SpinnerSize } from "../../../elements/Spinner";
import { BaseStage } from "../base";
import "../../../elements/forms/FormElement";
import "../../../elements/EmptyState";
import "../../FormStatic";
import { FlowURLManager } from "../../../api/legacy";

export interface CaptchaChallenge extends WithUserInfoChallenge {
    site_key: string;
}

@customElement("ak-stage-captcha")
export class CaptchaStage extends BaseStage {

    @property({ attribute: false })
    challenge?: CaptchaChallenge;

    static get styles(): CSSResult[] {
        return [PFBase, PFLogin, PFForm, PFFormControl, PFTitle, PFButton, AKGlobal];
    }

    submitFormAlt(token: string): void {
        const form = new FormData();
        form.set("token", token);
        this.host?.submit(form);
    }

    firstUpdated(): void {
        const script = document.createElement("script");
        script.src = "https://www.google.com/recaptcha/api.js";
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
            return html`<ak-empty-state
                    ?loading="${true}"
                    header=${gettext("Loading")}>
                </ak-empty-state>`;
        }
        return html`<header class="pf-c-login__main-header">
                <h1 class="pf-c-title pf-m-3xl">
                    ${this.challenge.title}
                </h1>
            </header>
            <div class="pf-c-login__main-body">
                <form class="pf-c-form">
                    <ak-form-static
                        class="pf-c-form__group"
                        userAvatar="${this.challenge.pending_user_avatar}"
                        user=${this.challenge.pending_user}>
                        <div slot="link">
                            <a href="${FlowURLManager.cancel()}">${gettext("Not you?")}</a>
                        </div>
                    </ak-form-static>
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
