/**
 * Application logger.
 *
 * @import { LoggerOptions, Level } from "pino"
 * @import { PrettyOptions } from "pino-pretty"
 * @import { IConsoleLogger } from "./shared.js"
 */

/// <reference types="../types/node.js" />

import { fixture, prefix } from "./shared.js";

let warnedAboutPino = false;

const { pino } = await import("pino").catch(() => {
    if (!warnedAboutPino) {
        console.warn(
            `Pino is not available. Falling back to a lightweight console logger.
            Please install Pino to get the full logging experience: npm install pino`,
        );
        warnedAboutPino = true;
    }

    return import("./shared.js").then((module) => ({ pino: module.pinoLight }));
});

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
 * A singleton logger instance for Node.js.
 *
 * ```js
 * import { ConsoleLogger } from "#logger/node";
 *
 * ConsoleLogger.info("Hello, world!");
 * ```
 *
 * @runtime node
 * @type {IConsoleLogger}
 */
export const ConsoleLogger = Object.assign(
    pino({
        ...DEFAULT_PINO_LOGGER_OPTIONS,
        level: readLogLevel(),
    }),
    {
        fixture,
        prefix,
    },
);
