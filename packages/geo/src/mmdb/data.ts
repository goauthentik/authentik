/**
 * @file Data section encoding for the MaxMind DB format.
 * @see https://maxmind.github.io/MaxMind-DB/
 */

type IntegerType = "uint16" | "uint32" | "uint64" | "uint128" | "int32";

/**
 * An integer pinned to a specific MMDB type. Plain numbers encode as `uint32` (or `double` when
 * fractional), which is wrong for metadata fields readers type-check.
 */
export class MMDBInteger {
    readonly type: IntegerType;
    readonly value: bigint;

    constructor(type: IntegerType, value: number | bigint) {
        this.type = type;
        this.value = BigInt(value);
    }
}

export type MMDBValue =
    | string
    | number
    | boolean
    | MMDBInteger
    | readonly MMDBValue[]
    | { readonly [key: string]: MMDBValue };

export const uint16 = (value: number) => new MMDBInteger("uint16", value);
export const uint32 = (value: number) => new MMDBInteger("uint32", value);
export const uint64 = (value: number | bigint) => new MMDBInteger("uint64", value);
export const int32 = (value: number) => new MMDBInteger("int32", value);

const TypeID = {
    Pointer: 1,
    String: 2,
    Double: 3,
    Uint16: 5,
    Uint32: 6,
    Map: 7,
    Int32: 8,
    Uint64: 9,
    Uint128: 10,
    Array: 11,
    Boolean: 14,
} as const;

const INTEGER_TYPE_IDS: Record<IntegerType, number> = {
    uint16: TypeID.Uint16,
    uint32: TypeID.Uint32,
    uint64: TypeID.Uint64,
    uint128: TypeID.Uint128,
    int32: TypeID.Int32,
};

const INTEGER_MAX_BYTES: Record<IntegerType, number> = {
    uint16: 2,
    uint32: 4,
    uint64: 8,
    uint128: 16,
    int32: 4,
};

/** A stable string identity for a value, used to deduplicate records and data. */
export function valueKey(value: MMDBValue): string {
    return JSON.stringify(value, (_key, item: unknown) =>
        item instanceof MMDBInteger ? `${item.type}:${item.value}` : item,
    );
}

const utf8 = new TextEncoder();

/** Strings shorter than a pointer aren't worth deduplicating. */
const MIN_POINTER_STRING_BYTES = 4;

/**
 * Appends values to an MMDB data section. Repeated strings, arrays and maps are written once and
 * referenced by pointer afterwards.
 */
export class DataSection {
    #buffer = new Uint8Array(1 << 16);
    #length = 0;
    #offsets = new Map<string, number>();
    readonly #deduplicate: boolean;

    constructor({ deduplicate = true } = {}) {
        this.#deduplicate = deduplicate;
    }

    get length(): number {
        return this.#length;
    }

    toBytes(): Uint8Array {
        return this.#buffer.subarray(0, this.#length);
    }

    /**
     * Write a value and return the offset of its encoding. A value that was written before returns
     * the earlier offset without writing anything, so the result always points at real data rather
     * than at a pointer.
     */
    add(value: MMDBValue): number {
        const key = this.#cacheKey(value);
        const existing = key === null ? undefined : this.#offsets.get(key);
        if (existing !== undefined) {
            return existing;
        }
        const offset = this.#length;
        this.#write(value);
        if (key !== null) {
            this.#offsets.set(key, offset);
        }
        return offset;
    }

    /** Write a nested value, as a pointer when it was written before. */
    #encode(value: MMDBValue): void {
        const key = this.#cacheKey(value);
        const existing = key === null ? undefined : this.#offsets.get(key);
        if (existing === undefined) {
            this.add(value);
        } else {
            this.#writePointer(existing);
        }
    }

    #cacheKey(value: MMDBValue): string | null {
        if (!this.#deduplicate) {
            return null;
        }
        if (typeof value === "string") {
            return utf8.encode(value).length < MIN_POINTER_STRING_BYTES ? null : `s${value}`;
        }
        if (typeof value === "object" && !(value instanceof MMDBInteger)) {
            return `o${valueKey(value)}`;
        }
        return null;
    }

    #write(value: MMDBValue): void {
        if (typeof value === "string") {
            const bytes = utf8.encode(value);
            this.#writeControl(TypeID.String, bytes.length);
            this.#writeBytes(bytes);
        } else if (typeof value === "boolean") {
            this.#writeControl(TypeID.Boolean, value ? 1 : 0);
        } else if (typeof value === "number") {
            if (Number.isInteger(value) && value >= 0 && value <= 0xffff_ffff) {
                this.#writeInteger(uint32(value));
            } else {
                const bytes = new Uint8Array(8);
                new DataView(bytes.buffer).setFloat64(0, value);
                this.#writeControl(TypeID.Double, 8);
                this.#writeBytes(bytes);
            }
        } else if (value instanceof MMDBInteger) {
            this.#writeInteger(value);
        } else if (Array.isArray(value)) {
            this.#writeControl(TypeID.Array, value.length);
            for (const item of value as readonly MMDBValue[]) {
                this.#encode(item);
            }
        } else {
            const entries = Object.entries(value);
            this.#writeControl(TypeID.Map, entries.length);
            for (const [key, item] of entries) {
                this.#encode(key);
                this.#encode(item);
            }
        }
    }

    #writeInteger({ type, value }: MMDBInteger): void {
        const max = INTEGER_MAX_BYTES[type];
        let unsigned = value;
        if (type === "int32") {
            if (value < -0x8000_0000n || value > 0x7fff_ffffn) {
                throw new RangeError(`${value} does not fit in int32`);
            }
            unsigned = BigInt.asUintN(32, value);
        } else if (value < 0n || value >= 1n << BigInt(max * 8)) {
            throw new RangeError(`${value} does not fit in ${type}`);
        }
        const bytes: number[] = [];
        for (let rest = unsigned; rest > 0n; rest >>= 8n) {
            bytes.unshift(Number(rest & 0xffn));
        }
        // Negative int32 values need all four bytes to keep the sign bit.
        if (type === "int32" && value < 0n) {
            while (bytes.length < 4) bytes.unshift(0xff);
        }
        this.#writeControl(INTEGER_TYPE_IDS[type], bytes.length);
        this.#writeBytes(bytes);
    }

    #writeControl(type: number, size: number): void {
        const header: number[] = [];
        let control = type <= 7 ? type << 5 : 0;
        let sizeBytes: number[] = [];
        if (size < 29) {
            control |= size;
        } else if (size < 29 + 256) {
            control |= 29;
            sizeBytes = [size - 29];
        } else if (size < 285 + 65_536) {
            control |= 30;
            const rest = size - 285;
            sizeBytes = [rest >> 8, rest & 0xff];
        } else {
            control |= 31;
            const rest = size - 65_821;
            sizeBytes = [(rest >> 16) & 0xff, (rest >> 8) & 0xff, rest & 0xff];
        }
        header.push(control);
        if (type > 7) {
            header.push(type - 7);
        }
        this.#writeBytes([...header, ...sizeBytes]);
    }

    #writePointer(offset: number): void {
        const base = TypeID.Pointer << 5;
        if (offset < 1 << 11) {
            this.#writeBytes([base | (offset >> 8), offset & 0xff]);
        } else if (offset < (1 << 19) + 2048) {
            const rest = offset - 2048;
            this.#writeBytes([base | (1 << 3) | (rest >> 16), (rest >> 8) & 0xff, rest & 0xff]);
        } else if (offset < (1 << 27) + 526_336) {
            const rest = offset - 526_336;
            this.#writeBytes([
                base | (2 << 3) | (rest >> 24),
                (rest >> 16) & 0xff,
                (rest >> 8) & 0xff,
                rest & 0xff,
            ]);
        } else {
            this.#writeBytes([
                base | (3 << 3),
                (offset >>> 24) & 0xff,
                (offset >> 16) & 0xff,
                (offset >> 8) & 0xff,
                offset & 0xff,
            ]);
        }
    }

    #writeBytes(bytes: ArrayLike<number>): void {
        this.#ensure(bytes.length);
        this.#buffer.set(bytes, this.#length);
        this.#length += bytes.length;
    }

    #ensure(extra: number): void {
        if (this.#length + extra <= this.#buffer.length) {
            return;
        }
        let size = this.#buffer.length * 2;
        while (size < this.#length + extra) size *= 2;
        const next = new Uint8Array(size);
        next.set(this.#buffer.subarray(0, this.#length));
        this.#buffer = next;
    }
}
