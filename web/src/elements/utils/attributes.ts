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
