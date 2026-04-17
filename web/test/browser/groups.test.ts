import { expect, test } from "#e2e";
import { randomName } from "#e2e/utils/generators";

import { IDGenerator } from "@goauthentik/core/id";
import { series } from "@goauthentik/core/promises";

import { snakeCase } from "change-case";

test.describe("Groups", () => {
    const adminGroupName = "authentik Admins";
    const adminUsername = "akadmin";
    const usernames = new Map<string, string>();
    const groupNames = new Map<string, string>();

    //#region Lifecycle

    test.beforeEach("Prepare user", async ({ session }, { testId }) => {
        const seed = IDGenerator.randomID(6);
        const groupName = `${randomName(seed)} (${seed})`;

        groupNames.set(testId, groupName);
        usernames.set(testId, snakeCase(groupName));

        await test.step("Authenticate", async () => {
            await session.login({
                to: "/if/admin/#/identity/groups",
            });
        });
    });

    //#endregion

    //#region Tests

    test("Creating a user within the admin group", async ({
        navigator,
        form,
        pointer,
        page,
    }, testInfo) => {
        const { fill, search } = form;
        const { click } = pointer;

        const displayName = groupNames.get(testInfo.testId)!;
        const username = usernames.get(testInfo.testId)!;

        const adminsURL = await test.step("Find admin group via search", async () => {
            const $adminGroupRow = await search(adminGroupName);

            await expect($adminGroupRow, "Admin group is visible").toBeVisible();

            const groupLink = $adminGroupRow.getByRole("link", { name: "view details" });
            await expect(groupLink, "Admin group link is visible").toBeVisible();

            return groupLink.evaluate((el: HTMLAnchorElement) => el.href);
        });

        expect(adminsURL, "Admin group link has href").not.toBeNull();

        await navigator.navigate(adminsURL);

        await test.step("User creation", async () => {
            await click("Users", "tab");

            const dialog = page.getByRole("dialog", { name: "New Group User" });

            await expect(dialog, "Dialog is initially closed").toBeHidden();

            await click("Add New User", "button");

            await click("New Group User...", "menuitem");

            await expect(dialog, "Dialog opens").toBeVisible();

            await series(
                [fill, /^Username/, username, dialog],
                [fill, /^Display Name/, displayName, dialog],
                [fill, /^Email Address/, `${username}@example.com`, dialog],
            );

            await dialog.getByRole("button", { name: "Create User" }).click();

            await dialog.waitFor({ state: "hidden" });

            await expect(dialog, "Dialog closes after creating user").toBeHidden();
        });

        await test.step("Verify user creation", async () => {
            const $user = await test.step("Find user via search", () => {
                const context = page.getByRole("tabpanel", { name: "Users" });

                return search(username, context);
            });

            await expect($user, "User is visible").toBeVisible();
        });
    });

    test("Simple group", async ({ form, pointer, page }, testInfo) => {
        const groupName = groupNames.get(testInfo.testId)!;

        const { fill, search } = form;
        const { click } = pointer;

        const dialog = page.getByRole("dialog", { name: "New Group" });

        await test.step("Group Creation", async () => {
            await expect(dialog, "Dialog is initially closed").toBeHidden();

            await click("New Group", "button");

            await expect(dialog, "Dialog opens").toBeVisible();

            await series(
                // ---
                [fill, /^Group Name/, groupName, dialog],
            );

            const createButton = dialog.getByRole("button", { name: "Create Group" });

            await expect(createButton, "Create button is visible").toBeVisible();
            await createButton.click();

            await expect(dialog, "Dialog closes after creating group").toBeHidden({
                timeout: 10_000,
            });
        });

        await test.step("Verify group creation", async () => {
            const groupRow = await test.step("Find group via search", () => search(groupName));

            await expect(groupRow, "Group is visible").toBeVisible();

            await groupRow.getByRole("link", { name: "view details" }).click();
        });

        await test.step("Assigning a user to the group", async () => {
            const assignUsersModal = page.getByRole("dialog", { name: "Assign Additional Users" });
            const selectUsersModal = page.getByRole("dialog", { name: "Select users" });

            await series(
                // ---
                [click, "users", "tab"],
                [click, "Add existing user", "button"],
                [click, "Open user selection dialog", "button"],
            );

            const adminRow = await test.step("Find admin via search", () =>
                search(adminUsername, selectUsersModal));

            await expect(adminRow, "Admin is visible").toBeVisible();

            await adminRow.getByRole("checkbox").check();

            const confirmButton = selectUsersModal.getByRole("button", { name: "Confirm" });

            await expect(confirmButton, "Confirm button is visible").toBeVisible();
            await confirmButton.click();

            const assignButton = assignUsersModal.getByRole("button", { name: "Assign" });

            await expect(assignButton, "Assign button is visible").toBeVisible();
            await assignButton.click();

            await expect(assignUsersModal, "Assign users modal closes").toBeHidden({
                timeout: 10_000,
            });

            await test.step("Verify admin user assignment", async () => {
                // eslint-disable-next-line max-nested-callbacks
                const groupRow = await test.step("Find group via search", () => {
                    const context = page.getByRole("tabpanel", { name: "Users" });

                    return search(adminUsername, context);
                });

                await expect(groupRow, "Group is visible").toBeVisible();
            });
        });
    });

    test("Edit group from view page", async ({ navigator, form, pointer, page }, testInfo) => {
        const groupName = groupNames.get(testInfo.testId)!;

        const { fill, search } = form;
        const { click } = pointer;

        const newGroupDialog = page.getByRole("dialog", { name: "New Group" });
        const editGroupDialog = page.getByRole("dialog", { name: "Edit Group" });

        await test.step("Create group", async () => {
            await click("New Group", "button");

            await expect(newGroupDialog, "Dialog opens").toBeVisible();

            await fill(/^Group Name/, groupName, newGroupDialog);

            await newGroupDialog.getByRole("button", { name: "Create Group" }).click();

            await expect(newGroupDialog, "Dialog closes after creating group").toBeHidden({
                timeout: 10_000,
            });
        });

        await test.step("Navigate to group view page", async () => {
            const $group = await search(groupName);

            await expect($group, "Group is visible").toBeVisible();

            const viewLink = $group.getByRole("link", { name: "view details" });
            await expect(viewLink, "View details link is visible").toBeVisible();

            await viewLink.click();
        });

        const updatedName = `${groupName} Edited`;

        await test.step("Edit group from view page", async () => {
            await expect(editGroupDialog, "Edit dialog is initially closed").toBeHidden();

            await click("Edit", "button");

            await expect(editGroupDialog, "Edit dialog opens").toBeVisible();

            const nameInput = editGroupDialog.getByRole("textbox", { name: /Group Name/ });

            await expect(nameInput, "Name input is visible").toBeVisible();
            await expect(nameInput, "Name is pre-filled").toHaveValue(groupName);

            await nameInput.fill(updatedName);

            await editGroupDialog.getByRole("button", { name: "Save Changes" }).click();

            await expect(editGroupDialog, "Edit dialog closes after saving").toBeHidden();
        });

        await test.step("Verify group name updated on view page", async () => {
            await expect(
                page.getByRole("heading", { name: updatedName }).first(),
                "Updated group name is visible on view page",
            ).toBeVisible();
        });
    });

    test("Edit group from related group list", async ({
        navigator,
        form,
        pointer,
        page,
    }, testInfo) => {
        const groupName = groupNames.get(testInfo.testId)!;

        const { fill, search } = form;
        const { click } = pointer;

        const newGroupDialog = page.getByRole("dialog", { name: "New Group" });

        await test.step("Create group with admin user", async () => {
            await click("New Group", "button");

            await expect(newGroupDialog, "Dialog opens").toBeVisible();

            await fill(/^Group Name/, groupName, newGroupDialog);

            await newGroupDialog.getByRole("button", { name: "Create Group" }).click();

            await expect(newGroupDialog, "Dialog closes").toBeHidden({ timeout: 10_000 });
        });

        await test.step("Navigate to admin user", async () => {
            await navigator.navigate("/if/admin/#/identity/users");

            const $adminUser = await search(adminUsername);

            await expect($adminUser, "Admin user is visible").toBeVisible();

            const viewLink = $adminUser.getByRole("link", {
                name: "View details for authentik Default Admin",
            });
            await expect(viewLink, "View details link is visible").toBeVisible();

            await viewLink.click();
        });

        await test.step("Add user to group via related group list", async () => {
            await click("Groups", "tab");

            const groupsPanel = page.getByRole("tabpanel", { name: "Groups" });

            const addGroupDialog = page.getByRole("dialog", { name: "Add Group" });

            await expect(addGroupDialog, "Add dialog is initially closed").toBeHidden();

            await groupsPanel.getByRole("button", { name: "Add to existing group" }).click();

            await expect(addGroupDialog, "Add dialog opens").toBeVisible();
        });
    });

    //#endregion
});
