import "../QuickActionsCard.js";

import { QuickAction } from "../QuickActionsCard.js";

import { render } from "#elements/tests/utils";

import { $, expect } from "@wdio/globals";

import { html } from "lit";

const ACTIONS: QuickAction[] = [
    ["Create a new application", "/core/applications"],
    ["Check the logs", "/events/log"],
    ["Explore integrations", "https://integrations.goauthentik.io/", true],
    ["Manage users", "/identity/users"],
    ["Check the release notes", "https://goauthentik.io/docs/releases/", true],
];

describe("ak-quick-actions-card", () => {
    it("display ak-quick-actions-card", async () => {
        render(
            html`<ak-quick-actions-card
                title="Alt Title"
                .actions=${ACTIONS}
            ></ak-quick-actions-card>`,
        );
        const component = await $("ak-quick-actions-card");
        const items = await component.$$(">>>.pf-c-list li");
        // @ts-expect-error "Another ChainablePromise mistake"
        await expect(Array.from(items).length).toEqual(5);
        await expect(await component.$(">>>.pf-c-list li:nth-of-type(4)")).toHaveText(
            "Manage users",
        );
    });
});
