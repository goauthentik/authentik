import { expect, test } from "#e2e";
import { randomName } from "#e2e/utils/generators";

import { AuthenticatorValidationChallengeFromJSON, DeviceClassesEnum } from "@goauthentik/api";
import { IDGenerator } from "@goauthentik/core/id";
import { series } from "@goauthentik/core/promises";

import { snakeCase } from "change-case";

// Tabs are path segments now: the `page-credentials` panel lives at
// `/if/user/settings/credentials`, not behind a legacy hash tab token.
const CREDENTIALS_SETTINGS = "/if/user/settings/credentials";
const AUTHENTICATION_EXECUTOR = "/api/v3/flows/executor/default-authentication-flow/";

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

    // A passkey is enrolled against a throwaway user rather than the shared admin: a device
    // on `test-admin` would push every other suite's `session.login()` through the MFA
    // validation stage, which they have no authenticator to answer.

    test.beforeEach(
        "Enroll a passkey",
        async ({ session, navigator, form, pointer, passkey, page }, testInfo) => {
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

            await expect($device, "Device row names the authenticator type").toContainText(
                /webauthn/i,
            );

            await test.step("Confirm the authenticator holds the credential", async () => {
                const credentials = await passkey.credentials();

                expect(credentials, "Virtual authenticator holds one credential").toHaveLength(1);
            });

            await test.step("Sign out of the enrollee session", () => session.signOut());
        },
    );

    //#endregion

    //#region Tests

    test("Enroll a passkey and sign in with it", async ({ session, page }, testInfo) => {
        const username = usernames.get(testInfo.testId)!;
        const password = passwords.get(testInfo.testId)!;

        await test.step("Sign back in through the passkey challenge", async () => {
            // No interaction with the WebAuthn stage: the virtual authenticator answers the
            // assertion and the flow advances on its own, too fast to observe by rendering.
            // Landing on `/if/user/` alone would also pass if the MFA stage never fired, so
            // watch for the assertion actually reaching the flow executor.
            const assertionSubmitted = page.waitForRequest(
                (request) =>
                    request.method() === "POST" &&
                    request.url().includes(AUTHENTICATION_EXECUTOR) &&
                    (request.postData() ?? "").includes("webauthn"),
            );

            await session.login({ username, password, to: "/if/user/" });

            await assertionSubmitted;

            await expect(
                page.getByRole("button", { name: "Toggle user navigation menu" }),
                "Enrollee is authenticated after the passkey challenge",
            ).toBeVisible();
        });
    });

    test("Complete passkey authentication after another tab renders the challenge", async ({
        session,
        form,
        context,
        page,
    }, testInfo) => {
        const username = usernames.get(testInfo.testId)!;
        const password = passwords.get(testInfo.testId)!;

        const heldAssertion = Promise.withResolvers<{
            challenge: string;
            submit: () => Promise<void>;
        }>();

        let intercepted = false;

        const assertion = await test.step("Hold tab A's first signed assertion", async () => {
            // Delay delivery so tab B renders the stage before the server validates
            // tab A's signed assertion.
            await page.route(`**${AUTHENTICATION_EXECUTOR}**`, async (route) => {
                const request = route.request();
                const body = request.method() === "POST" ? request.postDataJSON() : null;

                if (!intercepted && body?.webauthn) {
                    intercepted = true;

                    const clientData = JSON.parse(
                        Buffer.from(body.webauthn.response.clientDataJSON, "base64url").toString(),
                    );

                    heldAssertion.resolve({
                        challenge: clientData.challenge,
                        submit: () => route.continue(),
                    });

                    return;
                }

                await route.continue();
            });

            // Stop at MFA rather than session.login(), which waits for login to finish.
            await form.fill("Username", username);

            if (!(await session.$passwordField.isVisible())) {
                await session.$submitButton.click();
            }

            await session.$passwordField.fill(password);
            await session.$submitButton.click();

            return heldAssertion.promise;
        });

        await test.step("Render the pending challenge in tab B", async () => {
            const secondTab = await context.newPage();

            // Tab B should render the challenge, but must not complete authentication.
            await secondTab.route(`**${AUTHENTICATION_EXECUTOR}**`, async (route) => {
                const request = route.request();

                if (request.method() === "POST" && request.postDataJSON()?.webauthn) {
                    await route.abort();

                    return;
                }

                await route.continue();
            });

            const challengeResponse = secondTab.waitForResponse(
                (response) =>
                    response.url().includes(AUTHENTICATION_EXECUTOR) &&
                    response.request().method() === "GET",
            );

            await secondTab.goto(page.url());

            const challenge = AuthenticatorValidationChallengeFromJSON(
                await (await challengeResponse).json(),
            ).deviceChallenges.find((device) => device.deviceClass === DeviceClassesEnum.Webauthn)
                ?.challenge.challenge;

            expect(challenge, "Tab B receives a WebAuthn challenge").toEqual(expect.any(String));

            expect(challenge, "Tab B reuses tab A's pending challenge").toBe(assertion.challenge);
        });

        await test.step("Complete authentication with tab A's original assertion", async () => {
            await assertion.submit();

            await expect(
                page.getByRole("button", { name: "Toggle user navigation menu" }),
                "Tab A authenticates successfully with the original assertion",
            ).toBeVisible();
        });
    });

    //#endregion
});
