import { compressIPv6, truncateIPAddress } from "../src/ip-address.js";

import { describe, expect, it } from "vitest";

const cc = (maxWidth: number) => ({ maxWidth });

describe("compressIPv6", () => {
    it("strips leading zeros and collapses the longest zero run to ::", () => {
        expect(compressIPv6("2001:0db8:85a3:0000:0000:8a2e:0370:7334")).toBe(
            "2001:db8:85a3::8a2e:370:7334",
        );
    });

    it("leaves an already-compressed address canonical", () => {
        expect(compressIPv6("2001:db8::1")).toBe("2001:db8::1");
    });
});

describe("truncateIPAddress", () => {
    it("returns a short IPv4 unchanged", () => {
        expect(truncateIPAddress("192.168.1.100", cc(20))).toBe("192.168.1.100");
    });

    it("compresses IPv6 before truncating", () => {
        const out = truncateIPAddress("2001:0db8:0000:0000:0000:0000:0000:0001", cc(40));
        expect(out).toBe("2001:db8::1");
    });

    it("never exceeds the budget for a long IPv6", () => {
        const out = truncateIPAddress("2001:0db8:85a3:1234:5678:8a2e:0370:7334", cc(15));
        expect(out.length).toBeLessThanOrEqual(15);
        expect(out).toContain("…");
    });
});
