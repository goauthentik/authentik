import { render } from "@goauthentik/elements/tests/utils.js";
import { $, expect } from "@wdio/globals";

import { html } from "lit";

import "../Expand.js";
import { akExpand } from "../Expand.js";

describe("ak-expand", () => {
    afterEach(async () => {
        await browser.execute(() => {
            document.body.querySelector("ak-expand")?.remove();

            if ("_$litPart$" in document.body) {
                delete document.body._$litPart$;
            }
        });
    });

    it("should render the expansion content hidden by default", async () => {
        render(html`<ak-expand><p>This is the expanded text</p></ak-expand>`);
        const text = $("ak-expand").$(">>>.pf-c-expandable-section__content");
        await expect(text).not.toBeDisplayed();
    });

    it("should render the expansion content visible on demand", async () => {
        render(html`<ak-expand expanded><p>This is the expanded text</p></ak-expand>`);
        const paragraph = $("ak-expand").$(">>>p");
        await expect(paragraph).toExist();
        await expect(paragraph).toBeDisplayed();
        await expect(paragraph).toHaveText("This is the expanded text");
    });

    it("should respond to the click event", async () => {
        render(html`<ak-expand><p>This is the expanded text</p></ak-expand>`);
        let content = $("ak-expand").$(">>>.pf-c-expandable-section__content");
        await expect(content).toExist();
        await expect(content).not.toBeDisplayed();
        const control = $("ak-expand").$(">>>button");

        await control.click();
        content = $("ak-expand").$(">>>.pf-c-expandable-section__content");
        await expect(content).toExist();
        await expect(content).toBeDisplayed();

        await control.click();
        content = $("ak-expand").$(">>>.pf-c-expandable-section__content");
        await expect(content).toExist();
        await expect(content).not.toBeDisplayed();
    });

    it("should honor the header properties", async () => {
        render(
            html`<ak-expand textOpen="Close it" textClosed="Open it" expanded
                ><p>This is the expanded text</p></ak-expand
            >`,
        );
        const paragraph = $("ak-expand").$(">>>p");
        await expect(paragraph).toExist();
        await expect(paragraph).toBeDisplayed();
        await expect(paragraph).toHaveText("This is the expanded text");
        await expect($("ak-expand").$(".pf-c-expandable-section__toggle-text")).toHaveText(
            "Close it",
        );

        const control = $("ak-expand").$(">>>button");
        await control.click();
        await expect($("ak-expand").$(".pf-c-expandable-section__toggle-text")).toHaveText(
            "Open it",
        );
    });

    it("should honor the header properties via a function call", async () => {
        render(
            akExpand(
                { expanded: true, textOpen: "Close it now", textClosed: "Open it now" },
                html`<p>This is the new text.</p>`,
            ),
        );
        const paragraph = $("ak-expand").$(">>>p");
        await expect(paragraph).toExist();
        await expect(paragraph).toBeDisplayed();
        await expect(paragraph).toHaveText("This is the new text.");
        await expect($("ak-expand").$(".pf-c-expandable-section__toggle-text")).toHaveText(
            "Close it now",
        );
        const control = $("ak-expand").$(">>>button");
        await control.click();
        await expect($("ak-expand").$(".pf-c-expandable-section__toggle-text")).toHaveText(
            "Open it now",
        );
    });
});
