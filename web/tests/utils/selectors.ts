import { $, browser } from "@wdio/globals";
import { kebabCase } from "change-case";
import type { ChainablePromiseElement } from "webdriverio";

/**
 * The context in which a selector is being evaluated.
 */
export type SelectorContext = WebdriverIO.Element | WebdriverIO.Browser;

/**
 * A predicate that checks if an element matches a certain condition.
 */
export type ElementMatchPredicate = (element: WebdriverIO.Element) => Promise<boolean>;

export async function applyElementMatchPredicates(
    element: WebdriverIO.Element,
    predicates: ElementMatchPredicate[],
): Promise<boolean> {
    for await (const predicate of predicates) {
        if (!(await predicate(element))) {
            return false;
        }
    }

    return true;
}

/**
 * Check if an element is visible on the page.
 */
export async function checkIfElementVisible(
    elementLike: WebdriverIO.Element | string,
): Promise<boolean> {
    const element: Pick<ChainablePromiseElement, "isExisting" | "isDisplayed"> =
        typeof elementLike === "string" ? $(elementLike) : elementLike;

    const existsInDOM = await element.isExisting();

    if (!existsInDOM) return false;

    const visible = await element.isDisplayed();

    return visible;
}

/**
 * Check if an element contains a specific text.
 */
export async function elementContainsText(
    elementLike: WebdriverIO.Element | ChainablePromiseElement,
    pattern: string | RegExp,
): Promise<boolean> {
    const text = await elementLike.getElement().then((element) => element.getText());

    if (typeof pattern === "string") {
        return text.includes(pattern);
    }

    return pattern.test(text);
}

/**
 * Find the first matching element that satisfies all the given predicates.
 *
 * @throws Error if no element is found.
 */
export async function findElement(
    source: WebdriverIO.Element | ChainablePromiseElement,
    ...predicates: ElementMatchPredicate[]
): Promise<WebdriverIO.Element> {
    const element = await source.getElement();
    const result = await applyElementMatchPredicates(element, predicates);

    if (result) return element;

    throw new Error(`No element found that satisfies the given predicates`);
}

/**
 * Find the first element that contains the given text.
 */
export async function findElementByText(
    selectorResult: WebdriverIO.Element | ChainablePromiseElement,
    pattern: string | RegExp | ElementMatchPredicate,
): Promise<WebdriverIO.Element> {
    const textMatcher: ElementMatchPredicate =
        typeof pattern === "function"
            ? pattern
            : (element) => elementContainsText(element, pattern);

    return findElement(
        selectorResult,
        // ---
        checkIfElementVisible,
        textMatcher,
    ).catch(async (cause) => {
        const selector = await selectorResult.selector;

        let message: string;
        if (typeof pattern === "string") {
            message = `Unable find text '${pattern}' within element ${selector}`;
        } else {
            message = `Unable to find text via predicate within element ${selector}`;
        }

        const error = new Error(message);
        error.cause = cause;

        throw error;
    });
}

function createDatasetSelector(propertyName: string, value: string) {
    return `[data-${kebabCase(propertyName)}="${value}"]`;
}

/**
 * Find an element by its dataset attribute.
 */
export function findElementByDataset(
    propertyName: string,
    value: string,
    context: SelectorContext | ChainablePromiseElement = browser,
) {
    return context.$(createDatasetSelector(propertyName, value));
}

/**
 * Find elements by its dataset attribute.
 */
export function findElementsByDataset(
    propertyName: string,
    value: string,
    context: SelectorContext | ChainablePromiseElement = browser,
) {
    return context.$$(createDatasetSelector(propertyName, value));
}

/**
 *Find an element by its test ID attribute.
 */
export const findElementByTestID = findElementByDataset.bind(null, "test-id");

/**
 *Find elements by their test ID attribute.
 */
export const findElementsByTestID = findElementsByDataset.bind(null, "test-id");

/**
 *Find an OUID component by its name.
 */
export function findOUIDComponent(
    componentName: string,
    context: SelectorContext | ChainablePromiseElement = browser,
) {
    const selector = `[data-ouid-component-name="${componentName}"]`;

    return context.$(selector);
}
