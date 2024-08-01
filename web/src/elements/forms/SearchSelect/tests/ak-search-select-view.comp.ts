import type { Element } from "@wdio/globals";
import { $, browser } from "@wdio/globals";

import { SearchSelectView } from "../ak-search-select-view.js";
import { isVisible } from "./is-visible.js";

browser.addCommand(
    "focus",
    function () {
        browser.execute(function (domElement) {
            domElement.focus();
        }, this);
    },
    true,
);

export class AkSearchSelectViewDriver {
    constructor(
        private element: Element,
        private menu: Element,
    ) {
        /* no op */
    }

    static async build(element: Element) {
        const tagname = await element.getTagName();
        const comptype = await element.getAttribute("data-ouia-component-type");
        if (comptype !== "ak-search-select-view") {
            throw new Error(
                `SearchSelectView driver passed incorrect component. Expected ak-search-select-view, got ${comptype ? `'${comptype}` : `No test data type, tag name: '${tagname}'`}`,
            );
        }
        const id = await element.getAttribute("data-ouia-component-id");
        const menu = await $(`[data-ouia-component-id="menu-${id}"]`);
        return new AkSearchSelectViewDriver(element, menu);
    }

    inputState() {
        return this.element.getProperty("inputState");
    }

    input() {
        return this.element.$(">>>input");
    }

    focusOnInput() {
        $(this.input).focus();
    }

    async inputIsVisible() {
        return await this.element.$(">>>input").isDisplayed();
    }

    async menuIsVisible() {
        return (await this.menu.isExisting()) && (await this.menu.isDisplayed());
    }

    async clickInput() {
        return await (await this.input()).click();
    }
}
