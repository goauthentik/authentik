/**
 * @file Session-scoped persistence for sidebar group expansion.
 */

import { StorageAccessor } from "#common/storage";

/**
 * Expansion keyed by {@linkcode SidebarItem.key}. A missing entry means "never
 * toggled", which leaves the entry's declared default in place — distinct from
 * an entry of `false`, which means the person collapsed it on purpose.
 */
export type SidebarExpansionState = Record<string, boolean>;

const STORAGE_KEY = "authentik/sidebar/expansion";

let accessor: StorageAccessor | null = null;

function retrieveStorageAccessor(): StorageAccessor {
    return (accessor ??= StorageAccessor.session(STORAGE_KEY));
}

/**
 * Attempt to parse a stored value into a usable sidebar expansion state.
 */
export function parseSidebarExpansionState(value: unknown): SidebarExpansionState {
    if (!value || typeof value !== "object" || Array.isArray(value)) return {};

    return Object.fromEntries(
        Object.entries(value).filter(([, expanded]) => typeof expanded === "boolean"),
    ) as SidebarExpansionState;
}

/**
 * Read the whole expansion record.
 */
export function readSidebarExpansionState(): SidebarExpansionState {
    return parseSidebarExpansionState(retrieveStorageAccessor().readJSON<SidebarExpansionState>());
}

/**
 * The persisted expansion for a single key, or `null` when it has never been toggled.
 */
export function readSidebarExpansion(key: string): boolean | null {
    const expanded = readSidebarExpansionState()[key];

    return typeof expanded === "boolean" ? expanded : null;
}

/**
 * Record an explicit toggle.
 */
export function writeSidebarExpansion(key: string, expanded: boolean): boolean {
    return retrieveStorageAccessor().writeJSON({
        ...readSidebarExpansionState(),
        [key]: expanded,
    });
}

/**
 * Forget every recorded toggle.
 */
export function clearSidebarExpansionState(): boolean {
    return retrieveStorageAccessor().delete();
}
