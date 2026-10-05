import { expect, test } from "#e2e";
import { randomName } from "#e2e/utils/generators";

import { IDGenerator } from "@goauthentik/core/id";
import { series } from "@goauthentik/core/promises";

import { snakeCase } from "change-case";

const CREDENTIALS_SETTINGS = `/if/user/#/settings;${JSON.stringify({ page: "page-credentials" })}`;

test.describe("Passkeys", () => {
    const usernames = new Map<string, string>();
    const displayNames = new Map<string, string>();
    const passwords = new Map<string, string>();

    //#region Lifecycle

    test.beforeEach("Prepare enrollee", async ({ passkey, session }, { testId }) => {
        const seed = IDGenerator.randomID(6);
        const displayName = `${randomName(seed)} (${seed})`;

        displayNames.set(testId, displayName);
        usernames.set(testId, snakeCase(displayName));
        passwords.set(testId, `passkey-${IDGenerator.randomID(12)}`);

        // Before any navigation — the override is injected at document start, so a page
        // that has already loaded keeps the real `navigator.credentials`.
        await test.step("Install virtual authenticator", () => passkey.install());

        await test.step("Authenticate as admin", () =>
            session.login({ to: "/if/admin/#/identity/users" }));
    });

    //#endregion

    //#region Tests

    // A passkey is enrolled against a throwaway user rather than the shared admin: a device
    // on `test-admin` would push every other suite's `session.login()` through the MFA
    // validation stage, which they have no authenticator to answer.

    test("Enroll a passkey and sign in with it", async ({
        session,
        navigator,
        form,
        pointer,
        passkey,
        page,
    }, testInfo) => {
        const username = usernames.get(testInfo.testId)!;
        const displayName = displayNames.get(testInfo.testId)!;
        const password = passwords.get(testInfo.testId)!;

        const { fill, search } = form;
        const { click } = pointer;

        await test.step("Create the user", async () => {
            const dialog = page.getByRole("dialog", { name: "New User Wizard" });

            await expect(dialog, "Dialog is initially closed").toBeHidden();

            await click("New User", "button");

            await expect(dialog, "Dialog opens").toBeVisible();

            // TODO: `force` matches the users suite — slotted button content reads as
            // invisible to Playwright until native dialog modals land.
            await dialog.getByRole("radio", { name: "Internal" }).click({ force: true });

            await series(
                [fill, /^Username/, username, dialog],
                [fill, /^Display Name/, displayName, dialog],
                [fill, /^Email Address/, `${username}@example.com`, dialog],
                [fill, /^Path/, "users", dialog],
            );

            await dialog.getByRole("button", { name: "Create" }).click();

            await expect(dialog, "Dialog closes after creating user").toBeHidden();
        });

        await test.step("Set the user's password", async () => {
            const $user = await search(username);

            await expect($user, "User is visible").toBeVisible();

            await $user.getByRole("link", { name: `View details for ${displayName}` }).click();

            const dialog = page.getByRole("dialog", { name: /password/i });

            await click("Set password", "button");

            await expect(dialog, "Password dialog opens").toBeVisible();

            await fill("New Password", password, dialog);

            await dialog.getByRole("button", { name: "Set Password" }).click();

            await expect(dialog, "Password dialog closes after saving").toBeHidden();
        });

        await test.step("Sign out of the admin session", () => session.signOut());

        await test.step("Sign in as the enrollee", () =>
            session.login({ username, password, to: "/if/user/" }));

        await test.step("Open the credentials settings", async () => {
            // Not `navigator.navigate`: the MFA table writes its own page state into the
            // route as soon as it mounts, so the URL never settles on what we asked for.
            // The enroll control appearing is the meaningful wait.
            await page.goto(CREDENTIALS_SETTINGS);

            await expect(
                page.getByRole("button", { name: "Enroll" }),
                "Enroll control is visible",
            ).toBeVisible({ timeout: 15_000 });
        });

        await test.step("Enroll a WebAuthn device", async () => {
            await click("Enroll", "button");

            // The menu item links straight into the `default-authenticator-webauthn-setup`
            // flow, which returns here via `?next=`.
            await click("WebAuthn device", "menuitem");

            await navigator.waitForPathname("/if/user/");
        });

        const $device = await test.step("Confirm the device was recorded", async () => {
            const row = page.getByRole("row").filter({ hasText: /webauthn/i });

            await expect(row, "WebAuthn device is listed").toBeVisible({ timeout: 15_000 });

            return row;
        });

        await expect($device, "Device row names the authenticator type").toContainText(/webauthn/i);

        await test.step("Confirm the authenticator holds the credential", async () => {
            const credentials = await passkey.credentials();

            expect(credentials, "Virtual authenticator holds one credential").toHaveLength(1);
        });

        await test.step("Sign out of the enrollee session", () => session.signOut());

        await test.step("Sign back in through the passkey challenge", async () => {
            // No interaction with the WebAuthn stage: the virtual authenticator answers the
            // assertion and the flow advances on its own, too fast to observe by rendering.
            // Landing on `/if/user/` alone would also pass if the MFA stage never fired, so
            // watch for the assertion actually reaching the flow executor.
            const assertionSubmitted = page.waitForRequest(
                (request) =>
                    request.method() === "POST" &&
                    request.url().includes("/api/v3/flows/executor/default-authentication-flow/") &&
                    (request.postData() ?? "").includes("webauthn"),
            );

            await session.login({ username, password, to: "/if/user/" });

            await assertionSubmitted;

            await expect(
                page.getByRole("button", { name: "Switch user" }),
                "Enrollee is authenticated after the passkey challenge",
            ).toBeVisible();
        });
    });

    //#endregion
});
