import { $, browser } from "@wdio/globals";
import type { ChainablePromiseElement } from "webdriverio";

browser.addCommand(
    "focus",
    () => {
        browser.execute(function applyFocus(this: HTMLElement) {
            this?.focus?.();
        });
    },
    true, // Extend to all elements
);

declare global {
    namespace WebdriverIO {
        interface Element {
            focus: () => Promise<void>;
        }
    }
}

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
    ) {
        /* no op */
    }

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

    get open() {
        return this.element.getProperty("open");
    }

    input() {
        return this.element.$(">>>input");
    }

    async listElements() {
        return this.menu.$$(">>>li");
    }

    async focusOnInput() {
        await (await this.input().getElement()).focus();
    }

    async inputIsVisible() {
        return await this.element.$(">>>input").isDisplayed();
    }

    async menuIsVisible() {
        return (await this.menu.isExisting()) && (await this.menu.isDisplayed());
    }

    async clickInput() {
        return await this.input().click();
    }
}
