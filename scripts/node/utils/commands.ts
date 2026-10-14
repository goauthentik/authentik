/**
 * Utility functions for running shell commands and handling their results.
 */

import { exec, type ExecOptions } from "node:child_process";
import { resolve, sep } from "node:path";
import { promisify } from "node:util";

import { ConsoleLogger, type IConsoleLogger } from "#logger";

const logger = ConsoleLogger.prefix("commands");

type CommandErrorOptions = ErrorOptions & ExecOptions;

export class CommandError extends Error {
    name = "CommandError";

    constructor(command: string, { cause, cwd, shell }: CommandErrorOptions = {}) {
        const cwdInfo = cwd ? ` in directory ${cwd}` : "";
        const shellInfo = shell ? ` using shell ${shell}` : "";

        super(`Command failed: ${command}${cwdInfo}${shellInfo}`, { cause });
    }
}

/**
 * @param positionals
 * @returns The resolved current working directory for the script
 */
export function parseCWD(positionals: string[]): string {
    // `INIT_CWD` is present only if the script is run via npm.
    const initCWD = process.env.INIT_CWD || process.cwd();
    const [target] = positionals;

    return (target ? resolve(initCWD, target) : initCWD) + sep;
}

const execAsync = promisify(exec);

/**
 * A timeout value to prevent hanging indefinitely when running shell commands,
 * such as if CI is experiencing issues with provisioning or network connectivity.
 */
const DEFAULT_TIMEOUT_MS = 5 * 60 * 1000;

export const trimResult = (result: Awaited<ReturnType<typeof execAsync>>) => {
    return String(result.stdout).trim();
};

type CommandTag = (
    strings: TemplateStringsArray,
    ...expressions: unknown[]
) => (options?: ExecOptions) => Promise<string>;

function createTag(prefix = ""): CommandTag {
    return (strings, ...expressions) => {
        const command = (prefix ? prefix + " " : "") + String.raw(strings, ...expressions);

        logger.debug(command);

        return (options) =>
            execAsync(command, { timeout: DEFAULT_TIMEOUT_MS, ...options })
                .then(trimResult)
                .catch((cause) => {
                    throw new CommandError(command, { ...options, cause });
                });
    };
}

/**
 * A tagged template function for running shell commands.
 *
 * {@linkcode $.bind} derives a tag that prefixes every command, i.e. `$.bind("git")`.
 */
export const $ = Object.assign(createTag(), {
    bind: (prefix: string): CommandTag => createTag(prefix),
});

/**
 * Promisified version of {@linkcode exec} for easier async/await usage.
 *
 * @param command The command to run, with space-separated arguments.
 * @param [options] Optional execution options.
 * @throws {CommandError} If the command fails to execute.
 */
export function $2(command: string, options?: ExecOptions): Promise<string> {
    return execAsync(command, { timeout: DEFAULT_TIMEOUT_MS, ...options })
        .then(trimResult)
        .catch((cause) => {
            throw new CommandError(command, { ...options, cause });
        });
}

/**
 * Logs the given error and its cause (if any) and exits the process with a failure code.
 */
export function reportAndExit(error: unknown, logger: IConsoleLogger = ConsoleLogger): never {
    const message = error instanceof Error ? error.message : String(error);
    const cause = error instanceof Error && error.cause instanceof Error ? error.cause : null;

    logger.error(`❌ ${message}`);

    if (cause) {
        logger.error(`Caused by: ${cause.message}`);
    }

    process.exit(1);
}
