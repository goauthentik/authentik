/**
 * @file Assemble the ASN database from parsed routes and AS names.
 */

import { uint32 } from "../mmdb/data.ts";
import { MMDBWriter } from "../mmdb/writer.ts";
import type { Route } from "./sources.ts";

/**
 * Database type stored in the ASN database's metadata. It contains `GeoLite2-ASN`, which geoip2's
 * `Reader.asn()` requires before it reads a database.
 */
export const ASN_DATABASE_TYPE = "authentik-ASN (compat=GeoLite2-ASN)";

/**
 * Source credit stored in the database's description, required by RIPE NCC's terms.
 */
export const ASN_ATTRIBUTION =
    "Routing data from RIPE NCC's Routing Information Service (RIS), https://www.ripe.net/ris";

/**
 * Encode routes as an MMDB that maps each prefix to its origin AS number and organization name.
 */
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
