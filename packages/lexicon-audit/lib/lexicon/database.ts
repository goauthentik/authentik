import { DatabaseSync } from "node:sqlite";

import { SCHEMA_VERSION, type Tier } from "#constants";
import { LexiconError } from "#lexicon/errors";
import { normalize, tokenize } from "#translation/tokenize";

//#region Entries

export interface LexiconEntry {
    id: number;
    locale: string;
    word: string;
    tier: Tier;
    categoryHex: string;
    categoryBits: number;
    /**
     * Normalized tokens of the entry, e.g. two for a hyphenated compound.
     */
    tokens: string[];
    /**
     * Text between consecutive tokens, e.g. `["-"]`.
     */
    separators: string[];
    /**
     * All-caps entries such as acronyms match only in the same case, so `AN` doesn't match `an`.
     */
    caseSensitive: boolean;
}

/**
 * Whether an entry is written in capitals: at least two characters, with letters, all uppercase.
 *
 * Capitalized words don't count: German nouns are always capitalized, and sentence-initial
 * capitals must still match.
 */
export function isAllCaps(word: string, locale: string): boolean {
    return (
        [...word].length > 1 &&
        word !== word.toLocaleLowerCase(locale) &&
        word === word.toLocaleUpperCase(locale)
    );
}

/**
 * Entries for one locale, keyed by their first normalized token.
 */
export type LexiconIndex = Map<string, LexiconEntry[]>;

//#endregion

//#region Queries

/**
 * Begin a transaction that rolls back on disposal unless committed.
 */
export function transaction(db: DatabaseSync): Disposable & {
    commit(): void;
    /**
     * Commit the work so far and continue in a new transaction.
     */
    checkpoint(): void;
} {
    db.exec("BEGIN");

    return {
        commit: () => db.exec("COMMIT"),
        checkpoint: () => db.exec("COMMIT; BEGIN"),
        [Symbol.dispose]: () => {
            if (db.isOpen && db.isTransaction) {
                db.exec("ROLLBACK");
            }
        },
    };
}

/**
 * Open a lexicon database read-only, checking its schema version.
 *
 * The caller owns the returned database: declare it with `using`.
 */
export function openLexicon(databasePath: string): DatabaseSync {
    // Closes the database if validation throws; `move()` hands it to the caller otherwise.
    using stack = new DisposableStack();

    const db = stack.use(new DatabaseSync(databasePath, { readOnly: true }));
    const row: { user_version?: number } | undefined = db.prepare("PRAGMA user_version").get();

    if (row?.user_version !== SCHEMA_VERSION) {
        throw new LexiconError(
            `${databasePath} has schema version ${row?.user_version}, expected ${SCHEMA_VERSION}. Rebuild it.`,
        );
    }

    stack.move();

    return db;
}

export function lexiconLocales(db: DatabaseSync): string[] {
    return db
        .prepare("SELECT locale FROM lexicon_source WHERE row_count > 0 ORDER BY locale")
        .all()
        .map((row) => String(row.locale));
}

export function loadLexiconIndex(
    db: DatabaseSync,
    locale: string,
    tiers: readonly Tier[],
): LexiconIndex {
    const index: LexiconIndex = new Map();

    const rows = db
        .prepare(/* sql */ `
            SELECT id, word, tier, category_hex, category_bits
            FROM lexicon_entry
            WHERE locale = ? AND tier IN (${tiers.map(() => "?").join(", ")})
            ORDER BY id`)
        .iterate(locale, ...tiers);

    for (const row of rows) {
        const word = String(row.word);
        const tokens = tokenize(word, locale);
        const first = tokens[0];

        if (!first) {
            continue;
        }

        const entry: LexiconEntry = {
            id: Number(row.id),
            locale,
            word,
            tier: row.tier as Tier,
            categoryHex: String(row.category_hex),
            categoryBits: Number(row.category_bits),
            tokens: tokens.map((token) => token.norm),
            separators: tokens
                .slice(1)
                .map((token, i) => normalize(word.slice(tokens[i]!.end, token.start), locale)),
            caseSensitive: isAllCaps(word, locale),
        };

        const bucket = index.get(first.norm);

        if (bucket) {
            bucket.push(entry);
        } else {
            index.set(first.norm, [entry]);
        }
    }

    return index;
}

//#endregion
