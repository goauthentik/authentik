/**
 * @file Parsers for the public data the ASN database is built from.
 */

import { type Network, overlaps, parseNetwork } from "../mmdb/network.ts";

export const RIS_DUMP_IPV4 = "https://www.ris.ripe.net/dumps/riswhoisdump.IPv4.gz";
export const RIS_DUMP_IPV6 = "https://www.ris.ripe.net/dumps/riswhoisdump.IPv6.gz";
export const AS_NAMES = "https://ftp.ripe.net/ripe/asnames/asn.txt";

export interface Route {
    readonly prefix: string;
    readonly network: Network;
    readonly origin: number;
    /** How many RIS peers see this route. */
    readonly peers: number;
}

export interface RouteFilter {
    /** Routes seen by fewer peers are dropped as leaks or noise. */
    minPeers: number;
    /** Shorter prefixes are bogus aggregates, e.g. a `2000::/6` a few peers carry. */
    minIPv4Bits: number;
    minIPv6Bits: number;
    /** Longer prefixes are filtered by most networks anyway. */
    maxIPv4Bits: number;
    maxIPv6Bits: number;
}

export const DEFAULT_ROUTE_FILTER: RouteFilter = {
    minPeers: 3,
    minIPv4Bits: 8,
    minIPv6Bits: 16,
    maxIPv4Bits: 24,
    maxIPv6Bits: 48,
};

/** Special-purpose ranges (RFC 6890) that should never carry public routing data. */
const RESERVED_IPV4 = [
    "0.0.0.0/8",
    "10.0.0.0/8",
    "100.64.0.0/10",
    "127.0.0.0/8",
    "169.254.0.0/16",
    "172.16.0.0/12",
    "192.0.0.0/24",
    "192.0.2.0/24",
    "192.88.99.0/24",
    "192.168.0.0/16",
    "198.18.0.0/15",
    "198.51.100.0/24",
    "203.0.113.0/24",
    "224.0.0.0/4",
    "240.0.0.0/4",
].map(parseNetwork);

/** IPv4 lives under `::/96`, so these must only be checked against IPv6 routes. */
const RESERVED_IPV6 = [
    "::/8",
    "100::/64",
    "2001:db8::/32",
    "2002::/16",
    "fc00::/7",
    "fe80::/10",
    "ff00::/8",
].map(parseNetwork);

export function isReserved(network: Network, ipv4: boolean): boolean {
    return (ipv4 ? RESERVED_IPV4 : RESERVED_IPV6).some((reserved) => overlaps(network, reserved));
}

/**
 * Pick one origin per prefix from RIS whois dump lines (`<origin>\t<prefix>\t<peers>`). When
 * several networks announce the same prefix, the one most peers see wins.
 */
export function selectRoutes(lines: Iterable<string>, options: Partial<RouteFilter> = {}): Route[] {
    const filter = { ...DEFAULT_ROUTE_FILTER, ...options };
    const best = new Map<string, Route>();
    for (const line of lines) {
        if (line === "" || line.startsWith("%")) continue;
        const [originField, prefix, peersField] = line.split("\t");
        if (!originField || !prefix || !peersField) continue;
        // AS sets ("{64496,64497}") have no single origin.
        if (!/^\d+$/.test(originField)) continue;
        const peers = Number(peersField);
        if (peers < filter.minPeers) continue;
        const network = parseNetwork(prefix);
        const ipv4 = !prefix.includes(":");
        const bits = ipv4 ? network.bits - 96 : network.bits;
        if (bits < (ipv4 ? filter.minIPv4Bits : filter.minIPv6Bits)) continue;
        if (bits > (ipv4 ? filter.maxIPv4Bits : filter.maxIPv6Bits)) continue;
        if (isReserved(network, ipv4)) continue;
        const current = best.get(prefix);
        if (!current || peers > current.peers) {
            best.set(prefix, { prefix, network, origin: Number(originField), peers });
        }
    }
    // Less specific first, so more specific routes overwrite them in the tree.
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
        names.set(Number(asn), (name || rest).trim());
    }
    return names;
}
