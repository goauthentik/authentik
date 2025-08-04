import { $, browser } from "@wdio/globals";

browser.addCommand(
    "focus",
    function () {
        browser.execute(function (domElement) {
            domElement.focus();
            // @ts-ignore
        }, this);
    },
    true,
);

/**
 * Search Select View Driver
 *
 * This class provides a collection of easy-to-use methods for interacting with and examining the
 * results of an interaction with an `ak-search-select-view` via WebdriverIO.
 *
 * It's hoped that with the OUIA tags, we could automate testing further. The OUIA tag would
 * instruct the test harness "use this driver to test this component," and we could test Forms and
 * Tables with a small DSL of test language concepts
 */

export class AkSearchSelectViewDriver {
    public constructor(
        public element: WebdriverIO.Element,
        public menu: WebdriverIO.Element,
    ) {
        /* no op */
    }

    public static async build(element: WebdriverIO.Element) {
        const tagname = await element.getTagName();
        const comptype = await element.getAttribute("data-ouia-component-type");
        if (comptype !== "ak-search-select-view") {
            throw new Error(
                `SearchSelectView driver passed incorrect component. Expected ak-search-select-view, got ${comptype ? `'${comptype}` : `No test data type, tag name: '${tagname}'`}`,
            );
        }
        const id = await element.getAttribute("data-ouia-component-id");
        const menu = await $(`[data-ouia-component-id="menu-${id}"]`);
        // @ts-expect-error "Another ChainablePromise mistake"
        return new AkSearchSelectViewDriver(element, menu);
    }

    public get open() {
        return this.element.getProperty("open");
    }

    protected async input() {
        return await this.element.$(">>>input");
    }

    protected async listElements() {
        return await this.menu.$$(">>>li");
    }

    protected async focusOnInput() {
        // @ts-ignore
        await (await this.input()).focus();
    }

    protected async inputIsVisible() {
        return await this.element.$(">>>input").isDisplayed();
    }

    protected async menuIsVisible() {
        return (await this.menu.isExisting()) && (await this.menu.isDisplayed());
    }

    protected async clickInput() {
        return await (await this.input()).click();
    }
}
