import type { DatabaseSync } from "node:sqlite";

import { canonicalizeLocale } from "#translation/locale";
import { normalize } from "#translation/tokenize";
import { TSVError, readTSV } from "#translation/tsv";

const COLUMNS = ["locale", "word", "note"] as const;

/**
 * Matches every locale.
 */
export const ANY_LOCALE = "*";

export interface AllowlistEntry {
    /**
     * Canonical locale or {@linkcode ANY_LOCALE}.
     */
    locale: string;
    word: string;
    normalizedWord: string;
    note: string;
}

function normalizeFor(word: string, locale: string): string {
    return normalize(word, locale === ANY_LOCALE ? "und" : locale);
}

/**
 * Read an allowlist TSV with the header `locale\tword\tnote`.
 *
 * `locale` is a BCP 47 tag or `*`. `note` records why the word is allowed and may be empty.
 */
export async function* readAllowlist(filePath: string): AsyncGenerator<AllowlistEntry> {
    for await (const { line, fields } of readTSV(filePath, COLUMNS)) {
        const [tag, word, note] = fields as [string, string, string];
        const locale = tag === ANY_LOCALE ? tag : canonicalizeLocale(tag);

        if (!locale) {
            throw new TSVError(filePath, line, "invalid locale");
        }
        if (!word.trim()) {
            throw new TSVError(filePath, line, "empty word");
        }

        yield { locale, word, normalizedWord: normalizeFor(word, locale), note };
    }
}

/**
 * Lexicon words reviewed as false positives, by locale.
 */
export class Allowlist {
    /**
     * Normalized words, keyed by canonical locale or {@linkcode ANY_LOCALE}.
     */
    readonly #words = new Map<string, Set<string>>();

    /**
     * Load the allowlist stored in a lexicon database.
     */
    static fromDatabase(db: DatabaseSync): Allowlist {
        const allowlist = new Allowlist();

        for (const row of db.prepare("SELECT locale, normalized_word FROM allowlist").iterate()) {
            allowlist.#add(String(row.locale), String(row.normalized_word));
        }

        return allowlist;
    }

    #add(locale: string, normalizedWord: string): void {
        const words = this.#words.get(locale);

        if (words) {
            words.add(normalizedWord);
        } else {
            this.#words.set(locale, new Set([normalizedWord]));
        }
    }

    /**
     * Whether a lexicon word is allowed in a locale.
     */
    has(locale: string, word: string): boolean {
        return Boolean(
            this.#words.get(locale)?.has(normalizeFor(word, locale)) ||
            this.#words.get(ANY_LOCALE)?.has(normalizeFor(word, ANY_LOCALE)),
        );
    }
}
