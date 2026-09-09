import { PFSize } from "#common/enums";

import { SlottedTemplateResult } from "#elements/types";

import { LitElement } from "lit";

//#region Types

/**
 * Initialization options for dialog and modal rendering functions.
 */
export interface DialogInit {
    /**
     * The document to use for creating and rendering the dialog. Defaults to the global `document`.
     */
    ownerDocument?: Document;
    /**
     * The parent element to use for rendering the dialog. Defaults to the document body.
     */
    parentElement?: HTMLElement | string | null;
    /**
     * The element that invoked the dialog.
     * This determines the context where events are dispatched from the dialog.
     */
    invokerElement?: Element | null;
    /**
     * A value passed to {@linkcode HTMLDialogElement} to determine how the dialog can be closed.
     *
     * @see {@linkcode ClosedBy} for additional details on the available options and their behavior.
     */
    closedBy?: ClosedBy;
    /**
     * The inline-size to use for the dialog when rendered.
     * This can be used to control the width of the dialog.
     */
    size?: PFSize;
    /**
     * Additional CSS classes to apply to the dialog element when rendered.
     */
    classList?: string[];
    /**
     * An {@linkcode AbortSignal} that can be used to automatically close the dialog when aborted.
     */
    signal?: AbortSignal;
    /**
     * A callback function that is invoked when the dialog is disposed.
     *
     * @param event The event that triggered the disposal, if any.
     */
    onDispose?: (event?: Event) => void;
}

/* An "entity" is any Object (in the authentik sense) that we get from the server that has a primary
 * key and a REST Endpoint: an Application, a Group, a Policy Binding, a Certificate-Key Pair. We
 * use "Entity" because "Object" is a reserved word and a specific concept in Javascript/TypeScript,
 * so using it would imply the wrong thing to casual reviewers.
 */

/**
 * An Object (in the authentik sense) in the client API that has these traits: they have names that
 * we intend to display to the customer.
 */
export interface NamedEntity {
    /**
     * Singular label for the type of object this form creates/edits.
     */
    verboseName?: string | null;
    /**
     * Plural label for the type of object this form creates/edits.
     */
    verboseNamePlural?: string | null;
}

/**
 * In several cases, we have constructors that carry information about the verboseName with them to
 * enhance the displays of generic classes like Form and Table. This interface can be declared on
 * these generic classes so that TypeScript accept that the object's constructor carries these
 * fields.
 */

// eslint-disable-next-line @typescript-eslint/no-unsafe-function-type
export interface NamedEntityElement extends Function, NamedEntity {}

export interface NamedEntityElementConstructor extends NamedEntity, CustomElementConstructor {
    createLabel?: string | null;
}

//#endregion

//#region Transclusion

/**
 * A symbol used to identify elements that are designed to be transcluded
 * into dialogs or other containers that support transclusion.
 */
export const TransclusionChildSymbol = Symbol("transclusion-child");

/**
 * A symbol used to identify elements that are designed to be parents of transcluded elements,
 * such as dialogs or other containers that support transclusion.
 */
export const TransclusionParentSymbol = Symbol("transclusion-parent");

export interface TransclusionParentElement extends LitElement {
    [TransclusionParentSymbol]: boolean;

    slottedElementUpdatedAt?: Date | null;
}

/**
 * An element that is designed to included in a dialog or other container that supports transclusion.
 */
export interface TransclusionChildElement extends LitElement {
    /**
     * A marker property to identify this element as a TransclusionElement.
     *
     * This is useful to avoid a strict type or interface check,
     * which can be problematic when dealing with elements across different shadow roots.
     */
    [TransclusionChildSymbol]: boolean;

    /**
     * The parent element that this element is transcluded into, if any.
     * This can be used to determine the context in which the element is rendered,
     * and to access properties or methods of the parent container if needed.
     */
    parentElement: HTMLElement | TransclusionParentElement | null;

    /**
     * The display box to use for the element when rendered in a dialog or other container.
     */
    displayBox?: "contents" | "block";

    /**
     * The size to use for the element when rendered in a dialog or other container.
     */
    size?: PFSize | null;

    /**
     * Whether the element is considered visible for the purposes of rendering in a dialog or other container.
     */
    visible?: boolean;

    /**
     * An optional method to render a header for the element, which can be used
     * when the element is transcluded into a dialog or other container that supports headers.
     *
     * @param force Whether to force the contents to render.
     */
    renderHeader?(force?: boolean): SlottedTemplateResult;

    /**
     * An optional method to render action buttons for the element, which can be used
     * when the element is transcluded into a dialog or other container that supports action buttons.
     *
     * @param force Whether to force the contents to render.
     */
    renderActions?(force?: boolean): SlottedTemplateResult;

    /**
     * The label to use for the cancel button when this element is transcluded
     * into a dialog or other container.
     */
    cancelButtonLabel?: string | null;

    /**
     * Whether the dialog or other container should render a default cancel button
     * when this element is transcluded.
     */
    cancelable?: boolean;

    formatARIALabel?(): string;
}

/**
 * Type predicate to determine if an element is a {@linkcode TransclusionChildElement}.
 *
 * @param element The element to check.
 */
export function isTransclusionElement(element: Element): element is TransclusionChildElement {
    return TransclusionChildSymbol in element;
}

/**
 * Type predicate to determine if an element is a {@linkcode TransclusionParentElement}.
 *
 * @param element The element to check.
 */
export function isTransclusionParentElement(
    element: Element | null,
): element is TransclusionParentElement {
    return !!(element && TransclusionParentSymbol in element);
}

//#endregion
