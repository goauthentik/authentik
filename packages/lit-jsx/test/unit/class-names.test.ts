import { normalizeClassValue } from "@goauthentik/lit-jsx";

import { describe, expect, it } from "vitest";

describe("normalizeClassValue", () => {
    it("passes strings through", () => {
        expect(normalizeClassValue("pf-c-button pf-m-primary")).toBe("pf-c-button pf-m-primary");
    });

    it("joins arrays, dropping falsy entries", () => {
        expect(normalizeClassValue(["a", null, "b", false, undefined, ""])).toBe("a b");
    });

    it("selects truthy keys from records", () => {
        expect(normalizeClassValue({ "pf-m-active": true, "pf-m-disabled": false })).toBe(
            "pf-m-active",
        );
    });

    it("flattens nested arrays and records", () => {
        expect(normalizeClassValue(["a", ["b", { c: true, d: false }]])).toBe("a b c");
    });

    it("returns an empty string for null and undefined", () => {
        expect(normalizeClassValue(null)).toBe("");
        expect(normalizeClassValue(undefined)).toBe("");
    });

    it("drops falsy numbers but keeps truthy ones", () => {
        expect(normalizeClassValue(0)).toBe("");
        expect(normalizeClassValue(NaN)).toBe("");
        expect(normalizeClassValue(1)).toBe("1");
        expect(normalizeClassValue(["a", 0, 1])).toBe("a 1");
    });
});
