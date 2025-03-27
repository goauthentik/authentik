import { browser } from "@wdio/globals";
import { match } from "ts-pattern";
import type { ChainablePromiseElement } from "webdriverio";
import { Key } from "webdriverio";

import { waitForExist } from "./elements.js";
import { SelectorContext, elementContainsText, findElementByText } from "./selectors.js";

/**
 * Blur an element.
 */
export async function doBlur(elementLike: WebdriverIO.Element | ChainablePromiseElement) {
    const element = await elementLike.getElement();

    browser.execute(
        ($element: HTMLElement) => {
            $element.blur();
        },
        element as unknown as HTMLElement,
    );
}

/**
 * Assert that an element is visible on the page.
 *
 * @param selector The element selector to check for visibility.
 */
export async function assertVisible(selector: string) {
    await expect($(selector)).toBeDisplayed();
}

/**
 * Scroll an element into view and click it, blurring it afterwards.
 */
export async function clickElement(
    elementLike: WebdriverIO.Element | ChainablePromiseElement,
): Promise<void> {
    const element = await elementLike.getElement();

    await element.scrollIntoView();
    await element.click();
    await doBlur(element);
}

/**
 * Click a button matching the given text.
 *
 * @param textMatcher The text to match against the button.
 * @param context The context in which to search for the button.
 */
export async function clickButton(
    textMatcher: string | RegExp,
    context: SelectorContext = browser,
): Promise<void> {
    const matchedButton = await findElementByText(context.$$("button"), textMatcher);

    await clickElement(matchedButton);
}

/**
 * Click a button in a toggle group.
 *
 * @param componentName The OUID component name of the toggle group.
 * @param pattern The text to match against the button.
 */
export async function clickToggleGroup(
    componentName: string,
    pattern: string | RegExp,
): Promise<void> {
    const buttonGroups = $(`>>>[data-ouid-component-name=${componentName}]`).$$(
        ">>>.pf-c-toggle-group__button",
    );

    let matchedButton: WebdriverIO.Element | null = null;

    for await (const buttonGroup of buttonGroups) {
        const button = await findElementByText(
            buttonGroup.$(">>>.pf-c-toggle-group__text"),
            pattern,
        ).catch(() => null);

        if (button) {
            matchedButton = button;
            break;
        }
    }

    if (!matchedButton) {
        throw new Error(`Unable to locate toggle button ${componentName}:${pattern.toString()}`);
    }

    await clickElement(matchedButton);
}

/**
 * Set the expanded state of a form group.
 *
 * @param name The name of the form group.
 * @param nextExpandedValue The desired expanded state.
 */
export async function setFormGroup(
    name: string | RegExp,
    nextExpandedValue: "open" | "closed",
): Promise<void> {
    // Delightfully, wizards may have slotted elements that *exist* but are not *attached*,
    // and this can break the damn tests.
    const formGroup = await findElementByText(browser.$$(">>>ak-form-group"), (group) => {
        return elementContainsText(
            group.$(">>>div.pf-c-form__field-group-header-title-text"),
            name,
        );
    }).catch(() => null);

    if (!(formGroup && (await formGroup.isDisplayed()))) {
        throw new Error(`Unable to find ak-form-group[name="${name}"]`);
    }

    await formGroup.scrollIntoView();

    const toggleElement = formGroup.$(">>>div.pf-c-form__field-group-toggle-button button");

    await match([await toggleElement.getAttribute("aria-expanded"), nextExpandedValue])
        .with(["false", "open"], async () => await toggleElement.click())
        .with(["true", "closed"], async () => await toggleElement.click())
        .otherwise(async () => null);

    await doBlur(formGroup);
}

/**
 * Set a radio button.
 *
 * @param name The name of the radio element.
 * @param pattern The text to match against the radio label.
 */
export async function setRadio(name: string, pattern: string | RegExp): Promise<void> {
    const control = $(`>>>ak-radio[name="${name}"]`);
    await control.scrollIntoView();

    const item = await findElementByText(control.$$(">>>div.pf-c-radio"), (element) => {
        return elementContainsText(element.$(">>>.pf-c-radio__label"), pattern);
    }).catch(() => null);

    if (!item) {
        throw new Error(`Unable to find a radio that matches ${name}:${pattern}`);
    }

    await clickElement(item);
}

/**
 * Set the value of a search select input.
 *
 * @param name The name of the search select element.
 * @param pattern The text to match against the search select entry.
 */
export async function setSearchSelect(name: string, pattern: string | RegExp): Promise<void> {
    const control = await waitForExist($(`>>>ak-search-select[name="${name}"]`))
        .catch(() => waitForExist($(`>>>ak-search-selects-ez[name="${name}"]`)))
        .catch(() => null);

    if (!control) {
        throw new Error(`Unable to find an ak-search-select variant matching ${name}}`);
    }

    // Find the search select input control and activate it.
    const view = control.$(">>>ak-search-select-view");
    const input = view.$('>>>input[type="text"]');
    await input.scrollIntoView();
    await input.click();

    const button = await findElementByText(
        $(`>>>div[data-managed-for*="${name}"]`).$$("button"),
        pattern,
    );

    if (!button) {
        throw new Error(
            `Unable to find an ak-search-select entry matching ${name}:${pattern.toString()}`,
        );
    }

    await button.click();
    await browser.keys(Key.Tab);
    await doBlur(control);
}

/**
 * Set the value of a text input.
 *
 * @param name The name of the input element.
 * @param nextValue The value to set the input to.
 */
export async function setTextInput(name: string, nextValue: string): Promise<void> {
    const control = $(`>>>input[name="${name}"]`);

    await control.scrollIntoView();
    await control.setValue(nextValue);
    await doBlur(control);
}

/**
 * Set the value of a textarea input.
 * @param name The name of the input element.
 * @param nextValue The value to set the input to.
 */
export async function setTextareaInput(name: string, nextValue: string): Promise<void> {
    const control = $(`>>>textarea[name="${name}"]`);
    await control.scrollIntoView();
    await control.setValue(nextValue);
    await doBlur(control);
}

/**
 * Set the value of a toggle input.
 *
 * @param name The name of the input element.
 * @param nextValue The value to set the input to.
 */
export async function setToggle(name: string, nextValue: boolean): Promise<void> {
    const toggle = $(`>>>input[name="${name}"]`);
    await toggle.scrollIntoView();

    await expect(await toggle.getAttribute("type")).toBe("checkbox");

    const currentValue = await toggle.isSelected();

    if (nextValue !== currentValue) {
        const control = toggle.parentElement().$(">>>.pf-c-switch__toggle");
        await clickElement(control);
    }
}

/**
 * Set the value of the wizard page.
 *
 * @param name The name of the wizard page.
 * @param pattern The text to match against.
 */
export async function setTypeCreate(name: string, pattern: string | RegExp) {
    const control = $(`>>>ak-wizard-page-type-create[name="${name}"]`);
    await control.scrollIntoView();

    const card = await findElementByText(
        $(">>>ak-wizard-page-type-create").$$(
            '>>>[data-ouid-component-type="ak-type-create-grid-card"]',
        ),
        (element) => {
            return elementContainsText(element.$(">>>.pf-c-card__title"), pattern);
        },
    ).catch(() => null);

    if (!card) {
        throw new Error(`Unable to locate radio card ${name}:${pattern}`);
    }

    await card.scrollIntoView();
    await card.click();
    await doBlur(control);
}

/**
 * Infer the interaction type from the function signature.
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type InferInteraction<T extends (...args: any[]) => unknown> = [
    action: T,
    ...parameters: Parameters<T>,
];

export type CheckIsPresentAction = InferInteraction<typeof assertVisible>;
export type ClickButtonAction = InferInteraction<typeof clickButton>;
export type ClickToggleGroupAction = InferInteraction<typeof clickToggleGroup>;
export type SetFormGroupAction = InferInteraction<typeof setFormGroup>;
export type SetRadioAction = InferInteraction<typeof setRadio>;
export type SetSearchSelectAction = InferInteraction<typeof setSearchSelect>;
export type SetTextInputAction = InferInteraction<typeof setTextInput>;
export type SetTextareaInputAction = InferInteraction<typeof setTextareaInput>;
export type SetToggleAction = InferInteraction<typeof setToggle>;
export type SetTypeCreateAction = InferInteraction<typeof setTypeCreate>;

/**
 * A tuple of a function and its arguments.
 */
export type TestAction =
    | CheckIsPresentAction
    | ClickButtonAction
    | ClickToggleGroupAction
    | SetFormGroupAction
    | SetRadioAction
    | SetSearchSelectAction
    | SetTextInputAction
    | SetTextareaInputAction
    | SetToggleAction
    | SetTypeCreateAction;

export type TestSequence = () => TestAction[];

/**
 * Run a series of interactions, awaiting each one in turn.
 */
export async function runTestSequence(sequence: TestAction[]) {
    let i = 0;

    for (const [action, ...args] of sequence) {
        i++;
        console.log(`${i}/${sequence.length} Running ${args.join(", ")}`);

        await (action as (...args: unknown[]) => Promise<void>)(...args);
    }
}
