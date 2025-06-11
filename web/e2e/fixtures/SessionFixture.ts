import { PageFixture } from "#e2e/fixtures/PageFixture";
import { Page, expect } from "@playwright/test";

export const GOOD_USERNAME = "test-admin@goauthentik.io";
export const GOOD_PASSWORD = "test-runner";

export const BAD_USERNAME = "bad-username@bad-login.io";
export const BAD_PASSWORD = "-this-is-a-bad-password-";

export interface LoginInit {
    username?: string;
    password?: string;
    to?: URL | string;
}

export class SessionFixture extends PageFixture {
    static fixtureName = "Session";

    public static readonly pathname = "/if/flow/default-authentication-flow/";

    //#region Selectors

    public $identificationStage = this.page.locator("ak-stage-identification");

    /**
     * The username field on the login page.
     */
    public $usernameField = this.$identificationStage.locator('input[name="uidField"]');

    /**
     * The button to continue with the login process,
     * typically to the password flow stage.
     */
    public $submitUsernameStageButton = this.$identificationStage.locator('button[type="submit"]');

    public $passwordStage = this.page.locator("ak-stage-password");
    public $passwordField = this.$passwordStage.locator('input[name="password"]');
    /**
     * The button to submit the the login flow,
     * typically redirecting to the authenticated interface.
     */
    public $submitPasswordStageButton = this.$passwordStage.locator('button[type="submit"]');

    /**
     * A possible authentication failure message.
     */
    public $authFailureMessage = this.page.locator(".pf-m-error");

    //#endregion

    constructor(page: Page, testName: string) {
        super({ page, testName });
    }

    //#region Specific interactions

    public async submitUsernameStage(username: string) {
        this.logger.info("Submitting username stage", username);

        await this.$usernameField.fill(username);

        await expect(this.$submitUsernameStageButton).toBeEnabled();

        await this.$submitUsernameStageButton.click();
    }

    public async submitPasswordStage(password: string) {
        this.logger.info("Submitting password stage");

        await this.$passwordField.fill(password);

        await expect(this.$submitPasswordStageButton).toBeEnabled();

        await this.$submitPasswordStageButton.click();
    }

    public checkAuthenticated = async (): Promise<boolean> => {
        // TODO: Check if the user is authenticated via API
        return true;
    };

    /**
     * Log into the application.
     */
    public async login({
        username = GOOD_USERNAME,
        password = GOOD_PASSWORD,
        to = SessionFixture.pathname,
    }: LoginInit = {}) {
        this.logger.info("Logging in...");

        const initialURL = new URL(this.page.url());

        if (initialURL.pathname === SessionFixture.pathname) {
            this.logger.info("Skipping navigation because we're already in a authentication flow");
        } else {
            await this.page.goto(to.toString());
        }

        await this.submitUsernameStage(username);

        await this.$passwordField.waitFor({ state: "visible" });

        await this.submitPasswordStage(password);

        const expectedPathname = typeof to === "string" ? to : to.pathname;

        await this.page.waitForURL(`**${expectedPathname}`);
    }

    //#endregion

    //#region Navigation

    public async toLoginPage() {
        await this.page.goto(SessionFixture.pathname);
    }
}
