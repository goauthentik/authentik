import { matchRoute, type RoutePatternLike, sameRouteMatch } from "./matcher.js";

import { describe, expect, it } from "vitest";

function route(pathname: string): RoutePatternLike {
    return { pattern: new URLPattern({ pathname }) };
}

describe("matchRoute", () => {
    it("returns null for an empty pathname", () => {
        expect(matchRoute("", [route("/users")])).toBeNull();
    });

    it("returns the first matching route with its params and pathname", () => {
        const routes = [route("/users/:id"), route("/groups/:id")];

        const match = matchRoute("/users/42", routes);

        expect(match?.route).toBe(routes[0]);
        expect(match?.parameters.id).toBe("42");
        expect(match?.pathname).toBe("/users/42");
    });

    it("is first-match-wins when two patterns overlap", () => {
        const first = route("/users/:id");
        const second = route("/users/:slug");

        const match = matchRoute("/users/42", [first, second]);

        expect(match?.route).toBe(first);
        expect(match?.parameters.id).toBe("42");
    });

    it("returns null when nothing matches", () => {
        expect(matchRoute("/nope", [route("/users/:id")])).toBeNull();
    });
});

describe("sameRouteMatch", () => {
    const users = route("/users/:id");
    const groups = route("/groups/:id");

    it("treats two null matches as the same", () => {
        expect(sameRouteMatch(null, null)).toBe(true);
    });

    it("treats null vs a match as different", () => {
        expect(sameRouteMatch(null, matchRoute("/users/42", [users]))).toBe(false);
    });

    it("is true for fresh matches of the same route and params (a search-only change)", () => {
        expect(
            sameRouteMatch(matchRoute("/users/42", [users]), matchRoute("/users/42", [users])),
        ).toBe(true);
    });

    it("is false when the path parameters differ", () => {
        expect(
            sameRouteMatch(matchRoute("/users/1", [users]), matchRoute("/users/2", [users])),
        ).toBe(false);
    });

    it("is false when the matched route differs", () => {
        expect(
            sameRouteMatch(
                matchRoute("/users/1", [users, groups]),
                matchRoute("/groups/1", [users, groups]),
            ),
        ).toBe(false);
    });
});
