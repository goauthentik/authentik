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

export interface Logger {
    info: typeof console.info;
    warn: typeof console.warn;
    error: typeof console.error;
    debug: typeof console.debug;
    trace: typeof console.trace;
}

/**
 * Labels log levels in the browser console.
 */
const LogLevelLabel = {
    info: "[INFO]",
    warn: "[WARN]",
    error: "[ERROR]",
    debug: "[DEBUG]",
    trace: "[TRACE]",
} as const;

export type LogLevel = keyof typeof LogLevelLabel;

/**
 * Predefined log levels.
 */
const LogLevels = Object.keys(LogLevelLabel) as LogLevel[];

/**
 * Colors for log levels in the browser console.
 *
 * @remarks
 *
 * The colors are derived from Carbon Design System's palette to ensure
 * sufficient contrast and accessibility across light and dark themes.
 */
const LogLevelColors = {
    info: `light-dark(#0043CE, #4589FF)`,
    warn: `light-dark(#F1C21B, #F1C21B)`,
    error: `light-dark(#DA1E28, #FA4D56)`,
    debug: `light-dark(#8A3FFC, #A56EFF)`,
    trace: `light-dark(#8A3FFC, #A56EFF)`,
} as const;

/**
 * Creates a logger with the given prefix.
 */
export function createLogger(prefix?: string, ...args: string[][]): Logger {
    const suffix = prefix ? `(${prefix}):` : ":";

    const logger: Partial<Logger> = {};

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

    return logger as Logger;
}

//#endregion

//#region Console Logger

export type IConsoleLogger = Logger & { prefix: (logPrefix: string) => Logger };

/**
 * A singleton logger instance for the browser.
 *
 * ```ts
 * import { ConsoleLogger } from "#logger/browser";
 *
 * ConsoleLogger.info("Hello, world!");
 * ```
 *
 * @runtime browser
 */
export class ConsoleLogger {
    // Assigned below via `Object.assign` so the browser reports the caller's
    // call site rather than a wrapper's.
    declare static info: typeof console.info;
    declare static warn: typeof console.warn;
    declare static error: typeof console.error;
    declare static debug: typeof console.debug;
    declare static trace: typeof console.trace;

    /**
     * Creates a logger with the given prefix.
     */
    static prefix(logPrefix: string): Logger {
        return createLogger(logPrefix);
    }
}

Object.assign(ConsoleLogger, createLogger());

//#endregion
