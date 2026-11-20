/**
 * @file `lexicon-audit text`: check plain-text files as-is, line by line, in one locale.
 *   Prints counts only by default, like `audit`.
 */

import { existsSync } from "node:fs";
import { resolve } from "node:path";
import { parseArgs } from "node:util";

import { writeOutputs } from "#audit/report";
import { scanTextFiles } from "#audit/scan";
import { formatCounts } from "#audit/summary";
import { type Command, UsageError, parseMinLength } from "#command";
import { DATABASE_PATH, DEFAULT_MIN_LENGTH, type Tier } from "#constants";
import { Allowlist } from "#lexicon/allowlist";
import { openLexicon } from "#lexicon/database";

export const text: Command = {
    summary: "Check plain-text files, such as Markdown, as-is",
    usage: `Usage: lexicon-audit text [options] <file>...

Options:
      --source-locale <tag>  Locale of the text (default: en)
      --db <path>        Lexicon database (default: ${DATABASE_PATH})
      --report <dir>     Write Markdown reports, including matched text, to a directory
      --jsonl            Print findings, including matched text, to stdout as JSON Lines
      --include-sensitive  Include the "sensitive" tier
      --min-length <n>   Skip lexicon entries shorter than n characters, except in CJK
                         locales (default: ${DEFAULT_MIN_LENGTH})
      --region-fallback  Use another region's lexicon when the locale has none
  -h, --help             Show this help`,

    async run(argv) {
        const { values, positionals } = parseArgs({
            args: argv,
            strict: true,
            allowPositionals: true,
            options: {
                "source-locale": { type: "string", default: "en" },
                "db": { type: "string", default: DATABASE_PATH },
                "report": { type: "string" },
                "jsonl": { type: "boolean", default: false },
                "include-sensitive": { type: "boolean", default: false },
                "min-length": { type: "string", default: String(DEFAULT_MIN_LENGTH) },
                "region-fallback": { type: "boolean", default: false },
                "help": { type: "boolean", short: "h", default: false },
            },
        });

        if (values.help) {
            console.log(this.usage);
            return;
        }

        if (!positionals.length) {
            throw new UsageError("Expected at least one file.");
        }

        const dbPath = resolve(values.db);

        if (!existsSync(dbPath)) {
            throw new Error(`${dbPath} not found. Build it with \`lexicon-audit build\`.`);
        }

        const tiers: Tier[] = values["include-sensitive"]
            ? ["vulgar", "offensive", "sensitive"]
            : ["vulgar", "offensive"];

        using db = openLexicon(dbPath);

        const result = await scanTextFiles(
            db,
            positionals.map((path) => resolve(path)),
            {
                locale: values["source-locale"],
                tiers,
                minLength: parseMinLength(values["min-length"]),
                regionFallback: values["region-fallback"],
                allowlist: Allowlist.fromDatabase(db),
            },
        );

        const { lexicon, match } = result.sourceLexicon!;
        const via = match === "exact" ? "" : ` (${match})`;
        const allowed = result.allowed ? ` (${result.allowed} more skipped by the allowlist)` : "";

        console.error(
            `Checked ${result.files.length} files, ${result.sourceUnits} lines, lexicon ${lexicon}${via}: ${formatCounts(result.findings)}`,
        );
        console.error(`${result.findings.length} findings${allowed}.`);

        await writeOutputs(
            { result, tiers, generatedAt: new Date().toISOString() },
            { report: values.report ? resolve(values.report) : null, jsonl: values.jsonl },
        );

        if (result.findings.length) {
            process.exitCode = 1;
        }
    },
};
