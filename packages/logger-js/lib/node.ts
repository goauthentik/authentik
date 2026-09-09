/**
 * Application logger.
 */

/// <reference types="../types/node.js" />

import type { Level, LoggerOptions } from "./shared.ts";
import { fixture, type IConsoleLogger, prefix } from "./shared.ts";

export * from "./shared.ts";

let warnedAboutPino = false;

const { pino } = await import("pino").catch(() => {
    if (!warnedAboutPino) {
        console.warn(
            `Pino is not available. Falling back to a lightweight console logger.
            Please install Pino to get the full logging experience: npm install pino`,
        );
        warnedAboutPino = true;
    }

    return import("./shared.ts").then((module) => ({ pino: module.pinoLight }));
});

//#region Constants

/**
 * Pino spawns the transport in a worker thread and resolves this target as a
 * path, so it has to name the file that exists alongside *this* module: the
 * TypeScript source when Node is stripping types, the emitted JavaScript
 * otherwise. Unlike an import specifier, nothing rewrites it on emit.
 */
const TRANSPORT_TARGET = import.meta.filename.endsWith(".ts") ? "./transport.ts" : "./transport.js";

/**
 * Default options for creating a Pino logger.
 *
 * @category Logger
 */
export const DEFAULT_PINO_LOGGER_OPTIONS = {
    enabled: true,
    level: "info",
    transport: {
        target: TRANSPORT_TARGET,
        options: {
            colorize: true,
        },
    },
} satisfies LoggerOptions<never, false>;

//#endregion

//#region Functions

/**
 * Read the log level from the environment.
 */
export function readLogLevel(): Level {
    return (process.env.AK_LOG_LEVEL || DEFAULT_PINO_LOGGER_OPTIONS.level) as Level;
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
 */
export const ConsoleLogger: IConsoleLogger = Object.assign(
    pino({
        ...DEFAULT_PINO_LOGGER_OPTIONS,
        level: readLogLevel(),
    }),
    {
        fixture,
        prefix,
    },
) as unknown as IConsoleLogger;

//#endregion
