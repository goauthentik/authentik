/**
 * @file Utilities for working with slotted elements.
 */

import type { AbstractConstructor, Constructor } from "#elements/types";

export function findSlottedInstance<T>(
    NodeConstructor: Constructor<T> | AbstractConstructor<T>,
    slot: HTMLSlotElement,
): T | null {
    const assignedNodes = slot.assignedNodes({ flatten: true });

    const node = assignedNodes.find((node) => node instanceof NodeConstructor);

    return node ? (node as T) : null;
}

/**
 * Finds the assigned slot for the given element, optionally filtered by name.
 *
 * @param element The element to check for an assigned slot.
 * @param name The slot name to match. Pass `null` to match any named slot
 *   (excluding the default slot). If omitted, matches the default slot.
 *
 * @returns The matching assigned slot, or `null` if none is found.
 */
export function findAssignedSlot(
    element: HTMLElement,
    name?: string | null,
): HTMLSlotElement | null {
    const { assignedSlot } = element;

    if (!assignedSlot) {
        return null;
    }

    if (typeof name === "undefined") {
        return assignedSlot.name === "" ? assignedSlot : null;
    }

    if (name === null) {
        return assignedSlot.name !== "" ? assignedSlot : null;
    }

    return assignedSlot.name === name ? assignedSlot : null;
}

/**
 * Creates a new slot element with the specified name.
 *
 * @param name The name of the slot. Omit or pass `null` for the default slot.
 * @param ownerDocument The document to create the slot in. Defaults to the current document.
 *
 * @returns The created slot element.
 */
export function createSlot(name?: string | null, ownerDocument = document): HTMLSlotElement {
    const slot = ownerDocument.createElement("slot");

    if (name) {
        slot.setAttribute("name", name);
    }

    return slot;
}
