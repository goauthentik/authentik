import { t } from "@lingui/macro";
import { CSSResult, customElement, html, TemplateResult } from "lit-element";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import AKGlobal from "../../../authentik.css";
import { PFSize } from "../../../elements/Spinner";
import { BaseStage } from "../base";
import "../../../elements/forms/FormElement";
import "../../../elements/EmptyState";
import "../../FormStatic";
import { CaptchaChallenge, CaptchaChallengeResponseRequest } from "@goauthentik/api";
import { ifDefined } from "lit-html/directives/if-defined";

@customElement("ak-stage-captcha")
export class CaptchaStage extends BaseStage<CaptchaChallenge, CaptchaChallengeResponseRequest> {
    static get styles(): CSSResult[] {
        return [PFBase, PFLogin, PFForm, PFFormControl, PFTitle, PFButton, AKGlobal];
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
                if (!this.challenge?.siteKey) return;
                console.debug("authentik/stages/captcha: ready");
                const captchaId = grecaptcha.render(captchaContainer, {
                    sitekey: this.challenge.siteKey,
                    callback: (token) => {
                        this.host?.submit({
                            token: token,
                        });
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
            return html`<ak-empty-state ?loading="${true}" header=${t`Loading`}> </ak-empty-state>`;
        }
        return html`<header class="pf-c-login__main-header">
                <h1 class="pf-c-title pf-m-3xl">${this.challenge.flowInfo?.title}</h1>
            </header>
            <div class="pf-c-login__main-body">
                <form class="pf-c-form">
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
                    <div class="ak-loading">
                        <ak-spinner size=${PFSize.XLarge}></ak-spinner>
                    </div>
                </form>
            </div>
            <footer class="pf-c-login__main-footer">
                <ul class="pf-c-login__main-footer-links"></ul>
            </footer>`;
    }
}
