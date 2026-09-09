import { ifDefined } from "lit/directives/if-defined.js";

/**
 * A variant of {@linkcode ifDefined} which allows for truthy values to apply
 * an attribute value.
 */
export function ifPresent<T = unknown>(predicateLike: unknown, attributeValue?: T) {
    return ifDefined(
        predicateLike ? attributeValue || predicateLike || undefined : undefined,
    ) as NonNullable<T>;
}

/**
 * Given a list of parts and an optional prefix,
 * returns a string suitable for use in an `exportparts` attribute.
 *
 * This allows for easy re-exporting of multiple parts with a common prefix.
 *
 * @example
 * ```ts
 * const parts = exportParts(["header", "footer", "item"], "my-prefix");
 * // parts === "header:my-prefix-header, footer:my-prefix-footer, item:my-prefix-item"
 * ```
 *
 * @param prefix The prefix to apply to each part.
 * @param parts An iterable of part names to export.
 * @returns A string suitable for use in an `exportparts` attribute.
 */
export function exportParts<T extends Iterable<string>, P extends string>(
    parts: T,
    prefix?: P,
): string {
    if (!prefix) {
        return Array.from(parts).join(", ");
    }

    return Array.from(parts)
        .map((part) => `${part}:${prefix}-${part}`)
        .join(", ");
}
