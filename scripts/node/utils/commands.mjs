/**
 * Utility functions for running shell commands and handling their results.
 *
 * @import { ExecOptions } from "node:child_process"
 */

import { exec } from "node:child_process";
import { resolve, sep } from "node:path";
import { promisify } from "node:util";

import { ConsoleLogger } from "../../../packages/logger-js/lib/node.js";

const logger = ConsoleLogger.prefix("commands");

export class CommandError extends Error {
    name = "CommandError";

    /**
     * @param {string} command
     * @param {ErrorOptions & ExecOptions} options
     */
    constructor(command, { cause, cwd, shell } = {}) {
        const cwdInfo = cwd ? ` in directory ${cwd}` : "";
        const shellInfo = shell ? ` using shell ${shell}` : "";

        super(`Command failed: ${command}${cwdInfo}${shellInfo}`, { cause });
    }
}

/**
 * @param {string[]} positionals
 * @returns {string} The resolved current working directory for the script
 */
export function parseCWD(positionals) {
    // `INIT_CWD` is present only if the script is run via npm.
    const initCWD = process.env.INIT_CWD || process.cwd();

    const cwd = (positionals.length ? resolve(initCWD, positionals[0]) : initCWD) + sep;

    return cwd;
}

const execAsync = promisify(exec);

/**
 * @param {Awaited<ReturnType<typeof execAsync>>} result
 */
export const trimResult = (result) => String(result.stdout).trim();

/**
 * @typedef {(strings: TemplateStringsArray, ...expressions: unknown[]) =>
 *   (options?: ExecOptions) => Promise<string>
 * } CommandTag
 */

function createTag(prefix = "") {
    /** @type {CommandTag} */
    return (strings, ...expressions) => {
        const command = (prefix ? prefix + " " : "") + String.raw(strings, ...expressions);

        logger.debug(command);

        return (options) =>
            execAsync(command, options)
                .then(trimResult)
                .catch((cause) => {
                    throw new CommandError(command, { ...options, cause });
                });
    };
}

/**
 * A tagged template function for running shell commands.
 * @type {CommandTag & { bind(prefix: string): CommandTag }}
 */
export const $ = createTag();

/**
 * @param {string} prefix
 * @returns {CommandTag}
 */
$.bind = (prefix) => createTag(prefix);

/**
 * Promisified version of {@linkcode exec} for easier async/await usage.
 *
 * @param {string} command The command to run, with space-separated arguments.
 * @param {ExecOptions} [options] Optional execution options.
 * @throws {CommandError} If the command fails to execute.
 */
export function $2(command, options) {
    return execAsync(command, options)
        .then(trimResult)
        .catch((cause) => {
            throw new CommandError(command, { ...options, cause });
        });
}

/**
 * Logs the given error and its cause (if any) and exits the process with a failure code.
 * @param {unknown} error
 * @param {typeof ConsoleLogger} logger
 * @returns {never}
 */
export function reportAndExit(error, logger = ConsoleLogger) {
    const message = error instanceof Error ? error.message : String(error);
    const cause = error instanceof Error && error.cause instanceof Error ? error.cause : null;

    logger.error(`❌ ${message}`);

    if (cause) {
        logger.error(`Caused by: ${cause.message}`);
    }

    process.exit(1);
}
