/**
 * @file Modal and dialog rendering utilities.
 */

import "#elements/modals/ak-modal";

import { AKModal } from "#elements/modals/ak-modal";
import { SlottedTemplateResult } from "#elements/types";
import { isAKElementConstructor } from "#elements/utils/unsafe";

import { ElementPart, html, noChange, render } from "lit";
import {
    directive,
    Directive,
    DirectiveResult,
    PartInfo,
    PartType,
} from "lit-html/async-directive.js";

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

/**
 * Initialization options for dialog and modal rendering functions.
 */
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

    dialog.addEventListener("close", dispose, {
        passive: true,
        once: true,
    });

    signal?.addEventListener("abort", dispose, {
        passive: true,
        once: true,
    });

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

//#endregion

//#region Invokers

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
 * @param input The input to render as a modal dialog, either a custom element constructor or a function that returns a template result.
 * @param init Initialization options for the modal dialog.
 */
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

//#endregion

//#region Directives

type ModalDirectiveParameters = [
    factory: ModalTemplate | CustomElementConstructor,
    options?: ModalInvokerInit,
];

/**
 * Initialization options for the {@linkcode modalInvoker} directive.
 *
 * @see {@linkcode DialogInit} for the underlying dialog options.
 */
export interface ModalInvokerInit extends DialogInit {
    /**
     * Dependencies array for memoization. The directive will only rebind
     * the event listener when one of these values changes (shallow comparison).
     * If not provided, the listener rebinds on every update.
     */
    deps?: unknown[];
}

/**
 * A directive that manages the event listener for an invoker function created by {@linkcode asInvoker}.
 *
 * Supports memoization via an optional `deps` array in the options object. When `deps` is provided,
 * the directive will skip rebinding the event listener if all dep values are shallowly equal to the
 * previous render. If `deps` is omitted, the listener rebinds on every update (safe default).
 *
 * @see {@linkcode asInvoker} for the underlying invoker.
 * @see {@linkcode modalInvoker} for the Lit HTML variation.
 */
class ModalInvokerDirective extends Directive {
    constructor(partInfo: PartInfo) {
        super(partInfo);
        if (partInfo.type !== PartType.ELEMENT) {
            throw new Error("modalOpener() can only be used on an element");
        }
    }

    #cleanup: (() => void) | null = null;
    #prevDeps: unknown[] | null = null;

    /**
     * Shallow-compare new deps against the previously stored deps.
     *
     * Returns `true` if deps match (i.e. we should skip rebinding).
     * Returns `false` if deps are absent, previously unset, or any value differs.
     */
    #depsMatch(newDeps: unknown[] | undefined): boolean {
        if (!newDeps || !this.#prevDeps) return false;
        if (this.#prevDeps.length !== newDeps.length) return false;
        return this.#prevDeps.every((prev, i) => prev === newDeps[i]);
    }

    update(part: ElementPart, [factory, options]: ModalDirectiveParameters): void {
        const deps = options?.deps;

        // Deps provided and unchanged — skip rebind
        if (this.#depsMatch(deps)) {
            return;
        }

        // Tear down old listener before rebinding
        if (this.#cleanup) {
            this.#cleanup();
            this.#cleanup = null;
        }

        const listener = asInvoker(factory, options);
        part.element.addEventListener("click", listener);

        const cleanup = () => {
            part.element.removeEventListener("click", listener);
            // Null out prevDeps so that the next render cycle always rebinds.
            // This handles the case where an AbortSignal fires between renders.
            this.#prevDeps = null;
        };

        if (options?.signal) {
            options.signal.addEventListener("abort", cleanup, { once: true });
        }

        this.#cleanup = cleanup;
        this.#prevDeps = deps ?? null;
    }

    render(..._args: ModalDirectiveParameters) {
        return noChange;
    }
}

/**
 * A Lit HTML directive that can be used to attach a modal invoker to an element.
 *
 * @example Basic usage (rebinds every render):
 * ```ts
 * html`<button ${modalInvoker(SomeModalConstructor)}>Open</button>`
 * ```
 *
 * @example With memoized deps (only rebinds when deps change):
 * ```ts
 * html`<button ${modalInvoker(factory, { deps: [itemId] })}>Edit</button>`
 * ```
 */
export const modalInvoker = directive(ModalInvokerDirective);

export type ModalInvokerDirectiveResult = DirectiveResult<typeof ModalInvokerDirective>;

export interface ModelFormLike {
    instancePk?: string | number | null;
}

export interface ModelFormLikeConstructor {
    new (): ModelFormLike;
}

/**
 * A helper function to create a modal invoker for editing an instance of a form-like element.
 *
 * @remarks
 * This is defined externally from the form itself to allow existing forms to
 * easily add edit invokers without needing to extend a specific base class.
 */
export function asEditModalInvoker(
    this: ModelFormLikeConstructor,
    instancePk?: string | number | null,
    init?: ModalInvokerInit,
): ModalInvokerDirectiveResult {
    return modalInvoker(
        (_event) => {
            const FormConstructor = this as unknown as ModelFormLikeConstructor;

            const formElement = new FormConstructor();
            formElement.instancePk = instancePk;

            return formElement;
        },
        { ...init, deps: [instancePk] },
    );
}
