import { getRouterConfig, initRouter, resetRouterConfig } from "./config.js";

import { afterEach, describe, expect, it } from "vitest";

describe("router config", () => {
    afterEach(() => resetRouterConfig());

    it("defaults to a root base and unknown interface", () => {
        expect(getRouterConfig()).toEqual({ base: "/", interfaceName: "unknown" });
    });

    it("stores injected configuration", () => {
        initRouter({ base: "/auth/", interfaceName: "admin" });

        expect(getRouterConfig()).toEqual({ base: "/auth/", interfaceName: "admin" });
    });

    it("resets back to defaults", () => {
        initRouter({ base: "/auth/", interfaceName: "admin" });
        resetRouterConfig();

        expect(getRouterConfig()).toEqual({ base: "/", interfaceName: "unknown" });
    });

    it("returns a copy so mutations do not affect the stored config", () => {
        initRouter({ base: "/auth/", interfaceName: "admin" });

        const config = getRouterConfig();
        config.base = "/mutated/";

        expect(getRouterConfig().base).toBe("/auth/");
    });
});
