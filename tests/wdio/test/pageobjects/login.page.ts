import Page from "./page.js";
import UserLibraryPage from "./user-library.page.js";
import { $ } from "@wdio/globals";

/**
 * sub page containing specific selectors and methods for a specific page
 */
class LoginPage extends Page {
    /**
     * Selectors
     */
    get inputUsername() {
        return $('>>>input[name="uidField"]');
    }

    get inputPassword() {
        return $('>>>input[name="password"]');
    }

    get btnSubmit() {
        return $('>>>button[type="submit"]');
    }

    get authFailure() {
        return $(">>>h4.pf-c-alert__title");
    }

    /**
     * Specific interactions
     */

    async username(username: string) {
        await this.inputUsername.waitForClickable();
        await this.inputUsername.setValue(username);
        await this.btnSubmit.waitForEnabled();
        await this.btnSubmit.click();
    }

    async password(password: string) {
        await this.inputPassword.waitForClickable();
        await this.inputPassword.setValue(password);
        await this.btnSubmit.waitForEnabled();
        await this.btnSubmit.click();
    }

    async login(username: string, password: string) {
        await this.username(username);
        await this.pause();
        await this.password(password);
        await this.pause();
        await this.pause(">>>div.header h1");
        return UserLibraryPage;
    }

    /**
     * URL for accessing this page (if necessary)
     */
    open() {
        return super.open("");
    }
}

export default new LoginPage();
