import { getClient } from "@sentry/browser";
import { describe, expect, it } from "vitest";

describe("sentry/apply", () => {
    it("boots without a server-injected global", async () => {
        // `globalAK` falls back to `ConfigFromJSON({ capabilities: [] })` when the
        // server didn't inject `window.authentik`, and `errorReporting` comes back
        // undefined despite `Config` typing it as required. Reading through it
        // unguarded throws here — in the first import of every entrypoint, taking
        // the whole interface down rather than just Sentry.
        delete (window as Partial<Window & { authentik: unknown }>).authentik;

        await expect(import("#common/sentry/apply")).resolves.toBeDefined();

        expect(getClient(), "Sentry stays uninitialized with no configuration").toBeUndefined();
    });
});
