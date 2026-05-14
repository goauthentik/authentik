/* eslint-disable @typescript-eslint/triple-slash-reference */
/// <reference types="turnstile-types"/>
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

        if (!input || !URL.canParse(input)) return null;

        const url = new URL(input);

        // Use explicit rendering to prevent Turnstile's 3-hour self-upgrade
        // from calling implicitRenderAll() and duplicating widgets.
        url.searchParams.set("render", "explicit");
        url.searchParams.set("onload", "onTurnstileReady");

        return url;
    };

    /**
     * See {@link https://developers.cloudflare.com/turnstile/troubleshooting/client-side-errors/error-codes/ Turnstile Client-Side Error Codes}
     */
    #delegateError = (errorCode: string) => {
        this.host.error = `Turnstile error: ${errorCode}`;
    };

    /**
     * Renders the Turnstile captcha frame.
     *
     * Uses explicit rendering to avoid Turnstile's self-upgrade mechanism
     * (every ~3 hours) from calling `implicitRenderAll()` and duplicating widgets.
     *
     * @remarks
     *
     * Turnstile will log a warning if the `language` option
     * is not in lower-case format.
     *
     * @see {@link https://developers.cloudflare.com/turnstile/reference/supported-languages/ Turnstile Supported Languages}
     */
    public interactive = () => {
        const siteKey = this.host.challenge?.siteKey ?? "";
        const theme = this.host.activeTheme;
        const language = this.host.activeLanguageTag.toLowerCase();

        return html`<div id="ak-container"></div>
            <script>
                function onTurnstileReady() {
                    turnstile.render("#ak-container", {
                        sitekey: "${siteKey}",
                        theme: "${theme}",
                        language: "${language}",
                        size: "flexible",
                        callback,
                    });
                    loadListener();
                }
            </script>`;
    };

    public refreshInteractive = async () => {
        return this.host.iframeRef.value?.contentWindow?.turnstile.reset();
    };

    public execute = async () => {
        window.turnstile.render(this.host.captchaDocumentContainer, {
            "sitekey": this.host.challenge?.siteKey ?? "",
            "callback": this.host.onTokenChange,
            "error-callback": this.#delegateError,
            "theme": this.host.activeTheme,
        });
    };

    public refresh = async () => {
        return window.turnstile.reset();
    };
}
