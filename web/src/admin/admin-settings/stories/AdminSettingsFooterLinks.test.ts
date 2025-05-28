import { render } from "@goauthentik/elements/tests/utils.js";
import { $, expect } from "@wdio/globals";

import { html } from "lit";

import "../AdminSettingsFooterLinks.js";

describe("ak-admin-settings-footer-link", () => {
    afterEach(async () => {
        await browser.execute(async () => {
            await document.body.querySelector("ak-admin-settings-footer-link")?.remove();
            if (document.body._$litPart$) {
                // @ts-expect-error expression of type '"_$litPart$"' is added by Lit
                await delete document.body._$litPart$;
            }
        });
    });

    it("should render an empty control", async () => {
        render(html`<ak-admin-settings-footer-link name="link"></ak-admin-settings-footer-link>`);
        const link = await $("ak-admin-settings-footer-link");
        await expect(await link.getProperty("isValid")).toStrictEqual(false);
        await expect(await link.getProperty("toJson")).toEqual({ name: "", href: "" });
    });

    it("should not be valid if just a name is filled in", async () => {
        render(html`<ak-admin-settings-footer-link name="link"></ak-admin-settings-footer-link>`);
        const link = await $("ak-admin-settings-footer-link");
        await link.$('input[name="name"]').setValue("foo");
        await expect(await link.getProperty("isValid")).toStrictEqual(false);
        await expect(await link.getProperty("toJson")).toEqual({ name: "foo", href: "" });
    });

    it("should be valid if just a URL is filled in", async () => {
        render(html`<ak-admin-settings-footer-link name="link"></ak-admin-settings-footer-link>`);
        const link = await $("ak-admin-settings-footer-link");
        await link.$('input[name="href"]').setValue("https://foo.com");
        await expect(await link.getProperty("isValid")).toStrictEqual(true);
        await expect(await link.getProperty("toJson")).toEqual({
            name: "",
            href: "https://foo.com",
        });
    });

    it("should be valid if both are filled in", async () => {
        render(html`<ak-admin-settings-footer-link name="link"></ak-admin-settings-footer-link>`);
        const link = await $("ak-admin-settings-footer-link");
        await link.$('input[name="name"]').setValue("foo");
        await link.$('input[name="href"]').setValue("https://foo.com");
        await expect(await link.getProperty("isValid")).toStrictEqual(true);
        await expect(await link.getProperty("toJson")).toEqual({
            name: "foo",
            href: "https://foo.com",
        });
    });

    it("should not be valid if the URL is not valid", async () => {
        render(html`<ak-admin-settings-footer-link name="link"></ak-admin-settings-footer-link>`);
        const link = await $("ak-admin-settings-footer-link");
        await link.$('input[name="name"]').setValue("foo");
        await link.$('input[name="href"]').setValue("never://foo.com");
        await expect(await link.getProperty("toJson")).toEqual({
            name: "foo",
            href: "never://foo.com",
        });
        await expect(await link.getProperty("isValid")).toStrictEqual(false);
    });
});
