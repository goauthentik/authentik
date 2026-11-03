import { CapController } from "#flow/stages/captcha/controllers/cap";
import {
    CaptchaController,
    type CaptchaControllerConstructor,
} from "#flow/stages/captcha/controllers/CaptchaController";
import { GReCaptchaController } from "#flow/stages/captcha/controllers/grecaptcha";
import { HCaptchaController } from "#flow/stages/captcha/controllers/hcaptcha";
import { TurnstileController } from "#flow/stages/captcha/controllers/turnstile";

import { afterEach, describe, expect, it } from "vitest";

/**
 * The same set, in the same order, that the stage registers.
 */
const CONTROLLERS: CaptchaControllerConstructor[] = [
    HCaptchaController,
    GReCaptchaController,
    TurnstileController,
    CapController,
];

/**
 * Pretend the given provider globals have been installed by an already-loaded script.
 *
 * Provider scripts are never removed from the document, so by the time a second CAPTCHA
 * stage runs, the first stage's global is still sitting on `window`.
 */
function withGlobals(...globalNames: string[]) {
    const scope = globalThis as unknown as Record<string, unknown>;

    scope.window = Object.fromEntries(globalNames.map((name) => [name, {}]));

    scope.customElements = {
        get: (name: string) => (globalNames.includes(name) ? class {} : undefined),
    };
}

afterEach(() => {
    const scope = globalThis as unknown as Record<string, unknown>;

    delete scope.window;
    delete scope.customElements;
});

describe("CaptchaController.matchesURL", () => {
    const cases: [Constructor: CaptchaControllerConstructor, url: string][] = [
        [GReCaptchaController, "https://www.recaptcha.net/recaptcha/api.js"],
        [GReCaptchaController, "https://www.google.com/recaptcha/api.js"],
        [GReCaptchaController, "https://www.recaptcha.net/recaptcha/enterprise.js"],
        [HCaptchaController, "https://js.hcaptcha.com/1/api.js"],
        [TurnstileController, "https://challenges.cloudflare.com/turnstile/v0/api.js"],
        [CapController, "https://cap.example.com/assets/widget.js"],
        [CapController, "https://cap.example.com/cap-widget.js"],
    ];

    for (const [Constructor, url] of cases) {
        it(`matches ${url} to ${Constructor.name} and to no other provider`, () => {
            const matching = CONTROLLERS.filter((Candidate) => Candidate.matchesURL(new URL(url)));

            expect(matching).toEqual([Constructor]);
        });
    }

    it("matches no provider for an unrecognized host", () => {
        const url = new URL("https://captcha.example.com/some/bundle.js");

        expect(CONTROLLERS.filter((Candidate) => Candidate.matchesURL(url))).toEqual([]);
    });
});

describe("CaptchaController.resolve", () => {
    it("selects the provider named by the challenge URL", () => {
        withGlobals();

        const resolution = CaptchaController.resolve(
            CONTROLLERS,
            new URL("https://challenges.cloudflare.com/turnstile/v0/api.js"),
        );

        expect(resolution).toEqual({ Controller: TurnstileController, matched: "url" });
    });

    // The defect the wrapper iframe was hiding: a flow with an hCaptcha stage followed by a
    // Turnstile stage leaves `window.hcaptcha` in place, and picking by global returned
    // hCaptcha for the Turnstile challenge — rendering the wrong widget against the wrong
    // site key.
    it("selects by URL even when another provider's global is already loaded", () => {
        withGlobals("hcaptcha", "grecaptcha");

        const resolution = CaptchaController.resolve(
            CONTROLLERS,
            new URL("https://challenges.cloudflare.com/turnstile/v0/api.js"),
        );

        expect(resolution?.Controller).toBe(TurnstileController);
    });

    it("selects Cap by URL even when every other global is loaded", () => {
        withGlobals("hcaptcha", "grecaptcha", "turnstile");

        const resolution = CaptchaController.resolve(
            CONTROLLERS,
            new URL("https://cap.example.com/assets/widget.js"),
        );

        expect(resolution?.Controller).toBe(CapController);
    });

    it("falls back to an available global when the URL is unrecognized", () => {
        withGlobals("turnstile");

        const resolution = CaptchaController.resolve(
            CONTROLLERS,
            new URL("https://captcha.example.com/proxied/api.js"),
        );

        expect(resolution).toEqual({ Controller: TurnstileController, matched: "global" });
    });

    it("returns null when the URL is unrecognized and no provider has loaded", () => {
        withGlobals();

        const resolution = CaptchaController.resolve(
            CONTROLLERS,
            new URL("https://captcha.example.com/proxied/api.js"),
        );

        expect(resolution).toBeNull();
    });
});
