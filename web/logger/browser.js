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
 */

/* eslint-disable no-console */

//#region Functions

/**
 * @typedef {object} Logger
 * @property {typeof console.info} info;
 * @property {typeof console.warn} warn;
 * @property {typeof console.error} error;
 * @property {typeof console.debug} debug;
 * @property {typeof console.trace} trace;
 */

/**
 * Labels log levels in the browser console.
 */
const LogLevelLabel = /** @type {const} */ ({
    info: "[INFO]",
    warn: "[WARN]",
    error: "[ERROR]",
    debug: "[DEBUG]",
    trace: "[TRACE]",
});

/**
 * @typedef {keyof typeof LogLevelLabel} LogLevel
 */

/**
 * Predefined log levels.
 */
const LogLevels = /** @type {LogLevel[]} */ (Object.keys(LogLevelLabel));

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
});

/**
 * Creates a logger with the given prefix.
 *
 * @param {string} [prefix]
 * @param {...string} args
 * @returns {Logger}
 *
 */
export function createLogger(prefix, ...args) {
    const suffix = prefix ? `(${prefix}):` : ":";

    /**
     * @type {Partial<Logger>}
     */
    const logger = {};

    for (const level of LogLevels) {
        const label = LogLevelLabel[level];
        const color = LogLevelColors[level];

        logger[level] = console[level].bind(
            console,
            `%c${label}%c ${suffix}%c`,
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
 * @typedef {Logger & {prefix: (logPrefix: string) => Logger}} IConsoleLogger
 */

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
