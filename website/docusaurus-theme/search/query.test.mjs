import assert from "node:assert/strict";
import { test } from "node:test";

import { SNIPPET_LENGTH } from "./common.mjs";
import { FIXTURE_RECORDS } from "./fixtures.mjs";
import { openMemoryIndex } from "./index.mjs";
import {
    collapseBySection,
    correctTokens,
    damerauLevenshtein,
    HITS_PER_PAGE,
    lexicalRows,
    matchExpression,
    queryTokens,
    search,
    snippet,
    surfaceWord,
} from "./query.mjs";

/**
 * @import { SearchRecord } from "./common.mjs";
 * @import { SearchDatabase, SQLValue } from "./query.mjs";
 */

const memory = openMemoryIndex(FIXTURE_RECORDS);

/** @type {SearchDatabase} */
const db = {
    async query(sql, parameters = []) {
        const bound = /** @type {SQLValue[]} */ (Array.from(parameters));

        return /** @type {Record<string, SQLValue>[]} */ (memory.prepare(sql).all(...bound));
    },
};

//#region Lexical

test("queryTokens splits the text where the tokenizer does", () => {
    assert.deepEqual(queryTokens('  tier-1  "regression" -- *** 2025.8 '), [
        "tier",
        "1",
        "regression",
        "2025",
        "8",
    ]);
});

test("matchExpression quotes every token and marks the last one as a prefix", () => {
    assert.equal(matchExpression(["proxy", "prov"]), '"proxy" "prov"*');
    assert.equal(matchExpression(['say"hi']), '"say""hi"*');
    assert.equal(matchExpression([]), null);
});

/**
 * A query result identifies a record by its rowid, which is the fixture's position plus one.
 *
 * @param {string} fixtureID
 */
function rowID(fixtureID) {
    return String(FIXTURE_RECORDS.findIndex((record) => record.id === fixtureID) + 1);
}

test("lexicalRows ranks a heading match above a content match", async () => {
    const rows = await lexicalRows(db, ["proxy"]);

    assert.deepEqual(
        rows.map((row) => row.id),
        ["proxy-top", "proxy-section"].map(rowID),
    );
});

test("lexicalRows ranks a page whose heading matches above a table row whose name matches", async () => {
    assert.deepEqual(
        (await lexicalRows(db, ["grafana"])).map((row) => row.id),
        ["grafana-docs", "grafana-page", "row"].map(rowID),
    );
});

test("lexicalRows matches the last token as a prefix and a singular against a plural", async () => {
    assert.ok(
        (await lexicalRows(db, ["forward", "au"]))
            .map((row) => row.id)
            .includes(rowID("proxy-section")),
    );
    assert.deepEqual(
        (await lexicalRows(db, ["outpost"])).map((row) => row.id),
        [rowID("outposts")],
    );
});

test("lexicalRows returns rows or an empty list for FTS5 syntax in the text", async () => {
    for (const text of ['"', "a AND", "NEAR(a b)", "col:value", "a* OR", "(", "a - b", "^a", "-"]) {
        assert.ok(Array.isArray(await lexicalRows(db, queryTokens(text))), text);
    }
});

//#endregion

//#region Correction

test("damerauLevenshtein counts a transposition as one edit", () => {
    assert.equal(damerauLevenshtein("proxy", "proxy"), 0);
    assert.equal(damerauLevenshtein("porxy", "proxy"), 1);
    assert.equal(damerauLevenshtein("prxy", "proxy"), 1);
    assert.equal(damerauLevenshtein("abc", "xyz"), 3);
});

test("correctTokens replaces a transposed token with the vocabulary term", async () => {
    // The vocabulary holds porter stems, so `blueprints` corrects to `blueprint`.
    assert.deepEqual(await correctTokens(db, ["bluepirnts"]), ["blueprint"]);
    assert.deepEqual(await correctTokens(db, ["grafana", "blueprnts"]), ["grafana", "blueprint"]);
});

test("correctTokens cannot reach a term that shares no three-character window with the token", async () => {
    // A transposition inside a five-letter word changes every trigram.
    assert.equal(await correctTokens(db, ["porxy"]), null);
});

test("correctTokens leaves a token alone when no term is close or it is too short", async () => {
    assert.equal(await correctTokens(db, ["zzzzzzz"]), null);
    assert.equal(await correctTokens(db, ["ab"]), null);
});

//#endregion

//#region Snippet

test("snippet returns short content whole with the range of each token match", () => {
    assert.deepEqual(snippet("The proxy reads a Proxy grammar.", ["proxy"]), {
        snippet: "The proxy reads a Proxy grammar.",
        highlights: [
            [4, 9],
            [18, 23],
        ],
    });
});

test("snippet windows long content around the first match and stays within the length", () => {
    const content = `${"lorem ".repeat(100)}needle ${"ipsum ".repeat(100)}`;
    const result = snippet(content, ["needle"]);
    const [start, end] = /** @type {[number, number]} */ (result.highlights[0]);

    assert.ok(result.snippet.length <= SNIPPET_LENGTH);
    assert.equal(result.snippet.slice(start, end), "needle");
});

test("snippet returns the start of the content when no token occurs in it", () => {
    assert.deepEqual(snippet("a".repeat(500), ["zzz"]), {
        snippet: "a".repeat(SNIPPET_LENGTH),
        highlights: [],
    });
    assert.deepEqual(snippet("", ["x"]), { snippet: "", highlights: [] });
});

//#endregion

//#region Search

test("search returns one hit per section, so a page's matching sections each appear", async () => {
    const response = await search(db, "proxy");

    assert.deepEqual(
        response.hits
            .filter((hit) => hit.url === "/add-secure-apps/providers/proxy/")
            .map((hit) => hit.anchor),
        ["", "forward-auth"],
    );
    assert.equal(response.hits[0]?.hierarchy[1], "Proxy provider");
    assert.equal(response.corrected, null);
});

test("search corrects a misspelled token and reports the corrected text as a word from the hits", async () => {
    const response = await search(db, "bluepirnts");

    assert.equal(response.corrected, "blueprints");
    assert.equal(response.hits[0]?.url, "/customize/blueprints/");
});

test("search ranks the served site's records above another site's equal matches", async () => {
    // Without a site, the documentation page's shorter body ranks first.
    assert.equal((await search(db, "grafana")).hits[0]?.url, "/install-config/grafana/");
    assert.equal(
        (await search(db, "grafana", undefined, "Integrations")).hits[0]?.url,
        "https://integrations.goauthentik.io/monitoring/grafana/",
    );
});

test("search keeps a hit's site so the modal can label another site's page", async () => {
    const response = await search(db, "grafana", undefined, "Integrations");

    assert.equal(response.hits[0]?.site, "Integrations");
    assert.equal(response.hits[0]?.url, "https://integrations.goauthentik.io/monitoring/grafana/");
});

test("search runs no query for text without a letter or digit, and honors the limit", async () => {
    let queries = 0;

    /** @type {SearchDatabase} */
    const counting = {
        query(sql, parameters) {
            queries++;

            return db.query(sql, parameters);
        },
    };

    assert.deepEqual((await search(counting, "-- ***")).hits, []);
    assert.equal(queries, 0);
    assert.equal((await search(db, "the", 1)).hits.length, 1);
    assert.deepEqual(await search(db, "zzzzzzz"), { query: "zzzzzzz", corrected: null, hits: [] });
});

/**
 * @param {string} url
 * @param {string} anchor
 *
 * @returns {SearchRecord}
 */
function record(url, anchor) {
    return {
        id: `${url}#${anchor}`,
        site: "Documentation",
        url,
        anchor,
        hierarchy: ["Docs", url, null, null, null, null, null],
        content: "",
        level: 1,
        position: 0,
    };
}

test("collapseBySection keeps one hit per section and at most three per page, in rank order", () => {
    const ranked = [
        record("/a", ""),
        record("/a", "one"),
        record("/a", "one"),
        record("/a", "two"),
        record("/a", "three"),
        record("/b", ""),
    ];

    assert.deepEqual(
        collapseBySection(ranked, 10).map((hit) => `${hit.url}#${hit.anchor}`),
        ["/a#", "/a#one", "/a#two", "/b#"],
    );
    assert.equal(HITS_PER_PAGE, 3);
});

test("surfaceWord picks the most frequent hit word that begins with the stem", () => {
    const rows = [
        { ...record("/x", ""), content: "Provisioning a provider. Provisioning again." },
        { ...record("/y", ""), content: "The provisioner." },
    ];

    assert.equal(surfaceWord("provision", rows), "provisioning");
    assert.equal(surfaceWord("zzz", [record("/x", "")]), "zzz");
});

//#endregion
