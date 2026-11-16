import { openLines } from "#translation/files";
import {
    ParseError,
    type TranslationEntry,
    type TranslationReader,
    type TranslationReaderOptions,
} from "#translation/shared";

import { type GetTextTranslationRecord, po } from "gettext-parser";

//#region Block splitting

export interface POBlock {
    /**
     * 1-based line where the block starts.
     */
    line: number;
    text: string;
}

/**
 * Lazily split a PO file into blank-line-separated entries.
 *
 * Blank lines between entries are conventional rather than required by Gettext, but every
 * catalog we audit (Django and Transifex output) follows the convention.
 */
export async function* readPOBlocks(filePath: string): AsyncGenerator<POBlock> {
    using file = openLines(filePath);

    let block: string[] = [];
    let start = 0;
    let lineNumber = 0;

    for await (const line of file.lines) {
        lineNumber++;

        if (!line.trim()) {
            if (block.length) {
                yield { line: start, text: block.join("\n") };
            }

            block = [];
            continue;
        }

        if (!block.length) {
            start = lineNumber;
        }

        block.push(line);
    }

    if (block.length) {
        yield { line: start, text: block.join("\n") };
    }
}

//#endregion

//#region Entries

function* entriesFromRecord(
    record: GetTextTranslationRecord | undefined,
    locale: string,
    line: number,
    options: TranslationReaderOptions,
    obsolete: boolean,
): Generator<TranslationEntry> {
    for (const entries of Object.values(record ?? {})) {
        for (const entry of Object.values(entries)) {
            // The header entry.
            if (!entry.msgid && !entry.msgctxt) {
                continue;
            }

            const flags = (entry.comments?.flag ?? "").split(",").map((flag) => flag.trim());

            if (flags.includes("fuzzy") && !options.includeFuzzy) {
                continue;
            }

            const plural = Boolean(entry.msgid_plural);

            for (const [index, target] of entry.msgstr.entries()) {
                yield {
                    format: "po",
                    id: entry.msgid,
                    context: entry.msgctxt || undefined,
                    pluralIndex: plural ? index : undefined,
                    obsolete: obsolete || undefined,
                    locale,
                    line,
                    source: plural && index > 0 ? entry.msgid_plural! : entry.msgid,
                    target,
                };
            }
        }
    }
}

/**
 * Stream translation entries from a PO file, one Gettext entry at a time.
 */
export const readPO = async function* (filePath, options = {}) {
    let locale = "";

    for await (const block of readPOBlocks(filePath)) {
        let catalog: ReturnType<typeof po.parse>;

        try {
            catalog = po.parse(block.text);
        } catch (error) {
            throw new ParseError(
                `${filePath}:${block.line}: ${error instanceof Error ? error.message : error}`,
            );
        }

        locale ||= catalog.headers?.Language ?? "";

        yield* entriesFromRecord(catalog.translations, locale, block.line, options, false);

        if (options.includeObsolete) {
            yield* entriesFromRecord(catalog.obsolete, locale, block.line, options, true);
        }
    }
} satisfies TranslationReader;

//#endregion
