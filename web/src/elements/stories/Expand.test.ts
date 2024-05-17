import { ensureCSSStyleSheet } from "@goauthentik/elements/utils/ensureCSSStyleSheet.js";
import { $, expect } from "@wdio/globals";

import { TemplateResult, html, render as litRender } from "lit";

import AKGlobal from "@goauthentik/common/styles/authentik.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import "../Expand.js";

const render = (body: TemplateResult) => {
    document.adoptedStyleSheets = [
        ...document.adoptedStyleSheets,
        ensureCSSStyleSheet(PFBase),
        ensureCSSStyleSheet(AKGlobal),
    ];
    return litRender(body, document.body);
};

describe("ak-expand", () => {
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
});
