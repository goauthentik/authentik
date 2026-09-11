import { expect, test } from "#e2e";
import type { FormFixture } from "#e2e/fixtures/FormFixture";
import type { NavigatorFixture } from "#e2e/fixtures/NavigatorFixture";
import type { PointerFixture } from "#e2e/fixtures/PointerFixture";
import { randomName } from "#e2e/utils/generators";

import { IDGenerator } from "@goauthentik/core/id";
import { series } from "@goauthentik/core/promises";

import type { Page } from "@playwright/test";
import { snakeCase } from "change-case";

interface CreateUserContext {
    navigator: NavigatorFixture;
    form: FormFixture;
    pointer: PointerFixture;
    page: Page;
}

/**
 * Create an internal user through the admin UI and leave the browser on the users list.
 *
 * Both tests below need a user they own: they assert on a group's member list or on a
 * user's related group list, and reaching for `akadmin` makes them read shared state that
 * every other worker — and every previous run — has been writing to.
 */
async function createInternalUser(
    { navigator, form, pointer, page }: CreateUserContext,
    username: string,
    displayName: string,
): Promise<void> {
    const { fill } = form;
    const { click } = pointer;

    await navigator.navigate("/if/admin/identity/users");

    const dialog = page.getByRole("dialog", { name: "New User Wizard" });

    await click("New User", "button");

    await expect(dialog, "User wizard opens").toBeVisible();

    await dialog.getByRole("radio", { name: "Internal" }).click({ force: true });

    await series(
        [fill, /^Username/, username, dialog],
        [fill, /^Display Name/, displayName, dialog],
        [fill, /^Email Address/, `${username}@example.com`, dialog],
        [fill, /^Path/, "users", dialog],
    );

    await dialog.getByRole("button", { name: "Create" }).click();

    await expect(dialog, "User wizard closes after creation").toBeHidden();
}

test.describe("Groups", () => {
    const usernames = new Map<string, string>();
    const userDisplayNames = new Map<string, string>();
    const groupNames = new Map<string, string>();

    //#region Lifecycle

    test.beforeEach("Prepare user", async ({ session }, { testId }) => {
        const seed = IDGenerator.randomID(6);
        const groupName = `${randomName(seed)} (${seed})`;

        groupNames.set(testId, groupName);
        usernames.set(testId, snakeCase(groupName));
        // Deliberately unlike the group name: tests below assert on a group link by
        // accessible name, and a user sharing that name would match it too.
        userDisplayNames.set(testId, `Member ${randomName(seed)} (${seed})`);

        await test.step("Authenticate", async () => {
            await session.login({
                to: "/if/admin/identity/groups",
            });
        });
    });

    //#endregion

    //#region Tests

    test("Creating a user within a group", async ({ navigator, form, pointer, page }, testInfo) => {
        const { fill, search } = form;
        const { click } = pointer;

        const groupName = groupNames.get(testInfo.testId)!;
        const displayName = userDisplayNames.get(testInfo.testId)!;
        const username = usernames.get(testInfo.testId)!;

        // A group of our own rather than "authentik Admins". The mechanic under test is
        // creating a user from inside a group's Users tab, which doesn't care which group
        // it is — and every worker writing members into the one shared superuser group
        // both couples the tests together and quietly grants those users superuser.
        await test.step("Create the group", async () => {
            const newGroupDialog = page.getByRole("dialog", { name: "New Group" });

            await click("New Group", "button");

            await expect(newGroupDialog, "Dialog opens").toBeVisible();

            await fill(/^Group Name/, groupName, newGroupDialog);

            await newGroupDialog.getByRole("button", { name: "Create Group" }).click();

            await expect(newGroupDialog, "Dialog closes").toBeHidden();
        });

        const groupURL = await test.step("Find the group via search", async () => {
            const $groupRow = await search(groupName);

            await expect($groupRow, "Group is visible").toBeVisible();

            const groupLink = $groupRow.getByRole("link", { name: "view details" });

            await expect(groupLink, "Group link is visible").toBeVisible();

            return groupLink.evaluate((el: HTMLAnchorElement) => el.href);
        });

        expect(groupURL, "Group link has href").not.toBeNull();

        await navigator.navigate(groupURL);

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

    test("Simple group", async ({ navigator, form, pointer, page }, testInfo) => {
        const groupName = groupNames.get(testInfo.testId)!;
        const username = usernames.get(testInfo.testId)!;
        const userDisplayName = userDisplayNames.get(testInfo.testId)!;

        const { fill, search } = form;
        const { click } = pointer;

        const dialog = page.getByRole("dialog", { name: "New Group" });

        await test.step("Create a user to assign", () =>
            createInternalUser({ navigator, form, pointer, page }, username, userDisplayName));

        await test.step("Return to groups", () => navigator.navigate("/if/admin/identity/groups"));

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

            await expect(dialog, "Dialog closes after creating group").toBeHidden();
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

            const userRow = await test.step("Find the user via search", () =>
                search(username, selectUsersModal));

            await expect(userRow, "User is visible").toBeVisible();

            await userRow.getByRole("checkbox").check();

            const confirmButton = selectUsersModal.getByRole("button", { name: "Confirm" });

            await expect(confirmButton, "Confirm button is visible").toBeVisible();
            await confirmButton.click();

            const assignButton = assignUsersModal.getByRole("button", { name: "Assign" });

            await expect(assignButton, "Assign button is visible").toBeVisible();
            await assignButton.click();

            await expect(assignUsersModal, "Assign users modal closes").toBeHidden();

            await test.step("Verify user assignment", async () => {
                // eslint-disable-next-line max-nested-callbacks
                const memberRow = await test.step("Find member via search", () => {
                    const context = page.getByRole("tabpanel", { name: "Users" });

                    return search(username, context);
                });

                await expect(memberRow, "User is a member of the group").toBeVisible();
            });
        });
    });

    test("Edit group from view page", async ({ form, pointer, page }, testInfo) => {
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

            await expect(newGroupDialog, "Dialog closes after creating group").toBeHidden();
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
        const username = usernames.get(testInfo.testId)!;
        const userDisplayName = userDisplayNames.get(testInfo.testId)!;

        const { fill, search } = form;
        const { click } = pointer;

        const newGroupDialog = page.getByRole("dialog", { name: "New Group" });

        await test.step("Create the group", async () => {
            await click("New Group", "button");

            await expect(newGroupDialog, "Dialog opens").toBeVisible();

            await fill(/^Group Name/, groupName, newGroupDialog);

            await newGroupDialog.getByRole("button", { name: "Create Group" }).click();

            await expect(newGroupDialog, "Dialog closes").toBeHidden();
        });

        await test.step("Create a user to add to the group", () =>
            createInternalUser({ navigator, form, pointer, page }, username, userDisplayName));

        await test.step("Navigate to the new user", async () => {
            const $user = await search(username);

            await expect($user, "User is visible").toBeVisible();

            const viewLink = $user.getByRole("link", {
                name: `View details for ${userDisplayName}`,
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

            await test.step("Select group and verify loader message", async () => {
                const selectGroupsDialog = page.getByRole("dialog", {
                    name: "Select Groups",
                });

                await addGroupDialog
                    .getByRole("button", { name: "Add group", exact: true })
                    .click();

                await expect(selectGroupsDialog, "Select groups dialog opens").toBeVisible();
                const groupRow = await search(groupName, selectGroupsDialog);

                await expect(groupRow, "Group is visible in selection").toBeVisible();

                await groupRow.getByRole("checkbox").check();

                await selectGroupsDialog.getByRole("button", { name: "Confirm" }).click();

                await expect(selectGroupsDialog, "Select groups dialog closes").toBeHidden();

                await addGroupDialog
                    .getByRole("button", { name: "Add Group", exact: true })
                    .click();

                await expect(
                    page.getByText("Adding Group..."),
                    "Loader shows 'Adding Group...' not 'Creating Group...'",
                ).toBeVisible();

                await expect(
                    page.getByRole("link", { name: groupName }),
                    "Group appears in the user's related group list",
                ).toBeVisible();
            });
        });
    });

    //#endregion
});
