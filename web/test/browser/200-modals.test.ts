import { expect, test } from "#e2e";

test.describe("Modals", () => {
    test.beforeEach("Authenticate", async ({ session }) => {
        await session.login({
            to: "/if/admin/",
        });
    });

    test("About authentik modal", async ({ page }) => {
        const aboutButton = page
            .getByRole("contentinfo", { name: "authentik information" })
            .getByRole("button", { name: "Open about dialog" });

        await expect(aboutButton, "About button is visible").toBeVisible();

        const aboutDialog = page.getByRole("dialog", { name: "About authentik" });

        await expect(aboutDialog, "About dialog is initially closed").toBeHidden();

        await aboutButton.click();

        await expect(aboutDialog, "About dialog opens").toBeVisible();

        await test.step("Verify content loads", async () => {
            const definitionList = aboutDialog.getByRole("definition");

            // Wait for the API data to load (replaces the loading spinner)
            await definitionList.first().waitFor({ state: "visible" });

            // Verify key entries are present
            await expect(
                aboutDialog.getByText("UI Version"),
                "Version label is visible",
            ).toBeVisible();
        });

        await test.step("Close dialog", async () => {
            const closeButton = aboutDialog.getByRole("button", { name: "Close dialog" });

            await closeButton.click();

            await expect(aboutDialog, "About dialog closes").toBeHidden();
        });

        await test.step("Dialog removed from DOM", async () => {
            const dialogElement = page.locator("dialog:has(ak-about-modal)");

            await expect(
                dialogElement,
                "Dialog element is removed from the DOM after close",
            ).toHaveCount(0);
        });
    });
});
