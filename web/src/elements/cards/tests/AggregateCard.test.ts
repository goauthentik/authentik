import { ensureCSSStyleSheet } from "@goauthentik/elements/utils/ensureCSSStyleSheet.js";
import { $, expect } from "@wdio/globals";

import { TemplateResult, html, render as litRender } from "lit";

import AKGlobal from "@goauthentik/common/styles/authentik.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import "../AggregateCard.js";

const render = (body: TemplateResult) => {
    document.adoptedStyleSheets = [
        ...document.adoptedStyleSheets,
        ensureCSSStyleSheet(PFBase),
        ensureCSSStyleSheet(AKGlobal),
    ];
    return litRender(body, document.body);
};

describe("ak-aggregate-card", () => {
    it("should render the standard card without an icon, link, or subtext", async () => {
        render(
            html`<ak-aggregate-card header="Loading"
                ><p>This is the main content</p></ak-aggregate-card
            >`,
        );
        const component = await $("ak-aggregate-card");
        await expect(await component.$(">>>.pf-c-card__header a")).not.toExist();
        await expect(await component.$(">>>.pf-c-card__title i")).not.toExist();
        await expect(await component.$(">>>.pf-c-card__title")).toHaveText("Loading");
        await expect(await component.$(">>>.pf-c-card__body")).toHaveText(
            "This is the main content",
        );
        await expect(await component.$(">>>.subtext")).not.toExist();
    });

    it("should render the standard card with an icon", async () => {
        render(
            html`<ak-aggregate-card icon="fa fa-bath" header="Loading"
                ><p>This is the main content</p></ak-aggregate-card
            >`,
        );
        const component = await $("ak-aggregate-card");
        await expect(await component.$(">>>.pf-c-card__title i")).toExist();
        await expect(await component.$(">>>.pf-c-card__title")).toHaveText("Loading");
        await expect(await component.$(">>>.pf-c-card__body")).toHaveText(
            "This is the main content",
        );
    });

    it("should render the standard card with an icon, a link, and slotted content", async () => {
        render(
            html`<ak-aggregate-card icon="fa fa-bath" header="Loading" headerLink="http://localhost"
                ><p>This is the main content</p></ak-aggregate-card
            >`,
        );
        const component = await $("ak-aggregate-card");
        await expect(await component.$(">>>.pf-c-card__header a")).toExist();
        await expect(await component.$(">>>.pf-c-card__title i")).toExist();
        await expect(await component.$(">>>.pf-c-card__title")).toHaveText("Loading");
        await expect(await component.$(">>>.pf-c-card__body")).toHaveText(
            "This is the main content",
        );
    });

    it("should render the standard card with an icon, a link, and subtext", async () => {
        render(
            html`<ak-aggregate-card
                icon="fa fa-bath"
                header="Loading"
                headerLink="http://localhost"
                subtext="Xena had subtext"
                ><p>This is the main content</p></ak-aggregate-card
            >`,
        );
        const component = await $("ak-aggregate-card");
        await expect(await component.$(">>>.pf-c-card__header a")).toExist();
        await expect(await component.$(">>>.pf-c-card__title i")).toExist();
        await expect(await component.$(">>>.pf-c-card__title")).toHaveText("Loading");
        await expect(await component.$(">>>.subtext")).toHaveText("Xena had subtext");
    });
});
