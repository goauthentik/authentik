/* eslint-disable @typescript-eslint/triple-slash-reference */
/// <reference types="turnstile-types"/>
import { ifPresent } from "#elements/utils/attributes";

import { CaptchaController } from "#flow/stages/captcha/controllers/CaptchaController";

import { TurnstileObject } from "turnstile-types";

import { html } from "lit";

declare global {
    interface Window {
        turnstile: TurnstileObject;
    }
}

export class TurnstileController extends CaptchaController {
    public static readonly globalName = "turnstile";

    public prepareURL = (): URL | null => {
        const input = this.host.challenge?.jsUrl;

        return input && URL.canParse(input) ? new URL(input) : null;
    };

    /**
     * Renders the Turnstile captcha frame.
     *
     * @remarks
     *
     * Turnstile will log a warning if the `data-language` attribute
     * is not in lower-case format.
     *
     * @see {@link https://developers.cloudflare.com/turnstile/reference/supported-languages/ Turnstile Supported Languages}
     */
    public interactive = () => {
        const languageTag = this.host.activeLanguageTag.toLowerCase();

        return html`<div
            id="ak-container"
            class="cf-turnstile"
            data-sitekey=${ifPresent(this.host.challenge?.siteKey)}
            data-theme=${this.host.activeTheme}
            data-callback="callback"
            data-size="flexible"
            data-language=${ifPresent(languageTag)}
        ></div>`;
    };

    public execute = async () => {
        window.turnstile.render(this.host.captchaDocumentContainer, {
            sitekey: this.host.challenge?.siteKey ?? "",
            callback: this.host.onTokenChange,
        });
    };

    public refreshInteractive = async () => {
        return this.host.iframeRef.value?.contentWindow?.turnstile.reset();
    };

    public refresh = async () => {
        return window.turnstile.reset();
    };
}
