import { expect, test } from "#e2e";

import type { Locator, Page } from "@playwright/test";

const OVERVIEW = "/if/admin/administration/overview";
const SYSTEM_TASKS = "/if/admin/administration/system-tasks";
const APPLICATIONS = "/if/admin/core/applications";
const USERS = "/if/admin/identity/users";
const STAGES = "/if/admin/flow/stages";
const PROMPTS = "/if/admin/flow/stages/prompts";

const documentLoadPathname = (page: Page): Promise<string> =>
    page.evaluate(() => {
        const [entry] = performance.getEntriesByType("navigation");

        if (!entry) throw new Error("No navigation entry present");

        return new URL(entry.name).pathname;
    });

/**
 * A collapsible sidebar group, addressed by its toggle button. The accessible
 * name carries an "Expand"/"Collapse" prefix, so match on the label alone.
 */
const sidebarGroup = (page: Page, label: string): Locator =>
    page.getByRole("button", { name: new RegExp(label) });

const sidebarLink = (page: Page, label: string): Locator =>
    page.getByRole("link", { name: label, exact: true });

const expectCurrent = (link: Locator, message: string) =>
    expect(link, message).toHaveAttribute("aria-current", "page");

const expectNotCurrent = (link: Locator, message: string) =>
    expect(link, message).not.toHaveAttribute("aria-current", "page");

const expectExpanded = (group: Locator, expanded: boolean, message: string) =>
    expect(group, message).toHaveAttribute("aria-expanded", `${expanded}`);

test.describe("Admin interface routing", () => {
    test("Deep-load a nested admin path", async ({ session, page }) => {
        await session.login({ to: APPLICATIONS });

        await expect(
            page.locator("ak-application-list"),
            "Applications list renders",
        ).toBeVisible();

        expect(new URL(page.url()).pathname, "URL keeps the nested path").toBe(APPLICATIONS);
    });

    test("Deep-load a param route (flow detail)", async ({ session, navigator, page }) => {
        // Default flows are always seeded, so a detail link is guaranteed.
        await session.login({ to: "/if/admin/flow/flows" });

        const firstLink = page.locator("ak-flow-list a[href*='/if/admin/flow/flows/']").first();

        await expect(firstLink, "A flow detail link is present").toBeVisible({ timeout: 15_000 });

        const href = await firstLink.getAttribute("href");
        await firstLink.click();
        await navigator.waitForPathname(new URL(href!, page.url()).pathname);

        await expect(page.locator("ak-flow-view"), "Flow detail renders").toBeVisible();
    });

    test("Back and forward traverse pushState navigations", async ({
        session,
        navigator,
        page,
    }) => {
        await session.login({ to: OVERVIEW });

        // "System Tasks" lives in the default-expanded "Dashboards" section, so
        // its sidebar link is visible without expanding a collapsed group.
        await page.getByRole("link", { name: "System Tasks", exact: true }).click();
        await navigator.waitForPathname(SYSTEM_TASKS);

        expect(await documentLoadPathname(page), "System Tasks nav was same-document").toBe(
            OVERVIEW,
        );

        await page.goBack();
        await navigator.waitForPathname(OVERVIEW);

        await expect(
            page.locator("ak-admin-overview"),
            "Overview renders after back",
        ).toBeVisible();

        await page.goForward();
        await navigator.waitForPathname(SYSTEM_TASKS);

        await expect(
            page.locator("ak-system-tasks"),
            "System Tasks renders after forward",
        ).toBeVisible();
    });

    test("Table search persists to ?q= and survives reload", async ({ session, page }) => {
        // The applications list uses the standard (non-QL) table search.
        await session.login({ to: APPLICATIONS });

        const search = page.locator("input[placeholder*='Search for application']").first();
        await search.fill("authentik");
        await search.press("Enter");

        await expect(page, "URL carries the search as ?q=").toHaveURL(/[?&]q=authentik/);

        await page.reload();

        await expect(page, "URL still carries ?q= after reload").toHaveURL(/[?&]q=authentik/);
    });

    test("Legacy admin hash URL redirects through the shim", async ({
        session,
        navigator,
        page,
    }) => {
        await session.login({ to: OVERVIEW });

        await page.goto("/if/admin/#/identity/users");
        await navigator.waitForPathname(USERS);

        await expect(
            page.locator("ak-user-list"),
            "Users list renders after shim redirect",
        ).toBeVisible();
    });

    test("Sidebar follows the active route", async ({ session, navigator, page }) => {
        await session.login({ to: OVERVIEW });

        const group = sidebarGroup(page, "Flows and Stages");
        const stages = sidebarLink(page, "Stages");
        const prompts = sidebarLink(page, "Prompts");

        await test.step("Navigate to Stages via the sidebar", async () => {
            await group.click();
            await stages.click();
            await navigator.waitForPathname(STAGES);

            await expectCurrent(stages, "Stages is marked current");
        });

        await test.step("Deep load restores both markers", async () => {
            await page.reload();

            await expect(
                page.locator("ak-stage-list"),
                "Stages list renders after reload",
            ).toBeVisible({ timeout: 15_000 });

            await expectCurrent(stages, "Stages is still marked current");
            await expectExpanded(group, true, "Parent group expands without a manual click");
        });

        await test.step("Track pushState and history navigation", async () => {
            await prompts.click();
            await navigator.waitForPathname(PROMPTS);

            await expectCurrent(prompts, "Prompts becomes current");
            await expectNotCurrent(stages, "Stages gives up current");

            await page.goBack();
            await navigator.waitForPathname(STAGES);

            await expectCurrent(stages, "Stages is current again after back");
        });
    });

    test("Sidebar remembers expanded groups", async ({ session, navigator, page }) => {
        // Land outside the groups under test: a group holding the active route is
        // re-expanded on load no matter what was persisted.
        await session.login({ to: APPLICATIONS });

        const directory = sidebarGroup(page, "Directory");
        const dashboards = sidebarGroup(page, "Dashboards");
        const flows = sidebarGroup(page, "Flows and Stages");

        await test.step("Toggles survive a reload", async () => {
            await expectExpanded(directory, false, "Directory starts collapsed");
            await expectExpanded(dashboards, true, "Dashboards starts expanded by default");

            await directory.click();
            await dashboards.click();

            await page.reload();

            await expectExpanded(directory, true, "Directory is still expanded");
            await expectExpanded(dashboards, false, "Dashboards is still collapsed");
        });

        await test.step("Active route outranks a persisted collapse", async () => {
            await flows.click();
            await sidebarLink(page, "Stages").click();
            await navigator.waitForPathname(STAGES);

            await flows.click();

            await expectExpanded(flows, false, "Group collapses while its route is active");

            await page.reload();

            await expect(
                page.locator("ak-stage-list"),
                "Stages list renders after reload",
            ).toBeVisible({ timeout: 15_000 });

            await expectExpanded(flows, true, "Route expansion wins over the persisted collapse");
        });
    });

    test("Cross-interface link to the user interface is a full page load", async ({
        session,
        navigator,
        page,
    }) => {
        await session.login({ to: OVERVIEW });

        await page.getByRole("link", { name: "User interface" }).click();
        await navigator.waitForPathname("/if/user/");

        // The navbar links to the interface root (`/if/user/`); the user interface
        // then client-redirects to `/library`, so the document load lands on the root.
        expect(await documentLoadPathname(page), "User-interface nav was a full load").toBe(
            "/if/user/",
        );
    });
});
