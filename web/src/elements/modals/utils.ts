/**
 * @file Modal rendering utilities.
 */

import "#elements/modals/ak-modal";

import { SlottedTemplateResult } from "#elements/types";
import { isAKElementConstructor } from "#elements/utils/unsafe";

import { html, render } from "lit";

function resolveDialogContainer(
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

export interface RenderDialogInit {
    ownerDocument?: Document;
    parentElement?: HTMLElement | string;
    closedBy?: ClosedBy;
    classList?: string[];
    signal?: AbortSignal;
}

/**
 * Renders a dialog with the given template.
 *
 * @param renderable The template to render inside the dialog.
 * @param init Initialization options for the dialog.
 *
 * @returns A promise that resolves when the dialog is closed.
 */
export function renderDialog(
    renderable: unknown,
    {
        ownerDocument = document,
        signal,
        parentElement = '[data-test-id="interface-root"]',
        closedBy = "any",
        classList = [],
    }: RenderDialogInit = {},
): Promise<void> {
    const dialog = ownerDocument.createElement("dialog");
    dialog.classList.add("ak-c-modal", ...classList);
    dialog.closedBy = closedBy;

    const resolvers = Promise.withResolvers<void>();

    const container = resolveDialogContainer(ownerDocument, parentElement);
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

/**
 * Renders a modal dialog with the given template.
 *
 * @param renderable The template to render inside the modal.
 * @param init Initialization options for the modal.
 * @returns A promise that resolves when the modal is closed.
 */
export function renderModal(renderable: unknown, init?: RenderDialogInit): Promise<void> {
    return renderDialog(html`<ak-modal>${renderable}</ak-modal>`, init);
}

export type ModalChildRenderer = () => SlottedTemplateResult;

/**
 * A utility function that takes either a {@linkcode CustomElementConstructor}
 * or a {@linkcode ModalChildRenderer} and returns a function that renders the corresponding modal dialog.
 *
 * @param input The input to render as a modal dialog, either a custom element constructor or a function that returns a template result.
 * @param init Initialization options for the modal dialog.
 */
export function asModal(
    input: CustomElementConstructor | (() => SlottedTemplateResult),
    init?: RenderDialogInit,
) {
    return () => {
        const child = isAKElementConstructor(input) ? new input() : (input as ModalChildRenderer)();

        renderModal(child, init);
    };
}
