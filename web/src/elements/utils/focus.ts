/**
 * @fileoverview Utilities for DOM element interaction, focus management, and event handling.
 */

import { createRef, ref, Ref } from "lit/directives/ref.js";

export interface FocusErrorOptions extends ErrorOptions {
    target: Element | null;
}

export class FocusAssertionError extends Error {
    public override name = "FocusAssertionError";
    public readonly target: Element | null;

    constructor(message: string, { target, ...options }: FocusErrorOptions) {
        super(message, options);
        this.target = target;
    }
}

export function assertFocusable(target: Element | null | undefined): asserts target is HTMLElement {
    if (!target) {
        throw new FocusAssertionError("Skipping focus, no target", { target: null });
    }
    if (!(target instanceof HTMLElement)) {
        throw new FocusAssertionError("Skipping focus, target is not an HTMLElement", { target });
    }

    if (document.activeElement === target) {
        throw new FocusAssertionError("Target is already focused", { target });
    }

    // Despite our type definitions, this method isn't available in all browsers,
    // so we fallback to assuming the element is visible.
    const visible = target.checkVisibility?.() ?? true;

    if (!visible) {
        throw new FocusAssertionError("Skipping focus, target is not visible", { target });
    }

    if (typeof target.focus !== "function") {
        throw new FocusAssertionError("Skipping focus, target has no focus method", { target });
    }
}
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
    try {
        assertFocusable(target);
        return true;
    } catch (error) {
        if (error instanceof FocusAssertionError) {
            console.debug(error.message, error.target);
        } else {
            console.error("Unexpected error during focus assertion", error);
        }
        return false;
    }
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
