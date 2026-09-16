/**
 * @file CAPTCHA vendor test credentials.
 *
 * @remarks
 *
 * Kept out of `src/` deliberately. esbuild drops an unused module-level object only when
 * its initializer is free of property accesses — any reference to the vendor spine, dot or
 * computed, marks it as possibly side-effecting and pins it into the bundle. A record that
 * both references {@linkcode CaptchaVendorGlobal} and tree-shakes is therefore not
 * available; living here, it has nothing to shake out of.
 */

// `#flow/*` maps to `./src/flow/*.js`, which only a bundler resolves back to source.
// Playwright's loader takes it literally, so this import has to be relative.
import { CaptchaVendor, CaptchaVendorGlobal } from "../../src/flow/stages/captcha/shared";

/**
 * Cap is self-hosted and publishes no shared test server, so it has no entry in
 * {@linkcode CaptchaVendorRecord}.
 */
export type TestableCaptchaVendor = Exclude<CaptchaVendor, typeof CaptchaVendor.cap>;

/**
 * A CAPTCHA provider paired with the vendor's published always-pass test credentials.
 *
 * @remarks
 *
 * Every key below is documented by the vendor as a test credential and is safe to commit —
 * they are shared across every integrator and grant nothing.
 *
 * - `siteKey` renders a widget that solves without user input
 * - `secretKey` makes the matching `siteverify` call succeed, letting the flow advance past the stage.
 *
 * @see {@link https://developers.google.com/recaptcha/docs/faq#id-like-to-run-automated-tests-with-recaptcha-v2-what-should-i-do reCAPTCHA test keys}
 * @see {@link https://docs.hcaptcha.com/#integration-testing-test-keys hCaptcha test keys}
 * @see {@link https://developers.cloudflare.com/turnstile/troubleshooting/testing/ Turnstile test keys}
 */
export interface CaptchaVendorConfig {
    /**
     * The label of the option in the stage form's "Provider Type" select.
     */
    providerType: string;

    /**
     * A site key whose widget waits for the user, so it stays on screen to be asserted
     * against.
     */
    siteKey: string;

    /**
     * A site key whose widget solves itself, used to advance a flow past this stage
     * without simulating a click inside a cross-origin vendor frame.
     *
     * Only needed where the vendor offers one; reCAPTCHA and hCaptcha always require a
     * click on their test keys.
     */
    autoSolveSiteKey?: string;

    /**
     * The server-side secret key used to verify the CAPTCHA response.
     */
    secretKey: string;

    /**
     * The origin the vendor serves its widget iframe from, used to locate the rendered
     * widget without depending on vendor-specific markup.
     */
    widgetOrigin: string;

    /**
     * The global the vendor's script installs on `window`.
     */
    globalName: CaptchaVendorGlobal;

    /**
     * Whether completing the challenge requires clicking a checkbox.
     *
     * Turnstile's self-solving key completes unattended; reCAPTCHA and hCaptcha always
     * want the click, even on their always-pass keys.
     */
    requiresInteraction: boolean;
}

export const CaptchaVendorRecord: Record<TestableCaptchaVendor, CaptchaVendorConfig> = {
    recaptcha: {
        providerType: "Google reCAPTCHA v2",
        siteKey: "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI",
        secretKey: "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe",
        widgetOrigin: "recaptcha.net",
        globalName: CaptchaVendorGlobal[CaptchaVendor.reCAPTCHA],
        requiresInteraction: true,
    },
    hcaptcha: {
        providerType: "hCaptcha",
        // hCaptcha's "always passes" key solves with no interaction, completing the flow
        // before the widget can be asserted against.
        // The bot-detected key renders the same widget and never solves.
        siteKey: "30000000-ffff-ffff-ffff-000000000003",
        autoSolveSiteKey: "10000000-ffff-ffff-ffff-000000000001",
        secretKey: "0x0000000000000000000000000000000000000000",
        widgetOrigin: "hcaptcha.com",
        globalName: CaptchaVendorGlobal[CaptchaVendor.hCaptcha],
        requiresInteraction: true,
    },
    turnstile: {
        providerType: "Cloudflare Turnstile",
        // Turnstile's "always passes" key solves with no interaction,
        // which would complete the flow before the widget could be asserted against.
        // The forced-interactive key renders the same widget but waits.
        siteKey: "3x00000000000000000000FF",
        autoSolveSiteKey: "1x00000000000000000000AA",
        secretKey: "1x0000000000000000000000000000000AA",
        widgetOrigin: "challenges.cloudflare.com",
        globalName: CaptchaVendorGlobal[CaptchaVendor.turnstile],
        requiresInteraction: false,
    },
};
