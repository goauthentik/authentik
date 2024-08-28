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
    async inputUsername() {
        return await $('input[name="uidField"]');
    }

    async inputPassword() {
        return await $('input[name="password"]');
    }

    async btnSubmit() {
        return await $('button[type="submit"]');
    }

    async authFailure() {
        return await $(".pf-m-error");
    }

    /**
     * Specific interactions
     */

    async username(username: string) {
        await (await this.inputUsername()).setValue(username);
        await (await this.btnSubmit()).waitForEnabled();
        await (await this.btnSubmit()).click();
    }

    async password(password: string) {
        await (await this.inputPassword()).setValue(password);
        await (await this.btnSubmit()).waitForEnabled();
        await (await this.btnSubmit()).click();
    }

    async login(username: string, password: string) {
        await this.username(username);
        await this.pause();
        await this.password(password);
        await this.pause();
        await this.pause("div.header h1");
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
