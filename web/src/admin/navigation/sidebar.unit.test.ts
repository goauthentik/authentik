import { createAdminSidebarEntries } from "./sidebarEntries";
import {
    findSidebarSectionByRoute,
    resolveSidebarEntries,
} from "./sidebarTools";
import { type SidebarEntry, ExtendedSidebarItem } from "./types";

import { toAdminInterface } from "#elements/router/core/interfaces";

import { ROUTES } from "#admin/Routes";

import { describe, expect, it } from "vitest";

describe("findSidebarSectionByRoute", () => {
    const entries = resolveSidebarEntries(createAdminSidebarEntries(true), { licensed: false, canEnterprise: false });

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

        expect(children.map(({path}) => path)).toEqual([
            "/events/log",
            "/events/lifecycle-rules",
            "/events/exports",
        ]);

        expect(children[0]?.route).toEqual(["event-view"]);

        for (const { notice } of children.slice(1)) {
            expect(notice).toBeUndefined()
        }
    });

    it.each([false, true])(
        "skips enterprise entries when the build lacks the enterprise app (licensed: %s)",
        (licensed) => {
            const children = getChildren(
                resolveSidebarEntries(entries, { canEnterprise: false, licensed }),
            );

            expect(children.map(({path}) => path)).toEqual(["/events/log"]);
        },
    );

    it("routes unlicensed entries to Licenses with a badge, keeping their path", () => {
        const [logs, lifecycleRules] = getChildren(
            resolveSidebarEntries(entries, { canEnterprise: true, licensed: false }),
        );

        expect(logs).toEqual(["/events/log", "Logs", ["event-view"]]);

        expect(lifecycleRules?.path).toBe("/enterprise/licenses");
        expect(lifecycleRules?.notice).toBe("Enterprise only");
    });

    it("honors readonly on entries it is given", () => {
        const resolved = resolveSidebarEntries(entries, { canEnterprise: true, licensed: false });

        expect(getChildren(resolved)[1].notice).toBe("Enterprise only");
        const children = getChildren(resolved);
        expect(children[1]?.path).not.toBe("/events/lifecycle-rules");
    });

    it("keeps enterprise-only sibling paths distinct across the admin entries", () => {
        const resolved = resolveSidebarEntries(createAdminSidebarEntries(false), {
            canEnterprise: true,
            licensed: false,
        });

        for (const { label, children = [] } of resolved) {
            const paths = children.map(({path}) => path);
            expect(new Set(paths).size, `${label} has duplicate paths`).toBe(paths.length);
            expect(paths, `${label} rewrote a path`).not.toContain("/enterprise/licenses");
        }
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
