/**
 * @file `lexicon-audit seal` and `lexicon-audit unseal`: encrypt the lexicon database for commit,
 *   and decrypt it for an audit. The passphrase is read from the environment only.
 */

import { mkdir } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { parseArgs } from "node:util";

import { type Command, UsageError } from "#command";
import { DATABASE_PATH, PASSPHRASE_ENV, SEALED_DATABASE_PATH } from "#constants";
import { sealLexicon, unsealLexicon } from "#lexicon/seal";

function readPassphrase(): string {
    const passphrase = process.env[PASSPHRASE_ENV];

    if (!passphrase) {
        throw new UsageError(`Set ${PASSPHRASE_ENV} to the lexicon passphrase.`);
    }

    return passphrase;
}

function parsePaths(argv: string[]) {
    const { values } = parseArgs({
        args: argv,
        strict: true,
        options: {
            db: { type: "string", default: DATABASE_PATH },
            sealed: { type: "string", default: SEALED_DATABASE_PATH },
            help: { type: "boolean", short: "h", default: false },
        },
    });

    return { help: values.help, db: resolve(values.db), sealed: resolve(values.sealed) };
}

const OPTIONS = `Options:
      --db <path>        Lexicon database (default: ${DATABASE_PATH})
      --sealed <path>    Encrypted database (default: ${SEALED_DATABASE_PATH})
  -h, --help             Show this help

Environment:
  ${PASSPHRASE_ENV}  Passphrase (required)`;

export const seal: Command = {
    summary: "Encrypt the lexicon database for commit",
    usage: `Usage: lexicon-audit seal [options]\n\n${OPTIONS}`,

    async run(argv) {
        const { help, db, sealed } = parsePaths(argv);

        if (help) {
            console.log(this.usage);
            return;
        }

        await sealLexicon(db, sealed, readPassphrase());

        console.error(`Wrote ${sealed}`);
    },
};

export const unseal: Command = {
    summary: "Decrypt the committed lexicon database",
    usage: `Usage: lexicon-audit unseal [options]\n\n${OPTIONS}`,

    async run(argv) {
        const { help, db, sealed } = parsePaths(argv);

        if (help) {
            console.log(this.usage);
            return;
        }

        await mkdir(dirname(db), { recursive: true });
        await unsealLexicon(sealed, db, readPassphrase());

        console.error(`Wrote ${db}`);
    },
};
