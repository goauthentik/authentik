import { expect, test } from "#e2e";
import { FormFixture } from "#e2e/fixtures/FormFixture";
import { NavigatorFixture } from "#e2e/fixtures/NavigatorFixture";
import { GOOD_USERNAME, SessionFixture } from "#e2e/fixtures/SessionFixture";
import { randomName } from "#e2e/utils/generators";

import { IDGenerator } from "@goauthentik/core/id";
import { series } from "@goauthentik/core/promises";

import type { Page } from "@playwright/test";
import { snakeCase } from "change-case";

/**
 * The domain of the brand seeded by `blueprints/default/default-brand.yaml`, which is
 * the brand resolved for the test runner's origin.
 */
const DEFAULT_BRAND_DOMAIN = "authentik-default";

/**
 * The flow the default brand is pointed at for user switching.
 *
 * Reusing the default authentication flow is the configuration described in the feature
 * docs, and it is what makes the "identification skipped, password requested" path
 * observable: the switch plan carries `pending_user`, so the identification stage
 * auto-completes and the flow opens on the password stage.
 */
const USER_SWITCH_FLOW = /default-authentication-flow/;

/**
 * The password assigned — through the admin UI — to the secondary account each test
 * creates for itself. Long and unlike the generated username so Django's password
 * validators accept it.
 */
const SECONDARY_PASSWORD = "e2e-user-switching-secondary";

/**
 * Every entry in the switcher menu is labelled with the account's email, whichever
 * `UserDisplay` setting is in effect, so emails are what the tests match on.
 *
 * Passed as a plain string: role name matching is a case-insensitive substring match
 * unless `exact` is set, so no pattern escaping is involved.
 */
const ADMIN_ENTRY_NAME = GOOD_USERNAME;

interface SecondaryUser {
    username: string;
    displayName: string;
    email: string;
}

test.describe("User switching", () => {
    // Serial, because every test in here depends on one piece of global state: the
    // default brand's user switch flow. `playwright.config.js` sets `fullyParallel`, so
    // without this the per-worker `beforeAll` hooks below race each other writing the
    // same brand, and the losing worker's Edit Brand modal never closes.
    test.describe.configure({ mode: "serial" });

    const secondaryUsers = new Map<string, SecondaryUser>();

    //#region Lifecycle

    test.beforeAll(
        "Ensure the default brand has a user switch flow",
        async ({ browser }, { title: testName }) => {
            const context = await browser.newContext();
            const page = await context.newPage();
            const navigator = new NavigatorFixture(page, testName);
            const form = new FormFixture(page, testName);
            const session = new SessionFixture({ page, testName, navigator });

            await test.step("Authenticate", async () =>
                session.login({
                    to: "/if/admin/#/core/brands",
                    page,
                }));

            const $brand = await test.step("Find the default brand via search", () =>
                form.search(DEFAULT_BRAND_DOMAIN, page));

            await $brand.getByRole("button", { name: /^Edit .*Brand$/ }).click();

            const dialog = page.getByRole("dialog", { name: "Edit Brand" });
            await expect(dialog, "Edit modal opens after clicking edit").toBeVisible();

            await form.setFormGroup("Default flows", true, dialog);

            const $flowSearch = dialog.getByRole("textbox", { name: "User switch flow" });
            const configuredFlow = await $flowSearch.inputValue();

            if (USER_SWITCH_FLOW.test(configuredFlow)) {
                // An earlier run already pointed the brand at the switch flow. Leaving
                // the row alone keeps this hook read-only, so repeat runs cannot race
                // each other writing the same brand.
                await dialog.getByRole("button", { name: "Cancel" }).click();
            } else {
                await form.selectSearchValue("User switch flow", USER_SWITCH_FLOW, dialog);

                await dialog.getByRole("button", { name: "Save Changes" }).click();
            }

            await expect(dialog, "Edit modal closes").toBeHidden({ timeout: 15_000 });

            await context.close();
        },
    );

    test.beforeEach("Seed secondary account details", async ({ page: _page }, { testId }) => {
        const seed = IDGenerator.randomID(6);
        const displayName = `${randomName(seed)} (${seed})`;
        const username = snakeCase(displayName);

        secondaryUsers.set(testId, {
            username,
            displayName,
            email: `${username}@example.com`,
        });
    });

    //#endregion

    //#region Helpers

    /**
     * Create an internal, non-superuser account and give it a known password, entirely
     * through the admin UI.
     *
     * The account is deliberately not a superuser: the "Admin interface" link in the
     * User header then doubles as an independent signal of which account a switch
     * actually landed on.
     */
    async function createSecondaryUser(
        { form, page }: { form: FormFixture; page: Page },
        user: SecondaryUser,
    ): Promise<void> {
        const { fill, search } = form;

        // TODO: The use of `force: true` matches `300-users.test.ts` — buttons with
        // slotted content are not considered visible by Playwright. Remove once native
        // dialog modals are implemented.

        await test.step("Create the secondary account", async () => {
            const dialog = page.getByRole("dialog", { name: "New User Wizard" });

            await page.getByRole("button", { name: "New User" }).click();

            await expect(dialog, "Create dialog opens").toBeVisible();

            await dialog.getByRole("radio", { name: "Internal" }).click({ force: true });

            await series(
                [fill, /^Username/, user.username, dialog],
                [fill, /^Display Name/, user.displayName, dialog],
                [fill, /^Email Address/, user.email, dialog],
                [fill, /^Path/, "users", dialog],
            );

            await dialog.getByRole("button", { name: "Create" }).click();

            await expect(dialog, "Create dialog closes after creating user").toBeHidden({
                timeout: 10_000,
            });
        });

        await test.step("Set the secondary account's password", async () => {
            const $user = await search(user.username);

            await expect($user, "Secondary account is visible").toBeVisible();

            await $user.getByRole("button", { name: "Expand row" }).click();

            const setPasswordButton = page.getByRole("button", { name: "Set password" });

            await expect(setPasswordButton, "Set password button is revealed").toBeVisible();

            await setPasswordButton.click();

            const dialog = page.getByRole("dialog", { name: /password$/i });

            await expect(dialog, "Set password dialog opens").toBeVisible();

            await dialog.getByLabel("New Password").fill(SECONDARY_PASSWORD);
            await dialog.getByRole("button", { name: "Set Password" }).click();

            await expect(dialog, "Set password dialog closes after saving").toBeHidden({
                timeout: 10_000,
            });
        });
    }

    //#endregion

    //#region Tests

    test("Add another user and switch back", async ({
        session,
        navigator,
        switcher,
        form,
        page,
    }, testInfo) => {
        const user = secondaryUsers.get(testInfo.testId)!;

        const adminEntry = switcher.entry(ADMIN_ENTRY_NAME);
        const secondaryEntry = switcher.entry(user.username);
        const adminInterfaceLink = page.getByRole("link", { name: "Admin interface" });

        await test.step("Authenticate as the administrator", async () => {
            await session.login({ to: "/if/admin/#/identity/users" });
        });

        await createSecondaryUser({ form, page }, user);

        await test.step("Open the switcher as the administrator", async () => {
            // A path carrying a hash fragment, so the return trip also proves that
            // `next` survives fragment encoding through the switch endpoint.
            await navigator.navigate("/if/user/#/settings");

            await switcher.open();

            await expect(
                adminEntry,
                "Administrator is listed and marked as the current account",
            ).toBeDisabled();
            await expect(switcher.$addUser, "Add another user is offered").toBeVisible();
            await expect(
                adminInterfaceLink,
                "Admin interface link is available to the administrator",
            ).toBeVisible();
        });

        await test.step("Add the secondary account", async () => {
            await switcher.select(switcher.$addUser);

            await expect(
                session.$identificationStage,
                "Adding a user starts a full authentication flow",
            ).toBeVisible({ timeout: 15_000 });

            await session.login({
                username: user.username,
                password: SECONDARY_PASSWORD,
                to: "if/user/#/settings",
            });
        });

        await test.step("Verify the secondary account is now active", async () => {
            await switcher.open();

            await expect(
                secondaryEntry,
                "Secondary account is marked as the current account",
            ).toBeDisabled();
            await expect(
                adminEntry,
                "Administrator remains selectable as a switch target",
            ).toBeEnabled();
            await expect(
                adminInterfaceLink,
                "Admin interface link is hidden for the non-superuser account",
            ).toBeHidden();
        });

        await test.step("Switch back to the administrator", async () => {
            await navigator.navigate("/if/user/#/library");

            await switcher.select(adminEntry);

            await expect(
                session.$passwordStage,
                "Switching opens on the password stage, identification having been skipped",
            ).toBeVisible({ timeout: 15_000 });
            await expect(
                session.$identificationStage,
                "Identification is not asked again for a known switch target",
            ).toBeHidden();

            await session.completePassword({ to: "if/user/#/library" });
        });

        await test.step("Verify the administrator is active again", async () => {
            await switcher.open();

            await expect(
                adminEntry,
                "Administrator is marked as the current account",
            ).toBeDisabled();
            await expect(
                secondaryEntry,
                "Secondary account remains selectable as a switch target",
            ).toBeEnabled();
            await expect(
                adminInterfaceLink,
                "Admin interface link is available again",
            ).toBeVisible();
        });
    });

    test("Switcher is available in the admin interface", async ({ session, switcher }) => {
        await test.step("Authenticate as the administrator", async () => {
            await session.login({ to: "/if/admin/#/administration/overview" });
        });

        await test.step("Open the switcher from the admin header", async () => {
            await switcher.open();

            await expect(
                switcher.entry(ADMIN_ENTRY_NAME),
                "Administrator is marked as the current account",
            ).toBeDisabled();
            await expect(switcher.$addUser, "Add another user is offered").toBeVisible();
        });
    });

    test("Signing out the current user requires re-authentication", async ({
        session,
        switcher,
        page,
    }) => {
        await test.step("Authenticate as the administrator", async () => {
            await session.login({ to: "/if/user/#/library" });
        });

        await test.step("Sign out the current account", async () => {
            await switcher.select(switcher.$signOut);

            await expect(
                session.$identificationStage,
                "Signing out returns to the authentication flow",
            ).toBeVisible({ timeout: 15_000 });
        });

        await test.step("Verify the user interface is no longer reachable", async () => {
            // `navigator.navigate` cannot be used here: the interface bounces straight
            // back to the authentication flow, so the requested pathname never settles.
            await page.goto("/if/user/#/library");

            await expect(
                session.$identificationStage,
                "The signed-out session cannot reach the user interface",
            ).toBeVisible({ timeout: 15_000 });
        });
    });

    //#endregion
});
