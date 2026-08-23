import { shouldReleaseContinuousLogin } from "#flow/tabs/continuous-login";

import { describe, expect, it } from "vitest";

const origin = "https://authentik.example";

describe("shouldReleaseContinuousLogin", () => {
    it("returns true for a direct same-origin continuation", () => {
        expect(
            shouldReleaseContinuousLogin(
                new URL("/application/saml/app/sso/", origin),
                origin,
                false,
            ),
        ).toBe(true);
    });

    it("returns false for a same-origin continuation that may require authorization", () => {
        expect(
            shouldReleaseContinuousLogin(
                new URL("/application/saml/app/sso/", origin),
                origin,
                true,
            ),
        ).toBe(false);
    });

    it("returns true for an external continuation", () => {
        expect(
            shouldReleaseContinuousLogin(new URL("https://service.example/acs"), origin, true),
        ).toBe(true);
    });
});
