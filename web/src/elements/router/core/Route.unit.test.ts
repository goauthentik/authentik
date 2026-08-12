import { Route } from "./Route.js";

import { describe, expect, it, vi } from "vitest";

import { html } from "lit";

describe("Route", () => {
    it("compiles the pattern once at construction", () => {
        const route = new Route("/users/:id", () => html`ok`);

        expect(route.pattern).toBeInstanceOf(URLPattern);
        // The pattern is a stored instance, not rebuilt per access.
        expect(route.pattern).toBe(route.pattern);
        expect(route.pattern.exec({ pathname: "/users/42" })?.pathname.groups.id).toBe("42");
    });

    it("accepts a URLPatternInit object", () => {
        const route = new Route({ pathname: "/groups/:id" }, () => html`ok`);

        expect(route.pattern.exec({ pathname: "/groups/7" })?.pathname.groups.id).toBe("7");
    });

    it("derives a name from the pathname when none is given", () => {
        const route = new Route("/users/:id", () => html`ok`);

        expect(route.name).toBe("/users/:id");
    });

    it("uses an explicit name when provided", () => {
        const route = new Route("/users/:id", () => html`ok`, "user-detail");

        expect(route.name).toBe("user-detail");
    });

    it("invokes the render callback with the matched params", () => {
        const render = vi.fn(() => html`ok`);
        const route = new Route<{ id: string }>("/users/:id", render);

        route.render({ id: "42" });

        expect(render).toHaveBeenCalledWith({ id: "42" });
    });
});
