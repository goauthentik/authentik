import { createAdminSidebarEntries, findSidebarSectionByRoute, SidebarEntry } from "./sidebar.js";

import { ROUTES } from "#admin/Routes";

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

describe("validate Sidebar routes exist", () => {
    it("has a matching route in Routes for each sidebar entry", () => {
        const paths: string[] = createAdminSidebarEntries(true)
            .map((level1: SidebarEntry) =>
                (level1[3] ?? [])
                    .filter((level2: SidebarEntry) => level2[0]?.startsWith("/"))
                    .map((level2: SidebarEntry) => level2[0]),
            )
            .flat()
            .filter((path) => typeof path === "string");

        for (const path of paths) {
            const matchingRoute = ROUTES.find((route) => route.test(path));
            expect(matchingRoute).not.toBeFalsy();
        }
    });
});
