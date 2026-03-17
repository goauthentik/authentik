/**
 * @file Modal rendering utilities.
 */

import "#elements/modals/ak-modal";

import { AKModal } from "#elements/modals/ak-modal";
import { SlottedTemplateResult } from "#elements/types";
import { isAKElementConstructor } from "#elements/utils/unsafe";

import { html, render } from "lit";

/**
 * Resolves the container element for a dialog, given an optional parent element or selector.
 *
 * If the parent element is not provided or cannot be resolved, the document body is returned.
 *
 * @param ownerDocument The document to query for the parent element. Defaults to the global document.
 * @param parentElement An optional HTMLElement or selector string to use as the dialog container.
 *
 * @returns The resolved container HTMLElement for the dialog.
 */
export function resolveDialogContainer(
    ownerDocument: Document = document,
    parentElement?: HTMLElement | string | null,
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

export interface DialogInit {
    ownerDocument?: Document;
    parentElement?: HTMLElement | string | null;
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
        parentElement = ownerDocument.getElementById("interface-root"),
        closedBy = "any",
        classList = [],
    }: DialogInit = {},
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
export function renderModal(renderable: unknown, init?: DialogInit): Promise<void> {
    return renderDialog(html`<ak-modal>${renderable}</ak-modal>`, init);
}

export type ModalTemplate = (event: Event) => SlottedTemplateResult;
export type InvokerListener = (event: Event) => Promise<void> | void;

/**
 * A utility function that takes either a {@linkcode CustomElementConstructor}
 * or a {@linkcode ModalTemplate} and returns a function that renders the corresponding modal dialog.
 *
 * @param input The input to render as a modal dialog, either a custom element constructor or a function that returns a template result.
 * @param init Initialization options for the modal dialog.
 */
export function asInvoker(renderer: ModalTemplate, init?: DialogInit): InvokerListener;
export function asInvoker(
    Constructor: CustomElementConstructor,
    init?: DialogInit,
): () => Promise<void>;
export function asInvoker(
    input: ModalTemplate | CustomElementConstructor,
    init?: DialogInit,
): (event?: Event) => Promise<void>;
export function asInvoker(
    input: ModalTemplate | CustomElementConstructor,
    init?: DialogInit,
): (event?: Event) => Promise<void> {
    return (event?: Event) => {
        const child = isAKElementConstructor(input)
            ? new input()
            : (input as ModalTemplate)(event!);

        if (child instanceof AKModal) {
            return renderDialog(child, init);
        }

        return renderModal(child, init);
    };
}
