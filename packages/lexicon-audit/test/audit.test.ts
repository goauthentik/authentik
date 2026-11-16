import { readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";

import { renderJSONL, writeMarkdownReports } from "#audit/report";
import { type ScanOptions, scanTranslations } from "#audit/scan";
import { Allowlist } from "#lexicon/allowlist";
import { buildLexicon } from "#lexicon/build";
import { openLexicon } from "#lexicon/database";
import { fixture, po, tsv, xliff12 } from "#test/helpers";

import { describe, expect, it } from "vitest";

//#region Fixtures

/**
 * A repository laid out like authentik's, with a Jabberwocky "lexicon" for English and a
 * toki pona one.
 */
async function repository() {
    return fixture({
        "corpus/en-US.tsv": tsv([
            ["vulgar", "00000", "brillig"],
            ["offensive", "00200", "SLITHY"],
            ["offensive", "00200", "vorpal-blade"],
            ["sensitive", "00c00", "mimsy"],
        ]),
        "corpus/tok.tsv": tsv([
            ["vulgar", "00000", "ike"],
            ["vulgar", "00000", "IKE"],
            ["offensive", "00400", "pakala"],
        ]),
        "allowlist.tsv": "locale\tword\tnote\ntok\tpakala\tMeans broken, used for errors\n",

        "locale/en/LC_MESSAGES/django.po": po(
            "en",
            `msgid "Twas brillig, and the {brillig} toves"
msgstr ""

msgid "Brilligly slithy"
msgstr ""

msgid "The SLITHY toves"
msgstr ""

msgid "One vorpal-blade went snicker-snack"
msgstr ""

msgid "A vorpal blade"
msgstr ""
`,
        ),
        "locale/tok/LC_MESSAGES/django.po": po(
            "tok",
            `msgid "Twas brillig, and the {brillig} toves"
msgstr "tenpo ike la soweli li tawa"

msgid "Brilligly slithy"
msgstr "ilo ikea li pona"

msgid "The SLITHY toves"
msgstr "Ike! ilo li pakala"
`,
        ),
        "web/xliff/tok.xlf": xliff12(
            "tok",
            `<trans-unit id="beware">
  <source>Beware the Jabberwock</source>
  <target>o lukin e <x id="0" equiv-text="&lt;ike&gt;"/>monsuta ike-ike</target>
</trans-unit>`,
        ),
        "web/xliff/pt-PT.xlf": xliff12(
            "pt-PT",
            `<trans-unit id="beware">
  <source>Beware</source>
  <target>ike</target>
</trans-unit>`,
        ),
    });
}

async function audit(root: string, options: Partial<ScanOptions> = {}) {
    const dbPath = join(root, "lexicon.db");

    await buildLexicon(join(root, "corpus"), dbPath, {
        allowlistPath: join(root, "allowlist.tsv"),
    });

    using db = openLexicon(dbPath);

    return await scanTranslations(db, [join(root, "locale"), join(root, "web/xliff")], {
        tiers: ["vulgar", "offensive"],
        sourceLocale: "en-US",
        allowlist: Allowlist.fromDatabase(db),
        cwd: root,
        ...options,
    });
}

//#endregion

//#region Tests

describe("audit", () => {
    it("finds whole-token matches in translations and source strings", async () => {
        const root = await repository();
        const result = await audit(root);

        const summary = result.findings.map((f) => {
            const text = f.side === "target" ? f.target : f.source;

            return `${f.side} ${f.locale} ${f.file}:${f.line} ${f.matchType} ${text.slice(f.start, f.end)}`;
        });

        expect(summary).toEqual([
            // Sorted by side, locale, file, then line.
            "source en-US locale/en/LC_MESSAGES/django.po:6 exact brillig",
            "source en-US locale/en/LC_MESSAGES/django.po:12 exact SLITHY",
            "source en-US locale/en/LC_MESSAGES/django.po:15 exact vorpal-blade",
            "target tok locale/tok/LC_MESSAGES/django.po:6 exact ike",
            "target tok locale/tok/LC_MESSAGES/django.po:12 casefold Ike",
            "target tok web/xliff/tok.xlf:5 exact ike",
            "target tok web/xliff/tok.xlf:5 exact ike",
        ]);
    });

    it("does not match substrings, placeholders, markup or the wrong case of all-caps entries", async () => {
        const root = await repository();
        const result = await audit(root);
        const matched = result.findings.map((f) =>
            (f.side === "target" ? f.target : f.source).slice(f.start, f.end),
        );

        // "Brilligly", "ikea", "{brillig}", "slithy" (entry is SLITHY), "vorpal blade" (entry is
        // hyphenated) and the <x equiv-text="<ike>"> attribute all stay unmatched.
        expect(matched).not.toContain("Brilligly");
        expect(matched).not.toContain("ikea");
        expect(matched).not.toContain("slithy");
        expect(
            result.findings.filter((f) => f.side === "source" && f.matchType === "casefold"),
        ).toEqual([]);
        expect(result.findings.filter((f) => f.file.endsWith("tok.xlf"))).toHaveLength(2);
    });

    it("reports one finding per position when entries differ only in case", async () => {
        const root = await repository();
        const result = await audit(root);
        const spans = result.findings.map((f) => `${f.fingerprint}`);

        expect(new Set(spans).size).toBe(spans.length);

        const ike = result.findings.find((f) => f.target.startsWith("Ike!"));

        // Both "ike" and "IKE" are entries; the sentence-initial "Ike" matches "ike" by case folding.
        expect(ike?.word).toBe("ike");
        expect(ike?.matchType).toBe("casefold");
    });

    it("skips allowlisted words and counts them", async () => {
        const root = await repository();
        const result = await audit(root);

        expect(result.findings.some((f) => f.word === "pakala")).toBe(false);
        expect(result.allowed).toBe(1);
    });

    it("doesn't borrow another region's lexicon unless asked", async () => {
        const root = await repository();
        const strict = await audit(root);
        const ptPT = strict.files.find((file) => file.locale === "pt-PT");

        expect(ptPT?.lexicon).toBeNull();
        expect(strict.files.find((file) => file.locale === "en")?.lexicon).toEqual({
            lexicon: "en-US",
            match: "likely",
        });

        // There's no Portuguese lexicon at all, so even the fallback finds nothing.
        const fallback = await audit(root, { regionFallback: true });

        expect(fallback.files.find((file) => file.locale === "pt-PT")?.lexicon).toBeNull();
    });

    it("keeps fingerprints stable across runs and changes them when the target changes", async () => {
        const root = await repository();
        const first = await audit(root);
        const second = await audit(root);

        expect(second.findings).toEqual(first.findings);

        const path = join(root, "web/xliff/tok.xlf");

        await writeFile(
            path,
            (await readFile(path, "utf8")).replace("monsuta ike-ike", "monsuta ike-ike a"),
        );

        const third = await audit(root);
        const fingerprints = (result: typeof first) =>
            result.findings.filter((f) => f.file.endsWith("tok.xlf")).map((f) => f.fingerprint);

        expect(fingerprints(third)).toHaveLength(2);
        expect(fingerprints(third)).not.toEqual(fingerprints(first));
    });

    it("writes JSON Lines and per-locale Markdown reports", async () => {
        const root = await repository();
        const result = await audit(root);
        const context = {
            result,
            tiers: ["vulgar", "offensive"] as const,
            generatedAt: "2026-01-01T00:00:00.000Z",
        };

        const lines = renderJSONL(context)
            .trim()
            .split("\n")
            .map((line) => JSON.parse(line) as { type: string });

        expect(lines[0]?.type).toBe("metadata");
        expect(lines.slice(1)).toHaveLength(result.findings.length);

        const reports = join(root, "reports");
        const files = await writeMarkdownReports(reports, context);

        expect(files).toEqual(["tok.md", "source-en-US.md", "index.md"]);

        const tok = await readFile(join(reports, "tok.md"), "utf8");

        expect(tok).toContain("# tok lexicon findings");
        expect(tok).toContain("## vulgar, category `00000`");
        expect(tok).toContain("`locale/tok/LC_MESSAGES/django.po:6`");
        expect(tok).toContain("tenpo ⟦ike⟧ la soweli li tawa");
    });
});

//#endregion
