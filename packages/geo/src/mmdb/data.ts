/**
 * @file Data section encoding for the MaxMind DB format.
 * @see https://maxmind.github.io/MaxMind-DB/
 */

type IntegerType = "uint16" | "uint32" | "uint64" | "uint128" | "int32";

/**
 * An integer encoded as a specific MMDB type. Plain numbers encode as `uint32` or `double`.
 */
export class MMDBInteger {
    public readonly type: IntegerType;
    public readonly value: bigint;

    public constructor(type: IntegerType, value: number | bigint) {
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

/**
 * Highest type ID that fits in the control byte. Higher IDs follow it in an extra byte.
 */
const MAX_INLINE_TYPE_ID = 7;

const INTEGER_FORMATS: Record<IntegerType, { typeID: number; bits: number; signed: boolean }> = {
    uint16: { typeID: TypeID.Uint16, bits: 16, signed: false },
    uint32: { typeID: TypeID.Uint32, bits: 32, signed: false },
    uint64: { typeID: TypeID.Uint64, bits: 64, signed: false },
    uint128: { typeID: TypeID.Uint128, bits: 128, signed: false },
    int32: { typeID: TypeID.Int32, bits: 32, signed: true },
};

/**
 * Largest size stored directly in the control byte.
 */
const MAX_INLINE_SIZE = 28;

/**
 * Size encodings, smallest first. `marker` goes in the control byte and `bias` is subtracted from
 * the size written in the following `bytes`.
 */
const SIZE_FORMATS = [
    { marker: 29, bias: 29, bytes: 1 },
    { marker: 30, bias: 285, bytes: 2 },
    { marker: 31, bias: 65_821, bytes: 3 },
] as const;

/**
 * Pointer encodings, smallest first. The format's index is the pointer's size field, and `bias`
 * is subtracted from the offset written in the following `bytes`.
 */
const POINTER_FORMATS = [
    { bias: 0, bytes: 1 },
    { bias: 2048, bytes: 2 },
    { bias: 526_336, bytes: 3 },
    { bias: 0, bytes: 4 },
] as const;

/**
 * Shortest string worth deduplicating. Shorter strings are smaller than a pointer to them.
 */
const MIN_POINTER_STRING_BYTES = 4;

const utf8 = new TextEncoder();

/**
 * A stable string identity for a value, used to deduplicate records and data.
 */
export function valueKey(value: MMDBValue): string {
    return JSON.stringify(value, (_key, item: unknown) =>
        item instanceof MMDBInteger ? `${item.type}:${item.value}` : item,
    );
}

function toBigEndian(value: number, length: number): number[] {
    return Array.from(
        { length },
        (_, index) => Math.floor(value / 256 ** (length - 1 - index)) % 256,
    );
}

/**
 * Appends values to an MMDB data section. Repeated strings, arrays and maps are written once and
 * referenced by pointer afterwards.
 */
export class DataSection {
    #buffer = new Uint8Array(1 << 16);
    #length = 0;
    #offsets = new Map<string, number>();
    readonly #deduplicate: boolean;

    public constructor({ deduplicate = true } = {}) {
        this.#deduplicate = deduplicate;
    }

    public get length(): number {
        return this.#length;
    }

    public toBytes(): Uint8Array {
        return this.#buffer.subarray(0, this.#length);
    }

    /**
     * Write a value and return the offset of its encoding. A value written before returns its
     * earlier offset.
     */
    public add(value: MMDBValue): number {
        const key = this.#cacheKey(value);
        const cached = key ? this.#offsets.get(key) : null;

        if (typeof cached === "number") return cached;

        const offset = this.#length;

        this.#write(value);

        if (key) this.#offsets.set(key, offset);

        return offset;
    }

    /**
     * Write a nested value, as a pointer when it was written before.
     */
    #encode(value: MMDBValue): void {
        const key = this.#cacheKey(value);
        const cached = key ? this.#offsets.get(key) : null;

        if (typeof cached === "number") {
            this.#writePointer(cached);
        } else {
            this.add(value);
        }
    }

    #cacheKey(value: MMDBValue): string | null {
        if (!this.#deduplicate || value instanceof MMDBInteger) return null;

        if (typeof value === "string") {
            return utf8.encode(value).length < MIN_POINTER_STRING_BYTES ? null : `s${value}`;
        }

        return typeof value === "object" ? `o${valueKey(value)}` : null;
    }

    #write(value: MMDBValue): void {
        if (value instanceof MMDBInteger) return this.#writeInteger(value);
        if (Array.isArray(value)) return this.#writeArray(value as readonly MMDBValue[]);

        switch (typeof value) {
            case "string":
                return this.#writeString(value);
            case "number":
                return this.#writeNumber(value);
            case "boolean":
                return this.#writeControl(TypeID.Boolean, value ? 1 : 0);
            default:
                return this.#writeMap(value as { readonly [key: string]: MMDBValue });
        }
    }

    #writeString(value: string): void {
        const bytes = utf8.encode(value);

        this.#writeControl(TypeID.String, bytes.length);
        this.#writeBytes(bytes);
    }

    #writeNumber(value: number): void {
        if (Number.isInteger(value) && value >= 0 && value <= 0xffff_ffff) {
            return this.#writeInteger(uint32(value));
        }

        const bytes = new Uint8Array(8);

        new DataView(bytes.buffer).setFloat64(0, value);
        this.#writeControl(TypeID.Double, bytes.length);
        this.#writeBytes(bytes);
    }

    #writeInteger({ type, value }: MMDBInteger): void {
        const { typeID, bits, signed } = INTEGER_FORMATS[type];
        const min = signed ? -(1n << BigInt(bits - 1)) : 0n;
        const max = (1n << BigInt(signed ? bits - 1 : bits)) - 1n;

        if (value < min || value > max) {
            throw new RangeError(`${value} does not fit in ${type}`);
        }

        const bytes: number[] = [];

        for (let rest = BigInt.asUintN(bits, value); rest > 0n; rest >>= 8n) {
            bytes.unshift(Number(rest & 0xffn));
        }

        this.#writeControl(typeID, bytes.length);
        this.#writeBytes(bytes);
    }

    #writeArray(value: readonly MMDBValue[]): void {
        this.#writeControl(TypeID.Array, value.length);

        for (const item of value) {
            this.#encode(item);
        }
    }

    #writeMap(value: { readonly [key: string]: MMDBValue }): void {
        const entries = Object.entries(value);

        this.#writeControl(TypeID.Map, entries.length);

        for (const [key, item] of entries) {
            this.#encode(key);
            this.#encode(item);
        }
    }

    #writeControl(typeID: number, size: number): void {
        const inline = typeID <= MAX_INLINE_TYPE_ID;
        const control = inline ? typeID << 5 : 0;
        const extendedType = inline ? [] : [typeID - MAX_INLINE_TYPE_ID];

        if (size <= MAX_INLINE_SIZE) {
            return this.#writeBytes([control | size, ...extendedType]);
        }

        const format = SIZE_FORMATS.find(({ bias, bytes }) => size < bias + 256 ** bytes);

        if (!format) {
            throw new RangeError(`Size ${size} is too large to encode`);
        }

        this.#writeBytes([
            control | format.marker,
            ...extendedType,
            ...toBigEndian(size - format.bias, format.bytes),
        ]);
    }

    #writePointer(offset: number): void {
        const sizeField = POINTER_FORMATS.findIndex(
            ({ bias, bytes }) => offset < bias + 2 ** (bytes * 8 + 3),
        );
        const { bias, bytes } = POINTER_FORMATS[sizeField]!;
        const rest = offset - bias;
        // The 3 bits above `bytes` go in the control byte.
        const high = Math.floor(rest / 256 ** bytes) % 8;

        this.#writeBytes([
            (TypeID.Pointer << 5) | (sizeField << 3) | high,
            ...toBigEndian(rest, bytes),
        ]);
    }

    #writeBytes(bytes: ArrayLike<number>): void {
        this.#ensure(bytes.length);
        this.#buffer.set(bytes, this.#length);
        this.#length += bytes.length;
    }

    #ensure(extra: number): void {
        const required = this.#length + extra;

        if (required <= this.#buffer.length) return;

        let size = this.#buffer.length * 2;

        while (size < required) size *= 2;

        const next = new Uint8Array(size);

        next.set(this.#buffer.subarray(0, this.#length));
        this.#buffer = next;
    }
}
