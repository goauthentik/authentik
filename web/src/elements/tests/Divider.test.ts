import { render } from "@goauthentik/elements/tests/utils.js";
import { $, expect } from "@wdio/globals";

import { html } from "lit";

import "../Divider.js";
import { akDivider } from "../Divider.js";

describe("ak-divider", () => {
    it("should render the divider", async () => {
        render(html`<ak-divider></ak-divider>`);
        const empty = await $("ak-divider");
        await expect(empty).toExist();
    });

    it("should render the divider with the specified text", async () => {
        render(html`<ak-divider><span>Your Message Here</span></ak-divider>`);
        const span = await $("ak-divider").$(">>>span");
        await expect(span).toExist();
        await expect(span).toHaveText("Your Message Here");
    });

    it("should render the divider as a function with the specified text", async () => {
        render(akDivider("Your Message As A Function"));
        const divider = await $("ak-divider");
        await expect(divider).toExist();
        await expect(divider).toHaveText("Your Message As A Function");
    });

    it("should render the divider as a function", async () => {
        render(akDivider());
        const empty = await $("ak-divider");
        await expect(empty).toExist();
    });
});
