import { expect, test } from "#e2e";
import { randomName } from "#e2e/utils/generators";

import { IDGenerator } from "@goauthentik/core/id";
import { series } from "@goauthentik/core/promises";

interface Names {
    providerName: string;
    appName: string;
    endpointA: string;
    endpointB: string;
}

test.describe("RAC", () => {
    const fixtures = new Map<string, Names>();

    test.beforeEach("Seed entity names", async (_, { testId }) => {
        const seed = IDGenerator.randomID(6);
        const base = randomName(seed);

        fixtures.set(testId, {
            providerName: `${base} RAC (${seed})`,
            appName: `${base} RAC App (${seed})`,
            endpointA: `rac-vnc-a-${seed}`,
            endpointB: `rac-vnc-b-${seed}`,
        });
    });

    test("Configure provider, add endpoints, attach to application, and launch from user library", async ({
        session,
        navigator,
        form,
        pointer,
        page,
    }, testInfo) => {
        const { providerName, appName, endpointA, endpointB } = fixtures.get(testInfo.testId)!;
        const { fill, search, selectSearchValue, setRadio } = form;
        const { click } = pointer;

        await test.step("Authenticate", async () => {
            await session.login({ to: "/if/admin/#/core/providers" });
        });

        //#region Create RAC provider via the wizard

        const providerDialog = page.getByRole("dialog", { name: "New Provider Wizard" });

        await test.step("Create RAC provider", async () => {
            await expect(providerDialog, "Provider wizard is initially closed").toBeHidden();

            await click("New Provider", "button");

            await expect(providerDialog, "Provider wizard opens").toBeVisible();

            await series(
                [click, "RAC Provider", "option"],
                [fill, "Provider Name", providerName],
                [
                    selectSearchValue,
                    "Authorization Flow",
                    /default-provider-authorization-explicit-consent/,
                ],
                [click, "Create", "button", providerDialog],
            );

            await expect(providerDialog, "Provider wizard closes after creation").toBeHidden();
        });

        const $providerRow = await test.step("Find provider in table", () => search(providerName));

        await expect($providerRow, "Provider row is visible").toBeVisible();

        //#endregion

        //#region Add two endpoints from the provider detail page

        await test.step("Open provider detail page", async () => {
            await $providerRow.getByRole("link", { name: providerName }).click();

            await expect(
                page.getByRole("heading", { name: providerName }),
                "Provider detail page renders",
            ).toBeVisible();
        });

        const endpointDialog = page.getByRole("dialog", { name: /New RAC Endpoint/i });
        const endpointList = page.locator("ak-rac-endpoint-list");

        for (const endpointName of [endpointA, endpointB]) {
            await test.step(`Create endpoint ${endpointName}`, async () => {
                await expect(endpointDialog, "Endpoint dialog is initially closed").toBeHidden();

                await endpointList
                    .getByRole("button", { name: "New RAC Endpoint" })
                    .first()
                    .click();

                await expect(endpointDialog, "Endpoint dialog opens").toBeVisible();

                await series(
                    [fill, "Endpoint Name", endpointName, endpointDialog],
                    [setRadio, "Protocol", "VNC", endpointDialog],
                    [fill, "Host", "localhost:5900", endpointDialog],
                    [click, "Create RAC Endpoint", "button", endpointDialog],
                );

                await expect(endpointDialog, "Endpoint dialog closes after creation").toBeHidden();

                await expect(
                    endpointList.getByRole("cell", { name: endpointName }),
                    `Endpoint ${endpointName} appears in the sub-table`,
                ).toBeVisible();
            });
        }

        //#endregion

        //#region Attach the provider to an application

        await test.step("Navigate to applications", async () => {
            await navigator.navigate("/if/admin/#/core/applications");
        });

        const appDialog = page.getByRole("dialog", { name: "New Application" });

        await test.step("Create application with the RAC provider", async () => {
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

        await test.step("Verify application in admin table", async () => {
            const $appRow = await search(appName);

            await expect($appRow, "Application is visible in the admin table").toBeVisible();
        });

        //#endregion

        //#region User library: launch the application

        await test.step("Navigate to the user library", async () => {
            await navigator.navigate("/if/user/");
        });

        const librarySearch = page.getByPlaceholder("Search for an application by name...");

        await expect(librarySearch, "Library search input is ready").toBeVisible({
            timeout: 15_000,
        });

        await test.step("Filter library to the new application", async () => {
            await librarySearch.fill(appName);
        });

        // Newly created apps can take several seconds to surface in the
        // user-facing application list, so allow extra time for the card to
        // appear once the search filter is applied.
        const launchButton = page.getByRole("button", { name: `Open "${appName}"` });

        await expect(
            launchButton,
            "Application launch button appears in the filtered library",
        ).toBeVisible({ timeout: 15_000 });

        await test.step("Open the endpoint launcher", async () => {
            await launchButton.click();
        });

        const launchDialog = page.getByRole("dialog", { name: /Launch Endpoint/i });

        await expect(launchDialog, "Launch Endpoint dialog opens").toBeVisible();

        // Both endpoints must render on first open — no manual refresh, no
        // re-navigation. Two endpoints are required because a single endpoint
        // auto-launches and closes the modal.
        await test.step("Endpoint list populates on first open", async () => {
            await expect(
                launchDialog.getByRole("cell", { name: endpointA }),
                `Endpoint ${endpointA} is visible in the launcher`,
            ).toBeVisible({ timeout: 5_000 });

            await expect(
                launchDialog.getByRole("cell", { name: endpointB }),
                `Endpoint ${endpointB} is visible in the launcher`,
            ).toBeVisible();
        });

        //#endregion
    });
});
