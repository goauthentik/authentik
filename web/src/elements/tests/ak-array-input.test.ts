import "#admin/admin-settings/AdminSettingsFooterLinks";
import "../ak-array-input.js";

import { render } from "#elements/tests/utils";

import { FooterLink } from "@goauthentik/api";

import { $, expect } from "@wdio/globals";

import { html } from "lit";

const sampleItems: FooterLink[] = [
    { name: "authentik", href: "https://goauthentik.io" },
    { name: "authentik docs", href: "https://docs.goauthentik.io/docs/" },
];

describe("ak-array-input", () => {
    afterEach(async () => {
        await browser.execute(async () => {
            await document.body.querySelector("ak-array-input")?.remove();
            if (document.body._$litPart$) {
                // @ts-expect-error expression of type '"_$litPart$"' is added by Lit
                await delete document.body._$litPart$;
            }
        });
    });

    const component = (items: FooterLink[] = []) =>
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
        await component();
        const link = await $("ak-array-input");
        await browser.pause(500);
        await expect(await link.getProperty("isValid")).toStrictEqual(true);
        await expect(await link.getProperty("toJson")).toEqual([]);
    });

    it("should render a populated component", async () => {
        await component(sampleItems);
        const link = await $("ak-array-input");
        await browser.pause(500);
        await expect(await link.getProperty("isValid")).toStrictEqual(true);
        await expect(await link.getProperty("toJson")).toEqual(sampleItems);
    });
});
