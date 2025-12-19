/**
 * @file Modal rendering utilities.
 */

import { render } from "lit";

export interface RenderModalInit {
    ownerDocument?: Document;
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
    { ownerDocument = document, signal }: RenderModalInit = {},
): Promise<void> {
    const dialog = ownerDocument.createElement("dialog");
    dialog.classList.add("ak-c-modal");
    const resolvers = Promise.withResolvers<void>();

    ownerDocument.body.appendChild(dialog);

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
