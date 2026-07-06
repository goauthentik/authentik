import { truncateMacAddress } from "../src/mac-address.js";

import { describe, expect, it } from "vitest";

const cc = (maxWidth: number) => ({ maxWidth });

describe("truncateMacAddress", () => {
    it("returns the address unchanged when it fits", () => {
        expect(truncateMacAddress("00:1a:2b:3c:4d:5e", cc(20))).toBe("00:1a:2b:3c:4d:5e");
    });

    it("drops middle octets keeping the leading OUI and trailing octets", () => {
        const out = truncateMacAddress("00:1a:2b:3c:4d:5e", cc(11));
        expect(out.startsWith("00")).toBe(true);
        expect(out.endsWith("5e")).toBe(true);
        expect(out).toContain("…");
        expect(out.length).toBeLessThanOrEqual(11);
    });

    it("handles hyphen-separated addresses", () => {
        const out = truncateMacAddress("00-1a-2b-3c-4d-5e", cc(11));
        expect(out).toContain("-");
        expect(out).toContain("…");
    });
});
