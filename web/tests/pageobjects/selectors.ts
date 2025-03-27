/// <reference types="@wdio/globals/types" />
import { ChainablePromiseArray, ChainablePromiseElement } from "webdriverio";

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
    elements: ChainablePromiseArray | ChainablePromiseElement,
    ...predicates: ElementMatchPredicate[]
): Promise<WebdriverIO.Element> {
    if (Symbol.asyncIterator in elements) {
        for await (const element of elements) {
            const result = await applyElementMatchPredicates(element, predicates);

            if (result) return element;
        }
    } else {
        const element = await elements.getElement();
        const result = await applyElementMatchPredicates(element, predicates);

        if (result) return element;
    }

    throw new Error(`No element found that satisfies the given predicates`);
}

/**
 * Find the first element that contains the given text.
 */
export async function findElementByText(
    selectorResult: ChainablePromiseArray | ChainablePromiseElement,
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
    ).catch(() => {
        throw new Error(`Unable to find element with text '${pattern}'`);
    });
}
