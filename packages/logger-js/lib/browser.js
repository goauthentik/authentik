/**
 * @file Console logger for browser environments.
 *
 * @remarks
 * The repetition of log levels, typedefs, and method signatures is intentional
 * to give IDEs and type checkers a mapping of log methods to the TypeScript
 * provided JSDoc comments.
 *
 * Additionally, no wrapper functions are used to avoid the browser's console
 * reported call site being the wrapper instead of the actual caller.
 *
 * @import { IConsoleLogger } from "./shared.js"
 * @import { Logger } from "pino"
 */

import { LogLevelLabel, LogLevels } from "./shared.js";

/* eslint-disable no-console */

//#region Constants

/**
 * Colors for log levels in the browser console.
 *
 * @remarks
 *
 * The colors are derived from Carbon Design System's palette to ensure
 * sufficient contrast and accessibility across light and dark themes.
 */
const LogLevelColors = /** @type {const} */ ({
    info: `light-dark(#0043CE, #4589FF)`,
    warn: `light-dark(#F1C21B, #F1C21B)`,
    error: `light-dark(#DA1E28, #FA4D56)`,
    debug: `light-dark(#8A3FFC, #A56EFF)`,
    trace: `light-dark(#8A3FFC, #A56EFF)`,
    fatal: `light-dark(#DA1E28, #FA4D56)`,
});

//#endregion

//#region Functions

/**
 * Creates a logger with the given prefix.
 *
 * @param {string} [prefix]
 * @param {...string} args
 * @returns {Logger}
 *
 */
export function createLogger(prefix, ...args) {
    const msgPrefix = prefix ? `(${prefix}):` : ":";

    /**
     * @type {Partial<Logger>}
     */
    const logger = {
        msgPrefix,
    };

    for (const level of LogLevels) {
        const label = LogLevelLabel[level];
        const color = LogLevelColors[level];

        // @ts-expect-error Alias the log method to the appropriate console method,
        // defaulting to console.log if the level is not supported.
        const method = level in console ? console[level] : console.log;

        logger[level] = method.bind(
            console,
            `%c${label}%c ${msgPrefix}%c`,
            `font-weight: 700; color: ${color};`,
            `font-weight: 600; color: CanvasText;`,
            "",
            ...args,
        );
    }

    return /** @type {Logger} */ (logger);
}

//#endregion

//#region Console Logger

/**
 * A singleton logger instance for the browser.
 *
 * ```js
 * import { ConsoleLogger } from "#logger/browser";
 *
 * ConsoleLogger.info("Hello, world!");
 * ```
 *
 * @implements {IConsoleLogger}
 * @runtime browser
 */
// @ts-expect-error Logging properties are dynamically assigned.
export class ConsoleLogger {
    /** @type {typeof console.info} */
    static info;
    /** @type {typeof console.warn} */
    static warn;
    /** @type {typeof console.error} */
    static error;
    /** @type {typeof console.debug} */
    static debug;
    /** @type {typeof console.trace} */
    static trace;

    /**
     * Creates a logger with the given prefix.
     * @param {string} logPrefix
     */
    static prefix(logPrefix) {
        return createLogger(logPrefix);
    }
}

Object.assign(ConsoleLogger, createLogger());

//#endregion
