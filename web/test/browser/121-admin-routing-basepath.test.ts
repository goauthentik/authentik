import { expect, test } from "#e2e";

import type { Page } from "@playwright/test";

const BASE_PATH = "/auth/";

const documentLoadPathname = (page: Page): Promise<string> =>
    page.evaluate(() => {
        const [entry] = performance.getEntriesByType("navigation");

        if (!entry) throw new Error("No navigation entry present");

        return new URL(entry.name).pathname;
    });

test.describe("Admin interface routing under a deployment base path", () => {
    test.skip(
        ({ baseURL }) => new URL(baseURL!).pathname !== BASE_PATH,
        `Requires a stack restarted with AUTHENTIK_WEB__PATH=${BASE_PATH} and ` +
            `AK_TEST_RUNNER_PAGE_URL pointing at the prefixed origin — see the plan's ` +
            `environment step (web.path is baked into Django's urlconf at import time).`,
    );

    test("Deep-load keeps the deployment prefix", async ({ session, page }) => {
        await session.login({ to: `${BASE_PATH}if/admin/identity/users` });

        await expect(
            page.locator("ak-user-list"),
            "Users list renders under the prefix",
        ).toBeVisible();

        expect(new URL(page.url()).pathname, "URL keeps base path and nested path").toBe(
            "/auth/if/admin/identity/users",
        );
    });

    test("In-app navigation keeps the deployment prefix", async ({ session, navigator, page }) => {
        await session.login({ to: `${BASE_PATH}if/admin/administration/overview` });

        await page.getByRole("link", { name: "System Tasks", exact: true }).click();
        await navigator.waitForPathname("/auth/if/admin/administration/system-tasks");

        expect(
            await documentLoadPathname(page),
            "Document load entry still points at the prefixed overview",
        ).toBe("/auth/if/admin/administration/overview");
    });
});
