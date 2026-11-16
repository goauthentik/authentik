/**
 * @file The format-independent shape PO and XLIFF readers produce.
 */

export type TranslationFormat = "po" | "xlf";

/**
 * One translated string. Plural forms and XLIFF segments are separate entries.
 */
export interface TranslationEntry {
    format: TranslationFormat;
    /**
     * PO `msgid` or XLIFF unit ID.
     */
    id: string;
    /**
     * PO `msgctxt`.
     */
    context?: string;
    /**
     * Index of a PO `msgstr[n]` plural form.
     */
    pluralIndex?: number;
    /**
     * XLIFF segment ID, when a unit has several segments.
     */
    segment?: string;
    /**
     * Obsolete PO entry (`#~`).
     */
    obsolete?: boolean;
    /**
     * Locale declared by the file, as written. Empty when the file declares none.
     */
    locale: string;
    /**
     * 1-based line where the entry starts in its file.
     */
    line: number;
    source: string;
    /**
     * Target text, empty when untranslated. Inline placeholders are replaced with
     * {@linkcode PLACEHOLDER}.
     */
    target: string;
}

export interface TranslationReaderOptions {
    includeFuzzy?: boolean;
    includeObsolete?: boolean;
}

export type TranslationReader = (
    path: string,
    options?: TranslationReaderOptions,
) => AsyncIterable<TranslationEntry>;

export class ParseError extends Error {
    override name = "ParseError";
}

/**
 * Stands in for inline markup so tokens on either side stay separate.
 */
export const PLACEHOLDER = "￼";

/**
 * Stable identity of an entry within its file.
 *
 * Gettext joins context and msgid with EOT, as in compiled `.mo` files. Obsolete entries may share
 * an identity with a live one, so they're prefixed.
 */
export function entryKey(entry: TranslationEntry): string {
    const id = entry.context ? `${entry.context}\u0004${entry.id}` : entry.id;

    return entry.obsolete ? `#~${id}` : id;
}

/**
 * The plural index or segment ID, or empty when the entry has neither.
 */
export function entryVariant(entry: TranslationEntry): string {
    return entry.pluralIndex === undefined ? (entry.segment ?? "") : String(entry.pluralIndex);
}
