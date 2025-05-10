/// <reference types="@wdio/globals/types" />
import { type ChainablePromiseElement, Key, Selector } from "webdriverio";

import { SelectorContext, elementContainsText, findElementByText } from "./selectors.js";

/**
 * Assert that an element is visible on the page.
 *
 * @param selector The element selector to check for visibility.
 */
export async function assertVisible(selector: string) {
    await expect($(selector)).resolves.toBeDisplayed();
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
    await element.blur();
}

/**
 * Click a button matching the given text.
 *
 * @param textMatcher The text to match against the button.
 * @param context The context in which to search for the button.
 */
export async function clickButton(
    textMatcher: string | RegExp,
    selectorLike: string | SelectorContext = browser,
): Promise<void> {
    console.debug(`clickButton: Looking for "${textMatcher}"`);

    console.time(`clickButton: ${textMatcher}`);

    const context = typeof selectorLike === "string" ? $(selectorLike) : selectorLike;

    const matchedButton = await context.$$("button").find<WebdriverIO.Element>((element) => {
        return elementContainsText(element, textMatcher);
    });

    if (!matchedButton) {
        throw new Error(`Unable to locate button ${textMatcher}`);
    }
    console.timeEnd(`clickButton: ${textMatcher}`);

    console.debug(`clickButton: Found ${await matchedButton.getText()}`);

    console.time(`clickButton: ${textMatcher}: Waiting for enabled`);
    await matchedButton.waitForEnabled({ timeout: 1_000 });
    console.timeEnd(`clickButton: ${textMatcher}: Waiting for enabled`);

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
        );

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
 * @param nextExpandedAttribute The desired expanded state.
 */
export async function toggleFormGroup(
    name: string | RegExp,
    nextExpandedAttribute: boolean,
): Promise<void> {
    // Delightfully, wizards may have slotted elements that *exist* but are not *attached*,
    // and this can break the damn tests.
    const formGroup = await $$(">>>ak-form-group")
        .find<WebdriverIO.Element>((group) =>
            elementContainsText(group.$(">>>div.pf-c-form__field-group-header-title-text"), name),
        )
        .catch(() => null);

    if (!formGroup) {
        throw new Error(`Unable to find ak-form-group[name="${name}"]`);
    }
    const displayed = await formGroup.isDisplayed();

    if (!displayed) {
        throw new Error(`Unable to find ak-form-group[name="${name}"]`);
    }

    await formGroup.scrollIntoView();

    const toggleElement = formGroup.$(">>>div.pf-c-form__field-group-toggle-button button");

    await toggleElement.getProperty("expanded").then((currentExpanded) => {
        if (!!currentExpanded !== nextExpandedAttribute) {
            return toggleElement.click();
        }
    });

    await formGroup.blur();
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

    const item = await control.$$(">>>div.pf-c-radio").find<WebdriverIO.Element>((element) => {
        return elementContainsText(element.$(">>>.pf-c-radio__label"), pattern);
    });

    if (!item) {
        throw new Error(`Unable to find a radio that matches ${name}:${pattern}`);
    }

    await clickElement(item);
}

/**
 * Target a specific entry in {@linkcode SearchSelect}
 *
 * Requires that the `SearchSelect` have the `name` attribute set,
 * so that the managed selector can find the *right* SearchSelect if there are
 * multiple open SearchSelects on the board.
 *
 * - See `./ldap-form.view:LdapForm.setBindFlow` for an example,
 * - See `./oauth-form.view:OauthForm:setAuthorizationFlow` for a further example of
 * why it would be hard to simplify this further
 * (`flow` vs `tentanted-flow` vs a straight-up SearchSelect each have different a `searchSelector`).
 *
 * @todo Can we remove this in favour of a more generic `searchSelect` function?
 */
export async function searchSelect(
    searchSelector: Selector,
    managerName: string,
    buttonText: string,
) {
    await $(searchSelector).$('>>>input[type="text"]').click();

    const searchBlock = await $(`>>>div[data-managed-for="${managerName}"]`)
        .$(">>>ak-list-select")
        .getElement();

    await clickButton(buttonText, searchBlock);

    await browser.keys(Key.Tab);
}

/**
 * Set the value of a search select input.
 *
 * @param name The name of the search select element.
 * @param pattern The text to match against the search select entry.
 */
export async function setSearchSelect(name: string, pattern: string | RegExp): Promise<void> {
    const control = await $(`ak-search-select[name="${name}"]`)
        .getElement()
        .then((searchSelectElement) => {
            return searchSelectElement
                .waitForExist({ timeout: 500 })
                .then(() => searchSelectElement);
        })
        .catch(() => $(`ak-search-selects-ez[name="${name}"]`).getElement())
        .catch(() => null);

    if (!control) {
        throw new Error(`Unable to find an ak-search-select variant matching ${name}}`);
    }

    // Find the search select input control and activate it.
    const view = control.$(">>>ak-search-select-view");
    const input = view.$('>>>input[type="text"]');
    await input.scrollIntoView();
    await input.click();

    const button = await $(`>>>div[data-managed-for*="${name}"]`)
        .$$("button")
        .find<WebdriverIO.Element>((element) => elementContainsText(element, pattern));

    if (!button) {
        throw new Error(
            `Unable to find an ak-search-select entry matching ${name}:${pattern.toString()}`,
        );
    }

    await button.click();
    await browser.keys(Key.Tab);
    await control.blur();
}

/**
 * Set the value of a text input.
 *
 * @param inputName The name attribute of the input element.
 * @param nextValue The value to set the input to.
 */
export async function setTextInput(inputName: string, nextValue: string): Promise<void> {
    const control = $(`>>>input[name="${inputName}"]`);

    await control.scrollIntoView();
    await control.setValue(nextValue);
    await control.blur();
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
    await control.blur();
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

    await expect(toggle.getAttribute("type")).resolves.toBe("checkbox");

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
    await control.waitForDisplayed();

    const card = await control
        .$$('>>>[data-ouid-component-type="ak-type-create-grid-card"]')
        .find<WebdriverIO.Element>((cardElement) => {
            return elementContainsText(cardElement.$(">>>.pf-c-card__title"), pattern);
        });

    if (!card) {
        throw new Error(`Unable to locate radio card ${name}:${pattern}`);
    }

    await card.scrollIntoView();
    await card.click();

    await control.blur();
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
export type SetFormGroupAction = InferInteraction<typeof toggleFormGroup>;
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

        console.debug(
            `TEST SEQUENCE: (${i}/${sequence.length}) [${action.name}] Running ${args.join(", ")}`,
        );

        await new Promise<void>((resolve, reject) => {
            const timeout = setTimeout(() => {
                reject(new Error(`Timeout waiting for ${action.name} to complete`));
            }, 10_000);

            const result = (action as (...args: unknown[]) => unknown)(...args);

            if (result instanceof Promise) {
                result
                    .then(() => {
                        clearTimeout(timeout);
                        resolve();
                    })
                    .catch(reject);
            } else {
                clearTimeout(timeout);
                resolve();
            }
        });
    }
}
