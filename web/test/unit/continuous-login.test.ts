import { continuousLoginExit } from "#flow/tabs/continuous-login";

import { describe, expect, it } from "vitest";

const origin = "https://authentik.example";

describe("continuousLoginExit", () => {
    it("reports a direct same-origin continuation on pagehide", () => {
        expect(
            continuousLoginExit(new URL("/application/saml/app/sso/", origin), origin, false),
        ).toBe("on-pagehide");
    });

    it("suppresses the exit for a same-origin continuation that may require authorization", () => {
        expect(
            continuousLoginExit(new URL("/application/saml/app/sso/", origin), origin, true),
        ).toBe("suppress");
    });

    it("reports an external continuation immediately", () => {
        expect(continuousLoginExit(new URL("https://service.example/acs"), origin, true)).toBe(
            "now",
        );

        expect(continuousLoginExit(new URL("https://service.example/acs"), origin, false)).toBe(
            "now",
        );
    });
});
