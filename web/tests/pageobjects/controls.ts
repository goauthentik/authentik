import { browser } from "@wdio/globals";
import { match } from "ts-pattern";
import { Key } from "webdriverio";

export async function doBlur(el: WebdriverIO.Element | ChainablePromiseElement) {
    const element = await el;
    browser.execute((element) => element.blur());
}

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

    // @ts-expect-error "Types break on shadow$$"
    const button = await (async () => {
        for await (const button of $(`div[data-managed-for*="${name}"]`)
            .$("ak-list-select")
            .$$("button")) {
            if ((await button.getText()).includes(value)) {
                return button;
            }
        }
    })();

    // @ts-expect-error "TSC cannot tell if the `for` loop actually performs the assignment."
    if (!button.isExisting()) {
        throw new Error(`Expected to find an entry matching the spec ${value}`);
    }
    await (await button).click();
    await browser.keys(Key.Tab);
    await doBlur(control);
}

export async function setTextInput(name: string, value: string) {
    const control = await $(`input[name="${name}"]`);
    await control.scrollIntoView();
    await control.setValue(value);
    await doBlur(control);
}

export async function setRadio(name: string, value: string) {
    const control = await $(`ak-radio[name="${name}"]`);
    await control.scrollIntoView();
    const item = await control.$(`label.*=${value}`).parentElement();
    await item.scrollIntoView();
    await item.click();
    await doBlur(control);
}

export async function setTypeCreate(name: string, value: string | RegExp) {
    const control = await $(`ak-wizard-page-type-create[name="${name}"]`);
    await control.scrollIntoView();

    const comparator =
        typeof value === "string" ? (sample) => sample === value : (sample) => value.test(sample);

    const card = await (async () => {
        for await (const card of $("ak-wizard-page-type-create").$$(
            '[data-ouid-component-type="ak-type-create-grid-card"]',
        )) {
            if (comparator(await card.$(".pf-c-card__title").getText())) {
                return card;
            }
        }
    })();

    await card.scrollIntoView();
    await card.click();
    await doBlur(control);
}

export async function setFormGroup(name: string | RegExp, setting: "open" | "closed") {
    const comparator =
        typeof name === "string" ? (sample) => sample === name : (sample) => name.test(sample);

    const formGroup = await (async () => {
        for await (const group of $$("ak-form-group")) {
            if (
                comparator(await group.$("div.pf-c-form__field-group-header-title-text").getText())
            ) {
                return group;
            }
        }
    })();

    await formGroup.scrollIntoView();
    const toggle = await formGroup.$("div.pf-c-form__field-group-toggle-button button");
    await match([await toggle.getAttribute("aria-expanded"), setting])
        .with(["false", "open"], async () => await toggle.click())
        .with(["true", "closed"], async () => await toggle.click())
        .otherwise(async () => {});
    await doBlur(formGroup);
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
    await doBlur(button);
}

const tap = <T>(a: T): T => {
    console.log(a);
    return a;
};

export async function clickToggleGroup(name: string, value: string | RegExp) {
    const comparator =
        typeof name === "string"
            ? (sample) => tap(sample) === tap(value)
            : (sample) => value.test(sample);

    const button = await (async () => {
        for await (const button of $(`[data-ouid-component-name=${name}]`).$$(
            ".pf-c-toggle-group__button",
        )) {
            if (comparator(await button.$(".pf-c-toggle-group__text").getText())) {
                return button;
            }
        }
    })();
    await button.scrollIntoView();
    await button.click();
    await doBlur(button);
}
