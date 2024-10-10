import { render } from "@goauthentik/elements/tests/utils.js";
import { $, expect } from "@wdio/globals";

import { html } from "lit";

import "../Expand.js";
import { akExpand } from "../Expand.js";

describe("ak-expand", () => {
    afterEach(async () => {
        await browser.execute(async () => {
            await document.body.querySelector("ak-expand")?.remove();
            if (document.body["_$litPart$"]) {
                // @ts-expect-error expression of type '"_$litPart$"' is added by Lit
                await delete document.body["_$litPart$"];
            }
        });
    });

    it("should render the expansion content hidden by default", async () => {
        render(html`<ak-expand><p>This is the expanded text</p></ak-expand>`);
        const text = await $("ak-expand").$(">>>.pf-c-expandable-section__content");
        await expect(text).not.toBeDisplayed();
    });

    it("should render the expansion content visible on demand", async () => {
        render(html`<ak-expand expanded><p>This is the expanded text</p></ak-expand>`);
        const paragraph = await $("ak-expand").$(">>>p");
        await expect(paragraph).toExist();
        await expect(paragraph).toBeDisplayed();
        await expect(paragraph).toHaveText("This is the expanded text");
    });

    it("should respond to the click event", async () => {
        render(html`<ak-expand><p>This is the expanded text</p></ak-expand>`);
        let content = await $("ak-expand").$(">>>.pf-c-expandable-section__content");
        await expect(content).toExist();
        await expect(content).not.toBeDisplayed();
        const control = await $("ak-expand").$(">>>button");

        await control.click();
        content = await $("ak-expand").$(">>>.pf-c-expandable-section__content");
        await expect(content).toExist();
        await expect(content).toBeDisplayed();

        await control.click();
        content = await $("ak-expand").$(">>>.pf-c-expandable-section__content");
        await expect(content).toExist();
        await expect(content).not.toBeDisplayed();
    });

    it("should honor the header properties", async () => {
        render(
            html`<ak-expand text-open="Close it" text-closed="Open it" expanded
                ><p>This is the expanded text</p></ak-expand
            >`,
        );
        const paragraph = await $("ak-expand").$(">>>p");
        await expect(paragraph).toExist();
        await expect(paragraph).toBeDisplayed();
        await expect(paragraph).toHaveText("This is the expanded text");
        await expect(await $("ak-expand").$(".pf-c-expandable-section__toggle-text")).toHaveText(
            "Close it",
        );

        const control = await $("ak-expand").$(">>>button");
        await control.click();
        await expect(await $("ak-expand").$(".pf-c-expandable-section__toggle-text")).toHaveText(
            "Open it",
        );
    });

    it("should honor the header properties via a function call", async () => {
        render(
            akExpand(
                { "expanded": true, "text-open": "Close it now", "text-closed": "Open it now" },
                html`<p>This is the new text.</p>`,
            ),
        );
        const paragraph = await $("ak-expand").$(">>>p");
        await expect(paragraph).toExist();
        await expect(paragraph).toBeDisplayed();
        await expect(paragraph).toHaveText("This is the new text.");
        await expect(await $("ak-expand").$(".pf-c-expandable-section__toggle-text")).toHaveText(
            "Close it now",
        );
        const control = await $("ak-expand").$(">>>button");
        await control.click();
        await expect(await $("ak-expand").$(".pf-c-expandable-section__toggle-text")).toHaveText(
            "Open it now",
        );
    });
});
