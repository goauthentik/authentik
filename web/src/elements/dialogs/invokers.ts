import { AKModal } from "#elements/dialogs/ak-modal";
import { DialogInit } from "#elements/dialogs/shared";
import { renderDialog, renderModal } from "#elements/dialogs/utils";
import { SlottedTemplateResult } from "#elements/types";
import { isAKElementConstructor } from "#elements/utils/unsafe";

export type ModalTemplate = (event: Event) => SlottedTemplateResult;

export type InvokerListener = (event: Event) => Promise<void> | void;

/**
 * A utility function that takes a {@linkcode ModalTemplate} and returns
 * a function that renders the corresponding modal dialog when invoked.
 *
 * @param renderer A function that returns a template result to render inside the modal dialog.
 * @param init Initialization options for the modal dialog.
 */
export function asInvoker(renderer: ModalTemplate, init?: DialogInit): InvokerListener;
/**
 * A utility function that takes a {@linkcode CustomElementConstructor} and returns
 * a function that renders the corresponding modal dialog when invoked.
 *
 * @param Constructor A custom element constructor or a function that returns a template result.
 * @param init Initialization options for the modal dialog.
 */
export function asInvoker(
    Constructor: CustomElementConstructor,
    init?: DialogInit,
): () => Promise<void>;
/**
 * A utility function that takes either a {@linkcode CustomElementConstructor}
 * or a {@linkcode ModalTemplate} and returns a function that renders the corresponding modal dialog.
 *
 * @param factory The input to render as a modal dialog, either a custom element constructor or a function that returns a template result.
 * @param init Initialization options for the modal dialog.
 */
export function asInvoker(
    factory: ModalTemplate | CustomElementConstructor,
    init?: DialogInit,
): (event?: Event) => Promise<void>;
export function asInvoker(
    factory: ModalTemplate | CustomElementConstructor,
    init?: DialogInit,
): (event?: Event) => Promise<void> {
    return (event?: Event) => {
        const child = isAKElementConstructor(factory)
            ? new factory()
            : (factory as ModalTemplate)(event!);

        if (child instanceof AKModal) {
            return renderDialog(child, init);
        }

        return renderModal(child, init);
    };
}
