import { expect, test } from "#e2e";
import { randomName } from "#e2e/utils/generators";

import { IDGenerator } from "@goauthentik/core/id";
import { series } from "@goauthentik/core/promises";

test.describe("Applications", () => {
    const providerNames = new Map<string, string>();

    //#region Lifecycle

    test.beforeEach("Configure Providers", async ({ page: _page }, { testId }) => {
        const seed = IDGenerator.randomID(6);
        const providerName = `${randomName(seed)} (${seed})`;

        providerNames.set(testId, providerName);
    });

    test("Create application with existing provider", async ({
        session,
        navigator,
        form,
        pointer,
        page,
    }, testInfo) => {
        const providerName = providerNames.get(testInfo.testId)!;
        const appName = `${providerName} App`;

        const { fill, search, selectSearchValue } = form;
        const { click } = pointer;

        await test.step("Authenticate", async () => {
            await session.login({
                to: "/if/admin/#/core/providers",
            });
        });

        //#region Create provider

        const providerDialog = page.getByRole("dialog", { name: "New provider" });

        await test.step("Create OAuth2 provider", async () => {
            await expect(providerDialog, "Provider dialog is initially closed").toBeHidden();

            await page.getByRole("button", { name: "New Provider" }).click();

            await expect(providerDialog, "Provider dialog opens").toBeVisible();

            await series(
                [click, "OAuth2/OpenID", "option"],
                [click, "Next"],
                [fill, "Provider name", providerName],
                [
                    selectSearchValue,
                    "Authorization flow",
                    /default-provider-authorization-explicit-consent/,
                ],
                [click, "Finish"],
            );

            await expect(providerDialog, "Provider dialog closes after creation").toBeHidden();
        });

        await test.step("Verify provider creation", async () => {
            const $provider = await search(providerName);

            await expect($provider, "Provider is visible").toBeVisible();
        });

        //#endregion

        //#region Create application

        await test.step("Navigate to applications", async () => {
            await navigator.navigate("/if/admin/#/core/applications");
        });

        const appDialog = page.getByRole("dialog", { name: "New Application" });

        // await test.step("Create application", async () => {
        await expect(appDialog, "Application dialog is initially closed").toBeHidden();

        await click("New Application", "button");
        await click("With Existing Provider...", "menuitem");

        await expect(appDialog, "Application dialog opens").toBeVisible();

        await series(
            [fill, /^Application Name/, appName, appDialog],
            [selectSearchValue, "Provider", providerName, appDialog],
        );

        await appDialog.getByRole("button", { name: "Create Application" }).click();

        await expect(appDialog, "Application dialog closes after creation").toBeHidden();
        // });

        await test.step("Verify application creation", async () => {
            const $app = await search(appName);

            await expect($app, "Application is visible in the table").toBeVisible();
        });

        //#endregion
    });
});
