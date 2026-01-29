/// <reference types="@types/grecaptcha"/>

/// <reference types="@hcaptcha/types"/>
import { ifPresent } from "#elements/utils/attributes";

import { CaptchaController } from "#flow/stages/captcha/controllers/CaptchaController";

import { html } from "lit";

declare global {
    interface Window {
        grecaptcha: ReCaptchaV2.ReCaptcha & {
            enterprise: ReCaptchaV2.ReCaptcha;
        };
    }
}

declare global {
    interface Window {
        hcaptcha?: HCaptcha;
    }
}

export class GReCaptchaController extends CaptchaController {
    public static readonly globalName = "grecaptcha";

    public interactive = () => {
        return html`<div
            id="ak-container"
            class="g-recaptcha"
            data-theme=${this.host.activeTheme}
            data-sitekey=${ifPresent(this.host.challenge?.siteKey)}
            data-callback="callback"
        ></div>`;
    };

    public execute = async () => {
        return grecaptcha.ready(() => {
            return grecaptcha.execute(
                grecaptcha.render(this.host.captchaDocumentContainer, {
                    sitekey: this.host.challenge?.siteKey ?? "",
                    callback: this.host.onTokenChange,
                    size: "invisible",
                    hl: this.host.activeLanguageTag,
                }),
            );
        });
    };

    public refreshInteractive = async () => {
        this.host.iframeRef.value?.contentWindow?.grecaptcha.reset();
    };

    public refresh = async () => {
        window.grecaptcha.reset();
        window.grecaptcha.execute();
    };
}
