import {
    clickButton,
    clickToggleGroup,
    setRadio,
    setSearchSelect,
    setTextInput,
    setTextareaInput,
    setToggle,
    setTypeCreate,
} from "#tests/utils/controls";

// export async function doBlur(el: WebdriverIO.Element | ChainablePromiseElement) {
//     const element = await el;
//     browser.execute((element) => element.blur(), element);
// }

// const makeComparator = (value: string | RegExp) =>
//     typeof value === "string"
//         ? (sample: string) => sample === value
//         : (sample: string) => value.test(sample);

// export async function checkIsPresent(name: string) {
//     await expect(await $(name)).toBeDisplayed();
// }

// export async function clickButton(name: string, ctx?: WebdriverIO.Element) {
//     const context = ctx ?? browser;
//     const button = await (async () => {
//         for await (const button of context.$$("button")) {
//             if ((await button.isDisplayed()) && (await button.getText()).indexOf(name) !== -1) {
//                 return button;
//             }
//         }
//     })();

//     if (!(button && (await button.isDisplayed()))) {
//         throw new Error(`Unable to find button '${name}'`);
//     }

//     await button.scrollIntoView();
//     await button.click();
//     await doBlur(button);
// }

// export async function clickToggleGroup(name: string, value: string | RegExp) {
//     const comparator = makeComparator(value);
//     const button = await (async () => {
//         for await (const button of $(`>>>[data-ouid-component-name=${name}]`).$$(
//             ">>>.pf-c-toggle-group__button",
//         )) {
//             if (comparator(await button.$(">>>.pf-c-toggle-group__text").getText())) {
//                 return button;
//             }
//         }
//     })();

//     if (!(button && (await button?.isDisplayed()))) {
//         throw new Error(`Unable to locate toggle button ${name}:${value.toString()}`);
//     }

//     await button.scrollIntoView();
//     await button.click();
//     await doBlur(button);
// }

// export async function setFormGroup(name: string | RegExp, setting: "open" | "closed") {
//     const comparator = makeComparator(name);
//     const formGroup = await (async () => {
//         for await (const group of browser.$$(">>>ak-form-group")) {
//             // Delightfully, wizards may have slotted elements that *exist* but are not *attached*,
//             // and this can break the damn tests.
//             if (!(await group.isDisplayed())) {
//                 continue;
//             }
//             if (
//                 comparator(
//                     await group.$(">>>div.pf-c-form__field-group-header-title-text").getText(),
//                 )
//             ) {
//                 return group;
//             }
//         }
//     })();

//     if (!(formGroup && (await formGroup.isDisplayed()))) {
//         throw new Error(`Unable to find ak-form-group[name="${name}"]`);
//     }

//     await formGroup.scrollIntoView();
//     const toggle = await formGroup.$(">>>div.pf-c-form__field-group-toggle-button button");
//     await match([await toggle.getAttribute("aria-expanded"), setting])
//         .with(["false", "open"], async () => await toggle.click())
//         .with(["true", "closed"], async () => await toggle.click())
//         .otherwise(async () => {});
//     await doBlur(formGroup);
// }

// export async function setRadio(name: string, value: string | RegExp) {
//     const control = await $(`>>>ak-radio[name="${name}"]`);
//     await control.scrollIntoView();

//     const comparator = makeComparator(value);
//     const item = await (async () => {
//         for await (const item of control.$$(">>>div.pf-c-radio")) {
//             if (comparator(await item.$(">>>.pf-c-radio__label").getText())) {
//                 return item;
//             }
//         }
//     })();

//     if (!(item && (await item.isDisplayed()))) {
//         throw new Error(`Unable to find a radio that matches ${name}:${value.toString()}`);
//     }

//     await item.scrollIntoView();
//     await item.click();
//     await doBlur(control);
// }

// export async function setSearchSelect(name: string, value: string | RegExp) {
//     const control = await (async () => {
//         try {
//             const control = await $(`>>>ak-search-select[name="${name}"]`);
//             await control.waitForExist({ timeout: 500 });
//             return control;
//         } catch (_e: unknown) {
//             const control = await $(`>>>ak-search-selects-ez[name="${name}"]`);
//             return control;
//         }
//     })();

//     if (!(control && (await control.isExisting()))) {
//         throw new Error(`Unable to find an ak-search-select variant matching ${name}}`);
//     }

//     // Find the search select input control and activate it.
//     const view = await control.$(">>>ak-search-select-view");
//     const input = await view.$('>>>input[type="text"]');
//     await input.scrollIntoView();
//     await input.click();

//     const comparator = makeComparator(value);
//     const button = await (async () => {
//         for await (const button of $(`>>>div[data-managed-for*="${name}"]`)
//             .$(">>>ak-list-select")
//             .$$("button")) {
//             if (comparator(await button.getText())) {
//                 return button;
//             }
//         }
//     })();

//     if (!(button && (await button.isDisplayed()))) {
//         throw new Error(
//             `Unable to find an ak-search-select entry matching ${name}:${value.toString()}`,
//         );
//     }

//     await (await button).click();
//     await browser.keys(Key.Tab);
//     await doBlur(control);
// }

// export async function setTextInput(name: string, value: string) {
//     const control = await $(`>>>input[name="${name}"]`);
//     await control.scrollIntoView();
//     await control.setValue(value);
//     await doBlur(control);
// }

// export async function setTextareaInput(name: string, value: string) {
//     const control = await $(`>>>textarea[name="${name}"]`);
//     await control.scrollIntoView();
//     await control.setValue(value);
//     await doBlur(control);
// }

// export async function setToggle(name: string, set: boolean) {
//     const toggle = await $(`>>>input[name="${name}"]`);
//     await toggle.scrollIntoView();
//     await expect(await toggle.getAttribute("type")).toBe("checkbox");
//     const state = await toggle.isSelected();
//     if (set !== state) {
//         const control = await (await toggle.parentElement()).$(">>>.pf-c-switch__toggle");
//         await control.click();
//         await doBlur(control);
//     }
// }

// export async function setTypeCreate(name: string, value: string | RegExp) {
//     const control = await $(`>>>ak-wizard-page-type-create[name="${name}"]`);
//     await control.scrollIntoView();

//     const comparator = makeComparator(value);
//     const card = await (async () => {
//         for await (const card of $(">>>ak-wizard-page-type-create").$$(
//             '>>>[data-ouid-component-type="ak-type-create-grid-card"]',
//         )) {
//             if (comparator(await card.$(">>>.pf-c-card__title").getText())) {
//                 return card;
//             }
//         }
//     })();

//     if (!(card && (await card.isDisplayed()))) {
//         throw new Error(`Unable to locate radio card ${name}:${value.toString()}`);
//     }

//     await card.scrollIntoView();
//     await card.click();
//     await doBlur(control);
// }

export type TestInteraction =
    | [typeof clickButton, ...Parameters<typeof clickButton>]
    | [typeof clickToggleGroup, ...Parameters<typeof clickToggleGroup>]
    | [typeof setRadio, ...Parameters<typeof setRadio>]
    | [typeof setSearchSelect, ...Parameters<typeof setSearchSelect>]
    | [typeof setTextInput, ...Parameters<typeof setTextInput>]
    | [typeof setTextareaInput, ...Parameters<typeof setTextareaInput>]
    | [typeof setToggle, ...Parameters<typeof setToggle>]
    | [typeof setTypeCreate, ...Parameters<typeof setTypeCreate>];

export type TestSequence = TestInteraction[];

export type TestProvider = () => TestSequence;
