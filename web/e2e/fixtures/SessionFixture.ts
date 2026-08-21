import { NavigatorFixture } from "#e2e/fixtures/NavigatorFixture";
import { PageFixture, PageFixtureInit } from "#e2e/fixtures/PageFixture";

import { expect, Page } from "@playwright/test";

export const GOOD_USERNAME = "test-admin@goauthentik.io";
export const GOOD_PASSWORD = "test-runner";

export const BAD_USERNAME = "bad-username@bad-login.io";
export const BAD_PASSWORD = "-this-is-a-bad-password-";

export interface LoginInit {
    username?: string;
    password?: string;
    to?: URL | string;
    rememberMe?: boolean;
    page?: Page;
}

export interface SessionFixtureInit extends PageFixtureInit {
    navigator: NavigatorFixture;
}

export class SessionFixture extends PageFixture {
    static fixtureName = "Session";

    public static readonly pathname = "/if/flow/default-authentication-flow/";

    protected navigator: NavigatorFixture;

    //#region Selectors

    public $identificationStage = this.page.locator("ak-stage-identification");

    /**
     * The username field on the login page.
     */
    public $usernameField = this.page.getByLabel("Username");

    public $passwordStage = this.page.locator("ak-stage-password");
    // Exact match: the password stage's "Show password" visibility toggle
    // (ak-flow-password-input) also carries a "…password" accessible name, so a
    // substring getByLabel("Password") matches two elements.
    public $passwordField = this.page.getByLabel("Password", { exact: true });

    public $rememberMeCheckbox = this.page.getByRole("checkbox", {
        name: "Remember me on this device",
    });

    /**
     * The button to submit the the login flow,
     * typically redirecting to the authenticated interface.
     */
    public $submitButton = this.page.locator('button[type="submit"]');

    /**
     * A possible authentication failure message.
     */
    public $authFailureMessage = this.page.getByRole("alert", {
        name: /(?:failed to authenticate)|(?:invalid password)/i,
    });

    //#endregion

    constructor({ page, testName, navigator }: SessionFixtureInit) {
        super({ page, testName });
        this.navigator = navigator;
    }

    //#region Specific interactions

    public checkAuthenticated = async (): Promise<boolean> => {
        // TODO: Check if the user is authenticated via API
        return true;
    };

    /**
     * Log into the application.
     */
    public async login(
        { username = GOOD_USERNAME, password = GOOD_PASSWORD, to, rememberMe }: LoginInit = {},
        page = this.page,
    ): Promise<void> {
        this.logger.info("Logging in...");

        const initialURL = new URL(page.url());

        if (initialURL.pathname === SessionFixture.pathname) {
            this.logger.info("Skipping navigation because we're already in a authentication flow");
        } else {
            // Navigating to `to` while unauthenticated bounces through the flow with
            // `?next=`, so the post-login redirect lands on the destination.
            await page.goto((to ?? SessionFixture.pathname).toString());
        }

        if (typeof rememberMe === "boolean") {
            const rememberMeCheckboxVisible = await this.$rememberMeCheckbox.isVisible();

            if (rememberMeCheckboxVisible) {
                if (rememberMe) {
                    await this.$rememberMeCheckbox.check();

                    await expect(
                        this.$rememberMeCheckbox,
                        "Remember me checkbox is checked",
                    ).toBeChecked();
                } else {
                    await this.$rememberMeCheckbox.uncheck();

                    await expect(
                        this.$rememberMeCheckbox,
                        "Remember me checkbox is unchecked",
                    ).not.toBeChecked();
                }
            }
        }

        await this.$usernameField.fill(username);

        const passwordFieldVisible = await this.$passwordField.isVisible();

        if (!passwordFieldVisible) {
            await this.$submitButton.click();

            await this.$passwordField.waitFor({ state: "visible" });
        }

        await this.$passwordField.fill(password);

        await this.$submitButton.click();

        if (to) {
            await this.navigator.waitForPathname(to);

            return;
        }

        // With no destination the redirect lands on whichever interface the user
        // defaults to, which the caller doesn't know. Waiting on the flow pathname
        // would match the page we're already on and return before the redirect
        // lands, leaving the next step to run against the login screen.
        //
        // Raced against the failure alert so callers that log in with bad credentials
        // on purpose return here instead of waiting out the test timeout. Both sides
        // swallow their own timeout: whichever settles first is the outcome, and the
        // caller asserts on it.
        await Promise.race([
            this.navigator.waitForPathnameChange(SessionFixture.pathname).catch(() => undefined),
            this.$authFailureMessage.waitFor({ state: "visible" }).catch(() => undefined),
        ]);
    }

    //#endregion

    //#region Navigation

    public async toLoginPage(page: Page = this.page) {
        await page.goto(SessionFixture.pathname);
    }
}
