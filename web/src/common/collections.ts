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
