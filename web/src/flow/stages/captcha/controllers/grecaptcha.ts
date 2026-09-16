/// <reference types="@types/grecaptcha"/>
import { CaptchaController } from "#flow/stages/captcha/controllers/CaptchaController";
import { CaptchaVendor, CaptchaVendorGlobal } from "#flow/stages/captcha/shared";

declare global {
    interface Window {
        grecaptcha: ReCaptchaV2.ReCaptcha & {
            enterprise: ReCaptchaV2.ReCaptcha;
        };
    }
}

export class GReCaptchaController extends CaptchaController {
    public static override readonly vendor = CaptchaVendor.reCAPTCHA;

    public static readonly globalName = CaptchaVendorGlobal[CaptchaVendor.reCAPTCHA];

    protected static override logPrefix = "grecaptcha";

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
            theme: this.host.activeTheme,
            size: "invisible",
            hl: this.host.activeLanguageTag,
        });

        await this.#api.execute(this.#widgetID);
    };

    /**
     * `color-scheme` on an iframe element is not a paint instruction. It declares which
     * scheme the embedder expects the embedded document to render in, and the browser
     * compares that with what the document itself declares. When they agree the frame's
     * backdrop stays transparent; when they disagree the browser assumes the content
     * would be illegible against the parent and paints an opaque canvas behind it, in
     * the document's own scheme.
     *
     * The anchor document declares nothing (`normal`, so light) — Google paints the dark
     * widget with an explicit `#222` on a div and leaves `html` and `body` transparent —
     * while the frame element inherits `dark` from authentik's dark theme. That mismatch
     * is where the white behind the widget's rounded corners and along its 2px inset
     * comes from. Declaring the document as light, which is what it is, restores the
     * transparent backdrop; the widget stays dark because Google's CSS makes it so.
     *
     * The reverse holds too: a document that declares `dark` inside an element computing
     * `light` gets an opaque near-black canvas, so this is deliberately not applied to
     * every vendor's frame.
     *
     * @see {@link https://drafts.csswg.org/css-color-adjust-1/#color-scheme-effect}
     */
    public override decorateFrame(frame: HTMLIFrameElement): void {
        if (frame.title !== "reCAPTCHA") return;

        frame.style.colorScheme = "light";
    }

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
