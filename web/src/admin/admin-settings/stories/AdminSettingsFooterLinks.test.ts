import { render } from "@goauthentik/elements/tests/utils.js";
import { $, browser, expect } from "@wdio/globals";

import { html } from "lit";

import "../AdminSettingsFooterLinks.js";

describe("ak-admin-settings-footer-link", () => {
    afterEach(() =>
        browser.execute(() => {
            document.body.querySelector("ak-admin-settings-footer-link")?.remove();

            if ("_$litPart$" in document.body) {
                delete document.body._$litPart$;
            }
        }),
    );

    it("should render an empty control", async () => {
        render(html`<ak-admin-settings-footer-link name="link"></ak-admin-settings-footer-link>`);
        const link = $("ak-admin-settings-footer-link");

        await expect(link.getProperty("isValid")).resolves.toStrictEqual(false);
        await expect(link.getProperty("toJson")).resolves.toEqual({
            name: "",
            href: "",
        });
    });

    it("should not be valid if just a name is filled in", async () => {
        render(html`<ak-admin-settings-footer-link name="link"></ak-admin-settings-footer-link>`);
        const link = $("ak-admin-settings-footer-link");
        await link.$('input[name="name"]').setValue("foo");
        await expect(link.getProperty("isValid")).resolves.toStrictEqual(false);
        await expect(link.getProperty("toJson")).resolves.toEqual({
            name: "foo",
            href: "",
        });
    });

    it("should be valid if just a URL is filled in", async () => {
        render(html`<ak-admin-settings-footer-link name="link"></ak-admin-settings-footer-link>`);
        const link = $("ak-admin-settings-footer-link");
        await link.$('input[name="href"]').setValue("https://foo.com");
        await expect(link.getProperty("isValid")).resolves.toStrictEqual(true);
        await expect(link.getProperty("toJson")).resolves.toEqual({
            name: "",
            href: "https://foo.com",
        });
    });

    it("should be valid if both are filled in", async () => {
        render(html`<ak-admin-settings-footer-link name="link"></ak-admin-settings-footer-link>`);
        const link = $("ak-admin-settings-footer-link");

        await link.$('input[name="name"]').setValue("foo");
        await link.$('input[name="href"]').setValue("https://foo.com");

        await expect(link.getProperty("isValid")).resolves.toStrictEqual(true);
        await expect(link.getProperty("toJson")).resolves.toEqual({
            name: "foo",
            href: "https://foo.com",
        });
    });

    it("should not be valid if the URL is not valid", async () => {
        render(html`<ak-admin-settings-footer-link name="link"></ak-admin-settings-footer-link>`);
        const link = $("ak-admin-settings-footer-link");
        await link.$('input[name="name"]').setValue("foo");
        await link.$('input[name="href"]').setValue("never://foo.com");
        await expect(link.getProperty("toJson")).resolves.toEqual({
            name: "foo",
            href: "never://foo.com",
        });
        await expect(link.getProperty("isValid")).resolves.toStrictEqual(false);
    });
});
