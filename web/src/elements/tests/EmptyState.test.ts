import { render } from "@goauthentik/elements/tests/utils.js";
import { $, browser, expect } from "@wdio/globals";

import { msg } from "@lit/localize";
import { html } from "lit";

import "../EmptyState.js";
import { akEmptyState } from "../EmptyState.js";

describe("ak-empty-state", () => {
    afterEach(() =>
        browser.execute(() => {
            document.body.querySelector("ak-empty-state")?.remove();

            if ("_$litPart$" in document.body) {
                delete document.body._$litPart$;
            }
        }),
    );

    it("should render the default loader", async () => {
        render(
            html`<ak-empty-state loading
                ><span slot="header">${msg("Loading")}</span>
            </ak-empty-state>`,
        );

        const empty = $("ak-empty-state").$(">>>.pf-c-empty-state__icon");

        await expect(empty).resolves.toExist();

        const header = $("ak-empty-state").$(">>>.pf-c-title");

        await expect(header).resolves.toHaveText("Loading");
    });

    it("should handle standard boolean", async () => {
        render(
            html`<ak-empty-state loading
                ><span slot="header">${msg("Loading")}</span>
            </ak-empty-state>`,
        );

        const empty = $("ak-empty-state").$(">>>.pf-c-empty-state__icon");

        await expect(empty).resolves.toExist();

        const header = $("ak-empty-state").$(">>>.pf-c-title");

        await expect(header).resolves.toHaveText("Loading");
    });

    it("should render a static empty state", async () => {
        render(
            html`<ak-empty-state
                ><span slot="header">${msg("No messages found")}</span>
            </ak-empty-state>`,
        );

        const empty = $("ak-empty-state").$(">>>.pf-c-empty-state__icon");

        await expect(empty).resolves.toExist();
        await expect(empty).resolves.toHaveElementClass("fa-question-circle");

        const header = $("ak-empty-state").$(">>>.pf-c-title");

        await expect(header).resolves.toHaveText("No messages found");
    });

    it("should render a slotted message", async () => {
        render(
            html`<ak-empty-state
                ><span slot="header">${msg("No messages found")}</span>
                <p slot="body">Try again with a different filter</p>
            </ak-empty-state>`,
        );

        const message = $("ak-empty-state").$(">>>.pf-c-empty-state__body").$(">>>p");

        await expect(message).resolves.toHaveText("Try again with a different filter");
    });

    it("should render as a function call", async () => {
        render(akEmptyState({ loading: true }, "Being Thoughtful"));

        const empty = $("ak-empty-state").$(">>>.pf-c-empty-state__icon");

        await expect(empty).resolves.toExist();

        const header = $("ak-empty-state").$(">>>.pf-c-empty-state__body");

        await expect(header).resolves.toHaveText("Being Thoughtful");
    });

    it("should render as a complex function call", async () => {
        render(
            akEmptyState(
                { loading: true },
                html` <span slot="body">Introspecting</span>
                    <span slot="primary">... carefully</span>`,
            ),
        );

        const empty = $("ak-empty-state").$(">>>.pf-c-empty-state__icon");

        await expect(empty).resolves.toExist();

        const header = $("ak-empty-state").$(">>>.pf-c-empty-state__body");

        await expect(header).resolves.toHaveText("Introspecting");

        const primary = $("ak-empty-state").$(">>>.pf-c-empty-state__primary");

        await expect(primary).resolves.toHaveText("... carefully");
    });
});
