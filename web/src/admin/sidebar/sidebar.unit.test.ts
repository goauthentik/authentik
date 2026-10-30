import { ROUTES } from "#admin/Routes";
import { createAdminSidebarEntries } from "#admin/sidebar/constants";
import { findSidebarSectionByRoute, resolveSidebarEntries } from "#admin/sidebar/sidebarTools";
import { type SidebarEntry, ExtendedSidebarItem } from "#admin/sidebar/types";

import { describe, expect, it } from "vitest";

describe("findSidebarSectionByRoute", () => {
    const entries = resolveSidebarEntries(createAdminSidebarEntries(true), {
        licensed: false,
        canEnterprise: false,
    });

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

describe("resolveSidebarEntries", () => {
    // prettier-ignore
    const entries: readonly SidebarEntry[] = [
        [null, "Events", { key: "events" }, [
            ["/events/log", "Logs", ["event-view"]],
            ["/events/lifecycle-rules", "Lifecycle Rules", { enterprise: true }],
            ["/events/exports", "Data Exports", { enterprise: true }]]
        ],
    ];

    const getChildren = (resolved: readonly ExtendedSidebarItem[]) => resolved[0].children ?? [];

    it("includes entries through when the build is enterprise and licensed", () => {
        const children = getChildren(
            resolveSidebarEntries(entries, { canEnterprise: true, licensed: true }),
        );

        expect(children.map(({ path }) => path)).toEqual([
            "/if/admin/events/log",
            "/if/admin/events/lifecycle-rules",
            "/if/admin/events/exports",
        ]);

        expect(children[0]?.routes).toEqual(["event-view"]);

        for (const { notice } of children.slice(1)) {
            expect(notice).toBeUndefined();
        }
    });

    it.each([false, true])(
        "skips enterprise entries when the build lacks the enterprise app (licensed: %s)",
        (licensed) => {
            const children = getChildren(
                resolveSidebarEntries(entries, { canEnterprise: false, licensed }),
            );

            expect(children.map(({ path }) => path)).toEqual(["/if/admin/events/log"]);
        },
    );

    it("routes unlicensed entries to Licenses with a badge, keeping their path", () => {
        const [logs, lifecycleRules] = getChildren(
            resolveSidebarEntries(entries, { canEnterprise: true, licensed: false }),
        );

        expect(logs).toEqual({
            enterprise: false,
            key: "/events/log",
            label: "Logs",
            path: "/if/admin/events/log",
            routes: ["event-view"],
        });

        expect(lifecycleRules?.path).toBe("/if/admin/enterprise/licenses");
        expect(lifecycleRules?.notice).toBe("Enterprise only");
    });

    it("honors readonly on entries it is given", () => {
        const resolved = resolveSidebarEntries(entries, { canEnterprise: true, licensed: false });

        expect(getChildren(resolved)[1].notice).toBe("Enterprise only");
        const children = getChildren(resolved);
        expect(children[1]?.path).not.toBe("/if/admin/events/lifecycle-rules");
    });

    it("keeps enterprise-only sibling paths distinct across the admin entries", () => {
        const resolved = resolveSidebarEntries(createAdminSidebarEntries(false), {
            canEnterprise: true,
            licensed: false,
        });

        for (const { label, children = [] } of resolved) {
            const keys = children.map(({ key }) => key);
            expect(new Set(keys).size, `${label} has duplicate paths`).toBe(keys.length);
            expect(keys, `${label} rewrote a path`).not.toContain("/enterprise/licenses");
        }
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
