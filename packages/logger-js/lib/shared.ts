/**
 * @remarks
 *   The repetition of log levels and method signatures is intentional to give IDEs and type
 *   checkers a mapping of log methods to their documentation. Additionally, no wrapper functions
 *   are used to avoid the browser's console reported call site being the wrapper instead of the
 *   actual caller.
 * @file Console logger for browser environments.
 */

/* eslint-disable no-console */

import type {
    BaseLogger as PinoBaseLogger,
    ChildLoggerOptions,
    Level as PinoLevel,
    LogFn as PinoLogFn,
    Logger as PinoLogger,
    LoggerOptions,
} from "pino";

export type { ChildLoggerOptions, LoggerOptions };

export type Logger = PinoLogger;
export type Level = PinoLevel;
export type LogFn = PinoLogFn;
export type BaseLogger = Pick<PinoBaseLogger, Exclude<Level, "fatal">>;

//#region Constants

/**
 * Labels log levels in the browser console.
 */
export const LogLevelLabel = {
    info: "[INFO]",
    warn: "[WARN]",
    error: "[ERROR]",
    debug: "[DEBUG]",
    trace: "[TRACE]",
    fatal: "[FATAL]",
} as const satisfies Record<Level, string>;

/**
 * Predefined log levels.
 */
export const LogLevels = Object.keys(LogLevelLabel) as Level[];

/**
 * Creates a logger with the given prefix.
 */
export type LoggerFactory = (prefix?: string | null, ...args: string[][]) => Logger;

/**
 * Colors for log levels in the browser console.
 *
 * @remarks
 *
 *   The colors are derived from Carbon Design System's palette to ensure sufficient contrast and
 *   accessibility across light and dark themes.
 */
const LogLevelColors = {
    info: `light-dark(#0043CE, #4589FF)`,
    warn: `light-dark(#F1C21B, #F1C21B)`,
    error: `light-dark(#DA1E28, #FA4D56)`,
    debug: `light-dark(#8A3FFC, #A56EFF)`,
    trace: `light-dark(#8A3FFC, #A56EFF)`,
    fatal: `light-dark(#DA1E28, #FA4D56)`,
} as const satisfies Record<Level, string>;

/**
 * Aliases a log level to the matching console method, falling back to {@linkcode console.log} for
 * levels the console doesn't implement.
 */
function consoleMethod(level: Level): (...args: unknown[]) => void {
    return level in console
        ? (console[level as keyof Console] as (...args: unknown[]) => void)
        : console.log;
}

//#endregion

//#region Functions

/**
 * Creates a logger with the given prefix.
 */
const createConsoleLogger: LoggerFactory = (prefix, ...args) => {
    const msgPrefix = prefix ? `(${prefix}):` : ":";
    const logger: Partial<Logger> = { msgPrefix };

    for (const level of LogLevels) {
        const label = LogLevelLabel[level];

        logger[level] = consoleMethod(level).bind(console, `${label} ${msgPrefix}`, ...args);
    }

    return logger as Logger;
};

export type FixtureLogger = Logger;

export function fixture(
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

export function child(bindings: Record<string, unknown>, _options?: ChildLoggerOptions): Logger {
    const name = typeof bindings.name === "string" ? bindings.name : null;

    return Object.assign(createConsoleLogger(name), { ...bindings });
}

export function prefix(this: { child: typeof child }, label: string): IConsoleLogger {
    // A child logger carries the custom methods of the logger it came from.
    return this.child({ name: label }) as unknown as IConsoleLogger;
}

export interface CustomLoggerMethods {
    fixture: typeof fixture;
    prefix: typeof prefix;
    child: typeof child;
}

export type BaseConsoleLogger = Record<Level, LogFn>;

export type IConsoleLogger = BaseConsoleLogger & CustomLoggerMethods;

export const customLoggerMethods: CustomLoggerMethods = {
    fixture,
    prefix,
    child,
};

/**
 * Creates a lightweight logger that mimics the Pino API but falls back to console methods when Pino
 * is not available.
 */
export function pinoLight(options: LoggerOptions<never, false>): IConsoleLogger {
    const baseLogger = createConsoleLogger(options.name);

    return {
        ...baseLogger,
        fixture,
        prefix,
        child,
    };
}

/**
 * Creates a logger with the given prefix, styled for the browser console.
 */
export function createLogger(prefix?: string, ...args: string[][]): Logger {
    const msgPrefix = prefix ? `(${prefix}):` : ":";
    const logger: Partial<Logger> = { msgPrefix };

    for (const level of LogLevels) {
        const label = LogLevelLabel[level];
        const color = LogLevelColors[level];

        logger[level] = consoleMethod(level).bind(
            console,
            `%c${label}%c ${msgPrefix}%c`,
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

/**
 * A singleton logger instance for the browser.
 *
 * ```js
 * import { ConsoleLogger } from "#logger/browser";
 *
 * ConsoleLogger.info("Hello, world!");
 * ```
 *
 * @runtime browser
 */
export class ConsoleLogger {
    static info: typeof console.info;
    static warn: typeof console.warn;
    static error: typeof console.error;
    static debug: typeof console.debug;
    static trace: typeof console.trace;

    /**
     * Creates a logger with the given prefix.
     */
    static prefix(logPrefix: string): Logger {
        return createLogger(logPrefix);
    }
}

Object.assign(ConsoleLogger, createLogger());

//#endregion
