import { LitElement } from "lit";

/**
 * Returns the root interface element of the page.
 *
 * @param ownerDocument The document to query for the interface element. Defaults to the global document.
 */
export function resolveInterface<T extends HTMLElement = LitElement>(ownerDocument = document): T {
    const element = ownerDocument.getElementById("interface-root") as T | null;

    if (!element) {
        throw new Error(
            `Could not find root interface element. Was this element added before the parent interface element?`,
        );
    }

    return element;
}
