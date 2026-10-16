import assert from "node:assert/strict";
import { test } from "node:test";

import { nextSlot, rewriteForSlot, SLOT_POINTER_TABLE } from "./common.mjs";
import { d1Script, d1Statements } from "./d1.mjs";
import { FIXTURE_RECORDS } from "./fixtures.mjs";
import { search } from "./query.mjs";

/**
 * @import { SearchDatabase, SQLValue } from "./query.mjs";
 */

const { DatabaseSync } = /** @type {typeof import("node:sqlite")} */ (
    process.getBuiltinModule("node:sqlite")
);

/**
 * A database holding the script's result, read through the slot rewrite the worker applies.
 *
 * @param {string} script
 * @param {import("./common.mjs").IndexSlot} slot
 */
function applied(script, slot) {
    const db = new DatabaseSync(":memory:");

    db.exec(script);

    /** @type {SearchDatabase} */
    const adapter = {
        async query(sql, parameters = []) {
            const bound = /** @type {SQLValue[]} */ (Array.from(parameters));

            return /** @type {Record<string, SQLValue>[]} */ (
                db.prepare(rewriteForSlot(sql, slot)).all(...bound)
            );
        },
    };

    return { db, adapter };
}

test("rewriteForSlot renames every slot table and leaves the rest of the SQL alone", () => {
    assert.equal(
        rewriteForSlot(
            "SELECT r.id FROM records_fts JOIN records r ON r.rowid = records_fts.rowid WHERE records_fts MATCH ? ORDER BY bm25(records_fts, 10, 1)",
            "b",
        ),
        "SELECT r.id FROM records_fts_b JOIN records_b r ON r.rowid = records_fts_b.rowid WHERE records_fts_b MATCH ? ORDER BY bm25(records_fts_b, 10, 1)",
    );
    assert.equal(
        rewriteForSlot(
            "SELECT t.term FROM terms_trigram JOIN terms t ON t.rowid = terms_trigram.rowid",
            "a",
        ),
        "SELECT t.term FROM terms_trigram_a JOIN terms_a t ON t.rowid = terms_trigram_a.rowid",
    );
    assert.equal(nextSlot("a"), "b");
    assert.equal(nextSlot("b"), "a");
});

test("the D1 script fills a slot that answers the same queries as the local index", async () => {
    const script = d1Script(FIXTURE_RECORDS, "b", { commit: "abc1234" });
    const { db, adapter } = applied(script, "b");

    assert.deepEqual(
        { ...db.prepare(`SELECT slot FROM ${SLOT_POINTER_TABLE}`).get() },
        { slot: "b" },
    );
    assert.deepEqual(
        { ...db.prepare("SELECT commit_sha, records FROM build_b").get() },
        {
            commit_sha: "abc1234",
            records: FIXTURE_RECORDS.length,
        },
    );

    const response = await search(adapter, "proxy");

    assert.deepEqual(
        response.hits
            .filter((hit) => hit.url === "/add-secure-apps/providers/proxy/")
            .map((hit) => hit.anchor),
        ["", "forward-auth"],
    );

    // The vocabulary was computed locally and uploaded as rows.
    assert.equal((await search(adapter, "bluepirnts")).corrected, "blueprints");

    db.close();
});

test("the D1 script keeps every statement under the 100 KB limit and flips the pointer last", () => {
    const long = FIXTURE_RECORDS.map((record, index) => ({
        ...record,
        id: `${record.id}-${index}`,
        content: "word ".repeat(700),
    }));
    const statements = d1Statements([...long, ...long, ...long, ...long, ...long], "a", {
        commit: "",
    });

    assert.ok(statements.every((statement) => statement.length < 100_000));
    assert.ok(
        statements.filter((statement) => statement.startsWith("INSERT INTO records_a ")).length > 1,
    );
    assert.equal(statements.at(-1), `INSERT INTO ${SLOT_POINTER_TABLE} VALUES ('a');`);
});
