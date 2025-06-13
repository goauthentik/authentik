import UserLibraryPage from "#tests/pageobjects/user-library.page";
import { ConsoleTestRunner } from "#tests/utils/logger";
import { navigateBrowser } from "#tests/utils/navigation";
import { $, browser } from "@wdio/globals";

export const GOOD_USERNAME = "test-admin@goauthentik.io";
export const GOOD_PASSWORD = "test-runner";

export const BAD_USERNAME = "bad-username@bad-login.io";
export const BAD_PASSWORD = "-this-is-a-bad-password-";

export interface LoginInit {
    username?: string;
    password?: string;
    to?: URL | string;
}

export abstract class SessionPage {
    public static readonly pathname = "/if/flow/default-authentication-flow/";
    //#region Selectors

    public static get $interfaceRoot() {
        return $("[data-ak-interface-root]");
    }

    /**
     * The username field on the login page.
     */
    public static get $usernameField() {
        return $("ak-stage-identification").$('input[name="uidField"]');
    }

    /**
     * The button to continue with the login process,
     * typically to the password flow stage.
     */
    public static get $submitUsernameStageButton() {
        return $('button[type="submit"]');
    }

    /**
     * The password field on the login page.
     */
    public static get $passwordField() {
        return $("input#ak-stage-password-input");
    }

    /**
     * The button to submit the the login flow,
     * typically redirecting to the authenticated interface.
     */
    public static get $submitPasswordStageButton() {
        return $("ak-stage-password").$('button[type="submit"]');
    }

    /**
     * A possible authentication failure message.
     */
    public static get $authFailureMessage() {
        // return $("ak-form-element").$(".pf-m-error");
        return $(".pf-m-error");
    }

    //#endregion

    //#region Specific interactions

    public static async submitUsernameStage(username: string) {
        ConsoleTestRunner.info("Submitting username stage", username);
        await this.$usernameField.setValue(username);

        console.time("Waiting for submit button");
        await this.$submitUsernameStageButton.waitForEnabled();
        console.timeEnd("Waiting for submit button");

        console.time("Submitting username stage...");
        await this.$submitUsernameStageButton.click();
        console.timeEnd("Submitting username stage...");
    }

    public static async submitPasswordStage(password: string) {
        ConsoleTestRunner.info("Submitting password stage");
        await this.$passwordField.setValue(password);

        console.time("Waiting for submit button");
        await this.$submitPasswordStageButton.waitForEnabled();
        console.timeEnd("Waiting for submit button");

        console.time("Submitting password stage...");
        await this.$submitPasswordStageButton.click();
        console.timeEnd("Submitting password stage...");
    }

    /**
     * Log into the application.
     */
    public static async login({
        username = GOOD_USERNAME,
        password = GOOD_PASSWORD,
        to = SessionPage.pathname,
    }: LoginInit = {}) {
        ConsoleTestRunner.info("Session: Logging in...");

        const currentURL = new URL(await browser.getUrl());

        if (currentURL.pathname === SessionPage.pathname) {
            ConsoleTestRunner.info(
                "Skipping navigation because we're already in a authentication flow",
            );
        } else {
            await navigateBrowser(to);
        }

        await this.submitUsernameStage(username);

        await this.$passwordField.waitForDisplayed();
        await this.submitPasswordStage(password);
    }

    /**
     * Log out of the application.
     */
    public static async logout() {
        ConsoleTestRunner.info("Session: Logging out...");
        await navigateBrowser("/flows/-/default/invalidation/");

        ConsoleTestRunner.info("Waiting for ak-interface-root to exist...");
        await this.$interfaceRoot.waitForExist();
    }

    //#endregion
}

export default SessionPage;
