import { expect, test } from "#e2e";

import type { Page } from "@playwright/test";

const OVERVIEW = "/if/admin/administration/overview";
const SYSTEM_TASKS = "/if/admin/administration/system-tasks";
const APPLICATIONS = "/if/admin/core/applications";
const USERS = "/if/admin/identity/users";

const documentLoadPathname = (page: Page): Promise<string> =>
    page.evaluate(() => {
        const [entry] = performance.getEntriesByType("navigation");

        if (!entry) throw new Error("No navigation entry present");

        return new URL(entry.name).pathname;
    });

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
