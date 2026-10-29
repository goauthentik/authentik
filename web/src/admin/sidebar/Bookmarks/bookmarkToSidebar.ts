import { Bookmark } from "./bookmarkState";

import { currentInterfacePath } from "#elements/router/core/interfaces";
import { matchRoute } from "#elements/router/core/matcher";

import { ROUTES } from "#admin/Routes";
import { matchesPath } from "#admin/sidebar/sidebarTools";
import { ExtendedSidebarItem } from "#admin/sidebar/types";

/**
 * Attach each bookmark, as a third-tier child sorted by label, to the second-tier entry that
 * lists its object. Bookmarks whose route no entry lists are dropped.
 */
export function bookmarksToSidebar(
    entries: ExtendedSidebarItem[],
    bookmarks: Bookmark[],
): ExtendedSidebarItem[] {
    // Same route-name matching the breadcrumbs use, so `/flow/stages/prompts/…` can't land
    // under "Stages" by prefix.
    const matchers = bookmarks.map((bookmark) => {
        const path = currentInterfacePath(bookmark.path);

        return {
            bookmark,
            matches: matchesPath(path, matchRoute(path, ROUTES)?.route.name ?? null),
        };
    });

    const withBookmarks = (entry: ExtendedSidebarItem): ExtendedSidebarItem => {
        const marks = matchers
            .filter(({ matches }) => matches(entry))
            .map(({ bookmark: { path, label } }) => ({ label, path, key: path, enterprise: false }))
            .sort((a, b) => a.label.localeCompare(b.label));

        return marks.length > 0
            ? { ...entry, children: [...(entry.children ?? []), ...marks] }
            : entry;
    };

    return entries.map((group) =>
        group.children ? { ...group, children: group.children.map(withBookmarks) } : group,
    );
}
