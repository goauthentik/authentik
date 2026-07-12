import { type HashRouteScope, translateHashRoute } from "./hash-shim.js";

import { describe, expect, it } from "vitest";

const scope: HashRouteScope = { base: "/", interfaceName: "admin" };

describe("translateHashRoute", () => {
    it("returns null for non-hash-route URLs", () => {
        expect(translateHashRoute("", scope)).toBeNull();
        expect(translateHashRoute("#access_token=abc", scope)).toBeNull();
    });

    it("translates a bare hash path with no params", () => {
        expect(translateHashRoute("#/core/applications", scope)).toBe("/if/admin/core/applications");
    });

    it("translates a percent-encoded JSON blob", () => {
        const hash = "#/core/applications;" + encodeURIComponent(JSON.stringify({ page: 2 }));

        expect(translateHashRoute(hash, scope)).toBe("/if/admin/core/applications?page=2");
    });

    it("translates a raw JSON blob", () => {
        expect(translateHashRoute('#/core/applications;{"page":2}', scope)).toBe(
            "/if/admin/core/applications?page=2",
        );
    });

    it("translates JSON booleans", () => {
        const hash = "#/x;" + encodeURIComponent(JSON.stringify({ enabled: true }));

        expect(translateHashRoute(hash, scope)).toBe("/if/admin/x?enabled=true");
    });

    it("translates JSON arrays into repeated keys", () => {
        const hash = "#/x;" + encodeURIComponent(JSON.stringify({ ids: [1, 2] }));

        expect(translateHashRoute(hash, scope)).toBe("/if/admin/x?ids=1&ids=2");
    });

    it("drops empty JSON params", () => {
        expect(translateHashRoute("#/core/applications;{}", scope)).toBe(
            "/if/admin/core/applications",
        );
    });

    it("translates URLSearchParams-style params", () => {
        expect(translateHashRoute("#/core/groups;page=2&search=abc", scope)).toBe(
            "/if/admin/core/groups?page=2&search=abc",
        );
    });

    it("translates URLSearchParams booleans", () => {
        expect(translateHashRoute("#/x;active=true", scope)).toBe("/if/admin/x?active=true");
    });

    it("respects a non-root base and interface", () => {
        const authScope: HashRouteScope = { base: "/auth/", interfaceName: "user" };

        expect(translateHashRoute("#/settings", authScope)).toBe("/auth/if/user/settings");
    });
});
