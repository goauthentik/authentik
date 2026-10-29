/**
 * @file Session-scoped persistence for bookmark collection state
 */

import { StorageAccessor } from "#common/storage/accessor";
import type { PersistenceKey } from "#common/storage/shared";

export interface Bookmark {
    path: string;
    label: string;
}

const STORAGE_KEY = "ak:bookmark:collection" satisfies PersistenceKey;

type StorageAccessorType = StorageAccessor<typeof STORAGE_KEY>;

let accessor: StorageAccessorType | null = null;

function getAccessor(): StorageAccessorType {
    return (accessor ??= StorageAccessor.local(STORAGE_KEY));
}

/**
 * Attempt to parse a stored value into a usable bookmark collection state.
 */
export function parseState(value: unknown): Bookmark[] {
    if (!(value && Array.isArray(value))) {
        return [];
    }

    return value as Bookmark[];
}

/**
 * Read the whole expansion record.
 */
export function readState(): Bookmark[] {
    return parseState(getAccessor().readJSON<Bookmark[]>());
}

/**
 * Write the whole expansion record.
 */
export function writeState(state: Bookmark[]): boolean {
    return getAccessor().writeJSON(state);
}
