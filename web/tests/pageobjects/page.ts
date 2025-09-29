import { browser } from "@wdio/globals";
import { match } from "ts-pattern";
import { Key } from "webdriverio";

const CLICK_TIME_DELAY = 250;

/**
 * Main page object containing all methods, selectors and functionality that is shared across all
 * page objects
 */

export default class Page {
    /**
     * Opens a sub page of the page
     * @param path path of the sub page (e.g. /path/to/page.html)
     */
    public async open(path: string) {
        return await browser.url(`http://localhost:9000/${path}`);
    }

    public async pause(selector?: string) {
        if (selector) {
            return await $(selector).waitForDisplayed();
        }
        return await browser.pause(CLICK_TIME_DELAY);
    }

    /**
     * Target a specific entry in SearchSelect. Requires that the SearchSelect have the `name`
     * attribute set, so that the managed selector can find the *right* SearchSelect if there are
     * multiple open SearchSelects on the board. See `./ldap-form.view:LdapForm.setBindFlow` for an
     * example, and see `./oauth-form.view:OauthForm:setAuthorizationFlow` for a further example of
     * why it would be hard to simplify this further (`flow` vs `tentanted-flow` vs a straight-up
     * SearchSelect each have different a `searchSelector`).
     */
    async searchSelect(searchSelector: string, managedSelector: string, buttonSelector: string) {
        const inputBind = await $(searchSelector);
        const inputMain = await inputBind.$('>>>input[type="text"]');
        await inputMain.click();
        const searchBlock = await (
            await $(`>>>div[data-managed-for="${managedSelector}"]`).$(">>>ak-list-select")
        ).$$("button");
        let target: WebdriverIO.Element;
        for (const button of searchBlock) {
            if ((await button.getText()).includes(buttonSelector)) {
                target = button;
                break;
            }
        }
        // @ts-expect-error "TSC cannot tell if the `for` loop actually performs the assignment."
        if (!target) {
            throw new Error(`Expected to find an entry matching the spec ${buttonSelector}`);
        }
        await (await target).click();
        await browser.keys(Key.Tab);
    }

    async setSearchSelect(name: string, value: string) {
        const control = await (async () => {
            try {
                const control = await $(`ak-search-select[name="${name}"]`);
                await control.waitForExist({ timeout: 500 });
                return control;
            } catch (_e: unknown) {
                const control = await $(`ak-search-selects-ez[name="${name}"]`);
                return control;
            }
        })();

        // Find the search select input control and activate it.
        const view = await control.$("ak-search-select-view");
        const input = await view.$('input[type="text"]');
        await input.scrollIntoView();
        await input.click();

        // Weirdly necessary because it's portals!
        const searchBlock = await (
            await $(`>>>div[data-managed-for="${name}"]`).$(">>>ak-list-select")
        ).$$("button");

        let target: WebdriverIO.Element;
        for (const button of searchBlock) {
            if ((await button.getText()).includes(value)) {
                target = button;
                break;
            }
        }
        // @ts-expect-error "TSC cannot tell if the `for` loop actually performs the assignment."
        if (!target) {
            throw new Error(`Expected to find an entry matching the spec ${value}`);
        }

        await (await target).click();
        await browser.keys(Key.Tab);
    }

    async setTextInput(name: string, value: string) {
        const control = await $(`input[name="${name}"}`);
        await control.scrollIntoView();
        await control.setValue(value);
    }

    async setRadio(name: string, value: string) {
        const control = await $(`ak-radio[name="${name}"]`);
        await control.scrollIntoView();
        const item = await control.$(`label.*=${value}`).parentElement();
        await item.scrollIntoView();
        await item.click();
    }

    async setTypeCreate(name: string, value: string) {
        const control = await $(`ak-wizard-page-type-create[name="${name}"]`);
        await control.scrollIntoView();
        const selection = await $(`.pf-c-card__.*=${value}`);
        await selection.scrollIntoView();
        await selection.click();
    }

    async setFormGroup(name: string, setting: "open" | "closed") {
        const formGroup = await $(`ak-form-group span[slot="header"].*=${name}`).parentElement();
        await formGroup.scrollIntoView();
        const toggle = await formGroup.$("div.pf-c-form__field-group-toggle-button button");
        await match([await toggle.getAttribute("expanded"), setting])
            .with(["false", "open"], async () => await toggle.click())
            .with(["true", "closed"], async () => await toggle.click())
            .otherwise(async () => {});
    }

    public async logout() {
        await browser.url("http://localhost:9000/flows/-/default/invalidation/");
        return await this.pause();
    }
}
