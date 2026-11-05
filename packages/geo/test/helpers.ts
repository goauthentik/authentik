import { expect } from "vitest";

/**
 * Narrow away the `null | undefined` that lookups (`find`, `Map.get`, a
 * parser that rejects bad input) carry, failing the test if it is actually
 * absent. Keeps assertions readable instead of scattering `!` through them.
 */
export function required<T>(value: T | null | undefined, what = "value"): T {
    if (value === null || value === undefined) {
        expect.unreachable(`expected ${what} to be present`);
    }

    return value;
}
