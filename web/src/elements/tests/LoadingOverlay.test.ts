import { ensureCSSStyleSheet } from "@goauthentik/elements/utils/ensureCSSStyleSheet.js";
import { $, expect } from "@wdio/globals";

import { TemplateResult, html, render as litRender } from "lit";

import AKGlobal from "@goauthentik/common/styles/authentik.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import "../LoadingOverlay.js";

const render = (body: TemplateResult) => {
    document.adoptedStyleSheets = [
        ...document.adoptedStyleSheets,
        ensureCSSStyleSheet(PFBase),
        ensureCSSStyleSheet(AKGlobal),
    ];
    return litRender(body, document.body);
};

describe("ak-loading-overlay", () => {
    it("should render the default loader", async () => {
        render(html`<ak-loading-overlay></ak-loading-overlay>`);

        const empty = await $("ak-loading-overlay");
        await expect(empty).toExist();
    });

    it("should render a slotted message", async () => {
        render(
            html`<ak-loading-overlay>
                <p slot="body">Try again with a different filter</p>
            </ak-loading-overlay>`,
        );

        const message = await $("ak-loading-overlay").$(">>>p");
        await expect(message).toHaveText("Try again with a different filter");
    });
});
