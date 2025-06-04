import { render } from "@goauthentik/elements/tests/utils.js";
import { $, browser, expect } from "@wdio/globals";

import { html } from "lit";

import { QuickAction } from "../QuickActionsCard.js";
import "../QuickActionsCard.js";

const ACTIONS: QuickAction[] = [
    ["Create a new application", "/core/applications"],
    ["Check the logs", "/events/log"],
    ["Explore integrations", "https://goauthentik.io/integrations/", true],
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

        const component = $("ak-quick-actions-card");
        const items = component.$$(">>>.pf-c-list li");

        await expect(items.length).resolves.toEqual(5);
        await expect(component.$(">>>.pf-c-list li:nth-of-type(4)")).resolves.toHaveText(
            "Manage users",
        );
    });
});
