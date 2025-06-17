import { render } from "@goauthentik/elements/tests/utils.js";
import { $, browser, expect } from "@wdio/globals";

import { html } from "lit";

import "../Divider.js";
import { akDivider } from "../Divider.js";

describe("ak-divider", () => {
    it("should render the divider", async () => {
        render(html`<ak-divider></ak-divider>`);
        const empty = $("ak-divider");

        await expect(empty).resolves.toExist();
    });

    it("should render the divider with the specified text", async () => {
        render(html`<ak-divider><span>Your Message Here</span></ak-divider>`);
        const span = $("ak-divider").$(">>>span");

        await expect(span).resolves.toExist();
        await expect(span).resolves.toHaveText("Your Message Here");
    });

    it("should render the divider as a function with the specified text", async () => {
        render(akDivider("Your Message As A Function"));
        const divider = $("ak-divider");

        await expect(divider).resolves.toExist();
        await expect(divider).resolves.toHaveText("Your Message As A Function");
    });

    it("should render the divider as a function", async () => {
        render(akDivider());
        const empty = $("ak-divider");

        await expect(empty).resolves.toExist();
    });
});
