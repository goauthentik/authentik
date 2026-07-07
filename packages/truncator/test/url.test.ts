import { truncateURL } from "../src/url.js";

import { describe, expect, it } from "vitest";

const cc = (maxWidth: number) => ({ maxWidth });

describe("truncateURL", () => {
    it("returns a short url unchanged", () => {
        expect(truncateURL("example.com/path", cc(40))).toBe("example.com/path");
    });

    it("strips the protocol first", () => {
        expect(truncateURL("https://example.com/path", cc(16))).toBe("example.com/path");
    });

    it("strips www and protocol", () => {
        expect(truncateURL("https://www.example.com/a", cc(13))).toBe("example.com/a");
    });

    it("ellipsizes noisy query parameters", () => {
        const out = truncateURL(
            "example.com/search?q=authentik&sessiontoken=8f3b1c9d2e4a5f6b",
            cc(35),
        );
        expect(out).toContain("q=authentik");
        expect(out).toContain("…");
    });

    it("never exceeds the budget, hard-cutting as a last resort", () => {
        const out = truncateURL(
            "https://sub.averylongdomainname.example.com/very/deep/path/segments/here",
            cc(20),
        );
        expect(out.length).toBeLessThanOrEqual(20);
        expect(out).toContain("…");
    });
});
