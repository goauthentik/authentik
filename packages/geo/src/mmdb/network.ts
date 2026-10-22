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
 * Parse a CIDR network and clear its host bits.
 */
export function parseNetwork(cidr: string): Network {
    const [address, bits] = ipaddr.parseCIDR(cidr);

    if (address.kind() === "ipv4") {
        const mapped = new Uint8Array(16);

        mapped.set(ipaddr.IPv4.networkAddressFromCIDR(cidr).toByteArray(), 12);

        return { address: mapped, bits: bits + IPV4_OFFSET_BITS };
    }

    return {
        address: Uint8Array.from(ipaddr.IPv6.networkAddressFromCIDR(cidr).toByteArray()),
        bits,
    };
}

/**
 * Read one bit of a 16-byte address, most significant first.
 */
export function bitAt(address: Uint8Array, bit: number): 0 | 1 {
    return ((address[bit >> 3]! >> (7 - (bit & 7))) & 1) as 0 | 1;
}
