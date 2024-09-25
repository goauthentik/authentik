import { browser } from "@wdio/globals";
import { Key } from "webdriverio";

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
    public async open(path: string) {
        return await browser.url(`http://localhost:9000/${path}`);
    }

    public async pause(selector?: string) {
        if (selector) {
            return await $(selector).waitForDisplayed();
        }
        return await browser.pause(CLICK_TIME_DELAY);
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
        const inputMain = await inputBind.$('input[type="text"]');
        await inputMain.click();
        const searchBlock = await (
            await $(`div[data-managed-for="${managedSelector}"]`).$("ak-list-select")
        ).shadow$$("button");
        let target: WebdriverIO.Element;
        for (const button of searchBlock) {
            if ((await button.getText()).includes(buttonSelector)) {
                target = button;
                break;
            }
        }
        await (await target).click();
        await browser.keys(Key.Tab);
    }

    public async logout() {
        await browser.url("http://localhost:9000/flows/-/default/invalidation/");
        return await this.pause();
    }
}
