/**
 * @file Writes the search records as a SQL script for Cloudflare D1, the hosted copy of the
 *   index that the search worker queries.
 *   The script fills one slot's tables and then flips the pointer, so `wrangler d1 execute
 *   --file` applies it without a reader ever seeing a half-written index. D1 refuses the
 *   `fts5vocab` module the local writer uses for the vocabulary, so the vocabulary is computed
 *   here with `node:sqlite` and uploaded as rows. The FTS table holds its own text rather than
 *   reading `records`, so a slot's tables depend on nothing outside the slot.
 */

import { mkdirSync, writeFileSync } from "node:fs";
import { dirname } from "node:path";

import { INDEX_SLOTS, SLOT_POINTER_TABLE } from "./common.mjs";
import { headingsText, openMemoryIndex } from "./index.mjs";

/**
 * @import { IndexSlot, SearchRecord } from "./common.mjs";
 * @import { BuildStamp } from "./index.mjs";
 */

/**
 * The most characters one statement holds. D1 refuses a statement over 100 KB.
 */
const MAX_STATEMENT_LENGTH = 60_000;

/**
 * @param {string} value
 *
 * @returns {string}
 */
function quote(value) {
    return `'${value.replaceAll("'", "''")}'`;
}

/**
 * `INSERT` statements for the rows, each under {@link MAX_STATEMENT_LENGTH}.
 *
 * @param {string} head `INSERT INTO table (columns) VALUES`
 * @param {readonly string[]} rows Each a parenthesized value list.
 *
 * @returns {string[]}
 */
function insertStatements(head, rows) {
    /** @type {string[]} */
    const statements = [];

    /** @type {string[]} */
    let batch = [];
    let length = head.length;

    for (const row of rows) {
        if (batch.length && length + row.length + 2 > MAX_STATEMENT_LENGTH) {
            statements.push(`${head} ${batch.join(", ")};`);
            batch = [];
            length = head.length;
        }

        batch.push(row);
        length += row.length + 2;
    }

    if (batch.length) {
        statements.push(`${head} ${batch.join(", ")};`);
    }

    return statements;
}

/**
 * The statements that fill `slot` with the records and make it current.
 *
 * @param {readonly SearchRecord[]} records
 * @param {IndexSlot} slot
 * @param {BuildStamp} build
 *
 * @returns {string[]}
 */
export function d1Statements(records, slot, build) {
    if (!INDEX_SLOTS.includes(slot)) {
        throw new Error(
            `search: unknown slot "${slot}"; expected one of ${INDEX_SLOTS.join(", ")}`,
        );
    }

    if (!records.length) {
        throw new Error("search: the build produced zero records");
    }

    const table = (/** @type {(typeof import("./common.mjs").SLOT_TABLES)[number]} */ name) =>
        `${name}_${slot}`;

    /** @type {string[]} */
    const statements = [
        `DROP TABLE IF EXISTS ${table("records_fts")};`,
        `DROP TABLE IF EXISTS ${table("terms_trigram")};`,
        `DROP TABLE IF EXISTS ${table("records")};`,
        `DROP TABLE IF EXISTS ${table("terms")};`,
        `DROP TABLE IF EXISTS ${table("build")};`,
        `CREATE TABLE ${table("records")} (site TEXT NOT NULL, url TEXT NOT NULL, anchor TEXT NOT NULL, hierarchy TEXT NOT NULL, headings TEXT NOT NULL, content TEXT NOT NULL, level INTEGER NOT NULL, position INTEGER NOT NULL);`,
        `CREATE VIRTUAL TABLE ${table("records_fts")} USING fts5(headings, content, tokenize='porter unicode61', detail=column);`,
        `CREATE TABLE ${table("terms")} (term TEXT PRIMARY KEY, documents INTEGER NOT NULL);`,
        `CREATE VIRTUAL TABLE ${table("terms_trigram")} USING fts5(term, content='${table("terms")}', content_rowid='rowid', tokenize='trigram');`,
        `CREATE TABLE ${table("build")} (commit_sha TEXT NOT NULL, records INTEGER NOT NULL);`,
    ];

    /** @type {string[]} */
    const recordRows = [];

    /** @type {string[]} */
    const ftsRows = [];

    records.forEach((record, index) => {
        const headings = headingsText(record);

        recordRows.push(
            `(${index + 1}, ${quote(record.site)}, ${quote(record.url)}, ${quote(record.anchor)}, ${quote(JSON.stringify(record.hierarchy))}, ${quote(headings)}, ${quote(record.content)}, ${record.level}, ${record.position})`,
        );
        ftsRows.push(`(${index + 1}, ${quote(headings)}, ${quote(record.content)})`);
    });

    statements.push(
        ...insertStatements(
            `INSERT INTO ${table("records")} (rowid, site, url, anchor, hierarchy, headings, content, level, position) VALUES`,
            recordRows,
        ),
        ...insertStatements(
            `INSERT INTO ${table("records_fts")} (rowid, headings, content) VALUES`,
            ftsRows,
        ),
    );

    const local = openMemoryIndex(records, build);
    const terms = /** @type {{ term: string; documents: number }[]} */ (
        local.prepare("SELECT term, documents FROM terms ORDER BY rowid").all()
    );

    local.close();

    statements.push(
        ...insertStatements(
            `INSERT INTO ${table("terms")} (term, documents) VALUES`,
            terms.map((row) => `(${quote(row.term)}, ${row.documents})`),
        ),
        `INSERT INTO ${table("terms_trigram")} (rowid, term) SELECT rowid, term FROM ${table("terms")};`,
        `INSERT INTO ${table("records_fts")} (${table("records_fts")}) VALUES ('optimize');`,
        `INSERT INTO ${table("terms_trigram")} (${table("terms_trigram")}) VALUES ('optimize');`,
        `INSERT INTO ${table("build")} VALUES (${quote(build.commit)}, ${records.length});`,
        `CREATE TABLE IF NOT EXISTS ${SLOT_POINTER_TABLE} (slot TEXT NOT NULL);`,
        `DELETE FROM ${SLOT_POINTER_TABLE};`,
        `INSERT INTO ${SLOT_POINTER_TABLE} VALUES (${quote(slot)});`,
    );

    return statements;
}

/**
 * The SQL script that fills `slot` with the records and makes it current, one statement per
 * line. A quoted value may itself span lines; the statement splitter reads quotes.
 *
 * @param {readonly SearchRecord[]} records
 * @param {IndexSlot} slot
 * @param {BuildStamp} build
 *
 * @returns {string}
 */
export function d1Script(records, slot, build) {
    return `${d1Statements(records, slot, build).join("\n")}\n`;
}

/**
 * Write the D1 script for `slot` to `output`.
 *
 * @param {readonly SearchRecord[]} records
 * @param {string} output
 * @param {IndexSlot} slot
 * @param {BuildStamp} build
 *
 * @returns {{ bytes: number; statements: number }}
 */
export function writeD1Script(records, output, slot, build) {
    const statements = d1Statements(records, slot, build);
    const script = `${statements.join("\n")}\n`;

    mkdirSync(dirname(output), { recursive: true });
    writeFileSync(output, script);

    return { bytes: Buffer.byteLength(script), statements: statements.length };
}
