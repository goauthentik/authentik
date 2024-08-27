import { ensureCSSStyleSheet } from "@goauthentik/elements/utils/ensureCSSStyleSheet.js";
import { $, expect } from "@wdio/globals";

import { TemplateResult, html, render as litRender } from "lit";

import AKGlobal from "@goauthentik/common/styles/authentik.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { QuickAction } from "../QuickActionsCard.js";
import "../QuickActionsCard.js";

const render = (body: TemplateResult) => {
    document.adoptedStyleSheets = [
        ...document.adoptedStyleSheets,
        ensureCSSStyleSheet(PFBase),
        ensureCSSStyleSheet(AKGlobal),
    ];
    return litRender(body, document.body);
};

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
        const component = await $("ak-quick-actions-card");
        const items = await component.$$(">>>.pf-c-list li");
        await expect(Array.from(items).length).toEqual(5);
        await expect(await component.$(">>>.pf-c-list li:nth-of-type(4)")).toHaveText(
            "Manage users",
        );
    });
});
