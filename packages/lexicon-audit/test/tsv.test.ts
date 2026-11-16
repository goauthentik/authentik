import { join } from "node:path";

import { collect, fixture } from "#test/helpers";
import { TSVError, readTSV } from "#translation/tsv";

import { describe, expect, it } from "vitest";

const COLUMNS = ["tier", "category", "word"];

describe("readTSV", () => {
    it("reads rows after the header without losing the first one", async () => {
        const dir = await fixture({
            "a.tsv": "tier\tcategory\tword\nvulgar\t00000\tbrillig\noffensive\t00200\tslithy\n",
        });
        const rows = await collect(readTSV(join(dir, "a.tsv"), COLUMNS));

        expect(rows).toEqual([
            { line: 2, fields: ["vulgar", "00000", "brillig"] },
            { line: 3, fields: ["offensive", "00200", "slithy"] },
        ]);
    });

    it("handles a BOM, CRLF line endings, blank lines and non-Latin text", async () => {
        const dir = await fixture({
            "a.tsv":
                "﻿tier\tcategory\tword\r\n\r\nvulgar\t00000\tтоки\r\n\r\nsensitive\t00400\tborogove\u{1F409}\r\n",
        });

        const rows = await collect(readTSV(join(dir, "a.tsv"), COLUMNS));

        expect(rows.map((row) => row.fields[2])).toEqual(["токи", "borogove\u{1F409}"]);
        expect(rows.map((row) => row.line)).toEqual([3, 5]);
    });

    it("rejects a row with the wrong number of fields without echoing it", async () => {
        const dir = await fixture({
            "a.tsv": "tier\tcategory\tword\nvulgar\t00000\tmome\traths\n",
        });
        const error = await collect(readTSV(join(dir, "a.tsv"), COLUMNS)).catch((e: unknown) => e);

        expect(error).toBeInstanceOf(TSVError);
        expect((error as TSVError).line).toBe(2);
        expect((error as Error).message).toContain("expected 3 fields, found 4");
        expect((error as Error).message).not.toContain("mome");
    });

    it("rejects a missing or wrong header", async () => {
        const dir = await fixture({ "empty.tsv": "", "wrong.tsv": "word\ttier\tcategory\n" });

        await expect(collect(readTSV(join(dir, "empty.tsv"), COLUMNS))).rejects.toThrow(
            "missing header",
        );
        await expect(collect(readTSV(join(dir, "wrong.tsv"), COLUMNS))).rejects.toThrow(
            "expected header",
        );
    });
});
