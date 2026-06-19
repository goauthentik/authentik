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
 * @import {
 *    ChildLoggerOptions,
 *    LoggerOptions,
 *    Logger as PinoLogger,
 *    BaseLogger as PinoBaseLogger,
 *    Level as PinoLevel,
 *    LogFn as PinoLogFn
 *  } from "pino"
 */

/* eslint-disable no-console */

/**
 * @typedef {PinoLogger} Logger
 */

/**
 * @typedef {PinoLevel} Level
 */

/**
 * @typedef {PinoLogFn} LogFn
 */

/**
 * @typedef {Pick<PinoBaseLogger, Exclude<Level, "fatal">>} BaseLogger
 */

//#region Constants

/**
 * Labels log levels in the browser console.
 * @satisfies {Record<Level, string>}
 */
export const LogLevelLabel = /** @type {const} */ ({
    info: "[INFO]",
    warn: "[WARN]",
    error: "[ERROR]",
    debug: "[DEBUG]",
    trace: "[TRACE]",
    fatal: "[FATAL]",
});

/**
 * Predefined log levels.
 */
export const LogLevels = /** @type {Level[]} */ (Object.keys(LogLevelLabel));

/**
 * @callback LoggerFactory
 * @param {string | null} [prefix]
 * @param {...string[]} args
 * @returns {Logger}
 */

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

//#region Functions

/**
 * Creates a logger with the given prefix.
 *
 * @type {LoggerFactory}
 */
function createConsoleLogger(prefix, ...args) {
    const msgPrefix = prefix ? `(${prefix}):` : ":";

    /**
     * @type {Partial<Logger>}
     */
    const logger = {
        msgPrefix,
    };

    for (const level of LogLevels) {
        const label = LogLevelLabel[level];

        // @ts-expect-error Alias the log method to the appropriate console method,
        // defaulting to console.log if the level is not supported.
        const method = level in console ? console[level] : console.log;

        logger[level] = method.bind(console, `${label} ${msgPrefix}`, ...args);
    }

    return /** @type {Logger} */ (logger);
}

/**
 * @typedef {Logger} FixtureLogger
 */

/**
 * @this {Logger}
 * @param {string} fixtureName
 * @param {string} [testName]
 * @param {ChildLoggerOptions} [options]
 * @returns {FixtureLogger}
 */
export function fixture(fixtureName, testName, options) {
    return this.child(
        { name: fixtureName },
        {
            msgPrefix: `[${testName}] `,
            ...options,
        },
    );
}

/**
 * @this {Logger}
 * @param {Record<string, unknown>} bindings
 * @param {ChildLoggerOptions} [_options]
 * @returns {Logger}
 */
export function child(bindings, _options) {
    const prefix = typeof bindings.name === "string" ? bindings.name : null;
    return Object.assign(createConsoleLogger(prefix), { ...bindings });
}

/**
 * @this {{ child: typeof child }}
 * @param {string} label
 * @returns {IConsoleLogger}
 */
export function prefix(label) {
    // @ts-expect-error Create a child logger with the given prefix.
    return this.child({ name: label });
}

/**
 * @typedef {object} CustomLoggerMethods
 * @property {typeof fixture} fixture
 * @property {typeof prefix} prefix
 * @property {typeof child} child
 */

/**
 * @typedef {Record<Level, LogFn>} BaseConsoleLogger
 */

/**
 * @typedef {BaseConsoleLogger & CustomLoggerMethods} IConsoleLogger
 */

/**
 * @type {CustomLoggerMethods}
 */
export const customLoggerMethods = {
    fixture,
    prefix,
    child,
};

/**
 * Creates a lightweight logger that mimics the Pino API but falls back to
 * console methods when Pino is not available.
 * @param {LoggerOptions<never, false>} options
 * @return {IConsoleLogger}
 */
export function pinoLight(options) {
    const baseLogger = createConsoleLogger(options.name);

    /**
     * @type {IConsoleLogger}
     */
    const logger = {
        ...baseLogger,
        fixture,
        prefix,
        child,
    };

    return logger;
}

//#endregion

//#region Functions

/**
 * Creates a logger with the given prefix.
 *
 * @param {string} [prefix]
 * @param {...string[]} args
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
