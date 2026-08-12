import { expect, test } from "#e2e";

const USERS = "/if/admin/identity/users";

test.describe("Modal URL restore", () => {
    test("A modal restores search params written while it was open", async ({ session, page }) => {
        await session.login({ to: USERS });

        // The New User wizard is an AKModal (native dialog).
        await page.getByRole("button", { name: "New User", exact: true }).first().click();

        const dialog = page.getByRole("dialog", { name: "New User Wizard" });
        await expect(dialog, "Wizard opens").toBeVisible();

        // Simulate content inside the modal — e.g. a paginated table — writing a
        // search parameter to the page URL while the modal is open.
        await page.evaluate(() => {
            const url = new URL(window.location.href);
            url.searchParams.set("ak-modal-table-page", "2");
            history.replaceState(history.state, "", url.href);
        });

        await expect(page, "Param is present while the modal is open").toHaveURL(
            /[?&]ak-modal-table-page=2/,
        );

        await dialog.getByText("Cancel", { exact: true }).click();
        await expect(dialog, "Wizard closes").toBeHidden();

        // On close the modal restores the URL captured when it opened, dropping
        // the parameter its content added.
        await expect(page, "Param is cleared after the modal closes").not.toHaveURL(
            /ak-modal-table-page/,
        );
        expect(new URL(page.url()).pathname, "Path is unchanged").toBe(USERS);
    });
});
