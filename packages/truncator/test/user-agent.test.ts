import { truncateUserAgent } from "../src/user-agent.js";

import { describe, expect, it } from "vitest";

const cc = (maxWidth: number) => ({ maxWidth });

const CHROME_WIN =
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36";
const FIREFOX_MAC =
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0";
const EDGE_WIN =
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0";

describe("truncateUserAgent", () => {
    it("summarizes browser and OS", () => {
        expect(truncateUserAgent(CHROME_WIN, cc(40))).toBe("Chrome 120 · Windows");
    });

    it("detects Firefox on macOS", () => {
        expect(truncateUserAgent(FIREFOX_MAC, cc(40))).toBe("Firefox 121 · macOS");
    });

    it("prefers Edge over the Chrome token it also contains", () => {
        expect(truncateUserAgent(EDGE_WIN, cc(40))).toBe("Edge 120 · Windows");
    });

    it("end-ellipsizes the summary when it is still too wide", () => {
        const out = truncateUserAgent(CHROME_WIN, cc(8));
        expect(out.length).toBeLessThanOrEqual(8);
        expect(out).toContain("…");
    });

    it("falls back to the raw string for an unrecognized agent", () => {
        const out = truncateUserAgent("CustomBot/1.0", cc(40));
        expect(out).toBe("CustomBot/1.0");
    });
});
