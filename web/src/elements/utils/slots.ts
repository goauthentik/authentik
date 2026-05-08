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
