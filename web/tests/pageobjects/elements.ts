import { type ChainablePromiseElement, WaitForOptions } from "webdriverio";

/**
 * Wait for an element to exist on the page.
 *
 * @throws Error if the element does not appear within the timeout.
 */
export async function waitForExist(
    elementLike: ChainablePromiseElement,
    { timeout = 500, ...options }: WaitForOptions = {},
) {
    const found = await elementLike.waitForExist({ timeout, ...options });

    if (!found) {
        throw new Error(`Element ${await elementLike.selector} did not appear within the timeout`);
    }

    return elementLike.getElement();
}
