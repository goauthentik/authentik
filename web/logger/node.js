/**
 * Application logger.
 *
 * @import { LoggerOptions, Logger, Level, ChildLoggerOptions } from "pino"
 * @import { PrettyOptions } from "pino-pretty"
 */

import { pino } from "pino";

//#region Constants

/**
 * Default options for creating a Pino logger.
 *
 * @category Logger
 * @satisfies {LoggerOptions<never, false>}
 */
export const DEFAULT_PINO_LOGGER_OPTIONS = {
    enabled: true,
    level: "info",
    transport: {
        target: "./transport.js",
        options: /** @satisfies {PrettyOptions} */ ({
            colorize: true,
        }),
    },
};

//#endregion

//#region Functions

/**
 * Read the log level from the environment.
 * @return {Level}
 */
export function readLogLevel() {
    return process.env.AK_LOG_LEVEL || DEFAULT_PINO_LOGGER_OPTIONS.level;
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
function createFixtureLogger(fixtureName, testName, options) {
    return this.child(
        { name: fixtureName },
        {
            msgPrefix: `[${testName}] `,
            ...options,
        },
    );
}

/**
 * @typedef {object} CustomLoggerMethods
 * @property {typeof createFixtureLogger} fixture
 */

/**
 * @typedef {Logger & CustomLoggerMethods} ConsoleLogger
 */

/**
 * A singleton logger instance for Node.js.
 *
 * ```js
 * import { ConsoleLogger } from "#logger/node";
 *
 * ConsoleLogger.info("Hello, world!");
 * ```
 *
 * @runtime node
 * @type {ConsoleLogger}
 */
export const ConsoleLogger = Object.assign(
    pino({
        ...DEFAULT_PINO_LOGGER_OPTIONS,
        level: readLogLevel(),
    }),
    { fixture: createFixtureLogger },
);

/**
 * @typedef {ReturnType<ConsoleLogger['child']>} ChildConsoleLogger
 */

//#region Aliases

export const info = ConsoleLogger.info.bind(ConsoleLogger);
export const debug = ConsoleLogger.debug.bind(ConsoleLogger);
export const warn = ConsoleLogger.warn.bind(ConsoleLogger);
export const error = ConsoleLogger.error.bind(ConsoleLogger);

//#endregion
