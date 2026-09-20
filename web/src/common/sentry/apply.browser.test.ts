import { getClient } from "@sentry/browser";
import { describe, expect, it } from "vitest";

describe("sentry/apply", () => {
    it("boots without a server-injected context", async () => {
        // `globalAK` falls back to `ConfigFromJSON({ capabilities: [] })` when the
        // document carries no `ak-config` block, and `errorReporting` comes back
        // undefined despite `Config` typing it as required. Reading through it
        // unguarded throws here — in the first import of every entrypoint, taking
        // the whole interface down rather than just Sentry.
        expect(
            document.getElementById("ak-config"),
            "The test document carries no injected configuration",
        ).toBeNull();

        await expect(import("#common/sentry/apply")).resolves.toBeDefined();

        expect(getClient(), "Sentry stays uninitialized with no configuration").toBeUndefined();
    });
});
