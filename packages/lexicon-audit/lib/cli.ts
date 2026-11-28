#!/usr/bin/env node

/**
 * @file `lexicon-audit` entry point: dispatches to a command.
 */

import { type Command, UsageError } from "#command";
import { audit } from "#commands/audit";
import { build } from "#commands/build";
import { text } from "#commands/text";

const COMMANDS: Record<string, Command> = { build, audit, text };

const USAGE = `Usage: lexicon-audit <command> [options]

Commands:
${Object.entries(COMMANDS)
    .map(([name, { summary }]) => `  ${name.padEnd(8)} ${summary}`)
    .join("\n")}

Run \`lexicon-audit <command> --help\` for a command's options.`;

async function main() {
    const [name, ...argv] = process.argv.slice(2);

    if (!name || name === "-h" || name === "--help") {
        console.log(USAGE);
        process.exitCode = name ? 0 : 2;
        return;
    }

    const command = COMMANDS[name];

    if (!command) {
        throw new UsageError(`Unknown command: ${name}`);
    }

    try {
        await command.run(argv);
    } catch (error) {
        // parseArgs reports unknown or malformed options with this code.
        if (
            error instanceof UsageError ||
            (error as { code?: string }).code?.startsWith("ERR_PARSE_ARGS")
        ) {
            console.error(`${(error as Error).message}\n\n${command.usage}`);
            process.exit(2);
        }

        throw error;
    }
}

main().catch((error: unknown) => {
    if (error instanceof UsageError) {
        console.error(`${error.message}\n\n${USAGE}`);
        process.exit(2);
    }

    console.error(error instanceof Error ? error.message : error);
    process.exit(1);
});
