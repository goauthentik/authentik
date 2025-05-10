/// <reference types="@wdio/globals/types" />

const CLICK_TIME_DELAY = 250;

/**
 * Pause the browser for a given amount of time.
 */
export function waitFor(delay: number = CLICK_TIME_DELAY): Promise<unknown> {
    return browser.pause(delay);
}
