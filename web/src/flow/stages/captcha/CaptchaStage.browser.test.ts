import "#flow/stages/captcha/CaptchaStage";

import { CaptchaStage } from "#flow/stages/captcha/CaptchaStage";

import type { CaptchaChallenge } from "@goauthentik/api";

import type { TurnstileObject } from "turnstile-types";
import { afterEach, describe, expect, it, vi } from "vitest";

const mounted = new Set<HTMLElement>();

function mount<T extends HTMLElement>(element: T): T {
    mounted.add(element);
    document.body.appendChild(element);

    return element;
}

afterEach(() => {
    mounted.forEach((element) => element.remove());
    mounted.clear();
    Reflect.deleteProperty(window, "turnstile");
    document.querySelectorAll("script[data-test-turnstile]").forEach((script) => script.remove());
});

describe("ak-stage-captcha", () => {
    it("renders interactive Turnstile challenges without a blob iframe", async () => {
        const challengeURL = "data:text/javascript,void%200%3B%2F%2F";
        const providerScript = document.createElement("script");

        providerScript.dataset.testTurnstile = "true";
        providerScript.src = challengeURL;
        document.head.appendChild(providerScript);
        window.turnstile = {} as TurnstileObject;

        const stage = mount(new CaptchaStage());

        stage.challenge = {
            component: "ak-stage-captcha",
            interactive: true,
            jsUrl: challengeURL,
            siteKey: "test-site-key",
        } as CaptchaChallenge;

        await stage.updateComplete;

        const iframe = stage.renderRoot.querySelector<HTMLIFrameElement>("#ak-captcha");

        await vi.waitFor(() => {
            expect(iframe?.contentDocument?.querySelector("#ak-container")).not.toBeNull();
        });
        expect(iframe?.getAttribute("src")).toBeNull();
    });
});
