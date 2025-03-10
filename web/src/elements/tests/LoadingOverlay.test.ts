import { render } from "@goauthentik/elements/tests/utils.js";
import { $, expect } from "@wdio/globals";

import { html } from "lit";

import "../LoadingOverlay.js";
import { akLoadingOverlay } from "../LoadingOverlay.js";

describe("ak-loading-overlay", () => {
    it("should render the default loader", async () => {
        render(html`<ak-loading-overlay></ak-loading-overlay>`);

        const empty = await $("ak-loading-overlay");
        await expect(empty).toExist();
    });

    it("should render a slotted message", async () => {
        render(
            html`<ak-loading-overlay>
                <p>Try again with a different filter</p>
            </ak-loading-overlay>`,
        );

        const message = await $("ak-loading-overlay").$(">>>p");
        await expect(message).toHaveText("Try again with a different filter");
    });

    it("as a function should render a slotted message", async () => {
        render(akLoadingOverlay({}, "Try again with another filter"));
        const overlay = await $("ak-loading-overlay");
        await expect(overlay).toHaveText("Try again with another filter");
    });
});
