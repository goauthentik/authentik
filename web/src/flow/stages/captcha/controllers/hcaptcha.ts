/// <reference types="@hcaptcha/types"/>

import { ifPresent } from "#elements/utils/attributes";

import { CaptchaController } from "#flow/stages/captcha/controllers/CaptchaController";

import { html } from "lit";

declare global {
    interface Window {
        hcaptcha?: HCaptcha;
    }
}

export class HCaptchaController extends CaptchaController {
    public static readonly globalName = "hcaptcha";

    #hcaptchaID: HCaptchaId | null = null;

    public interactive = () => {
        return html`<div
            id="ak-container"
            class="h-captcha"
            data-sitekey=${ifPresent(this.host.challenge?.siteKey)}
            data-theme=${this.host.activeTheme}
            data-callback="callback"
        ></div>`;
    };

    public refreshInteractive = async () => {
        this.host.iframeRef.value?.contentWindow?.hcaptcha?.reset();
    };

    public execute = async () => {
        this.#hcaptchaID = hcaptcha.render(this.host.captchaDocumentContainer, {
            sitekey: this.host.challenge?.siteKey ?? "",
            callback: this.host.onTokenChange,
            size: "invisible",
            hl: this.host.activeLanguageTag,
        });

        await hcaptcha.execute(this.#hcaptchaID, {
            async: true,
        });
    };

    public refresh = async () => {
        if (this.#hcaptchaID === null) {
            this.logger.warn("Skipping refresh: no hCaptcha ID set");
            return;
        }

        window.hcaptcha.reset(this.#hcaptchaID);
        window.hcaptcha.execute(this.#hcaptchaID);
    };
}
