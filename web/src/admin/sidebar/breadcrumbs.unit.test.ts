import { matchRoute } from "#elements/router/core/matcher";

import { ROUTES } from "#admin/Routes";
import { findBreadcrumbEntries } from "#admin/sidebar/BreadcrumbController";
import { createAdminSidebarEntries } from "#admin/sidebar/constants";
import { resolveSidebarEntries } from "#admin/sidebar/sidebarTools";

import { describe, expect, it } from "vitest";

describe("findBreadcrumbEntries", () => {
    const entries = resolveSidebarEntries(createAdminSidebarEntries(false), {
        licensed: false,
        canEnterprise: false,
    });

    const trail = (path: string, objectName: string | null, tabLabel: string | null) =>
        findBreadcrumbEntries(entries, {
            pathname: `/if/admin${path}`,
            path,
            match: matchRoute(path, ROUTES)!,
            objectName,
            tabLabel,
        });

    const flow = "/flow/flows/default-authentication-flow";
    const name = "Default authentication flow";

    it("ignores a stale object name on a list page", () => {
        expect(trail("/flow/flows", name, null)).toEqual({
            path: "/if/admin/flow/flows",
            objectPath: null,
            crumbs: ["Flows and Stages", "Flows"],
            fullCrumbs: ["Flows and Stages", "Flows"],
        });
    });

    it("adds the object name, but not the default tab, on the object page", () => {
        expect(trail(flow, name, "Flow Overview")).toEqual({
            path: `/if/admin${flow}`,
            objectPath: `/if/admin${flow}`,
            crumbs: ["Flows and Stages", "Flows", name],
            fullCrumbs: ["Flows and Stages", "Flows", name],
        });
    });

    it("adds the tab label only to fullCrumbs on a subpage", () => {
        expect(trail(`${flow}/permissions`, name, "Permissions")).toEqual({
            path: `/if/admin${flow}/permissions`,
            objectPath: `/if/admin${flow}`,
            crumbs: ["Flows and Stages", "Flows", name],
            fullCrumbs: ["Flows and Stages", "Flows", name, "Permissions"],
        });
    });

    it("adds a tab label without an object on a tabbed page", () => {
        expect(trail("/administration/system-tasks/schedules", null, "Schedules")).toEqual({
            path: "/if/admin/administration/system-tasks/schedules",
            objectPath: null,
            crumbs: ["Dashboards", "System Tasks"],
            fullCrumbs: ["Dashboards", "System Tasks", "Schedules"],
        });
    });
});
