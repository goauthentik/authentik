/**
 * @file Assemble the ASN database from parsed routes and AS names.
 */

import { uint32 } from "../mmdb/data.ts";
import { MMDBWriter } from "../mmdb/writer.ts";
import type { Route } from "./sources.ts";

/** geoip2's `Reader.asn()` only accepts databases whose type contains `GeoLite2-ASN`. */
export const ASN_DATABASE_TYPE = "authentik-ASN (compat=GeoLite2-ASN)";

export const ASN_ATTRIBUTION =
    "Routing data from RIPE NCC's Routing Information Service (RIS), https://www.ripe.net/ris";

export function buildASNDatabase(
    routes: Iterable<Route>,
    names: ReadonlyMap<number, string>,
    buildEpoch?: number,
): Uint8Array {
    const writer = new MMDBWriter({
        databaseType: ASN_DATABASE_TYPE,
        description: { en: `authentik ASN database. ${ASN_ATTRIBUTION}` },
        languages: ["en"],
        buildEpoch,
    });
    for (const route of routes) {
        const name = names.get(route.origin);
        writer.insert(route.network, {
            autonomous_system_number: uint32(route.origin),
            ...(name ? { autonomous_system_organization: name } : {}),
        });
    }
    return writer.toBytes();
}
