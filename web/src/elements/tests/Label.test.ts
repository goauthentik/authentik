import { render } from "@goauthentik/elements/tests/utils.js";
import { $, expect } from "@wdio/globals";

import { html } from "lit";

import "../Label.js";
import { PFColor, akLabel } from "../Label.js";

describe("ak-label", () => {
    it("should render a label with the enum", async () => {
        render(html`<ak-label color=${PFColor.Red}>This is a label</ak-label>`);
        await expect(await $("ak-label").$(">>>span.pf-c-label")).toHaveElementClass("pf-c-label");
        await expect(await $("ak-label").$(">>>span.pf-c-label")).not.toHaveElementClass(
            "pf-m-compact",
        );
        await expect(await $("ak-label").$(">>>span.pf-c-label")).toHaveElementClass("pf-m-red");
        await expect(await $("ak-label").$(">>>i.fas")).toHaveElementClass("fa-times");
        await expect(await $("ak-label").$(">>>.pf-c-label__content")).toHaveText(
            "This is a label",
        );
    });

    it("should render a label with the attribute", async () => {
        render(html`<ak-label color="success">This is a label</ak-label>`);
        await expect(await $("ak-label").$(">>>span.pf-c-label")).toHaveElementClass("pf-m-green");
        await expect(await $("ak-label").$(">>>.pf-c-label__content")).toHaveText(
            "This is a label",
        );
    });

    it("should render a compact label with the default level", async () => {
        render(html`<ak-label compact>This is a label</ak-label>`);
        await expect(await $("ak-label").$(">>>span.pf-c-label")).toHaveElementClass("pf-m-grey");
        await expect(await $("ak-label").$(">>>span.pf-c-label")).toHaveElementClass(
            "pf-m-compact",
        );
        await expect(await $("ak-label").$(">>>i.fas")).toHaveElementClass("fa-info-circle");
        await expect(await $("ak-label").$(">>>.pf-c-label__content")).toHaveText(
            "This is a label",
        );
    });

    it("should render a compact label with an icon and the default level", async () => {
        render(html`<ak-label compact icon="fa-coffee">This is a label</ak-label>`);
        await expect(await $("ak-label").$(">>>span.pf-c-label")).toHaveElementClass("pf-m-grey");
        await expect(await $("ak-label").$(">>>span.pf-c-label")).toHaveElementClass(
            "pf-m-compact",
        );
        await expect(await $("ak-label").$(">>>.pf-c-label__content")).toHaveText(
            "This is a label",
        );
        await expect(await $("ak-label").$(">>>i.fas")).toHaveElementClass("fa-coffee");
    });

    it("should render a label with the function", async () => {
        render(akLabel({ color: "success" }, "This is a label"));
        await expect(await $("ak-label").$(">>>span.pf-c-label")).toHaveElementClass("pf-m-green");
        await expect(await $("ak-label").$(">>>.pf-c-label__content")).toHaveText(
            "This is a label",
        );
    });
});
