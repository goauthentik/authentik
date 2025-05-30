/**
 * @file WDIO logger utilities for Node.js.
 *
 * @import { Logger } from "@wdio/logger";
 */
import getLogger from "@wdio/logger";

/**
 * The default logger for the test runner.
 *
 * @type {Logger}
 */
export const ConsoleTestRunner = getLogger(`\x1b[1m@goauthentik/web\x1b[0m`);
