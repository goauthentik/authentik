import { expect, test } from "#e2e";

import { IDGenerator } from "@goauthentik/core/id";

const DEFAULT_BRAND_DOMAIN = "authentik-default";

const LOGO_SVG = `<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"/>`;

test.describe("Brands", () => {
    test("Upload a logo from the brand form", async ({ session, form, page }) => {
        const fileName = `e2e-brand-logo-${IDGenerator.randomID(6).toLowerCase()}`;

        await test.step("Authenticate", async () => {
            await session.login({ to: "/if/admin/core/brands" });
        });

        const dialog = page.getByRole("dialog", { name: "Edit Brand" });

        await test.step("Edit the default brand", async () => {
            const $brand = await form.search(DEFAULT_BRAND_DOMAIN);

            await $brand.getByRole("button", { name: /^Edit .*Brand$/ }).click();
            await expect(dialog, "Edit modal opens").toBeVisible();

            await form.setFormGroup("Branding settings", true, dialog);
        });

        const brandingGroup = dialog.locator("ak-form-group", { hasText: "Branding settings" });
        const logoField = dialog.locator('ak-file-search-input[name="brandingLogo"]');

        await test.step("Upload a file through the logo picker", async () => {
            await logoField.getByRole("button", { name: "Upload file" }).click();

            const uploadDialog = page.getByRole("dialog", { name: "Select File" });
            await expect(uploadDialog, "Upload modal opens").toBeVisible();

            await uploadDialog.locator('input[type="file"]').setInputFiles({
                name: "logo.svg",
                mimeType: "image/svg+xml",
                buffer: Buffer.from(LOGO_SVG),
            });

            await form.fill("Custom Name", fileName, uploadDialog);
            await uploadDialog.getByRole("button", { name: /^Upload/ }).click();

            await expect(uploadDialog, "Upload modal closes").toBeHidden();
        });

        await test.step("Brand form keeps its state and selects the upload", async () => {
            await expect(brandingGroup, "Branding group stays open").toHaveAttribute("open");

            const { combobox } = await form.findSearchSelect("Logo", dialog);

            await expect(combobox, "Uploaded file is selected").toHaveValue(
                new RegExp(`${fileName}\\.svg`),
            );
        });

        await dialog.getByRole("button", { name: "Cancel" }).click();
        await expect(dialog, "Edit modal closes").toBeHidden();
    });
});
