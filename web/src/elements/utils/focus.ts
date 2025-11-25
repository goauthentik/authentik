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
 * Type predicate to check if an element is focusable.
 *
 * @param target The element to check.
 *
 * @category DOM
 */
export function isFocusable(target: Element | null | undefined): target is HTMLElement {
    if (!target) {
        console.debug("FocusTarget: Skipping focus, no target", target);
        return false;
    }
    if (!(target instanceof HTMLElement)) {
        console.debug("FocusTarget: Skipping focus, target is not an HTMLElement", target);
        return false;
    }

    if (document.activeElement === target) {
        console.debug("FocusTarget: Target is already focused", target);
        return false;
    }

    // Despite our type definitions, this method isn't available in all browsers,
    // so we fallback to assuming the element is visible.
    const visible = target.checkVisibility?.() ?? true;

    if (!visible) {
        console.debug("FocusTarget: Skipping focus, target is not visible", target);
        return false;
    }

    if (typeof target.focus !== "function") {
        console.debug("FocusTarget: Skipping focus, target has no focus method", target);
        return false;
    }

    return true;
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
        if (isFocusable(this.target)) {
            this.target.focus(options);
        }
    };

    public toRef() {
        return ref(this.reference);
    }

    public toEventListener(options?: FocusOptions) {
        return () => this.focus(options);
    }
}
