import type { CaptchaHandlerHost } from "#flow/stages/captcha/controllers/CaptchaController";
import { TurnstileController } from "#flow/stages/captcha/controllers/turnstile";

import type { CaptchaChallenge } from "@goauthentik/api";

import { describe, expect, it, vi } from "vitest";

import { createRef } from "lit/directives/ref.js";

const createHost = (): CaptchaHandlerHost =>
    ({
        activeLanguageTag: "EN",
        activeTheme: "light",
        addController: vi.fn(),
        captchaDocumentContainer: {} as HTMLElement,
        challenge: {
            interactive: true,
            jsUrl: "https://challenges.cloudflare.com/turnstile/v0/api.js",
            siteKey: "1x00000000000000000000AA",
        } as CaptchaChallenge,
        error: null,
        iframeRef: createRef<HTMLIFrameElement>(),
        onTokenChange: vi.fn(),
        removeController: vi.fn(),
        requestUpdate: vi.fn(),
        updateComplete: Promise.resolve(true),
    }) satisfies CaptchaHandlerHost;

describe("TurnstileController", () => {
    it("reports interactive widget failures to the host frame", () => {
        const controller = new TurnstileController(createHost());

        const template = controller.interactive();
        const source = template.strings.join("");

        expect(source).toContain("self.parent.postMessage");
        expect(source).toContain('message: "error"');
        expect(source).toContain('"error-callback"');
        expect(source).toContain('reportTurnstileError("Turnstile error: " + errorCode)');
        expect(source).toContain("catch (error)");
    });

    it("reports an error when Turnstile does not initialize", () => {
        const controller = new TurnstileController(createHost());

        const template = controller.interactive();
        const source = template.strings.join("");

        expect(source).toContain('reportTurnstileError("Turnstile failed to initialize.")');
        expect(source).toContain("if (initializationFailed) return");
        expect(template.values).toContain(15_000);
    });
});
