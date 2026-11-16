/**
 * @file `lexicon-audit audit`: audit translation files against the lexicon database.
 *   By default only counts are printed, on stderr. Matched words and translation text are emitted
 *   only on request: `--jsonl` prints them to stdout, `--report` writes per-locale Markdown files.
 */

import { existsSync } from "node:fs";
import { resolve } from "node:path";
import { parseArgs } from "node:util";

import { renderJSONL, writeMarkdownReports } from "#audit/report";
import { scanTranslations } from "#audit/scan";
import { printScanSummary } from "#audit/summary";
import { type Command, UsageError, parseLocaleTags } from "#command";
import { DATABASE_PATH, type Tier } from "#constants";
import { Allowlist } from "#lexicon/allowlist";
import { openLexicon } from "#lexicon/database";

export const audit: Command = {
    summary: "Audit translation files against the lexicon database",
    usage: `Usage: lexicon-audit audit [options] <translation-dir>...

Options:
  -l, --locale <tag>     Only audit this locale (repeatable)
      --db <path>        Lexicon database (default: ${DATABASE_PATH})
      --report <dir>     Write per-locale Markdown reports, including matched text, to a directory
      --jsonl            Print findings, including matched text, to stdout as JSON Lines
      --include-sensitive  Include the "sensitive" tier
      --include-fuzzy    Audit fuzzy PO entries
      --include-obsolete Audit obsolete PO entries
      --source-locale <tag>  Also audit source strings in this locale, e.g. en-US
      --region-fallback  Use another region's lexicon when a locale has none, e.g. pt-PT → pt-BR
  -h, --help             Show this help`,

    async run(argv) {
        const { values, positionals } = parseArgs({
            args: argv,
            strict: true,
            allowPositionals: true,
            options: {
                "locale": { type: "string", short: "l", multiple: true, default: [] },
                "db": { type: "string", default: DATABASE_PATH },
                "report": { type: "string" },
                "jsonl": { type: "boolean", default: false },
                "include-sensitive": { type: "boolean", default: false },
                "include-fuzzy": { type: "boolean", default: false },
                "include-obsolete": { type: "boolean", default: false },
                "source-locale": { type: "string" },
                "region-fallback": { type: "boolean", default: false },
                "help": { type: "boolean", short: "h", default: false },
            },
        });

        if (values.help) {
            console.log(this.usage);
            return;
        }

        if (!positionals.length) {
            throw new UsageError("Expected at least one translation directory.");
        }

        const dbPath = resolve(values.db);

        if (!existsSync(dbPath)) {
            throw new Error(`${dbPath} not found. Build it with \`lexicon-audit build\`.`);
        }

        const tiers: Tier[] = values["include-sensitive"]
            ? ["vulgar", "offensive", "sensitive"]
            : ["vulgar", "offensive"];

        const sourceLocale = values["source-locale"] ?? null;
        using db = openLexicon(dbPath);

        const result = await scanTranslations(
            db,
            positionals.map((path) => resolve(path)),
            {
                locales: parseLocaleTags(values.locale),
                tiers,
                includeFuzzy: values["include-fuzzy"],
                includeObsolete: values["include-obsolete"],
                sourceLocale,
                regionFallback: values["region-fallback"],
                allowlist: Allowlist.fromDatabase(db),
            },
        );

        printScanSummary(result);

        if (sourceLocale && !result.sourceLexicon) {
            console.error(
                `No lexicon for source locale ${sourceLocale}; source strings were not audited.`,
            );
        }

        const context = { result, tiers, generatedAt: new Date().toISOString() };

        if (values.report) {
            const directory = resolve(values.report);
            const files = await writeMarkdownReports(directory, context);

            console.error(`Wrote ${files.length} files to ${directory}`);
        }

        if (values.jsonl) {
            process.stdout.write(renderJSONL(context));
        }

        if (result.findings.length) {
            process.exitCode = 1;
        }
    },
};
