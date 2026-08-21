import { expect, test } from "#e2e";
import { FormFixture } from "#e2e/fixtures/FormFixture";
import { NavigatorFixture } from "#e2e/fixtures/NavigatorFixture";
import { GOOD_USERNAME, SessionFixture } from "#e2e/fixtures/SessionFixture";

import type { Page } from "@playwright/test";

const REMEMBER_ME_USER_KEY = "authentik-remember-me-user";
const REMEMBER_ME_SESSION_KEY = "authentik-remember-me-session";

const IDENTIFICATION_STAGE_NAME = "default-authentication-identification";

const readStoredUserIdentifier = (page: Page) =>
    page.evaluate((k) => localStorage.getItem(k), REMEMBER_ME_USER_KEY);

test.describe("Session Lifecycle", () => {
    test.beforeAll(
        'Ensure "Enable Remember me on this device" is on for the default identification stage',
        async ({ browser }, { title: testName }) => {
            const context = await browser.newContext();
            const page = await context.newPage();
            const navigator = new NavigatorFixture(page, testName);
            const form = new FormFixture(page, testName);
            const session = new SessionFixture({ page, testName, navigator });

            await test.step("Authenticate", async () =>
                session.login({
                    to: "/if/admin/flow/stages",
                    page,
                }));

            const $stage = await test.step("Find stage via search", () =>
                form.search(IDENTIFICATION_STAGE_NAME, page));

            await $stage.getByRole("button", { name: "Edit Stage" }).click();

            const dialog = page.getByRole("dialog", { name: "Edit Identification Stage" });
            await expect(dialog, "Edit modal opens after clicking edit").toBeVisible();

            await form.setInputCheck(`Enable "Remember me on this device"`, true, dialog);
            await dialog.getByRole("button", { name: "Save Changes" }).click();
            await expect(dialog, "Edit modal closes after save").toBeHidden();

            await context.close();
        },
    );

    test.beforeEach(async ({ session, page }) => {
        await session.toLoginPage();

        await page.evaluate(
            ([userKey, sessionKey]) => {
                localStorage.removeItem(userKey);
                localStorage.removeItem(sessionKey);
            },
            [REMEMBER_ME_USER_KEY, REMEMBER_ME_SESSION_KEY],
        );

        await page.reload();
        await session.$identificationStage.waitFor({ state: "visible" });
    });

    test("Remember me persists username", async ({ navigator, session, page }) => {
        // This one walks the whole loop — sign in with remember-me, sign out, and come
        // back to a pre-filled form — so it pays the flow executor's startup cost twice
        // and doesn't fit the default budget.
        test.setTimeout(60_000);

        await test.step("Verify identification stage", async () => {
            await expect(
                session.$rememberMeCheckbox,
                "Remember me checkbox is visible",
            ).toBeVisible();
            await expect(
                session.$rememberMeCheckbox,
                "Remember me checkbox is not checked by default",
            ).not.toBeChecked();
        });

        await test.step("Identify with remember-me enabled", async () => {
            await session.login(
                {
                    rememberMe: true,
                    to: "/if/user/library",
                },
                page,
            );

            const storedUserIdentifier = await readStoredUserIdentifier(page);

            expect(
                storedUserIdentifier,
                "username persists to localStorage when remember-me is checked",
            ).toBe(GOOD_USERNAME);
        });

        await test.step("Sign out and verify username is remembered", async () => {
            // Sign-out lives in the user switcher's dropdown, which is `hidden` until the
            // toggle is pressed, and the entry carries an explicit role="menuitem" rather
            // than the implicit link role of its `<a>`.
            await page.getByRole("button", { name: "Switch user" }).click();

            const signOutItem = page.getByRole("menuitem", { name: "Sign out current user" });

            await expect(signOutItem, "Sign out entry is visible").toBeVisible();

            await signOutItem.click();

            await navigator.waitForPathname("/if/flow/default-authentication-flow/?next=%2F");
            // The shell is served before the executor has resolved the first stage, so
            // the pathname landing is not enough to act on.
            await session.$identificationStage.waitFor({ state: "visible", timeout: 20_000 });

            const passwordEmbedded = await session.$passwordField.isVisible();

            if (passwordEmbedded) {
                // Password is embedded in the identification stage, so the Not-you UI never renders.
                // Remember-me's only observable effect is the pre-filled username field.
                await expect(
                    session.$usernameField,
                    "Username pre-filled from remember-me",
                ).toHaveValue(GOOD_USERNAME);

                return;
            }

            await session.$submitButton.click();
            await session.$passwordStage.waitFor({ state: "visible" });

            const notYouLink = page.getByRole("link", { name: "Not you?" });

            await expect(notYouLink, "Not you? link is visible after sign out").toBeVisible();

            await notYouLink.click();

            await expect(
                session.$identificationStage,
                "Identification stage is visible after clicking not you link",
            ).toBeVisible();

            const storedUserIdentifier = await readStoredUserIdentifier(page);

            expect(storedUserIdentifier, "Removed after clicking not you link").toBeNull();
        });
    });
});
