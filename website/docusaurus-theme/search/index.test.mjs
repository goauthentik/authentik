import assert from "node:assert/strict";
import { mkdtempSync, readFileSync, rmSync, statSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";

import { FIXTURE_RECORDS } from "./fixtures.mjs";
import { headingsText, openIndexFile, slugWords, writeSearchIndex } from "./index.mjs";

const STAMP = { commit: "abc1234" };

/**
 * The first row of a statement as a plain object. `node:sqlite` returns rows without a
 * prototype, which a strict deep comparison distinguishes from an object literal.
 *
 * @param {import("./index.mjs").SQLiteDatabase} db
 * @param {string} sql
 */
function row(db, sql) {
    return { ...db.prepare(sql).get() };
}

test("writes a gzip SQLite file with the records, the vocabulary and the build row", () => {
    const scratch = mkdtempSync(join(tmpdir(), "ak-search-test-"));

    try {
        const output = join(scratch, "search-index.db.gz");
        const report = writeSearchIndex(FIXTURE_RECORDS, output, STAMP);

        assert.ok(report.gzipBytes < report.bytes);
        assert.equal(statSync(output).size, report.gzipBytes);
        assert.equal(report.changed, true);

        const db = openIndexFile(output);

        assert.deepEqual(row(db, "SELECT count(*) AS n FROM records"), {
            n: FIXTURE_RECORDS.length,
        });
        assert.deepEqual(
            row(db, `SELECT count(*) AS n FROM records_fts WHERE records_fts MATCH '"proxy"'`),
            { n: 2 },
        );
        assert.deepEqual(row(db, "SELECT documents FROM terms WHERE term = 'proxi'"), {
            documents: 2,
        });
        assert.deepEqual(
            row(db, `SELECT count(*) AS n FROM terms_trigram WHERE terms_trigram MATCH '"rox"'`),
            { n: 1 },
        );
        assert.deepEqual(row(db, "SELECT commit_sha, records FROM build"), {
            commit_sha: "abc1234",
            records: FIXTURE_RECORDS.length,
        });

        db.close();
    } finally {
        rmSync(scratch, { recursive: true, force: true });
    }
});

test("leaves an identical file untouched on a second write", () => {
    const scratch = mkdtempSync(join(tmpdir(), "ak-search-test-"));

    try {
        const output = join(scratch, "search-index.db.gz");

        writeSearchIndex(FIXTURE_RECORDS, output, STAMP);

        const before = readFileSync(output);
        const again = writeSearchIndex(FIXTURE_RECORDS, output, STAMP);

        assert.equal(again.changed, false);
        assert.ok(readFileSync(output).equals(before));
    } finally {
        rmSync(scratch, { recursive: true, force: true });
    }
});

test("indexes a page's slug words with its top-of-page headings only", () => {
    const url = "/add-secure-apps/flows-stages/";

    assert.equal(slugWords(url), "flows stages");
    assert.equal(
        headingsText({ hierarchy: ["Docs", "A page", null], url, anchor: "" }),
        "Docs\nA page\nflows stages",
    );
    assert.equal(
        headingsText({ hierarchy: ["Docs", "A page", "Part"], url, anchor: "part" }),
        "Docs\nA page\nPart",
    );
});

test("throws on a duplicate record id and on zero records", () => {
    const first = /** @type {(typeof FIXTURE_RECORDS)[number]} */ (FIXTURE_RECORDS[0]);

    assert.throws(
        () => writeSearchIndex([first, first], "/dev/null", STAMP),
        /duplicate record id/,
    );
    assert.throws(() => writeSearchIndex([], "/dev/null", STAMP), /zero records/);
});
