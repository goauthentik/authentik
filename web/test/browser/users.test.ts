import { expect, test } from "#e2e";
import { randomName } from "#e2e/utils/generators";

import { IDGenerator } from "@goauthentik/core/id";
import { series } from "@goauthentik/core/promises";

import { snakeCase } from "change-case";

test.describe("Users", () => {
    const usernames = new Map<string, string>();
    const displayNames = new Map<string, string>();

    //#region Lifecycle

    test.beforeEach("Prepare user", async ({ session }, { testId }) => {
        const seed = IDGenerator.randomID(6);
        const displayName = `${randomName(seed)} (${seed})`;

        displayNames.set(testId, displayName);
        usernames.set(testId, snakeCase(displayName));

        await test.step("Authenticate", async () => {
            await session.login({
                to: "/if/admin/#/identity/users",
            });
        });
    });

    test.afterEach("Verification", async ({ form }, { testId }) => {
        //#region Confirm user

        const username = usernames.get(testId)!;
        const { search } = form;

        const $user = await test.step("Find user via search", () => search(username));

        await expect($user, "User is visible").toBeVisible();

        //#endregion
    });

    //#endregion

    //#region Tests

    // TODO: The use of `force: true` is a temporary workaround for
    // buttons with slotted content, which are not considered visible by
    // Playwright. This should be removed after native dialog modals are implemented.

    test("Simple user", async ({ form, pointer, page }, testInfo) => {
        const displayName = displayNames.get(testInfo.testId)!;
        const username = usernames.get(testInfo.testId)!;

        const { fill } = form;
        const { click } = pointer;

        const dialog = page.getByRole("dialog", { name: "New User" });

        await expect(dialog, "Dialog is initially closed").toBeHidden();

        await click("New User", "button");

        await expect(dialog, "Dialog opens").toBeVisible();

        await series(
            [fill, /^Username/, username, dialog],
            [fill, /^Display Name/, displayName, dialog],
            [fill, /^Email Address/, `${username}@example.com`, dialog],
        );

        await dialog.getByRole("button", { name: "Create User" }).click();

        await expect(dialog, "Dialog closes after creating user").toBeHidden();
    });

    test("Service user", async ({ form, pointer, page }, testInfo) => {
        const username = usernames.get(testInfo.testId)!;

        const { fill } = form;
        const { click } = pointer;

        const dialog = page.getByRole("dialog", { name: "New Service Account" });

        await expect(dialog, "Dialog is initially closed").toBeHidden();

        await click("New Service Account", "button");

        await expect(dialog, "Dialog opens").toBeVisible();

        await series(
            // ---
            [fill, /^Username/, username, dialog],
        );

        await dialog.getByRole("button", { name: "Create Service Account" }).click();

        await expect(dialog, "Dialog is open after creating service account").toBeVisible();

        await click("Close", "button", dialog);

        const userPathsTree = page.getByRole("tree", { name: "User paths" });
        await expect(userPathsTree, "User paths tree is visible").toBeVisible();

        await userPathsTree.getByRole("button", { name: `Select "Root"`, exact: true }).click();
    });

    //#endregion
});

test.describe("Impersonation", () => {
    const usernames = new Map<string, string>();
    const displayNames = new Map<string, string>();

    test.beforeEach("Prepare user", async ({ session }, { testId }) => {
        const seed = IDGenerator.randomID(6);
        const displayName = `${randomName(seed)} (${seed})`;

        displayNames.set(testId, displayName);
        usernames.set(testId, snakeCase(displayName));

        await test.step("Authenticate", async () => {
            await session.login({
                to: "/if/admin/#/identity/users",
            });
        });
    });

    test("Impersonate user", async ({ form, pointer, page, navigator }, testInfo) => {
        const displayName = displayNames.get(testInfo.testId)!;
        const username = usernames.get(testInfo.testId)!;

        const { fill, search } = form;
        const { click } = pointer;

        const createDialog = page.getByRole("dialog", { name: "New User" });
        const impersonateDialog = page.getByRole("dialog", { name: "Impersonate User" });

        await test.step("Create user", async () => {
            await click("New User", "button");

            await expect(createDialog, "Create dialog opens").toBeVisible();

            await series(
                [fill, /^Username/, username, createDialog],
                [fill, /^Display Name/, displayName, createDialog],
                [fill, /^Email Address/, `${username}@example.com`, createDialog],
            );

            await createDialog.getByRole("button", { name: "Create User" }).click();

            await createDialog.waitFor({ state: "hidden" });
            await expect(createDialog, "Create dialog closes").toBeHidden();
        });

        await test.step("Open impersonate dialog", async () => {
            const $user = await search(username);

            await expect($user, "User is visible").toBeVisible();

            const impersonateButton = $user.getByRole("button", { name: "Impersonate" });
            await expect(impersonateButton, "Impersonate button is visible").toBeVisible();

            await impersonateButton.click();

            await expect(impersonateDialog, "Impersonate dialog opens").toBeVisible();

            const reasonInput = impersonateDialog.getByRole("textbox", { name: /Reason/ });
            await fill(reasonInput, "Testing impersonation");

            await impersonateDialog.getByRole("button", { name: "Impersonate" }).click();

            await navigator.waitForPathname("if/user/#/library");
        });

        await test.step("Confirm impersonation", async () => {
            const banner = page.getByRole("banner", { name: "Main" });

            await expect(
                banner,
                "User library banner is visible after impersonation",
            ).toBeVisible();

            const stopImpersonationButton = banner.getByRole("button", {
                name: "Stop impersonation",
            });

            await expect(
                stopImpersonationButton,
                "Stop impersonation button is visible",
            ).toBeVisible();
        });
    });
});
