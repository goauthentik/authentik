import { getSearchParam, getSearchParams } from "./search-params.js";

import { describe, expect, it } from "vitest";

describe("getSearchParams", () => {
    it("deserializes a query string to a typed record", () => {
        expect(getSearchParams("?q=foo&page=2&hideManaged=true")).toEqual({
            q: "foo",
            page: 2,
            hideManaged: true,
        });
    });

    it("returns an empty record for no query", () => {
        expect(getSearchParams("")).toEqual({});
    });
});

describe("getSearchParam", () => {
    it("returns the fallback when the key is absent", () => {
        expect(getSearchParam("missing", "fallback")).toBe("fallback");
    });
});
