import { browser } from "@wdio/globals";
import { match } from "ts-pattern";
import { ChainablePromiseArray, Key } from "webdriverio";

browser.addCommand('findByText', async function(items: ChainablePromiseArray, text: string) {
    let item: WebdriverIO.Element | undefined = undefined;
    for (const i of items) {
        const label = await i.getText();
        if (label.indexOf(text) !== -1) {
            item = i;
            break;
        }
    }
    return item;
}, true);

export async function setSearchSelect(name: string, value: string) {
    const control = await (async () => {
        try {
            const control = await $(`ak-search-select[name="${name}"]`);
            await control.waitForExist({ timeout: 500 });
            return control;
            // eslint-disable-next-line @typescript-eslint/no-explicit-any, @typescript-eslint/no-unused-vars
        } catch (_e: any) {
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
        await $(`div[data-managed-for*="${name}"]`).$("ak-list-select")
    ).shadow$$("button");

    // @ts-expect-error "Types break on shadow$$"
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

export async function setTextInput(name: string, value: string) {
    const control = await $(`input[name="${name}"]`);
    await control.scrollIntoView();
    await control.setValue(value);
}

export async function setRadio(name: string, value: string) {
    const control = await $(`ak-radio[name="${name}"]`);
    await control.scrollIntoView();
    const item = await control.$(`label.*=${value}`).parentElement();
    await item.scrollIntoView();
    await item.click();
}

export async function setTypeCreate(name: string, value: string) {
    const control = await $(`ak-wizard-page-type-create[name="${name}"]`);
    await control.scrollIntoView();
    const cards = ;
    const selection = await findByText(await control.$$("div.pf-c-card__title"), value);
    await selection.scrollIntoView();
    await selection.click();
}

export async function setFormGroup(name: string, setting: "open" | "closed") {
    const formGroup = await $(`.//span[contains(., "${name}")]`);
    await formGroup.scrollIntoView();
    const toggle = await formGroup.$("div.pf-c-form__field-group-toggle-button button");
    await match([toggle.getAttribute("expanded"), setting])
        .with(["false", "open"], async () => await toggle.click())
        .with(["true", "closed"], async () => await toggle.click())
        .otherwise(async () => {});
}

export async function clickButton(name: string, ctx?: WebdriverIO.Element) {
    const context = ctx ?? browser;
    const buttons = await context.$$("button");
    let button: WebdriverIO.Element;
    for (const b of buttons) {
        const label = await b.getText();
        if (label.indexOf(name) !== -1) {
            button = b;
            break;
        }
    }
    await button.scrollIntoView();
    await button.click();
}
