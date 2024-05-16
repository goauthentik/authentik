import { ensureCSSStyleSheet } from "@goauthentik/elements/utils/ensureCSSStyleSheet.js";
import { $, expect } from "@wdio/globals";

import { TemplateResult, html, render as litRender } from "lit";

import AKGlobal from "@goauthentik/common/styles/authentik.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import "../Divider.js";

const render = (body: TemplateResult) => {
    document.adoptedStyleSheets = [
        ...document.adoptedStyleSheets,
        ensureCSSStyleSheet(PFBase),
        ensureCSSStyleSheet(AKGlobal),
    ];
    return litRender(body, document.body);
};

describe("ak-divider", () => {
    it("should render the divider", async () => {
        render(html`<ak-divider></ak-divider>`);
        const empty = await $("ak-divider");
        await expect(empty).toExist();
    });

    it("should render the divider with the specified text", async () => {
        render(html`<ak-divider><span>Your Message Here</span></ak-divider>`);
        const span = await $("ak-divider").$("span");
        await expect(span).toExist();
        await expect(span).toHaveText("Your Message Here");
    });
});
