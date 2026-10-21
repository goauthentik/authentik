/* eslint-disable @typescript-eslint/triple-slash-reference */
/// <reference types="turnstile-types"/>
import { CaptchaController } from "#flow/stages/captcha/controllers/CaptchaController";
import { CaptchaVendor, CaptchaVendorGlobal } from "#flow/stages/captcha/shared";

import { TurnstileObject } from "turnstile-types";

declare global {
    interface Window {
        turnstile: TurnstileObject;
    }
}

export class TurnstileController extends CaptchaController {
    public static override readonly vendor = CaptchaVendor.turnstile;

    public static readonly globalName = CaptchaVendorGlobal[CaptchaVendor.turnstile];

    protected static override logPrefix = "turnstile";

    #widgetID: string | null = null;

    public override prepareURL = (): URL | null => {
        const input = this.host.challenge?.jsUrl;

        if (!input || !URL.canParse(input)) return null;

        const url = new URL(input);

        // Use explicit rendering to prevent Turnstile's 3-hour self-upgrade
        // from calling implicitRenderAll() and duplicating widgets.
        url.searchParams.set("render", "explicit");

        return url;
    };

    /**
     * See
     * {@link https://developers.cloudflare.com/turnstile/troubleshooting/client-side-errors/error-codes/ Turnstile Client-Side Error Codes}
     */
    #delegateError = (errorCode: string) => {
        this.host.error = `Turnstile error: ${errorCode}`;
    };

    /**
     * @remarks
     *
     *   Turnstile will log a warning if the `language` option
     *   is not in lower-case format.
     * @see {@link https://developers.cloudflare.com/turnstile/reference/supported-languages/ Turnstile Supported Languages}
     */
    public mount = async (container: HTMLElement): Promise<void> => {
        this.#widgetID = window.turnstile.render(container, {
            "sitekey": this.host.challenge?.siteKey ?? "",
            "callback": this.host.onTokenChange,
            "error-callback": this.#delegateError,
            "theme": this.host.activeTheme,
            "language": this.host.activeLanguageTag.toLowerCase(),
            "size": "flexible",
        });

        this.host.onWidgetLoad();
    };

    public execute = async (container: HTMLElement): Promise<void> => {
        this.#widgetID = window.turnstile.render(container, {
            "sitekey": this.host.challenge?.siteKey ?? "",
            "callback": this.host.onTokenChange,
            "error-callback": this.#delegateError,
            "theme": this.host.activeTheme,
            "language": this.host.activeLanguageTag.toLowerCase(),
        });
    };

    public reset = async (): Promise<void> => {
        if (this.#widgetID === null) {
            this.logger.warn("Skipping reset: no widget rendered");

            return;
        }

        window.turnstile.reset(this.#widgetID);
    };

    public override unmount(): void {
        if (this.#widgetID === null) return;

        window.turnstile.remove(this.#widgetID);
        this.#widgetID = null;
    }
}
