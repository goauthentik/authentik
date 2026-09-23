import { DISABLE_SENTRY_PARAM, isSentryEnabled } from "./utils.js";

import { type ErrorReportingConfig } from "@goauthentik/api";

import { describe, expect, it } from "vitest";

const reporting = (enabled: boolean): ErrorReportingConfig => ({ enabled }) as ErrorReportingConfig;

describe("isSentryEnabled", () => {
    it("is false when the administrator has error reporting off", () => {
        expect(
            isSentryEnabled({ errorReporting: reporting(false), debug: false, search: "" }),
        ).toBe(false);
    });

    it("is true when the administrator has error reporting on", () => {
        expect(isSentryEnabled({ errorReporting: reporting(true), debug: false, search: "" })).toBe(
            true,
        );
    });

    it("is true for a debug instance even with error reporting off", () => {
        // `CanDebug` is what activates Spotlight; it must not depend on the
        // administrator's reporting setting.
        expect(isSentryEnabled({ errorReporting: reporting(false), debug: true, search: "" })).toBe(
            true,
        );
    });

    it("is false when the config is absent entirely", () => {
        // `Config` types `errorReporting` as required, but the server may not
        // have injected `window.authentik` at all.
        expect(isSentryEnabled({ debug: false, search: "" })).toBe(false);
    });

    describe("in production", () => {
        const production = true;

        it("ignores the disable parameter", () => {
            expect(
                isSentryEnabled({
                    errorReporting: reporting(true),
                    debug: false,
                    search: `?${DISABLE_SENTRY_PARAM}`,
                    production,
                }),
            ).toBe(true);
        });
    });

    describe("in development", () => {
        const production = false;

        it("honors the disable parameter", () => {
            expect(
                isSentryEnabled({
                    errorReporting: reporting(true),
                    debug: false,
                    search: `?${DISABLE_SENTRY_PARAM}`,
                    production,
                }),
            ).toBe(false);
        });

        it("honors the disable parameter alongside other parameters", () => {
            expect(
                isSentryEnabled({
                    errorReporting: reporting(true),
                    debug: true,
                    search: `?q=authentik&${DISABLE_SENTRY_PARAM}=1`,
                    production,
                }),
            ).toBe(false);
        });

        it("reports when the parameter is absent", () => {
            expect(
                isSentryEnabled({
                    errorReporting: reporting(true),
                    debug: false,
                    search: "?q=authentik",
                    production,
                }),
            ).toBe(true);
        });
    });
});
