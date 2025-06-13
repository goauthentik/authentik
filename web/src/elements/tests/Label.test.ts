import { render } from "@goauthentik/elements/tests/utils.js";
import { $, browser, expect } from "@wdio/globals";

import { html } from "lit";

import "../Label.js";
import { PFColor, akLabel } from "../Label.js";

describe("ak-label", () => {
    it("should render a label with the enum", async () => {
        render(html`<ak-label color=${PFColor.Red}>This is a label</ak-label>`);

        await expect($("ak-label").$(">>>span.pf-c-label")).resolves.toHaveElementClass(
            "pf-c-label",
        );
        await expect($("ak-label").$(">>>span.pf-c-label")).resolves.not.toHaveElementClass(
            "pf-m-compact",
        );
        await expect($("ak-label").$(">>>span.pf-c-label")).resolves.toHaveElementClass("pf-m-red");
        await expect($("ak-label").$(">>>i.fas")).resolves.toHaveElementClass("fa-times");
        await expect($("ak-label").$(">>>.pf-c-label__content")).resolves.toHaveText(
            "This is a label",
        );
    });

    it("should render a label with the attribute", async () => {
        render(html`<ak-label color="success">This is a label</ak-label>`);

        await expect($("ak-label").$(">>>span.pf-c-label")).resolves.toHaveElementClass(
            "pf-m-green",
        );
        await expect($("ak-label").$(">>>.pf-c-label__content")).resolves.toHaveText(
            "This is a label",
        );
    });

    it("should render a compact label with the default level", async () => {
        render(html`<ak-label compact>This is a label</ak-label>`);

        await expect($("ak-label").$(">>>span.pf-c-label")).resolves.toHaveElementClass(
            "pf-m-grey",
        );
        await expect($("ak-label").$(">>>span.pf-c-label")).resolves.toHaveElementClass(
            "pf-m-compact",
        );
        await expect($("ak-label").$(">>>i.fas")).resolves.toHaveElementClass("fa-info-circle");
        await expect($("ak-label").$(">>>.pf-c-label__content")).resolves.toHaveText(
            "This is a label",
        );
    });

    it("should render a compact label with an icon and the default level", async () => {
        render(html`<ak-label compact icon="fa-coffee">This is a label</ak-label>`);

        await expect($("ak-label").$(">>>span.pf-c-label")).resolves.toHaveElementClass(
            "pf-m-grey",
        );
        await expect($("ak-label").$(">>>span.pf-c-label")).resolves.toHaveElementClass(
            "pf-m-compact",
        );
        await expect($("ak-label").$(">>>.pf-c-label__content")).resolves.toHaveText(
            "This is a label",
        );
        await expect($("ak-label").$(">>>i.fas")).resolves.toHaveElementClass("fa-coffee");
    });

    it("should render a label with the function", async () => {
        render(akLabel({ color: "success" }, "This is a label"));

        await expect($("ak-label").$(">>>span.pf-c-label")).resolves.toHaveElementClass(
            "pf-m-green",
        );
        await expect($("ak-label").$(">>>.pf-c-label__content")).resolves.toHaveText(
            "This is a label",
        );
    });
});
