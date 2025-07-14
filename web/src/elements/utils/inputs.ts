import type { LitElement } from "lit";

/**
 * An HTML element with a name attribute.
 */
export type NamedElement<T = Element> = T & {
    name: string;
};

export function isNamedElement(element: Element): element is NamedElement {
    if (!(element instanceof HTMLElement)) {
        return false;
    }

    return "name" in element.attributes;
}

declare global {
    interface HTMLElementTagNameMap {
        "[name]": NamedElement<HTMLElement>;
    }
}

/**
 * Create a map of files provided by input elements within the given iterable.
 */
export function createFileMap<T extends PropertyKey = PropertyKey>(
    fileInputParents?: Iterable<NamedElement<LitElement>> | null,
): Map<T, File> {
    const record = new Map<T, File>();

    for (const element of fileInputParents || []) {
        element.requestUpdate();

        const inputElement = element.querySelector<HTMLInputElement>("input[type=file]");

        if (!inputElement) continue;

        const file = inputElement.files?.[0];
        const name = element.name;

        if (!file || !name) continue;

        record.set(name as T, file);
    }

    return record;
}
