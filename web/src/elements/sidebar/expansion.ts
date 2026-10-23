/**
 * @file Session-scoped persistence for sidebar group expansion.
 */

import { StorageAccessor } from "#common/storage/accessor";
import type { PersistenceKey } from "#common/storage/shared";

const STORAGE_KEY = "ak:sidebar:expansion" satisfies PersistenceKey;

/**
 * Expansion keyed by {@linkcode SidebarItem.key}. A missing entry means "never
 * toggled", which leaves the entry's declared default in place — distinct from
 * an entry of `false`, which means the person collapsed it on purpose.
 */
export type SidebarExpansionState = Record<string, boolean>;

type StorageAccessorType = StorageAccessor<typeof STORAGE_KEY>;

let accessor: StorageAccessorType | null = null;

function getAccessor(): StorageAccessorType {
    return (accessor ??= StorageAccessor.session(STORAGE_KEY));
}

/**
 * Attempt to parse a stored value into a usable sidebar expansion state.
 */
export function parseState(value: unknown): SidebarExpansionState {
    if (!value || typeof value !== "object" || Array.isArray(value)) return {};

    return Object.fromEntries(
        Object.entries(value).filter(([, expanded]) => typeof expanded === "boolean"),
    ) as SidebarExpansionState;
}

/**
 * Read the whole expansion record.
 */
export function readState(): SidebarExpansionState {
    return parseState(getAccessor().readJSON<SidebarExpansionState>());
}

/**
 * Write the whole expansion record.
 */
export function writeState(state: SidebarExpansionState): boolean {
    return getAccessor().writeJSON(state);
}
