/**
 * @file Utilities for command invokers.
 */

import { ref, Ref } from "lit/directives/ref.js";

/**
 * An element that can invoke commands on another element,
 * typically a button or similar control.
 */
export interface InvokerElement {
    commandForElement: HTMLElement | null;
    command: string | null;
}

/**
 * Type predicate to determine if an element can invoke commands.
 *
 * @param element The element to check.
 */
export function isInvokerElement<T extends Element = Element>(
    element: Element,
): element is T & InvokerElement {
    return "commandForElement" in element;
}

/**
 * Type predicate to determine if an input is a Lit Ref.
 *
 * @param input The input to check.
 */
export function isRef<T>(input: unknown): input is Ref<T> {
    return typeof input === "object" && input !== null && "value" in input;
}

/**
 * Parameter type for command target, either an element or a callback
 * that receives the invoker element and returns the target element.
 */
export type CommandTargetParameter<T extends HTMLElement = HTMLElement> =
    | string
    | T
    | Ref<T>
    | ((invoker: T) => T | null);

/**
 * Lit ref directive to set the command target for an invoker element.
 *
 * @param elementOrCallback The target element or a callback to get it.
 */
export function commandForElementRef<T extends HTMLElement = HTMLElement>(
    elementOrCallback: CommandTargetParameter<T> | null,
) {
    return ref((invoker) => {
        if (!invoker || !isInvokerElement<T>(invoker) || !elementOrCallback) {
            return;
        }

        let commandForElement: T | null = null;

        if (typeof elementOrCallback === "function") {
            commandForElement = elementOrCallback(invoker);
        } else if (typeof elementOrCallback === "string") {
            commandForElement = invoker.ownerDocument.getElementById(elementOrCallback) as T | null;
        } else if (isRef<T>(elementOrCallback)) {
            commandForElement = elementOrCallback.value || null;
        } else {
            commandForElement = elementOrCallback;
        }

        invoker.commandForElement = commandForElement || null;
    });
}
