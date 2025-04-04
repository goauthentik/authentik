import { render } from "@goauthentik/elements/tests/utils.js";
import { $, expect } from "@wdio/globals";

import { msg } from "@lit/localize";
import { html } from "lit";

import "../EmptyState.js";
import { akEmptyState } from "../EmptyState.js";

describe("ak-empty-state", () => {
    afterEach(() => {
        return browser.execute(() => {
            document.body.querySelector("ak-empty-state")?.remove();

            if ("_$litPart$" in document.body) {
                delete document.body._$litPart$;
            }
        });
    });

    it("should render the default loader", async () => {
        render(html`<ak-empty-state ?loading=${true} header=${msg("Loading")}> </ak-empty-state>`);

        const empty = $("ak-empty-state").$(">>>.pf-c-empty-state__icon");
        await expect(empty).toExist();

        const header = $("ak-empty-state").$(">>>.pf-c-title");
        await expect(header).toHaveText("Loading");
    });

    it("should handle standard boolean", async () => {
        render(html`<ak-empty-state loading header=${msg("Loading")}> </ak-empty-state>`);

        const empty = $("ak-empty-state").$(">>>.pf-c-empty-state__icon");
        await expect(empty).toExist();

        const header = $("ak-empty-state").$(">>>.pf-c-title");
        await expect(header).toHaveText("Loading");
    });

    it("should render a static empty state", async () => {
        render(html`<ak-empty-state header=${msg("No messages found")}> </ak-empty-state>`);

        const empty = $("ak-empty-state").$(">>>.pf-c-empty-state__icon");
        await expect(empty).toExist();
        await expect(empty).toHaveClass("fa-question-circle");

        const header = $("ak-empty-state").$(">>>.pf-c-title");
        await expect(header).toHaveText("No messages found");
    });

    it("should render a slotted message", async () => {
        render(
            html`<ak-empty-state header=${msg("No messages found")}>
                <p slot="body">Try again with a different filter</p>
            </ak-empty-state>`,
        );

        const message = $("ak-empty-state").$(">>>.pf-c-empty-state__body").$(">>>p");
        await expect(message).toHaveText("Try again with a different filter");
    });

    it("should render as a function call", async () => {
        render(akEmptyState({ loading: true }, "Being Thoughtful"));

        const empty = $("ak-empty-state").$(">>>.pf-c-empty-state__icon");
        await expect(empty).toExist();

        const header = $("ak-empty-state").$(">>>.pf-c-empty-state__body");
        await expect(header).toHaveText("Being Thoughtful");
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
        await expect(empty).toExist();

        const header = $("ak-empty-state").$(">>>.pf-c-empty-state__body");
        await expect(header).toHaveText("Introspecting");

        const primary = $("ak-empty-state").$(">>>.pf-c-empty-state__primary");
        await expect(primary).toHaveText("... carefully");
    });
});
