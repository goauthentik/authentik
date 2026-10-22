/**
 * @file Writer for MaxMind DB (`.mmdb`) files, the format authentik's GeoIP and ASN readers load.
 * @see https://maxmind.github.io/MaxMind-DB/
 */

import { DataSection, type MMDBValue, uint16, uint32, uint64, valueKey } from "./data.ts";
import { bitAt, IPV4_OFFSET_BITS, type Network, parseNetwork } from "./network.ts";

export interface MMDBWriterOptions {
    /**
     * Readers check this, e.g. geoip2's ASN lookups require `GeoLite2-ASN` in it.
     */
    databaseType: string;
    description?: Record<string, string>;
    languages?: string[];

    /**
     * Seconds since the epoch. Defaults to now.
     */
    buildEpoch?: number;
}

const METADATA_MARKER = Uint8Array.of(0xab, 0xcd, 0xef, ...new TextEncoder().encode("MaxMind.com"));
const DATA_SECTION_SEPARATOR = 16;

/**
 * IPv6 ranges that MaxMind's databases point at the IPv4 subtree.
 */
const IPV4_ALIASES = ["::ffff:0:0/96", "2002::/16"].map(parseNetwork);

/**
 * A child slot with no data. Other slots hold a node index, or `-(record + 1)` for a record.
 */
const EMPTY = 0;

/**
 * Builds an IPv6 MMDB with IPv4 under `::/96`. An insert replaces everything below its prefix.
 * Insert less specific networks first.
 */
export class MMDBWriter {
    readonly #options: MMDBWriterOptions;
    #children = new Int32Array(1 << 20);
    #nodeCount = 1;
    #records: MMDBValue[] = [];
    #recordIndex = new Map<string, number>();

    public constructor(options: MMDBWriterOptions) {
        this.#options = options;
    }

    public insert(network: Network | string, record: MMDBValue): void {
        const { address, bits } = typeof network === "string" ? parseNetwork(network) : network;
        if (bits === 0) {
            throw new RangeError("Cannot insert the default route");
        }
        this.#set(address, bits, -(this.#recordId(record) + 1));
    }

    #recordId(record: MMDBValue): number {
        const key = valueKey(record);
        let id = this.#recordIndex.get(key);
        if (id === undefined) {
            id = this.#records.push(record) - 1;
            this.#recordIndex.set(key, id);
        }
        return id;
    }

    /**
     * Point the slot for `address/bits` at `value`, splitting any record above it.
     */
    #set(address: Uint8Array, bits: number, value: number): void {
        let node = 0;
        for (let depth = 0; depth < bits - 1; depth++) {
            const slot = node * 2 + bitAt(address, depth);
            const child = this.#children[slot]!;
            if (child > 0) {
                node = child;
                continue;
            }
            const next = this.#allocate();
            this.#children[next * 2] = child;
            this.#children[next * 2 + 1] = child;
            this.#children[slot] = next;
            node = next;
        }
        this.#children[node * 2 + bitAt(address, bits - 1)] = value;
    }

    #allocate(): number {
        if ((this.#nodeCount + 1) * 2 > this.#children.length) {
            const next = new Int32Array(this.#children.length * 2);
            next.set(this.#children);
            this.#children = next;
        }
        return this.#nodeCount++;
    }

    /**
     * Collapse nodes whose two halves hold the same record into that record.
     */
    #collapse(node: number): number {
        for (const side of [0, 1]) {
            const child = this.#children[node * 2 + side]!;
            if (child > 0) {
                this.#children[node * 2 + side] = this.#collapse(child);
            }
        }
        const left = this.#children[node * 2]!;
        const right = this.#children[node * 2 + 1]!;
        return left <= 0 && left === right ? left : node;
    }

    /**
     * The slot value at the root of the IPv4 subtree.
     */
    #ipv4Root(): number {
        let value = 0;
        for (let depth = 0; depth < IPV4_OFFSET_BITS; depth++) {
            value = this.#children[value * 2]!;
            if (value <= 0) return value;
        }
        return value;
    }

    public toBytes(): Uint8Array {
        this.#collapse(0);
        const ipv4Root = this.#ipv4Root();
        if (ipv4Root !== EMPTY) {
            for (const alias of IPV4_ALIASES) {
                this.#set(alias.address, alias.bits, ipv4Root);
            }
        }

        // The IPv4 aliases reach the same subtree twice.
        const order = new Int32Array(this.#nodeCount).fill(-1);
        const queue = [0];
        order[0] = 0;
        let nodeCount = 1;
        for (let index = 0; index < queue.length; index++) {
            const node = queue[index]!;
            for (const side of [0, 1]) {
                const child = this.#children[node * 2 + side]!;
                if (child > 0 && order[child] === -1) {
                    order[child] = nodeCount++;
                    queue.push(child);
                }
            }
        }

        const data = new DataSection();
        const offsets = this.#records.map((record) => data.add(record));
        const recordValue = (child: number): number => {
            if (child > 0) return order[child]!;
            if (child === EMPTY) return nodeCount;
            return nodeCount + DATA_SECTION_SEPARATOR + offsets[-child - 1]!;
        };

        const maxValue = nodeCount + DATA_SECTION_SEPARATOR + data.length;
        const recordSize = maxValue < 2 ** 24 ? 24 : maxValue < 2 ** 28 ? 28 : 32;
        if (maxValue >= 2 ** 32) {
            throw new RangeError("Database is too large for a 32-bit record size");
        }

        const nodeBytes = recordSize / 4;
        const tree = new Uint8Array(nodeCount * nodeBytes);
        const view = new DataView(tree.buffer);
        const writeUint24 = (value: number, offset: number) => {
            tree[offset] = value >>> 16;
            tree[offset + 1] = (value >>> 8) & 0xff;
            tree[offset + 2] = value & 0xff;
        };
        for (const node of queue) {
            const left = recordValue(this.#children[node * 2]!);
            const right = recordValue(this.#children[node * 2 + 1]!);
            const offset = order[node]! * nodeBytes;
            if (recordSize === 24) {
                writeUint24(left, offset);
                writeUint24(right, offset + 3);
            } else if (recordSize === 28) {
                writeUint24(left & 0xff_ffff, offset);
                tree[offset + 3] = ((left >>> 24) << 4) | (right >>> 24);
                writeUint24(right & 0xff_ffff, offset + 4);
            } else {
                view.setUint32(offset, left);
                view.setUint32(offset + 4, right);
            }
        }

        const { databaseType, description = {}, languages = [], buildEpoch } = this.#options;
        const metadata = new DataSection({ deduplicate: false });
        metadata.add({
            binary_format_major_version: uint16(2),
            binary_format_minor_version: uint16(0),
            build_epoch: uint64(buildEpoch ?? Math.floor(Date.now() / 1000)),
            database_type: databaseType,
            description,
            ip_version: uint16(6),
            languages,
            node_count: uint32(nodeCount),
            record_size: uint16(recordSize),
        });

        const parts = [
            tree,
            new Uint8Array(DATA_SECTION_SEPARATOR),
            data.toBytes(),
            METADATA_MARKER,
            metadata.toBytes(),
        ];
        const out = new Uint8Array(parts.reduce((total, part) => total + part.length, 0));
        let offset = 0;
        for (const part of parts) {
            out.set(part, offset);
            offset += part.length;
        }
        return out;
    }
}
