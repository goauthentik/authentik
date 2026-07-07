import { truncateEmail } from "../src/email.js";

import { describe, expect, it } from "vitest";

const cc = (maxWidth: number) => ({ maxWidth });

describe("truncateEmail", () => {
    it("returns the address unchanged when it fits", () => {
        expect(truncateEmail("me@example.com", cc(20))).toBe("me@example.com");
    });

    it("shrinks the local part first, keeping the domain intact", () => {
        const out = truncateEmail("firstname.lastname@company.com", cc(22));
        expect(out.endsWith("@company.com")).toBe(true);
        expect(out).toContain("…");
        expect(out.length).toBeLessThanOrEqual(22);
    });

    it("also shrinks the domain when the local part alone is not enough", () => {
        const out = truncateEmail("firstname.lastname@averylongcompany.example.com", cc(18));
        expect(out).toContain("@");
        expect(out).toContain("…");
        expect(out.length).toBeLessThanOrEqual(18);
    });

    it("middle-ellipsizes a value with no @ sign", () => {
        const out = truncateEmail("notanemailaddress", cc(10));
        expect(out).toContain("…");
        expect(out.length).toBeLessThanOrEqual(10);
    });
});
