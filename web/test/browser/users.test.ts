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

        const wizard = page.getByRole("dialog", { name: "New User" });

        await expect(wizard, "Wizard is initially closed").toBeHidden();

        await click("New User", "button");

        await expect(wizard, "Wizard opens").toBeVisible();

        await series(
            [fill, /^Username/, username],
            [fill, /^Display Name/, displayName],
            [fill, /^Email Address/, `${username}@example.com`],
        );

        await page.getByRole("button", { name: "Create User" }).click({ force: true });

        await expect(wizard, "Wizard closes after creating user").toBeHidden();
    });

    test("Service user", async ({ form, pointer, page }, testInfo) => {
        const username = usernames.get(testInfo.testId)!;

        const { fill } = form;
        const { click } = pointer;

        const wizard = page.getByRole("dialog", { name: "New Service Account" });

        await expect(wizard, "Wizard is initially closed").toBeHidden();

        await click("New Service Account", "button");

        await expect(wizard, "Wizard opens").toBeVisible();

        await series(
            // ---
            [fill, /^Username/, username],
        );

        await page.getByRole("button", { name: "Create Service Account" }).click({ force: true });

        await expect(wizard, "Wizard is open after creating service account").toBeVisible();

        await click("Close", "button");

        const userPathsTree = page.getByRole("tree", { name: "User paths" });
        await expect(userPathsTree, "User paths tree is visible").toBeVisible();

        await userPathsTree.getByRole("button", { name: `Select "Root"`, exact: true }).click();
    });

    //#endregion
});
