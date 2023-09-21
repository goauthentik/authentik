import { $ } from "@wdio/globals";
import Page from "./page.js";
import UserLibraryPage from "./user-library.page.js";

/**
 * sub page containing specific selectors and methods for a specific page
 */
class LoginPage extends Page {
    /**
     * define selectors using getter methods
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
     * a method to encapsule automation code to interact with the page
     * e.g. to login using username and password
     */
    async username(username: string) {
        await this.inputPassword.isDisplayed();
        await this.inputUsername.setValue(username);
        await this.btnSubmit.isEnabled();
        await this.btnSubmit.click();
    }

    async password(password: string) {
        await this.inputPassword.isDisplayed();
        await this.inputPassword.setValue(password);
        await this.btnSubmit.isEnabled();
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
     * overwrite specific options to adapt it to page object
     */
    open() {
        return super.open("");
    }
}

export default new LoginPage();
