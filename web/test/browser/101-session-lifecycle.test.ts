import { expect, test } from "#e2e";
import { GOOD_USERNAME } from "#e2e/fixtures/SessionFixture";

import type { Page } from "@playwright/test";

const REMEMBER_ME_USER_KEY = "authentik-remember-me-user";
const REMEMBER_ME_SESSION_KEY = "authentik-remember-me-session";

const readStoredUserIdentifier = (page: Page) =>
    page.evaluate((k) => localStorage.getItem(k), REMEMBER_ME_USER_KEY);

test.describe("Session Lifecycle", () => {
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
            await session.signOut();

            await navigator.waitForPathname("/if/flow/default-authentication-flow/?next=%2F");

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
