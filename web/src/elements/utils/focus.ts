/**
 * @fileoverview Utilities for DOM element interaction, focus management, and event handling.
 */

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
