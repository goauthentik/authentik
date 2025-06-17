/**
 * @file WDIO logger utilities for Node.js.
 *
 * @import { Logger } from "loglevel";
 */
import LogLevel from "loglevel";

/**
 * The default logger for the test runner.
 *
 * @type {Logger}
 */
export const ConsoleTestRunner = LogLevel.getLogger(`\x1b[1m@goauthentik/web\x1b[0m`);
ConsoleTestRunner.setDefaultLevel("info");
