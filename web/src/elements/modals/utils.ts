/**
 * @file Modal rendering utilities.
 */

import { render } from "lit";

function resolveModalContainer(
    ownerDocument: Document,
    parentElement?: HTMLElement | string,
): HTMLElement {
    if (parentElement instanceof HTMLElement) {
        return parentElement;
    }

    if (typeof parentElement === "string") {
        const resolvedElement = ownerDocument.querySelector(parentElement);

        if (resolvedElement instanceof HTMLElement) {
            return resolvedElement;
        }
    }

    return ownerDocument.body;
}

export interface RenderModalInit {
    ownerDocument?: Document;
    parentElement?: HTMLElement | string;
    closedBy?: ClosedBy;
    classList?: string[];
    signal?: AbortSignal;
}

/**
 * Renders a modal dialog with the given template.
 *
 * @param renderable The template to render inside the modal.
 * @param init Initialization options for the modal.
 *
 * @returns A promise that resolves when the modal is closed.
 */
export function renderModal(
    renderable: unknown,
    {
        ownerDocument = document,
        signal,
        parentElement = '[data-test-id="interface-root"]',
        closedBy = "any",
        classList = [],
    }: RenderModalInit = {},
): Promise<void> {
    const dialog = ownerDocument.createElement("dialog");
    dialog.classList.add("ak-c-modal", ...classList);
    dialog.closedBy = closedBy;

    const resolvers = Promise.withResolvers<void>();

    const container = resolveModalContainer(ownerDocument, parentElement);
    const shadowRoot = container.shadowRoot ?? container;

    shadowRoot.appendChild(dialog);

    const dispose = () => {
        dialog.close();
        dialog.remove();
        resolvers.resolve();
    };

    dialog.addEventListener("close", dispose);

    signal?.addEventListener("abort", dispose);

    render(renderable, dialog);

    return resolvers.promise;
}
