import "@goauthentik/admin/admin-settings/AdminSettingsFooterLinks.js";
import { render } from "@goauthentik/elements/tests/utils.js";
import { $, browser, expect } from "@wdio/globals";

import { html } from "lit";

import { FooterLink } from "@goauthentik/api";

import "../ak-array-input.js";

const sampleItems: FooterLink[] = [
    { name: "authentik", href: "https://goauthentik.io" },
    { name: "authentik docs", href: "https://docs.goauthentik.io/docs/" },
];

describe("ak-array-input", () => {
    afterEach(() =>
        browser.execute(() => {
            document.body.querySelector("ak-array-input")?.remove();

            if ("_$litPart$" in document.body) {
                delete document.body._$litPart$;
            }
        }),
    );

    const renderItems = (items: FooterLink[] = []) =>
        render(
            html` <ak-array-input
                id="ak-array-input"
                .items=${items}
                .newItem=${() => ({ name: "", href: "" })}
                .row=${(f?: FooterLink) =>
                    html`<ak-admin-settings-footer-link name="footerLink" .footerLink=${f}>
                    </ak-admin-settings-footer-link>`}
                validate
            ></ak-array-input>`,
        );

    it("should render an empty control", async () => {
        renderItems();

        const link = $("ak-array-input");
        await browser.pause(500);

        await expect(link.getProperty("isValid")).resolves.toStrictEqual(true);
        await expect(link.getProperty("toJson")).resolves.toEqual([]);
    });

    it("should render a populated component", async () => {
        renderItems(sampleItems);
        const link = $("ak-array-input");
        await browser.pause(1500);

        await expect(link.getProperty("isValid")).resolves.toStrictEqual(true);
        await expect(link.getProperty("toJson")).resolves.toEqual(sampleItems);
    });
});
