import { browser } from "@wdio/globals";

const CLICK_TIME_DELAY = 250;

/**
 * main page object containing all methods, selectors and functionality
 * that is shared across all page objects
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

    async searchSelect(searchSelector: string, managedSelector: string, buttonSelector: string) {
        const inputBind = await $(searchSelector);
        await inputBind.click();
        const searchBlock = await $(`>>>div[data-managed-for="${managedSelector}"]`);
        const target = searchBlock.$(buttonSelector);
        return await target.click();
    }
}
