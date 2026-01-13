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

    // TODO: The use of `force: true` is a temporary workaround for
    // buttons with slotted content, which are not considered visible by
    // Playwright. This should be removed after native dialog modals are implemented.

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

            const wizard = page.getByRole("dialog", { name: "New User" });

            await expect(wizard, "Wizard is initially closed").toBeHidden();

            await click("Add new user", "button");

            await click("New user...", "menuitem");

            await expect(wizard, "Wizard opens").toBeVisible();

            await series(
                [fill, /^Username/, username],
                [fill, /^Display Name/, displayName],
                [fill, /^Email Address/, `${username}@example.com`],
            );

            await page.getByRole("button", { name: "Create User" }).click({ force: true });

            await expect(wizard, "Wizard closes after creating user").toBeHidden();
        });

        await test.step("Verify user creation", async () => {
            const $user = await test.step("Find user via search", () => search(username));

            await expect($user, "User is visible").toBeVisible();
        });
    });

    test("Simple group", async ({ form, pointer, page }, testInfo) => {
        const groupName = groupNames.get(testInfo.testId)!;

        const { fill, search } = form;
        const { click } = pointer;

        const newGroupModal = page.getByRole("dialog", { name: "New Group" });

        await test.step("Group Creation", async () => {
            await expect(newGroupModal, "Wizard is initially closed").toBeHidden();

            await click("New Group", "button");

            await expect(newGroupModal, "Wizard opens").toBeVisible();

            await series(
                // ---
                [fill, /^Group Name/, groupName],
            );

            const createButton = page
                .getByRole("group", { name: "Form actions" })
                .getByRole("button", { name: "Create Group" });

            await expect(createButton, "Create button is visible").toBeVisible();
            await createButton.evaluate((element: HTMLButtonElement) => element.click());

            await expect(newGroupModal, "Wizard closes after creating group").toBeHidden();
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
            await confirmButton.evaluate((element: HTMLButtonElement) => element.click());

            const assignButton = assignUsersModal.getByRole("button", { name: "Assign" });

            await expect(assignButton, "Assign button is visible").toBeVisible();
            await assignButton.evaluate((element: HTMLButtonElement) => element.click());

            await expect(assignUsersModal, "Assign users modal closes").toBeHidden();

            await test.step("Verify admin user assignment", async () => {
                // eslint-disable-next-line max-nested-callbacks
                const groupRow = await test.step("Find group via search", () =>
                    search(adminUsername));

                await expect(groupRow, "Group is visible").toBeVisible();
            });
        });
    });

    //#endregion
});
