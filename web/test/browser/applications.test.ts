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

        const providerDialog = page.getByRole("dialog", { name: "New Provider Wizard" });

        await test.step("Create OAuth2 provider", async () => {
            await expect(providerDialog, "Provider dialog is initially closed").toBeHidden();

            await page.getByRole("button", { name: "New Provider" }).click();

            await expect(providerDialog, "Provider dialog opens").toBeVisible();

            await series(
                [click, "OAuth2/OpenID", "option"],
                [fill, "Provider Name", providerName],
                [
                    selectSearchValue,
                    "Authorization Flow",
                    /default-provider-authorization-explicit-consent/,
                ],
                [click, "Create"],
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

        await test.step("Create application", async () => {
            await expect(appDialog, "Application dialog is initially closed").toBeHidden();

            await click("New Application options", "button");
            await click("With Existing Provider...", "menuitem");

            await expect(appDialog, "Application dialog opens").toBeVisible();

            await series(
                [fill, /^Application Name/, appName, appDialog],
                [selectSearchValue, "Provider", providerName, appDialog],
            );

            await appDialog.getByRole("button", { name: "Create Application" }).click();

            await expect(appDialog, "Application dialog closes after creation").toBeHidden();
        });

        await test.step("Verify application creation", async () => {
            const $app = await search(appName);

            await expect($app, "Application is visible in the table").toBeVisible();
        });

        //#endregion
    });

    test("Create application with new provider via wizard", async ({
        session,
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
                to: "/if/admin/#/core/applications",
            });
        });

        const wizardDialog = page.getByRole("dialog", { name: "New Application Wizard" });

        await test.step("Open wizard", async () => {
            await expect(wizardDialog, "Wizard is initially closed").toBeHidden();

            await click("New Application", "button");

            await expect(wizardDialog, "Wizard opens").toBeVisible();
        });

        await test.step("Step 1: Configure Application", async () => {
            await fill(/^Application Name/, appName, wizardDialog);

            await click("Next", "button", wizardDialog);
        });

        await test.step("Step 2: Choose a Provider", async () => {
            await click("OAuth2/OpenID Provider", "option", wizardDialog);

            await click("Next", "button", wizardDialog);
        });

        await test.step("Step 3: Configure Provider", async () => {
            // Provider Name is auto-filled as "Provider for {appName}"
            const providerNameInput = wizardDialog.getByRole("textbox", {
                name: /Provider Name/,
            });

            await expect(providerNameInput, "Provider name is pre-filled").toHaveValue(
                `Provider for ${appName}`,
            );

            await series([
                selectSearchValue,
                "Authorization Flow",
                /default-provider-authorization-explicit-consent/,
                wizardDialog,
            ]);

            await click("Next", "button", wizardDialog);
        });

        await test.step("Step 4: Configure Bindings (skip)", async () => {
            await click("Next", "button", wizardDialog);
        });

        await test.step("Step 5: Review and Submit", async () => {
            await click("Create Application", "button", wizardDialog);

            await expect(
                wizardDialog.getByRole("heading", { name: "Your application has been saved" }),
            ).toBeVisible({
                timeout: 10_000,
            });

            await click("Finish", "button", wizardDialog);
        });

        await test.step("Verify application creation", async () => {
            await expect(wizardDialog, "Wizard closes after submission").toBeHidden();

            const $app = await search(appName);

            await expect($app, "Application is visible in the table").toBeVisible();
        });
    });
});
