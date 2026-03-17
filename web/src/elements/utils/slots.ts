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
