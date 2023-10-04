import { browser } from "@wdio/globals";

const CLICK_TIME_DELAY = 250;

/**
 * Main page object containing all methods, selectors and functionality that is shared across all
 * page objects
 */
export default class Page {
    /**
     * Opens a sub page of the page
     * @param path path of the sub page (e.g. /path/to/page.html)
     */
    public open(path: string) {
        return browser.url(`http://localhost:9000/${path}`);
    }

    public pause(selector?: string) {
        if (selector) {
            return $(selector).waitForDisplayed();
        }
        return browser.pause(CLICK_TIME_DELAY);
    }

    /**
     * Target a specific entry in SearchSelect. Requires that the SearchSelect have the `name`
     * attribute set, so that the managed selector can find the *right* SearchSelect if there are
     * multiple open SearchSelects on the board. See `./ldap-form.view:LdapForm.setBindFlow` for an
     * example, and see `./oauth-form.view:OauthForm:setAuthorizationFlow` for a further example of
     * why it would be hard to simplify this further (`flow` vs `tentanted-flow` vs a straight-up
     * SearchSelect each have different a `searchSelector`).
     */

    async searchSelect(searchSelector: string, managedSelector: string, buttonSelector: string) {
        const inputBind = await $(searchSelector);
        await inputBind.click();
        const searchBlock = await $(`>>>div[data-managed-for="${managedSelector}"]`);
        const target = searchBlock.$(buttonSelector);
        return await target.click();
    }

    public async logout() {
        await browser.url("http://localhost:9000/flows/-/default/invalidation/");
        return await this.pause();
    }
}
