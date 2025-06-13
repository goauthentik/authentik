import { ConsoleTestRunner } from "#tests/utils/logger";
import { browser } from "@wdio/globals";

const CLICK_TIME_DELAY = 250;

/**
 * Pause the browser for a given amount of time.
 * @deprecated
 */
export function waitFor(delay: number = CLICK_TIME_DELAY): Promise<unknown> {
    ConsoleTestRunner.info(`Waiting for ${delay}ms...`);
    return browser.pause(delay);
}
