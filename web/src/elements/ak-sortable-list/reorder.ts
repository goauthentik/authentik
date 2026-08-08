/**
 * Detail of the `reorder` event: the sortable keys in their new order.
 */
export interface SortableReorderDetail {
    keys: string[];
}

/**
 * Compute the new key order after dropping `draggingKey` onto `targetKey`.
 *
 * Pure helper (no DOM) so the reorder math can be unit-tested. Returns a new array; the input
 * is not mutated. If either key is missing, or they are the same, the original order is returned.
 *
 * @param keys the current keys in DOM order
 * @param draggingKey the key being dragged
 * @param targetKey the key of the row it was dropped on, or `null` when dropped past the last row
 * @param insertAfter whether to insert below (rather than above) the target row
 */
export function reorderKeys(
    keys: string[],
    draggingKey: string,
    targetKey: string | null,
    insertAfter: boolean,
): string[] {
    const next = [...keys];
    const from = next.indexOf(draggingKey);
    if (from === -1) {
        return next;
    }
    if (!targetKey || targetKey === draggingKey) {
        return next;
    }
    if (!next.includes(targetKey)) {
        return next;
    }
    next.splice(from, 1);
    let insertIndex = next.indexOf(targetKey);
    if (insertAfter) {
        insertIndex += 1;
    }
    next.splice(insertIndex, 0, draggingKey);
    return next;
}
