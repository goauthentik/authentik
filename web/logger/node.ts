/**
 * Application logger.
 */

import { type ChildLoggerOptions, type Level, type Logger, type LoggerOptions, pino } from "pino";
import type { PrettyOptions } from "pino-pretty";

//#region Constants

/**
 * Default options for creating a Pino logger.
 *
 * @category Logger
 */
export const DEFAULT_PINO_LOGGER_OPTIONS = {
    enabled: true,
    level: "info",
    transport: {
        target: "./transport.ts",
        options: {
            colorize: true,
        } satisfies PrettyOptions,
    },
} satisfies LoggerOptions<never, false>;

//#endregion

//#region Functions

/**
 * Read the log level from the environment.
 */
export function readLogLevel(): Level {
    return process.env.AK_LOG_LEVEL || DEFAULT_PINO_LOGGER_OPTIONS.level;
}

export type FixtureLogger = Logger;

function createFixtureLogger(
    this: Logger,
    fixtureName: string,
    testName?: string,
    options?: ChildLoggerOptions,
): FixtureLogger {
    return this.child(
        { name: fixtureName },
        {
            msgPrefix: `[${testName}] `,
            ...options,
        },
    );
}

export interface CustomLoggerMethods {
    fixture: typeof createFixtureLogger;
}

export type ConsoleLogger = Logger & CustomLoggerMethods;

/**
 * A singleton logger instance for Node.js.
 *
 * ```ts
 * import { ConsoleLogger } from "#logger/node";
 *
 * ConsoleLogger.info("Hello, world!");
 * ```
 *
 * @runtime node
 */
export const ConsoleLogger: ConsoleLogger = Object.assign(
    pino({
        ...DEFAULT_PINO_LOGGER_OPTIONS,
        level: readLogLevel(),
    }),
    { fixture: createFixtureLogger },
);

export type ChildConsoleLogger = ReturnType<ConsoleLogger["child"]>;

//#region Aliases

export const info = ConsoleLogger.info.bind(ConsoleLogger);
export const debug = ConsoleLogger.debug.bind(ConsoleLogger);
export const warn = ConsoleLogger.warn.bind(ConsoleLogger);
export const error = ConsoleLogger.error.bind(ConsoleLogger);

//#endregion
