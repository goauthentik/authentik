import { render } from "@goauthentik/elements/tests/utils.js";
import { $, browser, expect } from "@wdio/globals";

import { html } from "lit";

import "../AggregateCard.js";

describe("ak-aggregate-card", () => {
    it("should render the standard card without an icon, link, or subtext", async () => {
        render(
            html`<ak-aggregate-card header="Loading"
                ><p>This is the main content</p></ak-aggregate-card
            >`,
        );
        const component = $("ak-aggregate-card");

        await expect(component.$(">>>.pf-c-card__header a")).resolves.not.toExist();
        await expect(component.$(">>>.pf-c-card__title i")).resolves.not.toExist();
        await expect(component.$(">>>.pf-c-card__title")).resolves.toHaveText("Loading");
        await expect(component.$(">>>.pf-c-card__body")).resolves.toHaveText(
            "This is the main content",
        );
        await expect(component.$(">>>.subtext")).resolves.not.toExist();
    });

    it("should render the standard card with an icon", async () => {
        render(
            html`<ak-aggregate-card icon="fa fa-bath" header="Loading"
                ><p>This is the main content</p></ak-aggregate-card
            >`,
        );
        const component = $("ak-aggregate-card");

        await expect(component.$(">>>.pf-c-card__title i")).resolves.toExist();
        await expect(component.$(">>>.pf-c-card__title")).resolves.toHaveText("Loading");
        await expect(component.$(">>>.pf-c-card__body")).resolves.toHaveText(
            "This is the main content",
        );
    });

    it("should render the standard card with an icon, a link, and slotted content", async () => {
        render(
            html`<ak-aggregate-card icon="fa fa-bath" header="Loading" headerLink="http://localhost"
                ><p>This is the main content</p></ak-aggregate-card
            >`,
        );
        const component = $("ak-aggregate-card");

        await expect(component.$(">>>.pf-c-card__header a")).resolves.toExist();
        await expect(component.$(">>>.pf-c-card__title i")).resolves.toExist();
        await expect(component.$(">>>.pf-c-card__title")).resolves.toHaveText("Loading");
        await expect(component.$(">>>.pf-c-card__body")).resolves.toHaveText(
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
        const component = $("ak-aggregate-card");

        await expect(component.$(">>>.pf-c-card__header a")).resolves.toExist();
        await expect(component.$(">>>.pf-c-card__title i")).resolves.toExist();
        await expect(component.$(">>>.pf-c-card__title")).resolves.toHaveText("Loading");
        await expect(component.$(">>>.subtext")).resolves.toHaveText("Xena had subtext");
    });
});
