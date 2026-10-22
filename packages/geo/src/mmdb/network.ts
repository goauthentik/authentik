/**
 * @file IP network parsing for the MMDB search tree. Every address is held as 16 bytes, with IPv4
 *   mapped into `::/96` the way an IPv6 MMDB stores it.
 */

export interface Network {
    /** 16-byte address, IPv4 mapped into `::a.b.c.d`. */
    readonly address: Uint8Array;
    /** Prefix length in IPv6 bits. IPv4 prefixes are offset by 96. */
    readonly bits: number;
}

function parseIPv4(input: string): number[] | null {
    const parts = input.split(".");
    if (parts.length !== 4) return null;
    const bytes = parts.map((part) => (/^\d{1,3}$/.test(part) ? Number(part) : NaN));
    return bytes.every((byte) => byte <= 255) ? bytes : null;
}

function parseIPv6(input: string): number[] | null {
    const halves = input.split("::");
    if (halves.length > 2) return null;
    const groups = (half: string): number[] | null => {
        if (half === "") return [];
        const out: number[] = [];
        const parts = half.split(":");
        for (const [index, part] of parts.entries()) {
            // An embedded IPv4 address can only end the address.
            if (index === parts.length - 1 && part.includes(".")) {
                const v4 = parseIPv4(part);
                if (!v4) return null;
                out.push((v4[0]! << 8) | v4[1]!, (v4[2]! << 8) | v4[3]!);
            } else if (/^[0-9a-f]{1,4}$/i.test(part)) {
                out.push(parseInt(part, 16));
            } else {
                return null;
            }
        }
        return out;
    };
    const head = groups(halves[0]!);
    const tail = halves.length === 2 ? groups(halves[1]!) : [];
    if (!head || !tail) return null;
    const missing = 8 - head.length - tail.length;
    if (halves.length === 2 ? missing < 1 : missing !== 0) return null;
    const words = [...head, ...Array<number>(missing).fill(0), ...tail];
    return words.flatMap((word) => [word >> 8, word & 0xff]);
}

/** Parse an address or CIDR network. Host bits below the prefix are cleared. */
export function parseNetwork(input: string): Network {
    const [host = "", prefix] = input.split("/");
    const v4 = parseIPv4(host);
    const bytes = v4 ? [...Array<number>(12).fill(0), ...v4] : parseIPv6(host);
    if (!bytes) {
        throw new TypeError(`Invalid IP network: ${input}`);
    }
    const max = v4 ? 32 : 128;
    const length = prefix === undefined ? max : Number(prefix);
    if (!/^\d+$/.test(prefix ?? String(max)) || length > max) {
        throw new TypeError(`Invalid prefix length: ${input}`);
    }
    const bits = length + (v4 ? 96 : 0);
    const address = Uint8Array.from(bytes);
    for (let bit = bits; bit < 128; bit++) {
        address[bit >> 3]! &= ~(0x80 >> (bit & 7));
    }
    return { address, bits };
}

export function bitAt(address: Uint8Array, bit: number): 0 | 1 {
    return ((address[bit >> 3]! >> (7 - (bit & 7))) & 1) as 0 | 1;
}

/** Whether two networks share any address, i.e. one contains the other. */
export function overlaps(a: Network, b: Network): boolean {
    const bits = Math.min(a.bits, b.bits);
    for (let bit = 0; bit < bits; bit++) {
        if (bitAt(a.address, bit) !== bitAt(b.address, bit)) return false;
    }
    return true;
}
