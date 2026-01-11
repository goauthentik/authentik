import { DEFAULT_CONFIG } from "#common/api/config";

import { SidebarEntry } from "#admin/AdminInterface/AdminSidebar";

import { CoreApi, UserSelf } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing, TemplateResult } from "lit";

/**
 * Get the list of pinned tab paths from user settings.
 */
export function getPinnedPaths(user: UserSelf | null | undefined): string[] {
    const settings = user?.settings as Record<string, unknown> | undefined;
    const adminSettings = settings?.admin as Record<string, unknown> | undefined;
    return (adminSettings?.pinnedTabs as string[]) ?? [];
}

/**
 * Find sidebar entries by their paths from a nested entry structure.
 */
export function findEntriesByPaths(
    entries: readonly SidebarEntry[],
    paths: string[],
): SidebarEntry[] {
    const result: SidebarEntry[] = [];

    for (const entry of entries) {
        const [path, , , children] = entry;
        if (path && paths.includes(path)) {
            result.push(entry);
        }
        if (children) {
            result.push(...findEntriesByPaths(children, paths));
        }
    }

    return result;
}

/**
 * Handle pin toggle event by updating user settings.
 */
export async function handlePinToggle(
    user: UserSelf,
    pinnedPaths: string[],
    path: string,
    pinned: boolean,
    onSuccess: () => Promise<void>,
): Promise<void> {
    const currentPinned = [...pinnedPaths];

    if (pinned && !currentPinned.includes(path)) {
        currentPinned.push(path);
    } else if (!pinned) {
        const index = currentPinned.indexOf(path);
        if (index > -1) currentPinned.splice(index, 1);
    }

    try {
        const fullUser = await new CoreApi(DEFAULT_CONFIG).coreUsersRetrieve({
            id: user.pk,
        });

        await new CoreApi(DEFAULT_CONFIG).coreUsersPartialUpdate({
            id: user.pk,
            patchedUserRequest: {
                attributes: {
                    ...(fullUser.attributes ?? {}),
                    settings: {
                        ...((fullUser.attributes?.settings as Record<string, unknown>) ?? {}),
                        admin: {
                            ...((fullUser.attributes?.settings as Record<string, unknown>)?.admin ??
                                {}),
                            pinnedTabs: currentPinned,
                        },
                    },
                },
            },
        });

        await onSuccess();
    } catch (error) {
        console.error("Failed to update pinned tabs:", error);
    }
}

/**
 * Render a sidebar entry with pinnable/pinned state.
 */
export function renderSidebarEntry(
    entry: SidebarEntry,
    pinnedPaths: string[],
    excludePinned = false,
): TemplateResult | typeof nothing {
    const [path, label, attributes, children] = entry;

    // Exclude pinned entries from their original location
    if (excludePinned && path && pinnedPaths.includes(path)) {
        return nothing;
    }

    const properties: Record<string, unknown> = Array.isArray(attributes)
        ? { ".activeWhen": attributes }
        : { ...(attributes ?? {}) };

    if (path) {
        properties.path = path;
        // Leaf items (no children) are pinnable
        if (!children) {
            properties.pinnable = true;
            properties.pinned = pinnedPaths.includes(path);
        }
    }

    // Filter out pinned children
    const visibleChildren = children
        ? children.filter((child) => {
              const [childPath] = child;
              return !excludePinned || !childPath || !pinnedPaths.includes(childPath);
          })
        : undefined;

    // Hide parent if all children are pinned (and excluded)
    if (children && excludePinned && (!visibleChildren || visibleChildren.length === 0)) {
        return nothing;
    }

    return html`<ak-sidebar-item
        exportparts="list-item, link"
        label=${label}
        .path=${path}
        .pinnable=${properties.pinnable ?? false}
        .pinned=${properties.pinned ?? false}
        ?expanded=${properties["?expanded"]}
        ?enterprise=${properties.enterprise}
        .activeWhen=${properties[".activeWhen"] ?? []}
    >
        ${visibleChildren
            ? visibleChildren.map((child) => renderSidebarEntry(child, pinnedPaths, excludePinned))
            : nothing}
    </ak-sidebar-item>`;
}

/**
 * Render the pinned section at the top of the sidebar.
 */
export function renderPinnedSection(
    allEntries: readonly SidebarEntry[],
    pinnedPaths: string[],
): TemplateResult | typeof nothing {
    if (pinnedPaths.length === 0) return nothing;

    const pinnedEntries = findEntriesByPaths(allEntries, pinnedPaths);

    if (pinnedEntries.length === 0) return nothing;

    return html`<ak-sidebar-item label=${msg("Pinned")} ?expanded=${true}>
        ${pinnedEntries.map((entry) => renderSidebarEntry(entry, pinnedPaths, false))}
    </ak-sidebar-item>`;
}

/**
 * Render sidebar entries, excluding pinned items from their original location.
 */
export function renderSidebarEntries(
    entries: readonly SidebarEntry[],
    pinnedPaths: string[],
): TemplateResult[] {
    return entries
        .map((entry) => renderSidebarEntry(entry, pinnedPaths, true))
        .filter((t): t is TemplateResult => t !== nothing);
}
