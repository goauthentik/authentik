/**
 * @file Parsers for the public data the ASN database is built from.
 */

import { type Network, toNetwork } from "../mmdb/network.ts";

import ipaddr from "ipaddr.js";

export const RIS_DUMP_IPV4 = "https://www.ris.ripe.net/dumps/riswhoisdump.IPv4.gz";
export const RIS_DUMP_IPV6 = "https://www.ris.ripe.net/dumps/riswhoisdump.IPv6.gz";
export const AS_NAMES = "https://ftp.ripe.net/ripe/asnames/asn.txt";

export interface Route {
    /**
     * The announced prefix in CIDR notation.
     */
    readonly prefix: string;
    readonly network: Network;

    /**
     * Number of the autonomous system that announces the prefix.
     */
    readonly origin: number;

    /**
     * How many RIS peers see this route.
     */
    readonly peers: number;
}

export interface RouteFilter {
    /**
     * Minimum number of RIS peers that must see a route. Routes fewer peers see are usually leaks.
     */
    minPeers: number;

    /**
     * Shortest accepted IPv4 prefix length. Shorter prefixes are default routes or bogus
     * aggregates.
     */
    minIPv4Bits: number;

    /**
     * Shortest accepted IPv6 prefix length. Shorter prefixes are default routes or bogus aggregates
     * like `2000::/6`.
     */
    minIPv6Bits: number;

    /**
     * Longest accepted IPv4 prefix length. Most networks filter longer prefixes.
     */
    maxIPv4Bits: number;

    /**
     * Longest accepted IPv6 prefix length. Most networks filter longer prefixes.
     */
    maxIPv6Bits: number;
}

export const DEFAULT_ROUTE_FILTER: RouteFilter = {
    minPeers: 3,
    minIPv4Bits: 8,
    minIPv6Bits: 16,
    maxIPv4Bits: 24,
    maxIPv6Bits: 48,
};

/**
 * `ipaddr.js` range names for publicly routed addresses. Routes in other ranges are dropped as
 * special-purpose (RFC 6890).
 */
const ROUTABLE_RANGES = new Set(["unicast", "as112", "as112v6", "amt"]);

/**
 * Parse a CIDR prefix with its family's parser, or return `null` when it is malformed.
 */
function parseCIDR(prefix: string): [ipaddr.IPv4 | ipaddr.IPv6, number] | null {
    const family = prefix.includes(":") ? ipaddr.IPv6 : ipaddr.IPv4;

    try {
        return family.parseCIDR(prefix);
    } catch {
        return null;
    }
}

/**
 * Pick one origin per prefix from RIS whois dump lines (`<origin>\t<prefix>\t<peers>`). When
 * several networks announce the same prefix, the one most peers see wins.
 */
export function selectRoutes(lines: Iterable<string>, options: Partial<RouteFilter> = {}): Route[] {
    const filter = { ...DEFAULT_ROUTE_FILTER, ...options };
    const best = new Map<string, Route>();

    for (const line of lines) {
        const [originField, prefix, peersField] = line.split("\t");

        // AS sets like `{64496,64497}` have no single origin.
        if (!originField || !/^\d+$/.test(originField)) continue;
        if (!prefix || !peersField) continue;

        const peers = parseInt(peersField, 10);

        if (peers < filter.minPeers) continue;

        const parsed = parseCIDR(prefix);

        if (!parsed) continue;

        const [address, bits] = parsed;
        const ipv4 = address.kind() === "ipv4";

        if (bits < (ipv4 ? filter.minIPv4Bits : filter.minIPv6Bits)) continue;
        if (bits > (ipv4 ? filter.maxIPv4Bits : filter.maxIPv6Bits)) continue;
        if (!ROUTABLE_RANGES.has(address.range())) continue;

        const current = best.get(prefix);

        if (!current || peers > current.peers) {
            best.set(prefix, {
                prefix,
                network: toNetwork(address, bits),
                origin: parseInt(originField, 10),
                peers,
            });
        }
    }

    // More specific routes must be inserted last to override the routes they sit inside.
    return [...best.values()].sort((a, b) => a.network.bits - b.network.bits);
}

/**
 * Parse RIPE's AS name list. Lines look like `15169 GOOGLE - Google LLC, US` or
 * `47331 TTNET TTNet A.S., TR`: a handle, an optional dash, the organization, and a country code.
 */
export function parseASNames(lines: Iterable<string>): Map<number, string> {
    const names = new Map<number, string>();

    for (const line of lines) {
        const match = /^(\d+) (.+), [A-Z]{2}$/.exec(line.trim());

        if (!match) continue;

        const asn = match[1]!;
        const rest = match[2]!;
        const dash = rest.indexOf(" - ");
        const name = dash === -1 ? rest.slice(rest.indexOf(" ") + 1) : rest.slice(dash + 3);

        names.set(parseInt(asn, 10), (name || rest).trim());
    }

    return names;
}
