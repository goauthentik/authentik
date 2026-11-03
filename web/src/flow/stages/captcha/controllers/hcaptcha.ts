/// <reference types="@hcaptcha/types"/>

import { CaptchaController } from "#flow/stages/captcha/controllers/CaptchaController";
import { CaptchaVendor, CaptchaVendorGlobal } from "#flow/stages/captcha/shared";

declare global {
    interface Window {
        hcaptcha?: HCaptcha;
    }
}

export class HCaptchaController extends CaptchaController {
    public static override readonly vendor = CaptchaVendor.hCaptcha;

    public static readonly globalName = CaptchaVendorGlobal[CaptchaVendor.hCaptcha];

    protected static override logPrefix = "hcaptcha";

    #widgetID: HCaptchaId | null = null;

    public mount = async (container: HTMLElement): Promise<void> => {
        this.#widgetID = hcaptcha.render(container, {
            sitekey: this.host.challenge?.siteKey ?? "",
            callback: this.host.onTokenChange,
            theme: this.host.activeTheme,
            hl: this.host.activeLanguageTag,
        });

        this.host.onWidgetLoad();
    };

    public execute = async (container: HTMLElement): Promise<void> => {
        this.#widgetID = hcaptcha.render(container, {
            sitekey: this.host.challenge?.siteKey ?? "",
            callback: this.host.onTokenChange,
            size: "invisible",
            hl: this.host.activeLanguageTag,
        });

        await hcaptcha.execute(this.#widgetID, {
            async: true,
        });
    };

    public reset = async (): Promise<void> => {
        if (this.#widgetID === null) {
            this.logger.warn("Skipping reset: no widget rendered");

            return;
        }

        hcaptcha.reset(this.#widgetID);

        if (!this.host.challenge?.interactive) {
            await hcaptcha.execute(this.#widgetID, { async: true });
        }
    };

    public override unmount(): void {
        if (this.#widgetID === null) return;

        // hCaptcha keeps per-widget state keyed by the container it rendered into. Without
        // an explicit remove, re-rendering the stage leaks the old widget and its nested
        // iframes stay subscribed to postMessage traffic from the vendor origin.
        hcaptcha.remove(this.#widgetID);
        this.#widgetID = null;
    }
}
