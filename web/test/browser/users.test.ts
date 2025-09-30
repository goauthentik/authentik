import { expect, test } from "#e2e";
import { randomName } from "#e2e/utils/generators";
import { ConsoleLogger } from "#logger/node";

import { IDGenerator } from "@goauthentik/core/id";
import { series } from "@goauthentik/core/promises";

import { snakeCase } from "change-case";

test.describe("Users", () => {
    const usernames = new Map<string, string>();
    const displayNames = new Map<string, string>();

    //#region Lifecycle

    test.beforeEach("Prepare user", async ({ page, session }, { testId }) => {
        const seed = IDGenerator.randomID(6);
        const displayName = `${randomName(seed)} (${seed})`;

        displayNames.set(testId, displayName);
        usernames.set(testId, snakeCase(displayName));

        const wizard = page.getByRole("dialog", { name: "New User" });

        await test.step("Authenticate", async () => {
            await session.login({
                to: "/if/admin/#/identity/users",
            });
        });

        await test.step("Navigate to new user wizard", async () => {
            await expect(wizard, "Wizard is initially closed").toBeHidden();

            await page.getByRole("button", { name: "New User" }).click();

            await expect(wizard, "Wizard opens after clicking on New User").toBeVisible();
        });
    });

    test.afterEach("Verification", async ({ page, form }, { testId }) => {
        //#region Confirm user

        const username = usernames.get(testId)!;
        const { fill, findTextualInput } = form;

        const $user = await test.step("Find user via search", async () => {
            const userSearch = await findTextualInput("User Search");
            // We have to wait for the user to appear in the table,
            // but several UI elements will be rendered asynchronously.
            // We attempt several times to find the user to avoid flakiness.

            const tries = 10;
            let found = false;

            for (let i = 0; i < tries; i++) {
                await fill(userSearch, username);
                await userSearch.press("Enter");

                const $rowEntry = page.getByRole("row", {
                    name: username,
                });

                ConsoleLogger.info(
                    `${i + 1}/${tries} Waiting for user ${username} to appear in the table`,
                );

                found = await $rowEntry
                    .waitFor({
                        timeout: 1500,
                    })
                    .then(() => true)
                    .catch(() => false);

                if (found) {
                    ConsoleLogger.info(`User ${username} found in the table`);
                    return $rowEntry;
                }
            }

            throw new Error(`User ${username} not found in the table`);
        });

        await expect($user, "User is visible").toBeVisible();

        //#endregion
    });

    //#endregion

    //#region Tests

    test("Simple user", async ({ form, pointer, page }, testInfo) => {
        const displayName = displayNames.get(testInfo.testId)!;
        const username = usernames.get(testInfo.testId)!;
        const { fill } = form;
        const { click } = pointer;
        const wizard = page.getByRole("dialog", { name: "New User" });

        await expect(wizard, "Wizard is open at start of test").toBeVisible();

        await series(
            [fill, /^Username/, username],
            [fill, /^Display Name/, displayName],
            [fill, /^Email Address/, `${username}@example.com`],
            // [click, /^Create User/, "button"],
        );

        await click("Create User", "button");
        await expect(wizard, "Wizard closes after creating user").toBeHidden();
    });

    //#endregion
});
