import { render } from "@goauthentik/elements/tests/utils.js";
import { $, expect } from "@wdio/globals";

import { html } from "lit";

import "../Alert.js";
import { Level, akAlert } from "../Alert.js";

describe("ak-alert", () => {
    it("should render an alert with the enum", async () => {
        render(html`<ak-alert level=${Level.Info}>This is an alert</ak-alert>`, document.body);

        await expect(await $("ak-alert").$("div")).not.toHaveElementClass("pf-m-inline");
        await expect(await $("ak-alert").$("div")).toHaveElementClass("pf-c-alert");
        await expect(await $("ak-alert").$("div")).toHaveElementClass("pf-m-info");
        await expect(await $("ak-alert").$(".pf-c-alert__title")).toHaveText("This is an alert");
    });

    it("should render an alert with the attribute", async () => {
        render(html`<ak-alert level="info">This is an alert</ak-alert>`, document.body);
        await expect(await $("ak-alert").$("div")).toHaveElementClass("pf-m-info");
        await expect(await $("ak-alert").$(".pf-c-alert__title")).toHaveText("This is an alert");
    });

    it("should render an alert with an inline class and the default level", async () => {
        render(html`<ak-alert inline>This is an alert</ak-alert>`, document.body);
        await expect(await $("ak-alert").$("div")).toHaveElementClass("pf-m-warning");
        await expect(await $("ak-alert").$("div")).toHaveElementClass("pf-m-inline");
        await expect(await $("ak-alert").$(".pf-c-alert__title")).toHaveText("This is an alert");
    });

    it("should render an alert as a function call", async () => {
        render(akAlert({ level: "info" }, "This is an alert"));
        await expect(await $("ak-alert").$("div")).toHaveElementClass("pf-m-info");
        await expect(await $("ak-alert").$(".pf-c-alert__title")).toHaveText("This is an alert");
    });
});
