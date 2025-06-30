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
            document.body,
        );
        // @ts-expect-error "Another ChainablePromise mistake"
        select = await AkSearchSelectViewDriver.build(await $("ak-search-select-view"));
    });

    it("should open the menu when the input is clicked", async () => {
        expect(await select.open).toBe(false);
        expect(await select.menuIsVisible()).toBe(false);
        await select.clickInput();
        expect(await select.open).toBe(true);
        //  expect(await select.menuIsVisible()).toBe(true);
    });

    it("should not open the menu when the input is focused", async () => {
        expect(await select.open).toBe(false);
        await select.focusOnInput();
        expect(await select.open).toBe(false);
        expect(await select.menuIsVisible()).toBe(false);
    });

    it("should close the menu when the input is clicked a second time", async () => {
        expect(await select.open).toBe(false);
        expect(await select.menuIsVisible()).toBe(false);
        await select.clickInput();
        expect(await select.menuIsVisible()).toBe(true);
        expect(await select.open).toBe(true);
        await select.clickInput();
        expect(await select.open).toBe(false);
        expect(await select.open).toBe(false);
    });

    it("should open the menu from a focused but closed input when a search is begun", async () => {
        expect(await select.open).toBe(false);
        await select.focusOnInput();
        expect(await select.open).toBe(false);
        expect(await select.menuIsVisible()).toBe(false);
        await browser.keys("A");
        // @ts-expect-error "Another ChainablePromise mistake"
        select = await AkSearchSelectViewDriver.build(await $("ak-search-select-view"));
        expect(await select.open).toBe(true);
        expect(await select.menuIsVisible()).toBe(true);
    });

    it("should update the list as the user types", async () => {
        await select.focusOnInput();
        await browser.keys("Ap");
        await expect(await select.menuIsVisible()).toBe(true);
        // @ts-expect-error "Another ChainablePromise mistake"
        const elements = Array.from(await select.listElements());
        await expect(elements.length).toBe(2);
    });

    it("set the value when a match is close", async () => {
        await select.focusOnInput();
        await browser.keys("Ap");
        await expect(await select.menuIsVisible()).toBe(true);
        // @ts-expect-error "Another ChainablePromise mistake"
        const elements = Array.from(await select.listElements());
        await expect(elements.length).toBe(2);
        await browser.keys(Key.Tab);
        await expect(await (await select.input()).getValue()).toBe("Apples");
    });

    it("should close the menu when the user clicks away", async () => {
        document.body.insertAdjacentHTML(
            "afterbegin",
            '<input id="a-separate-component" type="text" />',
        );
        const input = await browser.$("#a-separate-component");

        await select.clickInput();
        expect(await select.open).toBe(true);
        await input.click();
        expect(await select.open).toBe(false);
    });

    afterEach(async () => {
        await browser.execute(() => {
            document.body.querySelector("#a-separate-component")?.remove();
            document.body.querySelector("ak-search-select-view")?.remove();
            // @ts-expect-error expression of type '"_$litPart$"' is added by Lit
            if (document.body._$litPart$) {
                // @ts-expect-error expression of type '"_$litPart$"' is added by Lit
                delete document.body._$litPart$;
            }
        });
    });
});
