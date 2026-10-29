import { initRouter, resetRouterConfig } from "#elements/router/core/config";

import { bookmarksToSidebar } from "#admin/sidebar/Bookmarks/bookmarkToSidebar";
import { createAdminSidebarEntries } from "#admin/sidebar/constants";
import { findSidebarEntries, resolveSidebarEntries } from "#admin/sidebar/sidebarTools";

import { afterAll, beforeAll, describe, expect, it } from "vitest";

describe("bookmarksToSidebar", () => {
    beforeAll(() => initRouter({ base: "/", interfaceName: "admin" }));
    afterAll(() => resetRouterConfig());

    const entries = resolveSidebarEntries(createAdminSidebarEntries(false), {
        licensed: false,
        canEnterprise: false,
    });

    const childrenOf = (items: typeof entries, key: string) =>
        findSidebarEntries(items, (entry) => entry.key === key).at(-1)?.children;

    it("attaches bookmarks to their listing entry, sorted by label", () => {
        const result = bookmarksToSidebar(entries, [
            { path: "/if/admin/flow/flows/zeta", label: "Zeta flow" },
            { path: "/if/admin/core/applications/app", label: "An app" },
            { path: "/if/admin/flow/flows/alpha", label: "Alpha flow" },
        ]);

        expect(childrenOf(result, "/flow/flows")?.map(({ label }) => label)).toEqual([
            "Alpha flow",
            "Zeta flow",
        ]);

        expect(childrenOf(result, "/core/applications")).toEqual([
            {
                label: "An app",
                path: "/if/admin/core/applications/app",
                key: "/if/admin/core/applications/app",
                enterprise: false,
            },
        ]);

        expect(childrenOf(result, "/flow/stages")).toBeUndefined();
    });

    it("drops bookmarks no entry lists and leaves the input alone", () => {
        const result = bookmarksToSidebar(entries, [{ path: "/if/admin/nowhere/1", label: "X" }]);

        expect(result).toEqual(entries);
        expect(childrenOf(entries, "/flow/flows")).toBeUndefined();
    });
});
