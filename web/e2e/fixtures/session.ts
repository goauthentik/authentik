import { ChildConsoleLogger, ConsoleLogger } from "#logger/node";
import { Locator, Page, expect } from "@playwright/test";

export const GOOD_USERNAME = "test-admin@goauthentik.io";
export const GOOD_PASSWORD = "test-runner";

export const BAD_USERNAME = "bad-username@bad-login.io";
export const BAD_PASSWORD = "-this-is-a-bad-password-";

export interface LoginInit {
    username?: string;
    password?: string;
    to?: URL | string;
}

export class SessionFixture {
    public static readonly pathname = "/if/flow/default-authentication-flow/";
    #logger: ChildConsoleLogger;

    //#region Selectors

    readonly $interfaceRoot: Locator;

    public $identificationStage: Locator;
    public $passwordStage: Locator;

    /**
     * The username field on the login page.
     */
    public $usernameField: Locator;

    /**
     * The button to continue with the login process,
     * typically to the password flow stage.
     */
    public $submitUsernameStageButton: Locator;

    /**
     * The password field on the login page.
     */
    public $passwordField: Locator;

    /**
     * The button to submit the the login flow,
     * typically redirecting to the authenticated interface.
     */
    public $submitPasswordStageButton: Locator;

    /**
     * A possible authentication failure message.
     */
    public $authFailureMessage: Locator;

    //#endregion

    constructor(
        public readonly page: Page,
        testName: string,
    ) {
        this.#logger = ConsoleLogger.child(
            { name: "Session" },
            {
                msgPrefix: `[${testName}] `,
            },
        );

        this.$interfaceRoot = this.page.getByTestId("interface-root");

        this.$identificationStage = this.page.locator("ak-stage-identification");
        this.$usernameField = this.$identificationStage.locator('input[name="uidField"]');
        this.$submitUsernameStageButton =
            this.$identificationStage.locator('button[type="submit"]');

        this.$passwordStage = this.page.locator("ak-stage-password");
        this.$passwordField = this.$passwordStage.locator('input[name="password"]');
        this.$submitPasswordStageButton = this.$passwordStage.locator('button[type="submit"]');

        this.$authFailureMessage = this.page.locator(".pf-m-error");
    }

    //#region Specific interactions

    public async submitUsernameStage(username: string) {
        this.#logger.info("Submitting username stage", username);
        await this.$usernameField.fill(username);

        await expect(this.$submitUsernameStageButton).toBeEnabled();

        await this.$submitUsernameStageButton.click();
    }

    public async submitPasswordStage(password: string) {
        this.#logger.info("Submitting password stage");
        await this.$passwordField.fill(password);

        await expect(this.$submitPasswordStageButton).toBeEnabled();

        await this.$submitPasswordStageButton.click();
    }

    /**
     * Log into the application.
     */
    public async login({
        username = GOOD_USERNAME,
        password = GOOD_PASSWORD,
        to = SessionFixture.pathname,
    }: LoginInit = {}) {
        this.#logger.info("Logging in...");

        const currentURL = new URL(this.page.url());

        if (currentURL.pathname === SessionFixture.pathname) {
            this.#logger.info("Skipping navigation because we're already in a authentication flow");
        } else {
            await this.page.goto(to.toString());
        }

        await this.submitUsernameStage(username);

        await this.$passwordField.waitFor({ state: "visible" });
        await this.submitPasswordStage(password);
    }

    //#endregion

    //#region Navigation

    public async toLoginPage() {
        await this.page.goto(SessionFixture.pathname);
    }

    /**
     * Log out of the application.
     */
    public async toLogoutPage() {
        this.#logger.info("Logging out...");
        await this.page.goto("/flows/-/default/invalidation/");

        this.#logger.info("Waiting for ak-interface-root to exist...");
        await this.$interfaceRoot.waitFor();
    }
}
