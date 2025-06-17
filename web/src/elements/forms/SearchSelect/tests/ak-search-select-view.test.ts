import { render } from "@goauthentik/elements/tests/utils.js";
import { $, browser, expect } from "@wdio/globals";
import { slug } from "github-slugger";
import { Key } from "webdriverio";

import { html } from "lit";

import "../ak-search-select-view.js";
import { sampleData } from "../stories/sampleData.js";
import { AkSearchSelectViewDriver } from "./ak-search-select-view.comp.js";

const longGoodForYouPairs = {
    grouped: false,
    options: sampleData.map(({ produce }) => [slug(produce), produce]),
};

describe("Search select: Test Input Field", () => {
    let select: AkSearchSelectViewDriver;

    beforeEach(async () => {
        render(
            html`<ak-search-select-view .options=${longGoodForYouPairs}> </ak-search-select-view>`,
        );

        select = await AkSearchSelectViewDriver.build($("ak-search-select-view"));
    });

    it("should open the menu when the input is clicked", async () => {
        await expect(select.isDropdownVisible()).resolves.toBe(false);
        await expect(select.menuIsVisible()).resolves.toBe(false);

        await select.clickInput();

        await expect(select.isDropdownVisible()).resolves.toBe(true);
    });

    it("should not open the menu when the input is focused", async () => {
        await expect(select.isDropdownVisible()).resolves.toBe(false);
        await select.focusOnInput();

        await expect(select.isDropdownVisible()).resolves.toBe(false);
        await expect(select.menuIsVisible()).resolves.toBe(false);
    });

    it("should close the menu when the input is clicked a second time", async () => {
        await expect(select.isDropdownVisible()).resolves.toBe(false);
        await expect(select.menuIsVisible()).resolves.toBe(false);

        await select.clickInput();

        await expect(select.menuIsVisible()).resolves.toBe(true);
        await expect(select.isDropdownVisible()).resolves.toBe(true);

        await select.clickInput();

        await expect(select.isDropdownVisible()).resolves.toBe(false);
        await expect(select.isDropdownVisible()).resolves.toBe(false);
    });

    it("should open the menu from a focused but closed input when a search is begun", async () => {
        await expect(select.isDropdownVisible()).resolves.toBe(false);
        await select.focusOnInput();

        await expect(select.isDropdownVisible()).resolves.toBe(false);
        await expect(select.menuIsVisible()).resolves.toBe(false);

        await browser.keys("A");

        select = await AkSearchSelectViewDriver.build($("ak-search-select-view"));

        await expect(select.isDropdownVisible()).resolves.toBe(true);
        await expect(select.menuIsVisible()).resolves.toBe(true);
    });

    it("should update the list as the user types", async () => {
        await select.focusOnInput();
        await browser.keys("Ap");

        await expect(select.menuIsVisible()).resolves.toBe(true);

        const elements = select.listElements();

        await expect(elements.length).resolves.toBe(2);
    });

    it("set the value when a match is close", async () => {
        await select.focusOnInput();
        await browser.keys("Ap");

        await expect(select.menuIsVisible()).resolves.toBe(true);
        const elements = Array.from(select.listElements());

        await expect(elements.length).resolves.toBe(2);
        await browser.keys(Key.Tab);
        await expect(select.input().getValue()).resolves.toBe("Apples");
    });

    it("should close the menu when the user clicks away", async () => {
        document.body.insertAdjacentHTML(
            "afterbegin",
            '<input id="a-separate-component" type="text" />',
        );
        const input = browser.$("#a-separate-component");

        await select.clickInput();

        await expect(select.isDropdownVisible()).resolves.toBe(true);

        await input.click();

        await expect(select.isDropdownVisible()).resolves.toBe(false);
    });

    afterEach(() =>
        browser.execute(() => {
            document.body.querySelector("#a-separate-component")?.remove();
            document.body.querySelector("ak-search-select-view")?.remove();

            if ("_$litPart$" in document.body) {
                delete document.body._$litPart$;
            }
        }),
    );
});
