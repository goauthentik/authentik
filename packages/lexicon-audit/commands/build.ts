/**
 * @file `lexicon-audit build`: build the lexicon database from the private TSV dump.
 *   Prints counts only; lexicon content never reaches the output.
 */

import { existsSync } from "node:fs";
import { mkdir } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { parseArgs } from "node:util";

import type { Command } from "#command";
import { ALLOWLIST_PATH, CORPUS_DIR, DATABASE_PATH } from "#constants";
import { buildLexicon } from "#lexicon/build";

export const build: Command = {
    summary: "Build the lexicon database from a directory of TSV files",
    usage: `Usage: lexicon-audit build [options]

Options:
  -i, --input <dir>      Lexicon TSV directory (default: ${CORPUS_DIR})
      --allowlist <path> False positives to store (default: ${ALLOWLIST_PATH}, if present)
      --db <path>        Database to write (default: ${DATABASE_PATH})
  -h, --help             Show this help`,

    async run(argv) {
        const { values } = parseArgs({
            args: argv,
            strict: true,
            options: {
                input: { type: "string", short: "i", default: CORPUS_DIR },
                allowlist: { type: "string" },
                db: { type: "string", default: DATABASE_PATH },
                help: { type: "boolean", short: "h", default: false },
            },
        });

        if (values.help) {
            console.log(this.usage);
            return;
        }

        const input = resolve(values.input);
        const db = resolve(values.db);

        // An explicit allowlist must exist; the default one is optional.
        const allowlistPath = values.allowlist
            ? resolve(values.allowlist)
            : existsSync(ALLOWLIST_PATH)
              ? ALLOWLIST_PATH
              : null;

        await mkdir(dirname(db), { recursive: true });

        console.error(`Building lexicon database from ${input}...`);

        const stats = await buildLexicon(input, db, { allowlistPath });

        for (const { locale, rows, duplicates, byTier } of stats.locales) {
            console.error(
                `  ${locale.padEnd(8)} ${String(rows).padStart(6)} entries ` +
                    `(vulgar ${byTier.vulgar}, offensive ${byTier.offensive}, sensitive ${byTier.sensitive}` +
                    `${duplicates ? `, ${duplicates} duplicates skipped` : ""})`,
            );
        }

        console.error(
            allowlistPath
                ? `Allowlist: ${stats.allowlist} entries from ${allowlistPath}`
                : `Allowlist: none (no ${ALLOWLIST_PATH})`,
        );

        console.error(`Wrote ${db}`);
    },
};
