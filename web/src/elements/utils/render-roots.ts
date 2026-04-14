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

/**
 * Finds the topmost element visible to the user, typically a dialog or the body.
 *
 * @param ownerDocument The document to query. Defaults to the global document.
 */
export function findTopmost(ownerDocument = document): HTMLElement {
    const interfaceElement = resolveInterface(ownerDocument);

    const dialogs = interfaceElement.renderRoot.querySelectorAll<HTMLDialogElement>("dialog[open]");
    return dialogs.length ? dialogs[dialogs.length - 1] : ownerDocument.body;
}

/**
 * Given a node, finds the nearest parent element, traversing through shadow DOM and document fragments if necessary.
 *
 * @param node The node to find the nearest parent element for.
 */
export function findClosestHost<T extends Element = Element | HTMLElement>(
    node: Node | ShadowRoot | DocumentFragment | null,
): T | null {
    let current = node;

    while (current) {
        if (current instanceof Element && current.parentElement instanceof Element) {
            return current.parentElement as unknown as T;
        }

        if (current.parentNode instanceof ShadowRoot) {
            return current.parentNode.host as T;
        }

        if (current.parentNode instanceof DocumentFragment) {
            current = current.parentNode;
            continue;
        }

        return null;
    }

    return null;
}

/**
 * Given a node, finds the nearest parent element that matches the provided predicate, traversing through shadow DOM and document fragments if necessary.
 *
 * @param node The node to find the nearest parent element for.
 * @param predicate A function that takes an element and returns a boolean indicating whether it matches the desired criteria.
 */
export function findClosestHostMatch<T extends Element = Element | HTMLElement>(
    node: Node,
    predicate: (element: Element) => boolean,
): T | null {
    let current = findClosestHost(node);

    while (current) {
        if (predicate(current)) {
            return current as unknown as T;
        }

        current = findClosestHost(current);
    }

    return null;
}

/**
 * Given a node, finds the nearest parent dialog element.
 *
 * @see {@linkcode findClosestHostMatch} for the underlying implementation.
 *
 * @param node The node to find the nearest parent dialog for.
 */
export function findNearestDialog(node: Node): HTMLDialogElement | null {
    return findClosestHostMatch(node, (element): element is HTMLDialogElement => {
        return element instanceof HTMLDialogElement;
    });
}
