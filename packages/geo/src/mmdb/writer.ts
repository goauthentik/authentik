/**
 * @file Writer for MaxMind DB (`.mmdb`) files, the format authentik's GeoIP and ASN readers load.
 * @see https://maxmind.github.io/MaxMind-DB/
 */

import { DataSection, type MMDBValue, uint16, uint32, uint64, valueKey } from "./data.ts";
import { bitAt, IPV4_OFFSET_BITS, type Network, parseNetwork } from "./network.ts";

export interface MMDBWriterOptions {
    /**
     * Name of the database's contents, stored in the metadata as `database_type`. Readers use it to
     * decide which lookups the database supports, e.g. geoip2's ASN lookups require `GeoLite2-ASN`
     * in the name.
     */
    databaseType: string;

    /**
     * Human-readable descriptions, keyed by language code.
     */
    description?: Record<string, string>;

    /**
     * Language codes the database's records contain names in.
     */
    languages?: string[];

    /**
     * Build time in seconds since the epoch. Defaults to now.
     */
    buildEpoch?: number;
}

const METADATA_MARKER = Uint8Array.of(0xab, 0xcd, 0xef, ...new TextEncoder().encode("MaxMind.com"));
const DATA_SECTION_SEPARATOR = 16;

/**
 * IPv6 networks that resolve to the IPv4 subtree: IPv4-mapped and 6to4 addresses.
 */
const IPV4_ALIASES = ["::ffff:0:0/96", "2002::/16"].map(parseNetwork);

/**
 * Child slot value for "no data". Other slots hold a node index, or `-(record + 1)` for a record.
 */
const EMPTY = 0;

type RecordSize = 24 | 28 | 32;

const RECORD_SIZES: readonly RecordSize[] = [24, 28, 32];

function setUint24(view: DataView, offset: number, value: number): void {
    view.setUint16(offset, value >>> 8);
    view.setUint8(offset + 2, value & 0xff);
}

/**
 * Write one search tree node's left and right records at `offset`, per record size.
 */
const NODE_WRITERS: Record<
    RecordSize,
    (view: DataView, offset: number, left: number, right: number) => void
> = {
    24: (view, offset, left, right) => {
        setUint24(view, offset, left);
        setUint24(view, offset + 3, right);
    },
    28: (view, offset, left, right) => {
        setUint24(view, offset, left & 0xff_ffff);
        view.setUint8(offset + 3, ((left >>> 24) << 4) | (right >>> 24));
        setUint24(view, offset + 4, right & 0xff_ffff);
    },
    32: (view, offset, left, right) => {
        view.setUint32(offset, left);
        view.setUint32(offset + 4, right);
    },
};

function concatBytes(parts: readonly Uint8Array[]): Uint8Array {
    const out = new Uint8Array(parts.reduce((total, part) => total + part.length, 0));
    let offset = 0;

    for (const part of parts) {
        out.set(part, offset);
        offset += part.length;
    }

    return out;
}

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

        this.#set(address, bits, -(this.#recordID(record) + 1));
    }

    public toBytes(): Uint8Array {
        this.#collapse(0);
        this.#aliasIPv4();

        const { order, nodes } = this.#numberNodes();
        const data = new DataSection();
        const offsets = this.#records.map((record) => data.add(record));
        const recordValue = (child: number): number => {
            if (child > 0) return order[child]!;
            if (child === EMPTY) return nodes.length;

            return nodes.length + DATA_SECTION_SEPARATOR + offsets[-child - 1]!;
        };

        const maxValue = nodes.length + DATA_SECTION_SEPARATOR + data.length;
        const recordSize = RECORD_SIZES.find((size) => maxValue < 2 ** size);

        if (!recordSize) {
            throw new RangeError("Database is too large for a 32-bit record size");
        }

        const nodeBytes = recordSize / 4;
        const tree = new Uint8Array(nodes.length * nodeBytes);
        const view = new DataView(tree.buffer);
        const writeNode = NODE_WRITERS[recordSize];

        for (const node of nodes) {
            writeNode(
                view,
                order[node]! * nodeBytes,
                recordValue(this.#children[node * 2]!),
                recordValue(this.#children[node * 2 + 1]!),
            );
        }

        return concatBytes([
            tree,
            new Uint8Array(DATA_SECTION_SEPARATOR),
            data.toBytes(),
            METADATA_MARKER,
            this.#metadata(nodes.length, recordSize),
        ]);
    }

    #recordID(record: MMDBValue): number {
        const key = valueKey(record);
        const existing = this.#recordIndex.get(key);

        if (typeof existing === "number") return existing;

        const recordID = this.#records.push(record) - 1;

        this.#recordIndex.set(key, recordID);

        return recordID;
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
     * Point the IPv4 aliases at the IPv4 subtree, when there is one.
     */
    #aliasIPv4(): void {
        let ipv4Root = 0;

        for (let depth = 0; depth < IPV4_OFFSET_BITS; depth++) {
            ipv4Root = this.#children[ipv4Root * 2]!;

            if (ipv4Root <= 0) break;
        }

        if (ipv4Root === EMPTY) return;

        for (const alias of IPV4_ALIASES) {
            this.#set(alias.address, alias.bits, ipv4Root);
        }
    }

    /**
     * Number the reachable nodes breadth first. The IPv4 aliases reach the same subtree twice.
     */
    #numberNodes(): { order: Int32Array; nodes: number[] } {
        const order = new Int32Array(this.#nodeCount).fill(-1);
        const nodes = [0];

        order[0] = 0;

        for (let index = 0; index < nodes.length; index++) {
            for (const side of [0, 1]) {
                const child = this.#children[nodes[index]! * 2 + side]!;

                if (child > 0 && order[child] === -1) {
                    order[child] = nodes.length;
                    nodes.push(child);
                }
            }
        }

        return { order, nodes };
    }

    #metadata(nodeCount: number, recordSize: RecordSize): Uint8Array {
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

        return metadata.toBytes();
    }
}
