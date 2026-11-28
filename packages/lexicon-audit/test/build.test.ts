import { existsSync } from "node:fs";
import { writeFile } from "node:fs/promises";
import { join } from "node:path";

import { Allowlist } from "#lexicon/allowlist";
import { LexiconError, buildLexicon, discoverLexicon } from "#lexicon/build";
import { lexiconLocales, openLexicon } from "#lexicon/database";
import { fixture, tsv } from "#test/helpers";

import { describe, expect, it } from "vitest";

describe("discoverLexicon", () => {
    it("accepts canonical and legacy file names, normalizing underscores", async () => {
        const dir = await fixture({
            "en-US.tsv": tsv([]),
            "nested/words-en_GB.tsv": tsv([]),
            "tok.tsv": tsv([]),
        });

        const sources = await discoverLexicon(dir);

        expect(sources.map(({ locale, originalTag }) => [locale, originalTag])).toEqual([
            ["en-US", "en-US"],
            ["en-GB", "en_GB"],
            ["tok", "tok"],
        ]);
    });

    it("rejects duplicate locales and unrecognized names", async () => {
        const duplicate = await fixture({ "en-US.tsv": tsv([]), "words-en_US.tsv": tsv([]) });
        const invalid = await fixture({ "jabberwocky!.tsv": tsv([]) });
        const empty = await fixture({ "README.md": "" });

        await expect(discoverLexicon(duplicate)).rejects.toThrow("duplicate locale en-US");
        await expect(discoverLexicon(invalid)).rejects.toThrow("file name is not");
        await expect(discoverLexicon(empty)).rejects.toThrow(LexiconError);
    });
});

describe("buildLexicon", () => {
    it("imports entries, deduplicates rows and stores the allowlist", async () => {
        const dir = await fixture({
            "words/en-US.tsv": tsv([
                ["vulgar", "00000", "brillig"],
                ["vulgar", "00000", "brillig"],
                ["offensive", "00200", "SLITHY"],
                ["sensitive", "00c00", "mimsy"],
            ]),
            "words/tok.tsv": tsv([["vulgar", "00000", "ike"]]),
            "allowlist.tsv": "locale\tword\tnote\ntok\tike\tMeans bad, harmless\n*\tmimsy\t\n",
        });

        const dbPath = join(dir, "lexicon.db");
        const stats = await buildLexicon(join(dir, "words"), dbPath, {
            allowlistPath: join(dir, "allowlist.tsv"),
        });

        expect(stats.locales).toEqual([
            {
                locale: "en-US",
                rows: 3,
                duplicates: 1,
                byTier: { vulgar: 1, offensive: 1, sensitive: 1 },
            },
            {
                locale: "tok",
                rows: 1,
                duplicates: 0,
                byTier: { vulgar: 1, offensive: 0, sensitive: 0 },
            },
        ]);
        expect(stats.allowlist).toBe(2);

        using db = openLexicon(dbPath);
        const allowlist = Allowlist.fromDatabase(db);

        expect(lexiconLocales(db)).toEqual(["en-US", "tok"]);
        expect(allowlist.has("tok", "IKE")).toBe(true);
        expect(allowlist.has("en-US", "ike")).toBe(false);
        expect(allowlist.has("en-GB", "Mimsy")).toBe(true);
    });

    it("produces identical counts when rebuilt", async () => {
        const dir = await fixture({ "words/tok.tsv": tsv([["vulgar", "00000", "ike"]]) });
        const dbPath = join(dir, "lexicon.db");

        const first = await buildLexicon(join(dir, "words"), dbPath);
        const second = await buildLexicon(join(dir, "words"), dbPath);

        expect(second).toEqual(first);
    });

    it("rejects malformed rows by location, without echoing values, and keeps the previous database", async () => {
        const dir = await fixture({ "words/tok.tsv": tsv([["vulgar", "00000", "ike"]]) });
        const dbPath = join(dir, "lexicon.db");

        await buildLexicon(join(dir, "words"), dbPath);

        for (const [row, reason] of [
            [["vulgar", "zz", "frumious"], "category is not hexadecimal"],
            [["wabe", "00000", "frumious"], "unknown tier"],
        ] as const) {
            await writeFile(
                join(dir, "words/tok.tsv"),
                tsv([["vulgar", "00000", "ike"], [...row]]),
            );

            const error = await buildLexicon(join(dir, "words"), dbPath).then(
                () => new Error("expected the build to fail"),
                (e: unknown) => e as Error,
            );

            expect(error.message).toContain("tok.tsv:3");
            expect(error.message).toContain(reason);
            expect(error.message).not.toContain("frumious");
        }

        expect(existsSync(`${dbPath}.tmp`)).toBe(false);

        using db = openLexicon(dbPath);

        expect(lexiconLocales(db)).toEqual(["tok"]);
    });
});
