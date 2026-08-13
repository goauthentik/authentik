import { expect, test } from "#e2e";

for (const scheme of ["light", "dark"]) {
    test.describe(`Appearance - ${scheme}`, () => {
        // locking the viewport size to ensure consistent snapshots
        test.use({ colorScheme: scheme, viewport: { width: 1280, height: 800 } });

        test("Dashboard renders", async ({ session, page }) => {
            await test.step("Authenticate", async () =>
                await session.login({ to: "/if/admin/#/administration/overview" }));

            await expect(
                page.locator("html"),
                `Document reports the ${scheme} color scheme`
            ).toHaveAttribute("data-theme", scheme, { timeout: 10_000 });

            await page.waitForTimeout(1000);

            await test.step("Compare the screenshot", async () => {
                await expect(page, `${scheme} matches the baseline`).toHaveScreenshot(
                    `overview-${scheme}.webp`,
                    // Fairly high, but needed to handle how dates and version numbers
                    // can change.
                    {
                        animations: "disabled",
                        caret: "hide",
                        mask: [page.locator("ak-version")],
                        maxDiffPixelRatio: 0.05,
                    }
                );
            });
        });

        test("Table renders", async ({ session, page }) => {
            await test.step("Authenticate", async () =>
                await session.login({ to: "/if/admin/#/events/rules" }));

            await page.getByRole("button", { name: "Expand row" }).first().click();

            await page.waitForTimeout(1000);

            await test.step("Compare the screenshot", async () => {
                await expect(page, `${scheme} matches the baseline`).toHaveScreenshot(
                    `notification-table-${scheme}.webp`,
                    // Tighter, since there are no dates, versions, etc on the page.
                    {
                        animations: "disabled",
                        caret: "hide",
                        maxDiffPixelRatio: 0.02,
                    }
                );
            });
        });

        test("Form renders", async ({ session, page }) => {
            await test.step("Authenticate", async () =>
                await session.login({ to: "/if/admin/#/flow/stages/prompts" }));

            await page.getByRole("button", { name: "New Prompt" }).click();

            await page.waitForTimeout(1000);

            await test.step("Compare the screenshot", async () => {
                await expect(page, `${scheme} matches the baseline`).toHaveScreenshot(
                    `new-prompt-form-${scheme}.webp`,
                    // Tighter, since there are no dates, versions, etc on the page.
                    {
                        animations: "disabled",
                        caret: "hide",
                        maxDiffPixelRatio: 0.02,
                    }
                );
            });
        });
    });
}
