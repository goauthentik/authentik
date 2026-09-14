/// <reference types="@types/grecaptcha"/>
import { CaptchaController } from "#flow/stages/captcha/controllers/CaptchaController";
import { matchesAnyHost } from "#flow/stages/captcha/controllers/shared";

declare global {
    interface Window {
        grecaptcha: ReCaptchaV2.ReCaptcha & {
            enterprise: ReCaptchaV2.ReCaptcha;
        };
    }
}

/**
 * Hosts that serve the reCAPTCHA bootstrap script.
 *
 * `recaptcha.net` is the alternate host Google documents for regions where
 * `google.com` is unreachable, and is authentik's default.
 */
const RECAPTCHA_HOSTS = ["google.com", "recaptcha.net", "gstatic.com"] as const;

export class GReCaptchaController extends CaptchaController {
    public static readonly globalName = "grecaptcha";

    protected static override logPrefix = "grecaptcha";

    public static override matchesURL(url: URL): boolean {
        return matchesAnyHost(url, RECAPTCHA_HOSTS) && url.pathname.includes("/recaptcha/");
    }

    #widgetID: number | null = null;

    /**
     * The reCAPTCHA API surface for this challenge.
     *
     * Enterprise ships the same method names under a separate `grecaptcha.enterprise`
     * namespace and rejects site keys issued for it when called through the classic
     * entry point, so the script URL decides which one we talk to.
     *
     * @see {@link https://cloud.google.com/recaptcha/docs/display-checkbox}
     */
    get #api(): ReCaptchaV2.ReCaptcha {
        const url = this.prepareURL();
        const enterprise = url?.pathname.endsWith("/enterprise.js");

        return enterprise && window.grecaptcha.enterprise
            ? window.grecaptcha.enterprise
            : window.grecaptcha;
    }

    #ready(): Promise<void> {
        return new Promise((resolve) => this.#api.ready(resolve));
    }

    public mount = async (container: HTMLElement): Promise<void> => {
        await this.#ready();

        this.#widgetID = this.#api.render(container, {
            sitekey: this.host.challenge?.siteKey ?? "",
            callback: this.host.onTokenChange,
            theme: this.host.activeTheme,
            hl: this.host.activeLanguageTag,
        });

        this.host.onWidgetLoad();
    };

    public execute = async (container: HTMLElement): Promise<void> => {
        await this.#ready();

        this.#widgetID = this.#api.render(container, {
            sitekey: this.host.challenge?.siteKey ?? "",
            callback: this.host.onTokenChange,
            size: "invisible",
            hl: this.host.activeLanguageTag,
        });

        await this.#api.execute(this.#widgetID);
    };

    public reset = async (): Promise<void> => {
        if (this.#widgetID === null) {
            this.logger.warn("Skipping reset: no widget rendered");
            return;
        }

        this.#api.reset(this.#widgetID);

        if (!this.host.challenge?.interactive) {
            await this.#api.execute(this.#widgetID);
        }
    };

    public override unmount(): void {
        this.#widgetID = null;
    }
}
