import type { LitElement } from "lit";

/**
 * An HTML element with a name attribute.
 */
export type NamedElement<T = Element> = T & {
    name: string;
};

/**
 * Type predicate to check if an element currently has a `name` attribute.
 *
 * @see {@linkcode isNameableElement} to check if an element is nameable.
 */
export function isNamedElement(element: Element): element is NamedElement {
    if (!(element instanceof HTMLElement)) {
        return false;
    }

    return "name" in element.attributes;
}

/**
 * A set of elements that can be named, i.e. have a `name` attribute.
 *
 * @deprecated This should be replaced with a less brittle approach.
 */
const NameableElements = new Set([
    "INPUT",
    "TEXTAREA",
    "SELECT",
    "AK-CODEMIRROR",
    "AK-CHIP-GROUP",
    "AK-SEARCH-SELECT",
    "AK-RADIO",
]);

/**
 * Type predicate to check if an element is nameable.
 *
 * @see {@linkcode isNamedElement} to check if an element currently has a `name` attribute.
 */
export function isNameableElement(element: Element): element is NamedElement {
    if (!(element instanceof HTMLElement)) {
        return false;
    }

    return NameableElements.has(element.tagName);
}

/**
 * Create a map of files provided by input elements within the given iterable.
 */
export function createFileMap<T extends PropertyKey = PropertyKey>(
    fileInputParents?: Iterable<LitElement> | null,
): Map<T, File> {
    const record = new Map<T, File>();

    for (const element of fileInputParents || []) {
        element.requestUpdate();

        if (!isNamedElement(element)) continue;

        const inputElement = element.querySelector<HTMLInputElement>("input[type=file]");

        if (!inputElement) continue;

        const file = inputElement.files?.[0];
        const name = element.name as T;

        if (!file || !name) continue;

        record.set(name, file);
    }

    return record;
}
