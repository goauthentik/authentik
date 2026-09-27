import { recordToSearchParams, searchParamsToRecord } from "./parameters.js";

import { describe, expect, it } from "vitest";

describe("recordToSearchParams", () => {
    it("serializes strings, numbers, and true booleans", () => {
        const search = recordToSearchParams({ q: "abc", page: 2, active: true });

        expect(search.toString()).toBe("q=abc&page=2&active=true");
    });

    it("omits null, undefined, empty-string, and false values", () => {
        const search = recordToSearchParams({ a: null, b: undefined, c: "", d: false, e: "x" });

        expect(search.toString()).toBe("e=x");
    });

    it("appends array members as repeated keys", () => {
        const search = recordToSearchParams({ ids: [1, 2, 3] });

        expect(search.toString()).toBe("ids=1&ids=2&ids=3");
    });

    it("returns a URLSearchParams input unchanged", () => {
        const input = new URLSearchParams("x=1");

        expect(recordToSearchParams(input)).toBe(input);
    });
});

describe("searchParamsToRecord", () => {
    it("deserializes numbers, true, and false", () => {
        const record = searchParamsToRecord(
            new URLSearchParams("page=2&active=true&archived=false&q=abc"),
        );

        expect(record).toEqual({ page: 2, active: true, archived: false, q: "abc" });
    });

    it("collects repeated keys into an array", () => {
        const record = searchParamsToRecord(new URLSearchParams("ids=1&ids=2&ids=3"));

        expect(record).toEqual({ ids: [1, 2, 3] });
    });

    it("round-trips a record through search params", () => {
        const original = { q: "abc", page: 2, active: true, ids: [1, 2] };

        const restored = searchParamsToRecord(recordToSearchParams(original));

        expect(restored).toEqual(original);
    });

    it("keeps leading-zero digit strings as strings", () => {
        expect(searchParamsToRecord(new URLSearchParams("code=007"))).toEqual({ code: "007" });
    });

    it("keeps digit strings that lose precision as strings", () => {
        expect(searchParamsToRecord(new URLSearchParams("id=123456789012345678"))).toEqual({
            id: "123456789012345678",
        });
    });

    it("still coerces safe integers", () => {
        expect(searchParamsToRecord(new URLSearchParams("page=42"))).toEqual({ page: 42 });
    });
});
