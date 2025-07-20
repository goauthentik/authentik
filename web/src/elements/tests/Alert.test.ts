import "../Alert.js";

import { akAlert, Level } from "../Alert.js";

import { render } from "#elements/tests/utils";

import { $, expect } from "@wdio/globals";

import { html } from "lit";

describe("ak-alert", () => {
    it("should render an alert with the enum", async () => {
        render(html`<ak-alert level=${Level.Info}>This is an alert</ak-alert>`);

        await expect($("ak-alert").$("div")).resolves.not.toHaveElementClass("pf-m-inline");
        await expect($("ak-alert").$("div")).resolves.toHaveElementClass("pf-c-alert");
        await expect($("ak-alert").$("div")).resolves.toHaveElementClass("pf-m-info");
        await expect($("ak-alert").$(".pf-c-alert__title")).resolves.toHaveText("This is an alert");
    });

    it("should render an alert with the attribute", async () => {
        render(html`<ak-alert level="info">This is an alert</ak-alert>`);

        await expect($("ak-alert").$("div")).resolves.toHaveElementClass("pf-m-info");
        await expect($("ak-alert").$(".pf-c-alert__title")).resolves.toHaveText("This is an alert");
    });

    it("should render an alert with an inline class and the default level", async () => {
        render(html`<ak-alert inline>This is an alert</ak-alert>`);

        await expect($("ak-alert").$("div")).resolves.toHaveElementClass("pf-m-warning");
        await expect($("ak-alert").$("div")).resolves.toHaveElementClass("pf-m-inline");
        await expect($("ak-alert").$(".pf-c-alert__title")).resolves.toHaveText("This is an alert");
    });

    it("should render an alert as a function call", async () => {
        render(akAlert({ level: "info" }, "This is an alert"));

        await expect($("ak-alert").$("div")).resolves.toHaveElementClass("pf-m-info");
        await expect($("ak-alert").$(".pf-c-alert__title")).resolves.toHaveText("This is an alert");
    });
});
