import { expect, test } from "#e2e";

import type { Page } from "@playwright/test";

const BASE_PATH = "/auth/";

const documentLoadPathname = (page: Page): Promise<string> =>
    page.evaluate(() => {
        const [entry] = performance.getEntriesByType("navigation");

        if (!entry) throw new Error("No navigation entry present");

        return new URL(entry.name).pathname;
    });

test.describe("User interface routing under a deployment base path", () => {
    test.skip(
        ({ baseURL }) => new URL(baseURL!).pathname !== BASE_PATH,
        `Requires a stack restarted with AUTHENTIK_WEB__PATH=${BASE_PATH} and ` +
            `AK_TEST_RUNNER_PAGE_URL pointing at the prefixed origin — see the plan's ` +
            `environment step (web.path is baked into Django's urlconf at import time).`,
    );

    test("Deep-load keeps the deployment prefix", async ({ session, page }) => {
        await test.step("Authenticate directly to the prefixed settings path", async () => {
            await session.login({ to: `${BASE_PATH}if/user/settings` });
        });

        await test.step("Settings page renders under the prefix", async () => {
            await expect(
                page.locator("ak-user-settings"),
                "Settings page renders under the prefix",
            ).toBeVisible();

            expect(new URL(page.url()).pathname, "URL keeps base path and nested path").toBe(
                "/auth/if/user/settings",
            );
        });
    });

    test("In-app navigation keeps the deployment prefix", async ({ session, navigator, page }) => {
        await test.step("Authenticate to the prefixed library", async () => {
            await session.login({ to: `${BASE_PATH}if/user/library` });
        });

        await test.step("Navigate to settings in-app", async () => {
            await page.getByRole("link", { name: "Settings", exact: true }).click();
            await navigator.waitForPathname("/auth/if/user/settings");
        });

        await test.step("The navigation was same-document", async () => {
            expect(
                await documentLoadPathname(page),
                "Document load entry still points at the prefixed library",
            ).toBe("/auth/if/user/library");
        });
    });
});
