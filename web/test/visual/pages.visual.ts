import { ColorSchemes, skipWithoutBaseline } from "./capture.ts";

import { expect, test } from "#e2e";

for (const scheme of ColorSchemes) {
    test.describe(scheme, () => {
        test.use({ colorScheme: scheme });

        test("Login page", async ({ session, navigator, page }, testInfo) => {
            const name = `login--${scheme}.png`;

            await session.toLoginPage();

            await expect(session.$usernameField).toBeVisible();
            await navigator.waitForContent();

            skipWithoutBaseline(testInfo, name);

            await expect(page).toHaveScreenshot(name);
        });

        test("Form in a modal", async ({ session, navigator, page }, testInfo) => {
            const name = `new-prompt-form--${scheme}.png`;
            const dialog = page.getByRole("dialog");

            await session.login({ to: "/if/admin/flow/stages/prompts" });

            await page
                .locator('[part="toolbar-secondary"]')
                .getByRole("button", { name: "New Prompt" })
                .click();

            await expect(dialog).toBeVisible();
            // The preview keeps loading until the form is filled in.
            await navigator.waitForContent({ allowLoading: true });

            skipWithoutBaseline(testInfo, name);

            await expect(dialog).toHaveScreenshot(name);
        });

        test("Wizard", async ({ session, navigator, page }, testInfo) => {
            const name = `new-provider-wizard--${scheme}.png`;
            const dialog = page.getByRole("dialog", { name: "New Provider Wizard" });

            await session.login({ to: "/if/admin/core/providers" });

            await page
                .locator('[part="toolbar-secondary"]')
                .getByRole("button", { name: "New Provider" })
                .click();

            await expect(page.getByRole("listbox", { name: "Choose Provider Type" })).toBeVisible();
            await navigator.waitForContent();

            skipWithoutBaseline(testInfo, name);

            // Provider icons are server assets whose antialiasing varies between loads.
            await expect(dialog).toHaveScreenshot(name, { mask: [dialog.locator("img")] });
        });
    });
}
