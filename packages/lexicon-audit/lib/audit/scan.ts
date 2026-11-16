import { basename, dirname, extname, relative } from "node:path";
import type { DatabaseSync } from "node:sqlite";

import { type FindingSink, collectFindings, compareFindings } from "#audit/matching";
import { type Tier } from "#constants";
import { sha256 } from "#hash";
import type { Allowlist } from "#lexicon/allowlist";
import { type LexiconIndex, lexiconLocales, loadLexiconIndex } from "#lexicon/database";
import { findFiles } from "#translation/files";
import {
    type LexiconLocaleMatch,
    type LexiconMatchOptions,
    canonicalizeLocale,
    matchLexiconLocale,
} from "#translation/locale";
import { readPO } from "#translation/po";
import {
    ParseError,
    type TranslationEntry,
    type TranslationReader,
    type TranslationReaderOptions,
    entryKey,
    entryVariant,
} from "#translation/shared";
import { readXLIFF } from "#translation/xliff";

//#region Options and results

export const TRANSLATION_PATTERNS = ["**/*.po", "**/*.xlf", "**/*.xliff"];

export interface ScanOptions extends TranslationReaderOptions, LexiconMatchOptions {
    tiers: readonly Tier[];
    /**
     * Only scan these canonical locales. Empty scans everything.
     */
    locales?: readonly string[];
    /**
     * Base for reported paths.
     */
    cwd?: string;
    /**
     * Locale of the source strings. When set, source text is scanned too, once per distinct string.
     */
    sourceLocale?: string | null;
    /**
     * Words reviewed as false positives. Their matches are counted but not reported.
     */
    allowlist?: Allowlist;
}

export interface ScannedFile {
    file: string;
    locale: string;
    /**
     * Translated units.
     */
    units: number;
    /**
     * The lexicon used for the file's locale, if any.
     */
    lexicon: LexiconLocaleMatch | null;
}

export interface ScanResult extends FindingSink {
    files: ScannedFile[];
    /**
     * Lexicon used for source strings, when source scanning is enabled.
     */
    sourceLexicon: LexiconLocaleMatch | null;
    /**
     * Distinct source strings scanned.
     */
    sourceUnits: number;
}

//#endregion

//#region Locale resolution

/**
 * Locale implied by a file's location: `<locale>/LC_MESSAGES/*.po` or `<locale>.xlf`.
 */
export function localeFromPath(filePath: string): string | null {
    if (extname(filePath) === ".po") {
        const parent = dirname(filePath);

        return basename(parent) === "LC_MESSAGES" ? basename(dirname(parent)) : null;
    }

    return basename(filePath, extname(filePath));
}

/**
 * Resolve a file's locale from its metadata and its path, failing when they disagree.
 */
export function resolveLocale(filePath: string, declared: string | null): string {
    const fromMetadata = declared ? canonicalizeLocale(declared) : null;
    const pathTag = localeFromPath(filePath);
    const fromPath = pathTag ? canonicalizeLocale(pathTag) : null;

    if (declared && !fromMetadata) {
        throw new ParseError(`${filePath}: declared locale is not a valid BCP 47 tag`);
    }

    if (fromMetadata && fromPath && fromMetadata !== fromPath) {
        throw new ParseError(
            `${filePath}: declared locale ${fromMetadata} conflicts with path locale ${fromPath}`,
        );
    }

    const locale = fromMetadata ?? fromPath;

    if (!locale) {
        throw new ParseError(`${filePath}: cannot determine the locale`);
    }

    return locale;
}

//#endregion

//#region Reading files

const READERS: Record<string, TranslationReader> = {
    ".po": readPO,
    ".xlf": readXLIFF,
    ".xliff": readXLIFF,
};

export function readTranslationFile(
    filePath: string,
    options: TranslationReaderOptions = {},
): AsyncIterable<TranslationEntry> {
    const reader = READERS[extname(filePath)];

    if (!reader) {
        throw new ParseError(`${filePath}: unsupported file type`);
    }

    return reader(filePath, options);
}

//#endregion

//#region Scanning

/**
 * Scan translation files under the given roots against the lexicon.
 */
export async function scanTranslations(
    db: DatabaseSync,
    roots: readonly string[],
    options: ScanOptions,
): Promise<ScanResult> {
    const cwd = options.cwd ?? process.cwd();
    const available = lexiconLocales(db);
    const indexes = new Map<string, LexiconIndex>();
    const filter = options.locales?.length ? new Set(options.locales) : null;

    const indexFor = (lexicon: string) => {
        let index = indexes.get(lexicon);

        if (!index) {
            index = loadLexiconIndex(db, lexicon, options.tiers);
            indexes.set(lexicon, index);
        }

        return index;
    };

    const sourceLocale = options.sourceLocale ? canonicalizeLocale(options.sourceLocale) : null;

    if (options.sourceLocale && !sourceLocale) {
        throw new ParseError(`invalid source locale: ${options.sourceLocale}`);
    }

    const sourceLexicon = sourceLocale
        ? matchLexiconLocale(sourceLocale, available, options)
        : null;
    const sourceIndex = sourceLexicon ? indexFor(sourceLexicon.lexicon) : null;
    const sourcesSeen = new Set<string>();

    const paths = new Set<string>();

    for (const root of roots) {
        const found = await findFiles(root, TRANSLATION_PATTERNS);

        if (!found.length) {
            throw new ParseError(`${root}: no .po or .xlf files found`);
        }

        for (const path of found) {
            paths.add(path);
        }
    }

    const result: ScanResult = {
        files: [],
        sourceLexicon,
        sourceUnits: 0,
        findings: [],
        allowed: 0,
    };

    for (const path of [...paths].sort()) {
        const file = relative(cwd, path);
        const scanned: ScannedFile = { file, locale: "", units: 0, lexicon: null };
        let declared: string | null = null;
        let skipTargets = false;

        for await (const unit of readTranslationFile(path, options)) {
            if (!scanned.locale || unit.locale !== declared) {
                declared = unit.locale;
                scanned.locale = resolveLocale(file, declared || null);
                scanned.lexicon = matchLexiconLocale(scanned.locale, available, options);
                skipTargets = Boolean(filter && !filter.has(scanned.locale));
            }

            if (sourceIndex && sourceLocale && unit.source) {
                const sourceKey = sha256(
                    JSON.stringify([unit.format, entryKey(unit), entryVariant(unit), unit.source]),
                );

                if (!sourcesSeen.has(sourceKey)) {
                    sourcesSeen.add(sourceKey);
                    result.sourceUnits++;

                    collectFindings(
                        {
                            side: "source",
                            file,
                            locale: sourceLocale,
                            lexicon: sourceLexicon!.lexicon,
                            unit,
                            index: sourceIndex,
                        },
                        result,
                        options.allowlist,
                    );
                }
            }

            if (skipTargets || !unit.target) {
                continue;
            }

            scanned.units++;

            if (!scanned.lexicon) {
                continue;
            }

            collectFindings(
                {
                    side: "target",
                    file,
                    locale: scanned.locale,
                    lexicon: scanned.lexicon.lexicon,
                    unit,
                    index: indexFor(scanned.lexicon.lexicon),
                },
                result,
                options.allowlist,
            );
        }

        if (!scanned.locale) {
            scanned.locale = resolveLocale(file, null);
            scanned.lexicon = matchLexiconLocale(scanned.locale, available, options);
        }

        if (filter && !filter.has(scanned.locale)) {
            continue;
        }

        result.files.push(scanned);
    }

    result.findings.sort(compareFindings);

    return result;
}

//#endregion
