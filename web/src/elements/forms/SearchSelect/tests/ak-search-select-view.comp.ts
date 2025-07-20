import { $ } from "@wdio/globals";
import { ChainablePromiseElement } from "webdriverio";

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
    constructor(
        public element: ChainablePromiseElement,
        public menu: ChainablePromiseElement,
    ) {}

    static async build(element: ChainablePromiseElement) {
        const tagname = await element.getTagName();
        const comptype = await element.getAttribute("data-ouia-component-type");

        if (comptype !== "ak-search-select-view") {
            throw new Error(
                `SearchSelectView driver passed incorrect component. Expected ak-search-select-view, got ${comptype ? `'${comptype}` : `No test data type, tag name: '${tagname}'`}`,
            );
        }

        const id = await element.getAttribute("data-ouia-component-id");
        const menu = $(`[data-ouia-component-id="menu-${id}"]`);

        return new AkSearchSelectViewDriver(element, menu);
    }

    isDropdownVisible() {
        return this.element.getProperty("open");
    }

    input() {
        return this.element.$(">>>input");
    }

    listElements() {
        return this.menu.$$(">>>li");
    }

    focusOnInput() {
        return this.input().focus();
    }

    inputIsVisible() {
        return this.element.$(">>>input").isDisplayed();
    }

    async menuIsVisible() {
        return (await this.menu.isExisting()) && (await this.menu.isDisplayed());
    }

    async clickInput() {
        return this.input().click();
    }
}
