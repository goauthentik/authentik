import { initRouter, resetRouterConfig } from "./config.js";
import {
    formatInterfacePrefix,
    toAdminInterface,
    toFlowInterface,
    toUserInterface,
} from "./interfaces.js";

import { afterEach, describe, expect, it } from "vitest";

describe("formatInterfacePrefix", () => {
    it("appends a trailing slash to a base without one", () => {
        expect(formatInterfacePrefix("/auth", "admin")).toBe("/auth/if/admin/");
    });

    it("does not double the slash on a root base", () => {
        expect(formatInterfacePrefix("/", "user")).toBe("/if/user/");
    });
});

describe("interface href builders", () => {
    afterEach(() => resetRouterConfig());

    describe("root base path", () => {
        it("builds an admin URL with search params", () => {
            initRouter({ base: "/", interfaceName: "admin" });

            expect(toAdminInterface("core/applications", { page: 2 })).toBe(
                "/if/admin/core/applications?page=2",
            );
        });

        it("builds a bare user-interface root", () => {
            initRouter({ base: "/", interfaceName: "user" });

            expect(toUserInterface()).toBe("/if/user/");
        });

        it("builds a flow URL with a trailing slash", () => {
            initRouter({ base: "/", interfaceName: "user" });

            expect(toFlowInterface("default-authentication-flow")).toBe(
                "/if/flow/default-authentication-flow/",
            );
        });

        it("normalizes a leading slash on the path", () => {
            initRouter({ base: "/", interfaceName: "admin" });

            expect(toAdminInterface("/core/applications")).toBe("/if/admin/core/applications");
        });
    });

    describe("/auth/ base path", () => {
        it("prefixes the base path on admin URLs", () => {
            initRouter({ base: "/auth/", interfaceName: "admin" });

            expect(toAdminInterface("core/applications", { page: 2 })).toBe(
                "/auth/if/admin/core/applications?page=2",
            );
        });

        it("prefixes the base path on user URLs", () => {
            initRouter({ base: "/auth/", interfaceName: "admin" });

            expect(toUserInterface("settings")).toBe("/auth/if/user/settings");
        });
    });
});
