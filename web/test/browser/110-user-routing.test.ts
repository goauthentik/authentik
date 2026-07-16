import { expect, test } from "#e2e";

import type { Page } from "@playwright/test";

const LIBRARY_PATHNAME = "/if/user/library";
const SETTINGS_PATHNAME = "/if/user/settings";

/**
 * Pathname of the document-level navigation entry — the URL of the last full
 * document load, unaffected by pushState/replaceState. Distinguishes
 * same-document (SPA) navigations from full page loads.
 */
const documentLoadPathname = (page: Page): Promise<string> =>
    page.evaluate(() => {
        const [entry] = performance.getEntriesByType("navigation");

        if (!entry) throw new Error("No navigation entry present");

        return new URL(entry.name).pathname;
    });

test.describe("User interface routing", () => {
    test("Deep-load a nested user URL from a fresh page load", async ({ session, page }) => {
        await test.step("Authenticate directly to the settings path", async () => {
            await session.login({ to: SETTINGS_PATHNAME });
        });

        await test.step("Settings page renders at the deep path", async () => {
            await expect(
                page.locator("ak-user-settings"),
                "Settings page renders from a deep load",
            ).toBeVisible();

            expect(new URL(page.url()).pathname, "URL keeps the nested path").toBe(
                SETTINGS_PATHNAME,
            );
        });
    });

    test("Back and forward traverse pushState navigations", async ({
        session,
        navigator,
        page,
    }) => {
        await test.step("Authenticate to the library", async () => {
            await session.login({ to: LIBRARY_PATHNAME });
        });

        await test.step("Navigate to settings in-app", async () => {
            await page.getByRole("link", { name: "Settings", exact: true }).click();
            await navigator.waitForPathname(SETTINGS_PATHNAME);

            await expect(
                page.locator("ak-user-settings"),
                "Settings page renders after in-app navigation",
            ).toBeVisible();
        });

        await test.step("The settings navigation was same-document", async () => {
            expect(
                await documentLoadPathname(page),
                "Document load entry still points at the library",
            ).toBe(LIBRARY_PATHNAME);
        });

        await test.step("Back returns to the library", async () => {
            await page.goBack();
            await navigator.waitForPathname(LIBRARY_PATHNAME);

            await expect(page.locator("ak-library"), "Library renders after back").toBeVisible();
        });

        await test.step("Forward returns to settings", async () => {
            await page.goForward();
            await navigator.waitForPathname(SETTINGS_PATHNAME);

            await expect(
                page.locator("ak-user-settings"),
                "Settings page renders after forward",
            ).toBeVisible();
        });
    });

    test("Search query persists to the URL and across reload", async ({ session, page }) => {
        await test.step("Authenticate to the library", async () => {
            await session.login({ to: LIBRARY_PATHNAME });
        });

        const $search = page.getByPlaceholder("Search for an application by name...");

        await test.step("Type a query", async () => {
            await $search.fill("authentik");

            await expect(page, "URL carries the query as a search param").toHaveURL(
                /[?&]q=authentik/,
            );
        });

        await test.step("Reload keeps the query", async () => {
            await page.reload();

            await expect($search, "Search input restores from the URL").toHaveValue("authentik");
            await expect(page, "URL still carries the query").toHaveURL(/[?&]q=authentik/);
        });
    });

    test("Legacy hash URLs redirect through the shim", async ({ session, navigator, page }) => {
        await test.step("Authenticate", async () => {
            await session.login({ to: LIBRARY_PATHNAME });
        });

        await test.step("Open a legacy hash URL", async () => {
            const legacyParams = encodeURIComponent(JSON.stringify({ page: "page-sources" }));

            await page.goto(`/if/user/#/settings;${legacyParams}`);
            await navigator.waitForPathname("/if/user/settings?page=page-sources");
        });

        await test.step("The deep-linked tab is selected", async () => {
            await expect(
                page.getByRole("tab", { name: "Connected services" }),
                "Connected services tab is selected",
            ).toHaveAttribute("aria-selected", "true");
        });
    });

    test("Cross-interface link to the admin interface is a full page load", async ({
        session,
        navigator,
        page,
    }) => {
        await test.step("Authenticate to the library", async () => {
            await session.login({ to: LIBRARY_PATHNAME });
        });

        await test.step("Open the admin interface", async () => {
            await page.getByRole("link", { name: "Admin interface" }).click();
            await navigator.waitForPathname("/if/admin/");
        });

        await test.step("The navigation was a full document load", async () => {
            expect(
                await documentLoadPathname(page),
                "Document load entry points at the admin interface",
            ).toBe("/if/admin/");
        });
    });
});
