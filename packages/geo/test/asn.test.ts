import { ASN_DATABASE_TYPE, buildASNDatabase } from "../src/asn/build.ts";
import { parseASNames, selectRoutes } from "../src/asn/sources.ts";

import { Reader } from "mmdb-lib";
import { describe, expect, test } from "vitest";

const RIS_DUMP = `% Full dump of combined RIS IPv4 routing tables
% Format:  <origin> <tab> <prefix> <tab> <seen by #rispeers>

174\t0.0.0.0/0\t4
15169\t8.8.8.0/24\t390
64496\t8.8.8.0/24\t2
{64496,64497}\t198.51.100.0/24\t300
23237\t130.113.0.0/16\t350
64500\t130.113.64.0/24\t1
64501\t100.80.128.0/18\t200
64502\t1.2.3.0/25\t300
29632\t2000::/6\t3
15169\t2a00:1450::/32\t400
6939\t2002::/16\t250`;

describe("selectRoutes", () => {
    const routes = selectRoutes(RIS_DUMP.split("\n"));
    const byPrefix = new Map(routes.map((route) => [route.prefix, route]));

    test("keeps the origin most peers see", () => {
        expect(byPrefix.get("8.8.8.0/24")?.origin).toBe(15169);
    });

    test("drops routes few peers see", () => {
        expect(byPrefix.has("130.113.64.0/24")).toBe(false);
    });

    test("drops default routes, AS sets, bogus aggregates and too-specific prefixes", () => {
        expect(byPrefix.has("0.0.0.0/0")).toBe(false);
        expect(byPrefix.has("198.51.100.0/24")).toBe(false);
        expect(byPrefix.has("2000::/6")).toBe(false);
        expect(byPrefix.has("1.2.3.0/25")).toBe(false);
    });

    test("drops routes in reserved ranges", () => {
        expect(byPrefix.has("100.80.128.0/18")).toBe(false);
        expect(byPrefix.has("2002::/16")).toBe(false);
    });

    test("orders less specific routes first", () => {
        const bits = routes.map((route) => route.network.bits);
        expect(bits).toEqual([...bits].sort((a, b) => a - b));
    });
});

describe("parseASNames", () => {
    const names = parseASNames(
        [
            "15169 GOOGLE - Google LLC, US",
            "47331 TTNET TTNet A.S., TR",
            "29571 Orange Côte d'Ivoire - Orange Côte d'Ivoire, CI",
            "not a line",
        ].values(),
    );

    test("strips handles and country codes", () => {
        expect(names.get(15169)).toBe("Google LLC");
        expect(names.get(47331)).toBe("TTNet A.S.");
        expect(names.get(29571)).toBe("Orange Côte d'Ivoire");
        expect(names.size).toBe(3);
    });
});

describe("buildASNDatabase", () => {
    const database = buildASNDatabase(
        selectRoutes(RIS_DUMP.split("\n")),
        new Map([[15169, "Google LLC"]]),
    );
    const reader = new Reader<Record<string, unknown>>(Buffer.from(database));

    test("uses a type geoip2 accepts for ASN lookups", () => {
        expect(reader.metadata.databaseType).toBe(ASN_DATABASE_TYPE);
        expect(ASN_DATABASE_TYPE).toContain("GeoLite2-ASN");
    });

    test("stores MaxMind's ASN field names", () => {
        expect(reader.get("8.8.8.8")).toEqual({
            autonomous_system_number: 15169,
            autonomous_system_organization: "Google LLC",
        });
        expect(reader.get("2a00:1450:4001::1")).toMatchObject({ autonomous_system_number: 15169 });
    });

    test("leaves out unknown names", () => {
        expect(reader.get("130.113.64.30")).toEqual({ autonomous_system_number: 23237 });
    });
});
