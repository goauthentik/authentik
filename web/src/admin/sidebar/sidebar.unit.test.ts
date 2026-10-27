import { findSidebarSectionByRoute, type SidebarEntry } from "#elements/sidebar/utils";

import { ROUTES } from "#admin/Routes";
import { createAdminSidebarEntries } from "#admin/sidebar/constants";

import { describe, expect, it } from "vitest";

describe("findSidebarSectionByRoute", () => {
    const entries = createAdminSidebarEntries(true);

    it.each([
        ["outpost-view", "Outposts"],
        ["provider-view", "Providers"],
        ["application-view", "Applications"],
        ["user-view", "Users"],
        ["flow-view", "Flows"],
        ["system-tasks", "System Tasks"],
    ])("names the entry that lists %s", (routeName, section) => {
        expect(findSidebarSectionByRoute(entries, routeName)).toBe(section);
    });

    it("returns null for a route no entry lists", () => {
        expect(findSidebarSectionByRoute(entries, "outposts")).toBeNull();
        expect(findSidebarSectionByRoute(entries, "stage-prompts")).toBeNull();
        expect(findSidebarSectionByRoute(entries, null)).toBeNull();
    });
});

describe("sidebar routes", () => {
    const collectPaths = (entries: readonly SidebarEntry[]): string[] =>
        entries.flatMap(([path, , , children]) => [
            ...(path?.startsWith("/") ? [path] : []),
            ...(children ? collectPaths(children) : []),
        ]);

    it.each(collectPaths(createAdminSidebarEntries(true)))("%s resolves to a route", (path) => {
        expect(ROUTES.some((route) => route.test(path))).toBe(true);
    });
});
