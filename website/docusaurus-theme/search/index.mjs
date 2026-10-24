/**
 * @file Writes search records to a gzip-compressed SQLite file.
 *   The FTS5 tables are external-content tables over `records` and `terms`, so each text is
 *   stored once. `porter unicode61` folds plurals, and a `trigram` table over the vocabulary
 *   supports typo correction against indexed terms rather than against page content.
 *   The whole file is republished with every site build, so the writer builds from scratch in a
 *   temporary file and compresses the result.
 */

import { copyFileSync, existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { gzipSync } from "node:zlib";

/**
 * @import { SearchRecord } from "./common.mjs";
 */

/**
 * Docusaurus loads a plugin through jiti, whose module resolver predates `node:sqlite`.
 * `process.getBuiltinModule` is a plain call the loader leaves alone.
 */
const { DatabaseSync } = /** @type {typeof import("node:sqlite")} */ (
    process.getBuiltinModule("node:sqlite")
);

/**
 * @typedef {import("node:sqlite").DatabaseSync} SQLiteDatabase
 */

/**
 * The index is read whole into memory in the browser, so the page size is tuned for in-memory
 * b-tree depth rather than for range requests.
 */
const PAGE_SIZE = 4096;

/**
 * Creates the tables and the FTS5 virtual tables, all empty.
 *
 * A record is identified by its rowid; the extractor's hash id serves the duplicate check at
 * build time and is not stored, since 32 random hex characters per row compress poorly.
 * `detail=column` keeps a term's count per column, which `bm25` ranks by, and drops its
 * positions, which only phrase and NEAR queries read; the index is about half the size.
 */
export const SCHEMA_SQL = `
CREATE TABLE records (
  site      TEXT NOT NULL,
  url       TEXT NOT NULL,
  anchor    TEXT NOT NULL,
  hierarchy TEXT NOT NULL,
  headings  TEXT NOT NULL,
  content   TEXT NOT NULL,
  level     INTEGER NOT NULL,
  position  INTEGER NOT NULL
);
CREATE VIRTUAL TABLE records_fts USING fts5(
  headings, content, content='records', content_rowid='rowid', tokenize='porter unicode61',
  detail=column
);
CREATE TABLE terms (term TEXT PRIMARY KEY, documents INTEGER NOT NULL);
CREATE VIRTUAL TABLE terms_trigram USING fts5(term, content='terms', content_rowid='rowid', tokenize='trigram');
CREATE TABLE build (commit_sha TEXT NOT NULL, records INTEGER NOT NULL);
`;

/**
 * Fills both FTS tables and the vocabulary after `records` holds every row.
 *
 * `fts5vocab` in `row` mode yields each term once with the number of rows that contain it.
 */
export const FILL_SQL = `
INSERT INTO records_fts (rowid, headings, content) SELECT rowid, headings, content FROM records;
CREATE VIRTUAL TABLE temp.vocab USING fts5vocab(main, records_fts, row);
INSERT INTO terms (term, documents) SELECT term, doc FROM temp.vocab WHERE length(term) >= 3;
DROP TABLE temp.vocab;
INSERT INTO terms_trigram (rowid, term) SELECT rowid, term FROM terms;
INSERT INTO records_fts (records_fts) VALUES ('optimize');
INSERT INTO terms_trigram (terms_trigram) VALUES ('optimize');
`;

/**
 * @typedef {object} BuildStamp
 * @property {string} commit The commit the index was built from, or the empty string.
 */

/**
 * The words of a page's last path segment, so `/add-secure-apps/flows-stages/` yields
 * `flows stages`.
 *
 * @param {string} url
 *
 * @returns {string}
 */
export function slugWords(url) {
    const segments = url.split("/");
    const last = segments.findLast((segment) => segment !== "") ?? "";

    return last.replace(/[-_]+/g, " ");
}

/**
 * The text of the headings column: the heading path, plus the page's slug words on its
 * top-of-page record.
 *
 * A page whose URL holds a term that its headings lack then matches that term in the weighted
 * column. Without the slug, BM25's length normalization ranks a short mention elsewhere above the
 * page's long body.
 *
 * @param {Pick<SearchRecord, "hierarchy" | "url" | "anchor">} record
 *
 * @returns {string}
 */
export function headingsText(record) {
    const names = record.hierarchy.filter((entry) => entry !== null);

    return (record.anchor === "" ? [...names, slugWords(record.url)] : names).join("\n");
}

/**
 * Inserts the rows into a database that already holds the schema.
 *
 * @param {SQLiteDatabase} db
 * @param {readonly SearchRecord[]} records
 * @param {BuildStamp} build
 */
export function insertRecords(db, records, build) {
    const insert = db.prepare("INSERT INTO records VALUES (?, ?, ?, ?, ?, ?, ?, ?)");

    db.exec("BEGIN");

    for (const record of records) {
        insert.run(
            record.site,
            record.url,
            record.anchor,
            JSON.stringify(record.hierarchy),
            headingsText(record),
            record.content,
            record.level,
            record.position,
        );
    }

    db.prepare("INSERT INTO build VALUES (?, ?)").run(build.commit, records.length);
    db.exec("COMMIT");
}

/**
 * An in-memory index built from the records, for tests and for the CLI's self-check.
 *
 * @param {readonly SearchRecord[]} records
 * @param {BuildStamp} [build]
 *
 * @returns {SQLiteDatabase}
 */
export function openMemoryIndex(records, build = { commit: "" }) {
    const db = new DatabaseSync(":memory:");

    db.exec(SCHEMA_SQL);
    insertRecords(db, records, build);
    db.exec(FILL_SQL);

    return db;
}

/**
 * Opens a gzip index file read-only, in memory.
 *
 * @param {string} path
 *
 * @returns {SQLiteDatabase}
 */
export function openIndexFile(path) {
    const { gunzipSync } = /** @type {typeof import("node:zlib")} */ (
        process.getBuiltinModule("node:zlib")
    );
    const bytes = gunzipSync(readFileSync(path));
    const scratch = mkdtempSync(join(tmpdir(), "ak-search-"));
    const plain = join(scratch, "search-index.db");

    try {
        copyBytes(bytes, plain);

        return new DatabaseSync(plain, { readOnly: true });
    } finally {
        // SQLite keeps its own handle; the directory entry can go.
        rmSync(scratch, { recursive: true, force: true });
    }
}

/**
 * @param {Uint8Array} bytes
 * @param {string} path
 */
function copyBytes(bytes, path) {
    const { writeFileSync } = /** @type {typeof import("node:fs")} */ (
        process.getBuiltinModule("node:fs")
    );

    writeFileSync(path, bytes);
}

/**
 * @typedef {object} WriteReport
 * @property {number} bytes The size of the SQLite file before compression.
 * @property {number} gzipBytes The size of the file written.
 * @property {boolean} changed Whether the file's bytes differ from what was there before. The
 *   dev server watches `static/`, so an unchanged file is left untouched.
 */

/**
 * Write the records to `output` as a gzip-compressed SQLite file.
 *
 * @param {readonly SearchRecord[]} records
 * @param {string} output
 * @param {BuildStamp} build
 *
 * @returns {WriteReport}
 */
export function writeSearchIndex(records, output, build) {
    if (!records.length) {
        throw new Error("search: the build produced zero records");
    }

    /** @type {Map<string, string>} */
    const seen = new Map();

    for (const record of records) {
        const earlier = seen.get(record.id);

        if (earlier) {
            throw new Error(
                `search: duplicate record id ${record.id} on ${record.url} and ${earlier}`,
            );
        }

        seen.set(record.id, record.url);
    }

    const scratch = mkdtempSync(join(tmpdir(), "ak-search-"));
    const plain = join(scratch, "search-index.db");

    try {
        const db = new DatabaseSync(plain);

        db.exec(`PRAGMA page_size = ${PAGE_SIZE};`);
        db.exec(SCHEMA_SQL);
        insertRecords(db, records, build);
        db.exec(FILL_SQL);
        db.exec("VACUUM");
        db.close();

        const bytes = readFileSync(plain);
        const compressed = gzipSync(bytes, { level: 9 });
        const changed = !(existsSync(output) && readFileSync(output).equals(compressed));

        if (changed) {
            mkdirSync(dirname(output), { recursive: true });

            const staged = join(scratch, "search-index.db.gz");

            copyBytes(compressed, staged);
            copyFileSync(staged, output);
        }

        return { bytes: bytes.byteLength, gzipBytes: compressed.byteLength, changed };
    } finally {
        rmSync(scratch, { recursive: true, force: true });
    }
}
