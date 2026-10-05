import { createAdminSidebarEntries, findSidebarSectionByRoute } from "./sidebar.js";

import { describe, expect, it } from "vitest";

describe("findSidebarSectionByRoute", () => {
    const entries = createAdminSidebarEntries();

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
