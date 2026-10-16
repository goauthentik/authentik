/**
 * @file One query against the index: the lexical rows, a vocabulary correction when they are
 *   empty, then one hit per section with a cap per page, each with its snippet.
 *   This module runs in the browser and under `node --test`, so it imports nothing from Node.
 *   Every token of the user's text becomes a quoted FTS5 string, so the text never reaches the
 *   FTS5 parser as an operator, a column filter or a bare `*`.
 */

import { SNIPPET_LENGTH, TABLE_ROW_LEVEL } from "./common.mjs";

/**
 * @import { SearchRecord, SearchResponse } from "./common.mjs";
 */

/**
 * A value SQLite can bind to a statement parameter or return in a result column.
 *
 * @typedef {string | number | bigint | Uint8Array | null} SQLValue
 */

/**
 * The one interface the query code needs. The browser passes the worker client; the tests pass
 * an adapter over `node:sqlite`.
 *
 * @typedef {object} SearchDatabase
 * @property {(
 *     sql: string,
 *     parameters?: readonly SQLValue[],
 * ) => Promise<Record<string, SQLValue>[]>} query
 */

//#region Lexical

/**
 * The hit count a query returns when the caller names no limit.
 */
export const DEFAULT_LIMIT = 8;

/**
 * The most hits a caller may request.
 */
export const MAX_LIMIT = 20;

/**
 * The most sections of one page that a response holds, so one long page cannot fill the list.
 */
export const HITS_PER_PAGE = 3;

/**
 * The most rows one lexical query reads, before the rows collapse to one hit per section.
 */
export const LEXICAL_ROWS = 40;

/**
 * `bm25` column weights: a match in the heading path counts ten times a match in the content.
 */
const HEADINGS_WEIGHT = 10;
const CONTENT_WEIGHT = 1;

/**
 * The share of its `bm25` score a table row keeps.
 *
 * A row's headings column is a few words, so its score is large under length normalization. The
 * factor keeps a matching page or section heading above a matching option name.
 */
const TABLE_ROW_SCORE_FACTOR = 0.5;

/**
 * The share of its `bm25` score a record on another site keeps.
 *
 * A reader searching the documentation site wants its pages first; an integration guide or an
 * API operation with the same words still lists, below them.
 */
const OTHER_SITE_SCORE_FACTOR = 0.85;

const LEXICAL_SQL = `SELECT r.id, r.site, r.url, r.anchor, r.hierarchy, r.content, r.level, r.position
 FROM records_fts JOIN records r ON r.rowid = records_fts.rowid
 WHERE records_fts MATCH ?
 ORDER BY bm25(records_fts, ${HEADINGS_WEIGHT}, ${CONTENT_WEIGHT})
   * (CASE WHEN r.level = ${TABLE_ROW_LEVEL} THEN ${TABLE_ROW_SCORE_FACTOR} ELSE 1 END)
   * (CASE WHEN r.site = ? THEN 1 ELSE ${OTHER_SITE_SCORE_FACTOR} END), r.level, r.position
 LIMIT ${LEXICAL_ROWS}`;

/**
 * @param {string} text
 *
 * @returns {string}
 */
export function quoteTerm(text) {
    return `"${text.replaceAll('"', '""')}"`;
}

/**
 * The whitespace-separated parts of the text that the tokenizer can index: those with a letter
 * or a digit.
 *
 * @param {string} text
 *
 * @returns {string[]}
 */
export function queryTokens(text) {
    return text.split(/\s+/).filter((token) => /[\p{L}\p{N}]/u.test(token));
}

/**
 * The FTS5 expression for the tokens: each quoted, the last one as a prefix.
 *
 * @param {readonly string[]} tokens
 *
 * @returns {string | null}
 */
export function matchExpression(tokens) {
    if (!tokens.length) return null;

    return tokens
        .map((token, index) =>
            index === tokens.length - 1 ? `${quoteTerm(token)}*` : quoteTerm(token),
        )
        .join(" ");
}

/**
 * @param {SearchDatabase} db
 * @param {readonly string[]} tokens
 * @param {string} [site] The label of the site being served. A record on another site keeps
 *   {@link OTHER_SITE_SCORE_FACTOR} of its score. The empty string ranks every site alike.
 *
 * @returns {Promise<SearchRecord[]>}
 */
export async function lexicalRows(db, tokens, site = "") {
    const expression = matchExpression(tokens);

    if (!expression) return [];

    const rows = await db.query(LEXICAL_SQL, [expression, site]);

    return rows.map((row) => {
        const record = /** @type {Omit<SearchRecord, "hierarchy"> & { hierarchy: string }} */ (
            /** @type {unknown} */ (row)
        );

        return { ...record, hierarchy: JSON.parse(record.hierarchy) };
    });
}

//#endregion

//#region Correction

const MIN_TOKEN = 3;
const CANDIDATES = 10;
const SHORT_TOKEN = 6;
const MAX_EDITS = 2;
const MAX_EDITS_SHORT = 1;
const TRIGRAM = 3;

const CANDIDATE_SQL = `SELECT t.term, t.documents FROM terms_trigram JOIN terms t ON t.rowid = terms_trigram.rowid
 WHERE terms_trigram MATCH ? ORDER BY bm25(terms_trigram), t.documents DESC LIMIT ${CANDIDATES}`;

/**
 * Edit distance counting insertions, deletions, substitutions and adjacent transpositions as one
 * edit each.
 *
 * @param {string} a
 * @param {string} b
 *
 * @returns {number}
 */
export function damerauLevenshtein(a, b) {
    const rows = a.length + 1;
    const cols = b.length + 1;

    /** @type {number[][]} */
    const d = Array.from({ length: rows }, (_row, i) =>
        Array.from({ length: cols }, (_column, j) => (i === 0 ? j : j === 0 ? i : 0)),
    );

    for (let i = 1; i < rows; i++) {
        const row = /** @type {number[]} */ (d[i]);
        const above = /** @type {number[]} */ (d[i - 1]);

        for (let j = 1; j < cols; j++) {
            const cost = a[i - 1] === b[j - 1] ? 0 : 1;

            row[j] = Math.min(
                /** @type {number} */ (above[j]) + 1,
                /** @type {number} */ (row[j - 1]) + 1,
                /** @type {number} */ (above[j - 1]) + cost,
            );

            if (i > 1 && j > 1 && a[i - 1] === b[j - 2] && a[i - 2] === b[j - 1]) {
                const transposed = /** @type {number[]} */ (d[i - 2]);

                row[j] = Math.min(
                    /** @type {number} */ (row[j]),
                    /** @type {number} */ (transposed[j - 2]) + 1,
                );
            }
        }
    }

    return /** @type {number} */ (/** @type {number[]} */ (d[rows - 1])[cols - 1]);
}

/**
 * @param {string} token
 *
 * @returns {string | null}
 */
function trigramExpression(token) {
    /** @type {Set<string>} */
    const windows = new Set();
    const characters = [...token.toLowerCase()];

    for (let start = 0; start + TRIGRAM <= characters.length; start++) {
        windows.add(characters.slice(start, start + TRIGRAM).join(""));
    }

    return windows.size ? [...windows].map(quoteTerm).join(" OR ") : null;
}

/**
 * The nearest vocabulary term to a token, or `null` when the token is in the vocabulary or no
 * term is close enough.
 *
 * A term that shares no three-character window with the token is never proposed, so a
 * transposition inside a word of four letters or fewer is not corrected.
 *
 * @param {SearchDatabase} db
 * @param {string} token
 *
 * @returns {Promise<string | null>}
 */
async function correctToken(db, token) {
    // Lengths count code points, as the trigram windows do.
    const length = [...token].length;

    if (length < MIN_TOKEN) return null;

    const expression = trigramExpression(token);

    if (!expression) return null;

    const candidates = await db.query(CANDIDATE_SQL, [expression]);
    const lower = token.toLowerCase();
    const allowed = length < SHORT_TOKEN ? MAX_EDITS_SHORT : MAX_EDITS;

    /** @type {{ term: string; distance: number; documents: number } | null} */
    let best = null;

    for (const candidate of candidates) {
        const term = String(candidate.term);
        const documents = Number(candidate.documents);
        const distance = damerauLevenshtein(lower, term);

        if (distance === 0) return null;

        if (distance > allowed) continue;

        // Among terms equally close, the one more pages use is the likelier intent.
        if (
            !best ||
            distance < best.distance ||
            (distance === best.distance && documents > best.documents)
        ) {
            best = { term, distance, documents };
        }
    }

    return best?.term ?? null;
}

/**
 * The tokens with each correctable token replaced by its nearest vocabulary term, or `null` when
 * no token changed.
 *
 * @param {SearchDatabase} db
 * @param {readonly string[]} tokens
 *
 * @returns {Promise<string[] | null>}
 */
export async function correctTokens(db, tokens) {
    const corrected = await Promise.all(
        tokens.map(async (token) => (await correctToken(db, token)) ?? token),
    );

    return corrected.some((token, index) => token !== tokens[index]) ? corrected : null;
}

//#endregion

//#region Snippet

/**
 * Characters of context kept before the first match.
 */
const LEAD = 40;

/**
 * @param {readonly string[]} tokens
 *
 * @returns {string[]}
 */
function needles(tokens) {
    return tokens
        .map((token) => token.replace(/^[^\p{L}\p{N}]+|[^\p{L}\p{N}]+$/gu, "").toLowerCase())
        .filter((token) => token !== "");
}

/**
 * The excerpt a hit displays, with the character ranges that matched a query token.
 *
 * The match here is a case-insensitive substring search. It marks what to emphasize and takes no
 * part in ranking.
 *
 * @param {string} content
 * @param {readonly string[]} tokens
 *
 * @returns {{ snippet: string; highlights: [start: number, end: number][] }}
 */
export function snippet(content, tokens) {
    const lower = content.toLowerCase();
    const terms = needles(tokens);
    const first = terms.map((term) => lower.indexOf(term)).filter((index) => index >= 0);
    const anchor = first.length ? Math.min(...first) : 0;
    const start = Math.max(0, Math.min(anchor - LEAD, content.length - SNIPPET_LENGTH));
    const text = content.slice(start, start + SNIPPET_LENGTH);
    const window = text.toLowerCase();

    /** @type {[number, number][]} */
    const highlights = [];

    for (const term of terms) {
        for (
            let index = window.indexOf(term);
            index >= 0;
            index = window.indexOf(term, index + term.length)
        ) {
            highlights.push([index, index + term.length]);
        }
    }

    highlights.sort((a, b) => a[0] - b[0]);

    return { snippet: text, highlights };
}

//#endregion

//#region Search

/**
 * One hit per section, at most {@link HITS_PER_PAGE} per page, in rank order.
 *
 * @param {readonly SearchRecord[]} ranked
 * @param {number} limit
 *
 * @returns {SearchRecord[]}
 */
export function collapseBySection(ranked, limit) {
    /** @type {Set<string>} */
    const sections = new Set();

    /** @type {Map<string, number>} */
    const perPage = new Map();

    /** @type {SearchRecord[]} */
    const kept = [];

    for (const record of ranked) {
        const page = `${record.site}\n${record.url}`;
        const section = `${page}#${record.anchor}`;
        const onPage = perPage.get(page) ?? 0;

        if (sections.has(section) || onPage >= HITS_PER_PAGE) continue;

        sections.add(section);
        perPage.set(page, onPage + 1);
        kept.push(record);

        if (kept.length === limit) break;
    }

    return kept;
}

/**
 * The word the index text shows for a corrected token.
 *
 * The vocabulary holds porter stems. A correction such as `authent` is shown as the most frequent
 * hit word that begins with it. A stem with no such word is shown as itself.
 *
 * @param {string} stem
 * @param {readonly SearchRecord[]} rows
 *
 * @returns {string}
 */
export function surfaceWord(stem, rows) {
    const lower = stem.toLowerCase();

    /** @type {Map<string, number>} */
    const counts = new Map();

    for (const row of rows) {
        const text = `${row.hierarchy.filter((entry) => entry !== null).join(" ")} ${row.content}`;

        for (const word of text.match(/[\p{L}\p{N}'-]+/gu) ?? []) {
            const folded = word.toLowerCase();

            if (folded.startsWith(lower)) {
                counts.set(folded, (counts.get(folded) ?? 0) + 1);
            }
        }
    }

    let best = stem;
    let bestCount = 0;

    for (const [word, count] of counts) {
        if (count > bestCount || (count === bestCount && word.length < best.length)) {
            best = word;
            bestCount = count;
        }
    }

    return best;
}

/**
 * Run one query.
 *
 * @param {SearchDatabase} db
 * @param {string} text
 * @param {number} [limit]
 * @param {string} [site] The label of the site being served, whose records rank first.
 *
 * @returns {Promise<SearchResponse>}
 */
export async function search(db, text, limit = DEFAULT_LIMIT, site = "") {
    const bounded = Math.min(Math.max(1, Math.trunc(limit)), MAX_LIMIT);
    const typed = queryTokens(text);
    let tokens = typed;

    if (!tokens.length) return { query: text, corrected: null, hits: [] };

    let rows = await lexicalRows(db, tokens, site);

    /** @type {string[] | null} */
    let replacement = null;

    if (!rows.length) {
        replacement = await correctTokens(db, tokens);

        if (replacement) {
            tokens = replacement;
            rows = await lexicalRows(db, tokens, site);
        }
    }

    const hits = collapseBySection(rows, bounded).map((record) => ({
        site: record.site,
        url: record.url,
        anchor: record.anchor,
        hierarchy: record.hierarchy,
        ...snippet(record.content, tokens),
    }));

    const corrected =
        replacement && hits.length
            ? replacement
                  .map((token, index) =>
                      token === typed[index] ? token : surfaceWord(token, rows),
                  )
                  .join(" ")
            : null;

    return { query: text, corrected, hits };
}

//#endregion
