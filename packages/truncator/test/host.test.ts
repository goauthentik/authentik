import { shrinkHost } from "../src/internal/host.js";

import { describe, expect, it } from "vitest";

const cc = (maxWidth: number) => ({ maxWidth });

describe("shrinkHost", () => {
    it("returns the host unchanged when it fits", () => {
        expect(shrinkHost("example.com", cc(20))).toBe("example.com");
    });

    it("collapses subdomains to a leading ellipsis, keeping domain and TLD", () => {
        expect(shrinkHost("a.b.c.example.com", cc(15))).toBe("….example.com");
    });

    it("middle-ellipsizes when even the domain and TLD do not fit", () => {
        const out = shrinkHost("averylongdomainname.com", cc(10));
        expect(out.length).toBeLessThanOrEqual(10);
        expect(out).toContain("…");
    });
});
