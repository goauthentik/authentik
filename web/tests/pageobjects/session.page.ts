/// <reference types="@wdio/globals/types" />
import { navigateBrowser } from "../utils/navigation.js";
import { waitFor } from "../utils/timers.js";

export const GOOD_USERNAME = process.env.AK_GOOD_USERNAME ?? "test-admin@goauthentik.io";
export const GOOD_PASSWORD = process.env.AK_GOOD_PASSWORD ?? "test-runner";

export const BAD_USERNAME = process.env.AK_BAD_USERNAME ?? "bad-username@bad-login.io";
export const BAD_PASSWORD = process.env.AK_BAD_PASSWORD ?? "-this-is-a-bad-password-";

export interface LoginInit {
    username?: string;
    password?: string;
}

export abstract class SessionPage {
    //#region Selectors

    /**
     * The username field on the login page.
     */
    public static get $usernameField() {
        return $(">>>ak-stage-identification").$('>>>input[name="uidField"]');
    }

    /**
     * The button to continue with the login process,
     * typically to the password flow stage.
     */
    public static get $submitUsernameStageButton() {
        return $('>>>button[type="submit"]');
    }

    /**
     * The password field on the login page.
     */
    public static get $passwordField() {
        return $(">>>input#ak-stage-password-input");
    }

    /**
     * The button to submit the the login flow,
     * typically redirecting to the authenticated interface.
     */
    public static get $submitPasswordStageButton() {
        return $(">>>ak-stage-password").$('>>>button[type="submit"]');
    }

    /**
     * A possible authentication failure message.
     */
    public static get $authFailureMessage() {
        // return $("ak-form-element").$(">>>.pf-m-error");
        return $(">>>.pf-m-error");
    }

    //#endregion

    //#region Specific interactions

    public static async submitUsernameStage(username: string) {
        console.debug("Submitting username stage", username);
        await this.$usernameField.setValue(username);

        console.time("Waiting for submit button");
        await this.$submitUsernameStageButton.waitForEnabled();
        console.timeEnd("Waiting for submit button");

        console.time("Submitting username stage...");
        await this.$submitUsernameStageButton.click();
        console.timeEnd("Submitting username stage...");
    }

    public static async submitPasswordStage(password: string) {
        console.debug("Submitting password stage");
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
    }: LoginInit = {}) {
        await navigateBrowser();
        await this.submitUsernameStage(username);

        await this.$passwordField.waitForDisplayed();
        await this.submitPasswordStage(password);

        console.time("Waiting for header");
        await $(">>>div.header h1").waitForDisplayed();
        console.timeEnd("Waiting for header");
    }

    /**
     * Log out of the application.
     */
    public static logout() {
        return navigateBrowser("/flows/-/default/invalidation/").then(() => waitFor());
    }

    //#endregion
}

export default SessionPage;
