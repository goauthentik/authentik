import {
    createAdminSidebarEntries,
    findSidebarSectionByRoute,
    resolveSidebarEntries,
    SidebarEntry,
} from "./sidebar.js";

import { toAdminInterface } from "#elements/router/core/interfaces";

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

describe("resolveSidebarEntries", () => {
    // prettier-ignore
    const entries: readonly SidebarEntry[] = [
        [null, "Events", { key: "events" }, [
            ["/events/log", "Logs", ["event-view"]],
            ["/events/lifecycle-rules", "Lifecycle Rules", { enterprise: true }],
            ["/events/exports", "Data Exports", { enterprise: true }]]
        ],
    ];

    const childrenOf = (resolved: readonly SidebarEntry[]) => resolved[0]?.[3] ?? [];

    it("passes entries through when the build is enterprise and licensed", () => {
        const children = childrenOf(
            resolveSidebarEntries(entries, { canEnterprise: true, licensed: true }),
        );

        expect(children.map(([path]) => path)).toEqual([
            "/events/log",
            "/events/lifecycle-rules",
            "/events/exports",
        ]);

        expect(children[0]?.[2]).toEqual(["event-view"]);

        for (const [, , attributes] of children.slice(1)) {
            expect(attributes).not.toHaveProperty("pathOverride");
            expect(attributes).not.toHaveProperty("badge");
        }
    });

    it.each([false, true])(
        "drops enterprise entries when the build lacks the enterprise app (licensed: %s)",
        (licensed) => {
            const children = childrenOf(
                resolveSidebarEntries(entries, { canEnterprise: false, licensed }),
            );

            expect(children.map(([path]) => path)).toEqual(["/events/log"]);
        },
    );

    it("routes unlicensed entries to Licenses with a badge, keeping their path", () => {
        const [logs, lifecycleRules] = childrenOf(
            resolveSidebarEntries(entries, { canEnterprise: true, licensed: false }),
        );

        expect(logs).toEqual(["/events/log", "Logs", ["event-view"]]);

        expect(lifecycleRules?.[0]).toBe("/events/lifecycle-rules");
        expect(lifecycleRules?.[2]).toEqual({
            enterprise: true,
            pathOverride: toAdminInterface("/enterprise/licenses"),
            notice: "Enterprise only",
        });
    });

    it("does not mutate the entries it is given", () => {
        resolveSidebarEntries(entries, { canEnterprise: true, licensed: false });

        expect(childrenOf(entries)[1]?.[2]).toEqual({ enterprise: true });

        const children = childrenOf(entries);

        expect(children[1]?.[2]).not.toHaveProperty("pathOverride");
    });

    it("keeps locked sibling paths distinct across the admin entries", () => {
        const resolved = resolveSidebarEntries(createAdminSidebarEntries(), {
            isEnterprise: true,
            licensed: false,
        });

        for (const [, label, , children = []] of resolved) {
            const paths = children.map(([path]) => path);

            expect(new Set(paths).size, `${label} has duplicate paths`).toBe(paths.length);
            expect(paths, `${label} rewrote a path`).not.toContain("/enterprise/licenses");
        }
    });
});
