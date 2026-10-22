import { int32, uint64 } from "../src/mmdb/data.ts";
import { parseNetwork } from "../src/mmdb/network.ts";
import { MMDBWriter } from "../src/mmdb/writer.ts";

import { Reader } from "mmdb-lib";
import { describe, expect, test } from "vitest";

function read(writer: MMDBWriter) {
    return new Reader<Record<string, unknown>>(Buffer.from(writer.toBytes()));
}

describe("parseNetwork", () => {
    test("maps IPv4 into ::/96", () => {
        const { address, bits } = parseNetwork("192.0.2.0/24");
        expect(bits).toBe(120);
        expect(address.slice(0, 12).every((byte) => byte === 0)).toBe(true);
        expect(address.slice(12)).toEqual(Uint8Array.of(192, 0, 2, 0));
    });

    test("expands compressed IPv6 and clears host bits", () => {
        const { address, bits } = parseNetwork("2001:db8::ff/32");
        expect(bits).toBe(32);
        expect(address.slice(0, 4)).toEqual(Uint8Array.of(0x20, 0x01, 0x0d, 0xb8));
        expect(address[15]).toBe(0);
    });

    test("rejects invalid input", () => {
        expect(() => parseNetwork("256.0.0.0/8")).toThrow();
        expect(() => parseNetwork("1::2::3/64")).toThrow();
        expect(() => parseNetwork("10.0.0.0/33")).toThrow();
    });
});

describe("MMDBWriter", () => {
    test("writes metadata readers accept", () => {
        const writer = new MMDBWriter({
            databaseType: "Test-ASN",
            description: { en: "test" },
            languages: ["en"],
            buildEpoch: 1_700_000_000,
        });
        writer.insert("192.0.2.0/24", { value: 1 });
        const { metadata } = read(writer);
        expect(metadata.databaseType).toBe("Test-ASN");
        expect(metadata.ipVersion).toBe(6);
        expect(metadata.binaryFormatMajorVersion).toBe(2);
        expect(metadata.recordSize).toBe(24);
        expect(metadata.description).toEqual({ en: "test" });
        expect(metadata.buildEpoch.getTime()).toBe(1_700_000_000_000);
    });

    test("looks up IPv4 and IPv6 networks", () => {
        const writer = new MMDBWriter({ databaseType: "Test" });
        writer.insert("192.0.2.0/24", { name: "v4" });
        writer.insert("2001:db8::/32", { name: "v6" });
        const reader = read(writer);
        expect(reader.getWithPrefixLength("192.0.2.77")).toEqual([{ name: "v4" }, 24]);
        expect(reader.getWithPrefixLength("2001:db8:1::1")).toEqual([{ name: "v6" }, 32]);
        expect(reader.get("198.51.100.1")).toBeNull();
    });

    test("more specific networks override earlier, less specific ones", () => {
        const writer = new MMDBWriter({ databaseType: "Test" });
        writer.insert("10.0.0.0/8", { name: "outer" });
        writer.insert("10.1.0.0/16", { name: "inner" });
        const reader = read(writer);
        expect(reader.get("10.1.2.3")).toEqual({ name: "inner" });
        expect(reader.get("10.2.0.1")).toEqual({ name: "outer" });
    });

    test("aliases IPv4-mapped and 6to4 addresses to the IPv4 tree", () => {
        const writer = new MMDBWriter({ databaseType: "Test" });
        writer.insert("8.8.8.0/24", { name: "v4" });
        const reader = read(writer);
        expect(reader.get("::ffff:8.8.8.8")).toEqual({ name: "v4" });
        expect(reader.get("2002:808:808::1")).toEqual({ name: "v4" });
    });

    test("round-trips every data type", () => {
        const record = {
            string: "hello, wörld",
            long: "x".repeat(70_000),
            uint32: 4_294_967_295,
            uint64: uint64(2n ** 64n - 1n),
            negative: int32(-5),
            double: 51.5,
            true: true,
            false: false,
            array: [1, "two", { three: 3 }],
            nested: { names: { en: "London", de: "London" } },
        };
        const writer = new MMDBWriter({ databaseType: "Test" });
        writer.insert("203.0.113.0/24", record);
        expect(read(writer).get("203.0.113.1")).toEqual({
            ...record,
            uint64: 2n ** 64n - 1n,
            negative: -5,
        });
    });

    test("stores repeated records and strings once", () => {
        const single = new MMDBWriter({ databaseType: "Test" });
        single.insert("10.0.0.0/24", { org: "Example Networks Inc." });
        const many = new MMDBWriter({ databaseType: "Test" });
        for (let index = 0; index < 256; index += 2) {
            many.insert(`10.0.${index}.0/24`, { org: "Example Networks Inc." });
        }
        const repeated = many.toBytes().length - single.toBytes().length;
        // Each extra network costs tree nodes only, not another copy of the record.
        expect(repeated).toBeLessThan(256 * 6 * 2);
        expect(read(many).get("10.0.200.1")).toEqual({ org: "Example Networks Inc." });
    });

    test("merges adjacent networks that hold the same record", () => {
        const split = new MMDBWriter({ databaseType: "Test" });
        split.insert("10.0.0.0/25", { name: "a" });
        split.insert("10.0.0.128/25", { name: "a" });
        const whole = new MMDBWriter({ databaseType: "Test" });
        whole.insert("10.0.0.0/24", { name: "a" });
        expect(split.toBytes().length).toBe(whole.toBytes().length);
        expect(read(split).getWithPrefixLength("10.0.0.200")).toEqual([{ name: "a" }, 24]);
    });

    test("switches to larger record sizes as the database grows", () => {
        const writer = new MMDBWriter({ databaseType: "Test" });
        for (let index = 0; index < 1100; index++) {
            writer.insert(`10.${index >> 8}.${index & 0xff}.0/24`, {
                id: index,
                pad: `${index}`.padEnd(16_000, "x"),
            });
        }
        const reader = read(writer);
        expect(reader.metadata.recordSize).toBe(28);
        expect(reader.get("10.4.75.1")).toMatchObject({ id: 1099 });
    });
});
