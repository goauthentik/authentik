/**
 * @file Modal and dialog rendering utilities.
 */

import "#elements/dialogs/ak-modal";

import { AKRefreshEvent } from "#common/events";

import { DialogInit } from "#elements/dialogs/shared";
import { RouteChangeEvent } from "#elements/router/events";
import { ifPresent } from "#elements/utils/attributes";

import { html, render } from "lit";

//#region Rendering

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

function setDialogCountAttribute(delta: number, ownerDocument: Document = document): void {
    const { dataset } = ownerDocument.documentElement;

    const currentCount = parseInt(dataset.dialogCount || "0", 10);
    const nextCount = Math.max(0, currentCount + delta);

    if (nextCount === 0) {
        delete dataset.dialogCount;
    } else {
        dataset.dialogCount = nextCount.toString();
    }
}

/**
 * Renders a dialog with the given template.
 *
 * @param renderable The template to render inside the dialog.
 * @param init Initialization options for the dialog.
 *
 * @returns A promise that resolves when the dialog is closed.
 *
 * @remarks
 * In the context of the {@link HTMLDialogElement}, we distinguish between __modal__
 * dialogs, which are shown using the `showModal()` method and block interaction with the rest of the page,
 * and __non-modal__ dialogs, which are shown using the `show()` method and allow interaction with the rest of the page.
 *
 * For almost all use cases in authentik, dialogs are modal. However, {@linkcode AKModal}
 * (and its implementors) are what a developer would typically consider to be the modal itself.
 *
 * Here be dragons! The delination between "dialog" and "modal" is not based on
 * the presence of a backdrop or blocking behavior, but rather on the underlying HTML elements
 *  and method used to display it.
 *
 * **Incorrect usage can impact accessibility significantly.**
 */
export function renderDialog(
    renderable: unknown,
    {
        ownerDocument = document,
        signal,
        parentElement = ownerDocument.getElementById("interface-root"),
        invokerElement,
        closedBy = "any",
        classList = [],
        onDispose,
    }: DialogInit = {},
): Promise<void> {
    const eventAbortController = new AbortController();

    const dialog = ownerDocument.createElement("dialog");
    dialog.classList.add("ak-c-dialog", ...classList);
    dialog.closedBy = closedBy;
    dialog.part = "dialog";

    const messageContainer = ownerDocument.createElement("ak-message-container");
    messageContainer.alignment = "bottom-left";

    dialog.appendChild(messageContainer);

    const resolvers = Promise.withResolvers<void>();

    const container = resolveDialogContainer(ownerDocument, parentElement);
    const shadowRoot = container.shadowRoot ?? container;

    shadowRoot.appendChild(dialog);

    const dispose = (event?: Event) => {
        const { returnValue } = dialog;

        if (returnValue === "submitted") {
            const dispatcher = invokerElement ?? dialog;
            dispatcher.dispatchEvent(new AKRefreshEvent());
        }

        dialog.close();
        dialog.remove();
        resolvers.resolve();

        setDialogCountAttribute(-1, ownerDocument);

        onDispose?.(event);
        eventAbortController.abort();
    };

    window.addEventListener(RouteChangeEvent.eventName, dispose, {
        passive: true,
        once: true,
        signal: eventAbortController.signal,
    });

    dialog.addEventListener("close", dispose, {
        passive: true,
        once: true,
    });

    signal?.addEventListener("abort", dispose, {
        passive: true,
        once: true,
    });

    render(renderable, dialog);

    setDialogCountAttribute(1, ownerDocument);

    return resolvers.promise;
}

/**
 * Renders a modal dialog with the given template.
 *
 * @param renderable The template to render inside the modal.
 * @param init Initialization options for the modal.
 *
 * @returns A promise that resolves when the modal is closed.
 */
export function renderModal(renderable: unknown, init?: DialogInit): Promise<void> {
    return renderDialog(
        html`<ak-modal size=${ifPresent(init?.size)}>${renderable}</ak-modal>`,
        init,
    );
}

//#endregion
