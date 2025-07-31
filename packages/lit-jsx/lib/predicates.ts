/**
 * Type predicate to check if a given value is a custom element constructor.
 */
export function isElementFactory(elementLike: unknown): elementLike is Lit.ElementFactoryLike {
    return typeof elementLike === "function" && elementLike.prototype instanceof HTMLElement;
}

/**
 * Type predicate to check if a given value is a custom element constructor.
 */
export function isCustomElementConstructor<P = unknown, T extends HTMLElement = HTMLElement>(
    elementLike: Lit.ElementFactoryLike<P>,
): elementLike is Lit.CustomElementConstructor<P, T> {
    return elementLike.prototype instanceof HTMLElement;
}
