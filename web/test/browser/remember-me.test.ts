import { expect, test } from "#e2e";
import { GOOD_PASSWORD, GOOD_USERNAME, SessionFixture } from "#e2e/fixtures/SessionFixture";

import type { Page } from "@playwright/test";

const REMEMBER_ME_USER_KEY = "authentik-remember-me-user";
const REMEMBER_ME_SESSION_KEY = "authentik-remember-me-session";

const IDENTIFICATION_STAGE_NAME = "default-authentication-identification";

const REMEMBER_ME_ADMIN_TOGGLE =
    'ak-stage-identification-form ak-switch-input[name="enableRememberMe"] input[type="checkbox"]';

const readStoredUsername = (page: Page) =>
    page.evaluate((k) => localStorage.getItem(k), REMEMBER_ME_USER_KEY);

const readStoredSession = (page: Page) =>
    page.evaluate((k) => localStorage.getItem(k), REMEMBER_ME_SESSION_KEY);

test.describe('Remember me — "Not you?" clears stored identity (regression #21571)', () => {
    test.beforeAll(
        'Ensure "Enable Remember me on this device" is on for the default identification stage',
        async ({ browser }) => {
            test.setTimeout(120_000);
            const context = await browser.newContext();
            const page = await context.newPage();

            try {
                await page.goto(SessionFixture.pathname);
                await page.getByLabel("Username").fill(GOOD_USERNAME);

                if (!(await page.getByLabel("Password").isVisible())) {
                    await page.locator('button[type="submit"]').click();
                    await page.getByLabel("Password").waitFor({ state: "visible" });
                }

                await page.getByLabel("Password").fill(GOOD_PASSWORD);
                await page.locator('button[type="submit"]').click();

                await page.waitForURL((url) => !url.pathname.startsWith("/if/flow/"), {
                    timeout: 30_000,
                });
                await page.goto("/if/admin/#/flow/stages");

                const $search = page.locator('input[name="search"][type="search"]');
                await $search.waitFor({ state: "visible", timeout: 15_000 });
                await $search.fill(IDENTIFICATION_STAGE_NAME);
                await $search.press("Enter");

                const $row = page.getByRole("row", {
                    name: new RegExp(IDENTIFICATION_STAGE_NAME),
                });
                await expect($row, "Identification stage row visible").toBeVisible({
                    timeout: 15_000,
                });

                await $row.getByRole("button", { name: "Edit Stage" }).click();

                const $dialog = page.locator("dialog:has(ak-stage-identification-form)");
                await expect($dialog, "Edit modal opens").toBeVisible({ timeout: 15_000 });

                const $toggle = $dialog.locator(REMEMBER_ME_ADMIN_TOGGLE);
                await $toggle.waitFor({ state: "attached", timeout: 10_000 });
                await $toggle.scrollIntoViewIfNeeded();

                const wasChecked = await $toggle.isChecked();

                if (!wasChecked) {
                    await $toggle.check({ force: true });
                    await expect($toggle).toBeChecked();
                }

                await $dialog.getByRole("button", { name: "Save Changes" }).click();
                await expect($dialog, "Edit modal closes after save").toBeHidden({
                    timeout: 15_000,
                });
            } finally {
                await context.close();
            }
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

    test('Clicking "Not you?" clears the remembered username before navigation', async ({
        session,
        page,
    }) => {
        const $rememberMe = page.locator("#authentik-remember-me");
        const $notYouLink = page.getByRole("link", { name: "Not you?" });

        await test.step("Remember me checkbox is offered", async () => {
            await expect($rememberMe).toBeVisible();
            await expect($rememberMe).not.toBeChecked();
        });

        await test.step("Identify with remember-me enabled", async () => {
            await session.$usernameField.fill(GOOD_USERNAME);
            await $rememberMe.check();
            await expect($rememberMe).toBeChecked();

            expect(
                await readStoredUsername(page),
                "username persists to localStorage when remember-me is checked",
            ).toBe(GOOD_USERNAME);

            await session.$submitButton.click();
            await session.$passwordField.waitFor({ state: "visible" });
        });

        await test.step('"Not you?" link renders cleanly (no stray ">" character)', async () => {
            await expect($notYouLink).toBeVisible();
            await expect($notYouLink).toHaveText("Not you?");
        });

        await test.step('Clicking "Not you?" returns to identification with empty fields', async () => {
            await $notYouLink.click();

            await session.$identificationStage.waitFor({ state: "visible" });
            await session.$usernameField.waitFor({ state: "visible" });

            await expect(
                session.$usernameField,
                "username field must not be auto-populated from prior session",
            ).toHaveValue("");

            await expect(
                page.locator("#authentik-remember-me"),
                "remember-me toggle must be reset",
            ).not.toBeChecked();

            expect(
                await readStoredUsername(page),
                "remembered username must be cleared from localStorage",
            ).toBeNull();

            // Session token is rewritten by the controller on hostConnected; assert it does not leak the username.
            expect(
                await readStoredSession(page),
                "session token must not retain remembered identity",
            ).not.toBe(GOOD_USERNAME);
        });

        await test.step("Identification does not auto-resubmit", async () => {
            await expect(
                session.$passwordField,
                "password field must not appear without explicit submit",
            ).toBeHidden();
        });
    });
});
