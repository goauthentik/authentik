import { type SidebarEntry, findSidebarSectionByPath } from "./sidebar.js";

import { describe, expect, it } from "vitest";

const entries: SidebarEntry[] = [
    [null, "Dashboards", { key: "dashboards" }, [["/administration/overview", "Overview"]]],
    [
        null,
        "Applications",
        { key: "applications" },
        [
            ["/core/applications", "Applications", ["^/core/applications/(?<slug>[-\\w]+)$"]],
            ["/core/providers", "Providers", ["^/core/providers/(?<id>\\d+)$"]],
        ],
    ],
];

describe("findSidebarSectionByPath", () => {
    it("does not name a list page by its own path", () => {
        expect(findSidebarSectionByPath(entries, "/core/providers")).toBeNull();
        expect(findSidebarSectionByPath(entries, "/administration/overview")).toBeNull();
    });

    it("names the entry whose activeWhen pattern matches a detail path", () => {
        expect(findSidebarSectionByPath(entries, "/core/providers/74")).toBe("Providers");
        expect(findSidebarSectionByPath(entries, "/core/applications/my-app")).toBe("Applications");
    });

    it("returns null for a path no entry claims", () => {
        expect(findSidebarSectionByPath(entries, "/core/providers/74/extra")).toBeNull();
        expect(findSidebarSectionByPath(entries, "/unknown")).toBeNull();
    });

    it("never names a group by its label alone", () => {
        expect(findSidebarSectionByPath(entries, "Dashboards")).toBeNull();
    });
});
