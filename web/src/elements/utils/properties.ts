import { PropertyDeclaration } from "lit";

/**
 * A helper function for Lit's `hasChanged` property option to detect previous values.
 *
 * This is particularly useful when a property binding is used, and you want to
 * avoid triggering updates on initial assignment.
 */
export function ifPreviousValue<T = unknown>(this: unknown, value: T, oldValue: T): boolean {
    return !!(typeof oldValue !== "undefined" && oldValue !== value);
}

/**
 * A default property declaration for properties that are only bound,
 * and should not reflect to attributes or have other special behavior.
 */
export const onlyBinding: PropertyDeclaration<unknown> = {
    attribute: false,
    useDefault: true,
    hasChanged: ifPreviousValue,
};
