import { Bookmark } from "./bookmarkState";

import { currentInterfacePath } from "#elements/router/core/interfaces";
import { matchRoute } from "#elements/router/core/matcher";

import { ROUTES } from "#admin/Routes";
import { matchesPath } from "#admin/sidebar/sidebarTools";
import { ExtendedSidebarItem } from "#admin/sidebar/types";

/**
 * For each second-tier navigation entry that has one or more bookmarks, populate that tier's
 * `children` field with synthetic SidebarItems linking to the bookmarked item.
 */
export function bookmarksToSidebar(
    entries: ExtendedSidebarItem[],
    bookmarks: Bookmark[],
): ExtendedSidebarItem[] {
    // Same route-name matching breadcrumbss, so `/flow/stages/prompts/...` will point to
    // the prompts, and the stages object.
    const matchers = bookmarks.map((bookmark) => {
        const path = currentInterfacePath(bookmark.path);

        return {
            bookmark,
            key: path, // We do this for other unkeyed things, it just needs to be unique.
            matches: matchesPath(path, matchRoute(path, ROUTES)?.route.name ?? null),
        };
    });

    const withBookmarks = (entry: ExtendedSidebarItem): ExtendedSidebarItem => {
        const marks = matchers
            .filter(({ matches }) => matches(entry))
            .map(({ bookmark: { path, label }, key }) => ({ label, path, key, enterprise: false }))
            .sort((a, b) => a.label.localeCompare(b.label));

        return marks.length > 0
            ? { ...entry, children: [...(entry.children ?? []), ...marks] }
            : entry;
    };

    return entries.map((group) =>
        group.children ? { ...group, children: group.children.map(withBookmarks) } : group,
    );
}
