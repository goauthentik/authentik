import { readFile, rename, rm } from "node:fs/promises";
import { basename, relative } from "node:path";
import { DatabaseSync } from "node:sqlite";

import { SCHEMA_VERSION, type Tier, isTier } from "#constants";
import { sha256 } from "#hash";
import { readAllowlist } from "#lexicon/allowlist";
import { transaction } from "#lexicon/database";
import { LexiconError } from "#lexicon/errors";
import { findFiles } from "#translation/files";
import { canonicalizeLocale } from "#translation/locale";
import { normalize } from "#translation/tokenize";
import { TSVError, readTSV } from "#translation/tsv";

//#region Schema

const COLUMNS = ["tier", "category", "word"] as const;

const BATCH_SIZE = 1000;

const SCHEMA = /* sql */ `
PRAGMA foreign_keys = ON;

CREATE TABLE lexicon_source (
    id INTEGER PRIMARY KEY,
    locale TEXT NOT NULL UNIQUE,
    file_name TEXT NOT NULL,
    original_tag TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    row_count INTEGER NOT NULL,
    duplicate_count INTEGER NOT NULL,
    imported_at TEXT NOT NULL
);

CREATE TABLE lexicon_entry (
    id INTEGER PRIMARY KEY,
    source_id INTEGER NOT NULL REFERENCES lexicon_source(id),
    locale TEXT NOT NULL,
    word TEXT NOT NULL,
    normalized_word TEXT NOT NULL,
    tier TEXT NOT NULL CHECK (tier IN ('vulgar', 'offensive', 'sensitive')),
    category_hex TEXT NOT NULL,
    category_bits INTEGER NOT NULL,
    UNIQUE (locale, word, tier, category_bits)
);

CREATE INDEX lexicon_lookup ON lexicon_entry (locale, normalized_word);

CREATE TABLE allowlist (
    id INTEGER PRIMARY KEY,
    locale TEXT NOT NULL,
    word TEXT NOT NULL,
    normalized_word TEXT NOT NULL,
    note TEXT NOT NULL,
    UNIQUE (locale, normalized_word)
);
`;

//#endregion

//#region Discovery

export interface LexiconSourceFile {
    path: string;
    /**
     * The tag as written in the file name.
     */
    originalTag: string;
    locale: string;
}

export { LexiconError } from "#lexicon/errors";

/**
 * Parse a lexicon file name: `<tag>.tsv` or `words-<tag>.tsv`.
 */
export function parseLexiconFileName(filePath: string): Omit<LexiconSourceFile, "path"> | null {
    const name = basename(filePath);

    if (!name.endsWith(".tsv")) {
        return null;
    }

    let originalTag = name.slice(0, -".tsv".length);

    if (originalTag.startsWith("words-")) {
        originalTag = originalTag.slice("words-".length);
    }

    const locale = canonicalizeLocale(originalTag);

    return locale ? { originalTag, locale } : null;
}

/**
 * Find and validate lexicon files under a directory.
 */
export async function discoverLexicon(inputDir: string): Promise<LexiconSourceFile[]> {
    const paths = await findFiles(inputDir, ["**/*.tsv"]);

    if (!paths.length) {
        throw new LexiconError(`No .tsv files found in ${inputDir}`);
    }

    const byLocale = new Map<string, LexiconSourceFile>();

    for (const path of paths) {
        const parsed = parseLexiconFileName(path);

        if (!parsed) {
            throw new LexiconError(
                `${path}: file name is not "<BCP 47 tag>.tsv" or "words-<tag>.tsv"`,
            );
        }

        const existing = byLocale.get(parsed.locale);

        if (existing) {
            throw new LexiconError(
                `${path}: duplicate locale ${parsed.locale} (also ${existing.path})`,
            );
        }

        byLocale.set(parsed.locale, { path, ...parsed });
    }

    return [...byLocale.values()];
}

//#endregion

//#region Building

export interface LocaleImportStats {
    locale: string;
    rows: number;
    duplicates: number;
    byTier: Record<Tier, number>;
}

export interface BuildOptions {
    /**
     * Allowlist TSV to store alongside the lexicon.
     */
    allowlistPath?: string | null;
}

export interface BuildStats {
    locales: LocaleImportStats[];
    /**
     * Allowlist entries stored.
     */
    allowlist: number;
}

/**
 * Build the lexicon database from a directory of TSV files.
 *
 * Writes to a temporary file and renames it into place, so a failed import leaves the previous
 * database untouched.
 */
export async function buildLexicon(
    inputDir: string,
    databasePath: string,
    options: BuildOptions = {},
): Promise<BuildStats> {
    const sources = await discoverLexicon(inputDir);
    const tempPath = `${databasePath}.tmp`;

    await rm(tempPath, { force: true });

    const stats: BuildStats = { locales: [], allowlist: 0 };

    try {
        {
            // Closed at the end of this block, before the rename.
            using db = new DatabaseSync(tempPath);

            db.exec(SCHEMA);
            db.exec(`PRAGMA user_version = ${SCHEMA_VERSION}`);

            for (const source of sources) {
                stats.locales.push(await importSource(db, inputDir, source));
            }

            if (options.allowlistPath) {
                stats.allowlist = await importAllowlist(db, options.allowlistPath);
            }
        }

        await rename(tempPath, databasePath);
    } catch (error) {
        await rm(tempPath, { force: true });
        throw error;
    }

    return stats;
}

//#endregion

//#region Importing

async function importAllowlist(db: DatabaseSync, filePath: string): Promise<number> {
    const insert = db.prepare(
        /* sql */ `INSERT OR IGNORE INTO allowlist (locale, word, normalized_word, note) VALUES (?, ?, ?, ?)`,
    );

    let count = 0;

    using tx = transaction(db);

    for await (const { locale, word, normalizedWord, note } of readAllowlist(filePath)) {
        count += Number(insert.run(locale, word, normalizedWord, note).changes);
    }

    tx.commit();

    return count;
}

async function importSource(
    db: DatabaseSync,
    inputDir: string,
    source: LexiconSourceFile,
): Promise<LocaleImportStats> {
    const checksum = sha256(await readFile(source.path));

    const { lastInsertRowid: sourceID } = db
        .prepare(/* sql */ `
            INSERT INTO lexicon_source
                (locale, file_name, original_tag, sha256, row_count, duplicate_count, imported_at)
            VALUES (?, ?, ?, ?, 0, 0, ?)
        `)
        .run(
            source.locale,
            relative(inputDir, source.path),
            source.originalTag,
            checksum,
            new Date().toISOString(),
        );

    const insert = db.prepare(/* sql */ `
        INSERT OR IGNORE INTO lexicon_entry
            (source_id, locale, word, normalized_word, tier, category_hex, category_bits)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    `);

    const result: LocaleImportStats = {
        locale: source.locale,
        rows: 0,
        duplicates: 0,
        byTier: { vulgar: 0, offensive: 0, sensitive: 0 },
    };

    let pending = 0;

    using tx = transaction(db);

    for await (const { line, fields } of readTSV(source.path, COLUMNS)) {
        const [tier, categoryHex, word] = fields as [string, string, string];

        if (!isTier(tier)) {
            throw new TSVError(source.path, line, "unknown tier");
        }

        if (!categoryHex || !/^[0-9a-f]+$/i.test(categoryHex)) {
            throw new TSVError(source.path, line, "category is not hexadecimal");
        }

        if (!word.trim()) {
            throw new TSVError(source.path, line, "empty word");
        }

        const { changes } = insert.run(
            sourceID,
            source.locale,
            word,
            normalize(word, source.locale),
            tier,
            categoryHex,
            Number.parseInt(categoryHex, 16),
        );

        if (changes) {
            result.rows++;
            result.byTier[tier]++;
        } else {
            result.duplicates++;
        }

        if (++pending >= BATCH_SIZE) {
            tx.checkpoint();
            pending = 0;
        }
    }

    db.prepare(/* sql */ `
        UPDATE lexicon_source
        SET row_count = ?, duplicate_count = ?
        WHERE id = ?
    `).run(result.rows, result.duplicates, sourceID);

    tx.commit();

    return result;
}

//#endregion
