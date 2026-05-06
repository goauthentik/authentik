import { expect, test } from "#e2e";
import { randomName } from "#e2e/utils/generators";

import { IDGenerator } from "@goauthentik/core/id";

test.describe("Roles", () => {
    const roleNames = new Map<string, string>();

    //#region Lifecycle

    test.beforeEach("Prepare role", async ({ session }, { testId }) => {
        const seed = IDGenerator.randomID(6);
        const roleName = `${randomName(seed)} (${seed})`;

        roleNames.set(testId, roleName);

        await test.step("Authenticate", async () => {
            await session.login({
                to: "/if/admin/#/identity/roles",
            });
        });
    });

    //#endregion

    //#region Tests

    test("Simple role", async ({ form, pointer, page }, testInfo) => {
        const roleName = roleNames.get(testInfo.testId)!;

        const { fill, search } = form;
        const { click } = pointer;

        const dialog = page.getByRole("dialog", { name: "New Role" });

        await test.step("Create role", async () => {
            await expect(dialog, "Dialog is initially closed").toBeHidden();

            await click("New Role", "button");

            await expect(dialog, "Dialog opens").toBeVisible();

            await fill(/^Role Name/, roleName, dialog);

            await dialog.getByRole("button", { name: "Create Role" }).click();

            await expect(dialog, "Dialog closes after creating role").toBeHidden();
        });

        await test.step("Verify role creation", async () => {
            const $role = await search(roleName);

            await expect($role, "Role is visible in the table").toBeVisible();
        });
    });

    test("Edit role", async ({ form, pointer, page }, testInfo) => {
        const roleName = roleNames.get(testInfo.testId)!;

        const { fill, search } = form;
        const { click } = pointer;

        const newRoleDialog = page.getByRole("dialog", { name: "New Role" });
        const editRoleDialog = page.getByRole("dialog", { name: "Edit Role" });

        await test.step("Create role", async () => {
            await click("New Role", "button");

            await expect(newRoleDialog, "Dialog opens").toBeVisible();

            await fill(/^Role Name/, roleName, newRoleDialog);

            await newRoleDialog.getByRole("button", { name: "Create Role" }).click();

            await expect(newRoleDialog, "Dialog closes after creating role").toBeHidden();
        });

        const updatedName = `${roleName} Edited`;

        await test.step("Edit role via row action", async () => {
            const $role = await search(roleName);

            await expect($role, "Role is visible").toBeVisible();

            await $role.getByRole("button", { name: "Edit" }).click();

            await expect(editRoleDialog, "Edit dialog opens").toBeVisible();

            const nameInput = editRoleDialog.getByRole("textbox", { name: /Role Name/ });

            await expect(nameInput, "Name input is visible").toBeVisible();

            await expect(nameInput, "Name is pre-filled").toHaveValue(roleName);

            await nameInput.fill(updatedName);

            await editRoleDialog.getByRole("button", { name: "Save Changes" }).click();

            await expect(editRoleDialog, "Edit dialog closes after saving").toBeHidden();
        });

        await test.step("Verify role was updated", async () => {
            const $updatedRole = await search(updatedName);

            await expect($updatedRole, "Updated role is visible in the table").toBeVisible();
        });
    });

    test("Edit role from view page", async ({ navigator, form, pointer, page }, testInfo) => {
        const roleName = roleNames.get(testInfo.testId)!;

        const { fill, search } = form;
        const { click } = pointer;

        const newRoleDialog = page.getByRole("dialog", { name: "New Role" });
        const editRoleDialog = page.getByRole("dialog", { name: "Edit Role" });

        await test.step("Create role", async () => {
            await click("New Role", "button");

            await expect(newRoleDialog, "Dialog opens").toBeVisible();

            await fill(/^Role Name/, roleName, newRoleDialog);

            await newRoleDialog.getByRole("button", { name: "Create Role" }).click();

            await expect(newRoleDialog, "Dialog closes after creating role").toBeHidden();
        });

        await test.step("Navigate to role view page", async () => {
            const $role = await search(roleName);

            await expect($role, "Role is visible").toBeVisible();

            const viewLink = $role.getByRole("link", { name: "view details" });
            await expect(viewLink, "View details link is visible").toBeVisible();

            const viewURL = await viewLink.evaluate((el: HTMLAnchorElement) => el.href);
            await navigator.navigate(viewURL);
        });

        const updatedName = `${roleName} View Edited`;

        await test.step("Edit role from view page", async () => {
            await expect(editRoleDialog, "Edit dialog is initially closed").toBeHidden();

            await click("Edit", "button");

            await expect(editRoleDialog, "Edit dialog opens").toBeVisible();

            const nameInput = editRoleDialog.getByRole("textbox", { name: /Role Name/ });

            await expect(nameInput, "Name input is visible").toBeVisible();
            await expect(nameInput, "Name is pre-filled").toHaveValue(roleName);

            await nameInput.fill(updatedName);

            await editRoleDialog.getByRole("button", { name: "Save Changes" }).click();

            await expect(editRoleDialog, "Edit dialog closes after saving").toBeHidden();
        });

        await test.step("Verify role name updated on view page", async () => {
            await expect(
                page.getByText(updatedName),
                "Updated role name is visible on view page",
            ).toBeVisible();
        });
    });

    //#endregion
});
