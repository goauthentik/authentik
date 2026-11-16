import { join } from "node:path";

import { scanTextFiles } from "#audit/scan";
import { Allowlist } from "#lexicon/allowlist";
import { buildLexicon } from "#lexicon/build";
import { openLexicon } from "#lexicon/database";
import { fixture, tsv } from "#test/helpers";

import { describe, expect, it } from "vitest";

const README = `# The Jabberwock

'Twas brillig, and the slithy toves
Did gyre and gimble in the wabe:

\`\`\`sh
mimsy --borogoves
\`\`\`

Beware the [Brillig](https://example.com/brillig) bird, and shun
The frumious Bandersnatch! Brilligly so.

Country: \`TF\`. 龍 flew by.
`;

async function check(locale?: string, minLength?: number) {
    const root = await fixture({
        "corpus/en-US.tsv": tsv([
            ["vulgar", "00000", "brillig"],
            ["offensive", "00200", "mimsy"],
            ["vulgar", "00000", "tf"],
        ]),
        "corpus/zh-Hant.tsv": tsv([["vulgar", "00000", "龍"]]),
        "corpus/tok.tsv": tsv([["vulgar", "00000", "ike"]]),
        "README.md": README,
    });

    const dbPath = join(root, "lexicon.db");

    await buildLexicon(join(root, "corpus"), dbPath);

    using db = openLexicon(dbPath);

    return scanTextFiles(db, [join(root, "README.md")], {
        locale: locale ?? "en",
        tiers: ["vulgar", "offensive"],
        allowlist: Allowlist.fromDatabase(db),
        cwd: root,
        minLength,
    });
}

describe("scanTextFiles", () => {
    it("matches the file as-is, line by line, including code and link text", async () => {
        const result = await check();

        expect(result.sourceLexicon).toEqual({ lexicon: "en-US", match: "likely" });
        expect(
            result.findings.map((f) => `${f.file}:${f.line} ${f.source.slice(f.start, f.end)}`),
        ).toEqual([
            "README.md:3 brillig",
            "README.md:7 mimsy",
            "README.md:10 Brillig",
            "README.md:10 brillig",
        ]);
    });

    it("rejects a locale without a lexicon", async () => {
        await expect(check("fr")).rejects.toThrow("no lexicon for fr");
    });

    it("skips entries shorter than the minimum length", async () => {
        const matched = (result: Awaited<ReturnType<typeof check>>) =>
            result.findings.map((f) => f.source.slice(f.start, f.end));

        expect(matched(await check())).not.toContain("TF");
        expect(matched(await check("en", 2))).toContain("TF");
    });

    it("keeps short entries in CJK locales", async () => {
        const result = await check("zh-TW");

        expect(result.sourceLexicon).toEqual({ lexicon: "zh-Hant", match: "likely" });
        expect(result.findings.map((f) => `${f.line} ${f.source.slice(f.start, f.end)}`)).toEqual([
            "13 龍",
        ]);
    });
});
