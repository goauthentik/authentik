import { truncateHash } from "../src/hash.js";

import { describe, expect, it } from "vitest";

const cc = (maxWidth: number) => ({ maxWidth });

describe("truncateHash", () => {
    it("returns short hashes unchanged", () => {
        expect(truncateHash("abc123", cc(10))).toBe("abc123");
    });

    it("keeps head and tail around an ellipsis", () => {
        const sha = "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678";
        const out = truncateHash(sha, cc(13));
        expect(out).toContain("…");
        expect(out.length).toBeLessThanOrEqual(13);
        expect(out.startsWith("a1b2")).toBe(true);
    });

    it("keeps at least as much head as tail (head-biased)", () => {
        const sha = "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678";
        const out = truncateHash(sha, cc(12));
        const [head = "", tail = ""] = out.split("…");
        expect(head.length).toBeGreaterThanOrEqual(tail.length);
    });
});
