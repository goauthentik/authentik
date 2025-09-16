/**
 * @fileoverview Utilities for DOM element interaction, focus management, and event handling.
 */

import { createRef, ref, Ref } from "lit/directives/ref.js";

/**
 * Recursively check if the target element or any of its children are active (i.e. "focused").
 *
 * @param targetElement The element to check if it is active.
 * @param containerElement The container element to check if the target element is active within.
 */
export function isActiveElement(
    targetElement: Element | null,
    containerElement: Element | null,
): boolean {
    // Does the container element even exist?
    if (!containerElement) return false;

    // Does the container element have a shadow root?
    if (!("shadowRoot" in containerElement)) return false;
    if (containerElement.shadowRoot === null) return false;

    // Is the target element the active element?
    if (containerElement.shadowRoot.activeElement === targetElement) return true;

    // Let's check the children of the container element...
    return isActiveElement(containerElement.shadowRoot.activeElement, containerElement);
}

/**
 * A combination reference and focus target.
 *
 * @category DOM
 * @category Lit
 */
export class FocusTarget<T extends HTMLElement = HTMLElement> {
    public readonly reference: Ref<T>;

    constructor(reference: Ref<T> = createRef<T>()) {
        this.reference = reference;
    }

    public get target(): T | null {
        return this.reference.value || null;
    }

    public focus = (options?: FocusOptions): void => {
        const { target } = this;

        if (!target) return;
        if (document.activeElement === target) return;

        // Despite our type definitions, this method isn't available in all browsers,
        // so we fallback to assuming the element is visible.
        const visible = target.checkVisibility?.() ?? true;

        if (!visible) return;

        target.focus?.(options);
    };

    public toRef() {
        return ref(this.reference);
    }
}
