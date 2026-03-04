/**
 * @file Lightweight logging when Pino is not available
 * @import { ChildLoggerOptions, LoggerOptions, Logger, BaseLogger, LoggerExtras, LogFnFields, Level, LogFn } from "pino"
 * @import { PrettyOptions } from "pino-pretty"
 */

/* eslint-disable no-console */

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

//#region Functions

/**
 * Creates a logger with the given prefix.
 *
 * @param {string | null} [prefix]
 * @param {...string} args
 * @returns {Logger}
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
