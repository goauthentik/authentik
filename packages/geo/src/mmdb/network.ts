/**
 * @file IP networks in the 16-byte form the MMDB search tree walks.
 */

import ipaddr from "ipaddr.js";

/**
 * An IPv6 MMDB stores IPv4 networks under `::/96`.
 */
export const IPV4_OFFSET_BITS = 96;

export interface Network {
    /**
     * 16-byte address. IPv4 is mapped into `::a.b.c.d`.
     */
    readonly address: Uint8Array;

    /**
     * Prefix length in IPv6 bits. IPv4 prefixes are offset by 96.
     */
    readonly bits: number;
}

/**
 * Convert a parsed address and prefix length to a network, clearing the host bits.
 */
export function toNetwork(address: ipaddr.IPv4 | ipaddr.IPv6, bits: number): Network {
    const ipv4 = address.kind() === "ipv4";
    const mask = ipv4
        ? ipaddr.IPv4.subnetMaskFromPrefixLength(bits)
        : ipaddr.IPv6.subnetMaskFromPrefixLength(bits);
    const maskBytes = mask.toByteArray();
    const bytes = address.toByteArray().map((byte, index) => byte & maskBytes[index]!);
    const mapped = new Uint8Array(16);

    mapped.set(bytes, ipv4 ? 12 : 0);

    return { address: mapped, bits: ipv4 ? bits + IPV4_OFFSET_BITS : bits };
}

/**
 * Parse a CIDR network and clear its host bits.
 */
export function parseNetwork(cidr: string): Network {
    return toNetwork(...ipaddr.parseCIDR(cidr));
}

/**
 * Read one bit of a 16-byte address, most significant first.
 */
export function bitAt(address: Uint8Array, bit: number): 0 | 1 {
    return ((address[bit >> 3]! >> (7 - (bit & 7))) & 1) as 0 | 1;
}
