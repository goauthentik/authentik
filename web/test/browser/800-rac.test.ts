import { expect, test } from "#e2e";
import { randomName } from "#e2e/utils/generators";

import { IDGenerator } from "@goauthentik/core/id";
import { series } from "@goauthentik/core/promises";

interface Names {
    providerName: string;
    appName: string;
    deviceA: string;
    deviceB: string;
}

test.describe("RAC", () => {
    const fixtures = new Map<string, Names>();

    test.beforeEach("Seed entity names", async ({ page: _page }, { testId }) => {
        const seed = IDGenerator.randomID(6);
        const base = randomName(seed);

        fixtures.set(testId, {
            providerName: `${base} RAC (${seed})`,
            appName: `${base} RAC App (${seed})`,
            deviceA: `rac-vnc-a-${seed}`,
            deviceB: `rac-vnc-b-${seed}`,
        });
    });

    test("Configure provider, add devices, attach to application, and launch from user library", async ({
        session,
        navigator,
        form,
        pointer,
        page,
    }, testInfo) => {
        const { providerName, appName, deviceA, deviceB } = fixtures.get(testInfo.testId)!;
        const { fill, search, selectSearchValue, setRadio } = form;
        const { click } = pointer;

        await test.step("Authenticate", async () => {
            await session.login({ to: "/if/admin/core/providers" });
        });

        //#region Create RAC provider via the wizard

        const providerDialog = page.getByRole("dialog", {
            name: "New Provider Wizard",
        });

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

        await test.step("Find provider in table", async () => {
            await expect(await search(providerName), "Provider row is visible").toBeVisible();
        });

        //#endregion

        //#region Add two devices to connect to

        await test.step("Navigate to devices", async () => {
            await navigator.navigate("/if/admin/endpoints/devices");
        });

        const deviceDialog = page.getByRole("dialog", { name: /New Device/i });
        const deviceList = page.locator("ak-endpoints-device-list");

        for (const deviceName of [deviceA, deviceB]) {
            await test.step(`Create device ${deviceName}`, async () => {
                await expect(deviceDialog, "Device dialog is initially closed").toBeHidden();

                await deviceList.getByRole("button", { name: "New Device" }).first().click();

                await expect(deviceDialog, "Device dialog opens").toBeVisible();

                // A device which is added by hand cannot report how it is reached, so
                // the host and protocol are required
                await series(
                    [fill, "Device name", deviceName, deviceDialog],
                    [fill, "Host", "localhost:5900", deviceDialog],
                    [setRadio, "Protocol", "VNC", deviceDialog],
                    [click, "Create Device", "button", deviceDialog],
                );

                await expect(deviceDialog, "Device dialog closes after creation").toBeHidden();

                await expect(
                    await search(deviceName),
                    `Device ${deviceName} appears in the table`,
                ).toBeVisible();
            });
        }

        //#endregion

        //#region Attach the provider to an application

        await test.step("Navigate to applications", async () => {
            await navigator.navigate("/if/admin/core/applications");
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
        const launchButton = page.getByRole("button", {
            name: `Open "${appName}"`,
        });

        await expect(
            launchButton,
            "Application launch button appears in the filtered library",
        ).toBeVisible({ timeout: 15_000 });

        const launchDialog = page.getByRole("dialog", {
            name: /Launch Device/i,
        });

        // Click the card rather than relying on the library's single-match
        // auto-launch: that fires from the search input's `change` event, and
        // `locator.fill()` dispatches only `input`, so it never runs under
        // Playwright. Activating the card is what a user does anyway.
        await test.step("Device launcher opens for the single match", async () => {
            await launchButton.click();

            await expect(launchDialog, "Launch Device dialog opens").toBeVisible({
                timeout: 15_000,
            });
        });

        // Both devices must render on first open — no manual refresh, no
        // re-navigation. Two devices are required because a single device with a
        // single protocol auto-launches and closes the modal. Every device the user can
        // reach is launchable through the provider, so each one is searched for by name.
        await test.step("Device list populates on first open", async () => {
            await expect(
                await search(deviceA, launchDialog),
                `Device ${deviceA} is visible in the launcher`,
            ).toBeVisible();
        });

        await test.step("Device is launchable with the protocol it is reached with", async () => {
            const $deviceRow = await search(deviceB, launchDialog);

            await expect($deviceRow, `Device ${deviceB} is visible in the launcher`).toBeVisible();

            await expect(
                $deviceRow.getByRole("button", { name: "VNC" }),
                `Device ${deviceB} can be launched with VNC`,
            ).toBeVisible();
        });

        //#endregion
    });
});
