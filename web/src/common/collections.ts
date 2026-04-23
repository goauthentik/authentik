/**
 * Given an array or length, return logical index of the element at the given delta.
 * This is effectively a modulo loop, allowing for positive and negative deltas.
 */
export function torusIndex(lengthLike: number | ArrayLike<number>, delta: number): number {
    const length = typeof lengthLike === "number" ? lengthLike : lengthLike.length;

    if (delta < 0) {
        return (length + delta) % length;
    }

    return ((delta % length) + length) % length;
}

/**
 * Shallow-compare new deps against the previously stored deps.
 *
 * Returns `true` if deps match (i.e. we should skip rebinding).
 * Returns `false` if deps are absent, previously unset, or any value differs.
 */
export function checkIterableShallowEquality(
    newDeps?: unknown[] | null,
    prevDeps?: unknown[] | null,
): boolean {
    if (!newDeps || !prevDeps) return false;
    if (prevDeps.length !== newDeps.length) return false;
    return prevDeps.every((prev, i) => prev === newDeps[i]);
}

/**
 * Shallow-compare new deps against the previously stored deps.
 *
 * Returns `true` if deps match (i.e. we should skip rebinding).
 * Returns `false` if deps are absent, previously unset, or any value differs.
 */
export function checkObjectShallowEquality(
    newDeps?: object | null,
    prevDeps?: object | null,
): boolean {
    if (!newDeps || !prevDeps) {
        return newDeps === prevDeps;
    }
    const newKeys = Object.keys(newDeps);
    const prevKeys = Object.keys(prevDeps);

    if (newKeys.length !== prevKeys.length) return false;

    for (const key of newKeys) {
        if (
            (newDeps as Record<string, unknown>)[key] !== (prevDeps as Record<string, unknown>)[key]
        ) {
            return false;
        }
    }

    return true;
}
