import { existsSync } from "node:fs";
import { readFile } from "node:fs/promises";
import { join } from "node:path";

import { scanTranslations } from "#audit/scan";
import { buildLexicon } from "#lexicon/build";
import { openLexicon } from "#lexicon/database";
import { sealLexicon, unsealLexicon } from "#lexicon/seal";
import { fixture, po, tsv } from "#test/helpers";

import { describe, expect, it } from "vitest";

async function sealedRepository() {
    const root = await fixture({
        "corpus/tok.tsv": tsv([["vulgar", "00000", "ike"]]),
        "locale/tok/LC_MESSAGES/django.po": po(
            "tok",
            `msgid "Beware the Jabberwock"
msgstr "o lukin e monsuta ike"
`,
        ),
    });

    await buildLexicon(join(root, "corpus"), join(root, "lexicon.db"), { allowlistPath: null });
    await sealLexicon(join(root, "lexicon.db"), join(root, "lexicon.db.gpg"), "jubjub bird");

    return root;
}

async function fingerprints(root: string, databasePath: string) {
    using db = openLexicon(databasePath);

    const { findings } = await scanTranslations(db, [join(root, "locale")], {
        tiers: ["vulgar"],
        cwd: root,
    });

    return findings.map((finding) => finding.fingerprint);
}

describe("seal", () => {
    it("audits the same findings after a round trip, without the vocabulary in the sealed file", async () => {
        const root = await sealedRepository();
        const unsealed = join(root, "unsealed.db");

        await unsealLexicon(join(root, "lexicon.db.gpg"), unsealed, "jubjub bird");

        expect(await readFile(join(root, "lexicon.db.gpg"))).not.toContain("ike");
        expect(await fingerprints(root, unsealed)).toEqual(
            await fingerprints(root, join(root, "lexicon.db")),
        );
        expect(await fingerprints(root, unsealed)).toHaveLength(1);
    });

    it("rejects the wrong passphrase and leaves no database behind", async () => {
        const root = await sealedRepository();
        const unsealed = join(root, "unsealed.db");

        await expect(
            unsealLexicon(join(root, "lexicon.db.gpg"), unsealed, "bandersnatch"),
        ).rejects.toThrow("gpg exited");
        expect(existsSync(unsealed)).toBe(false);
    });

    it("refuses to seal a file that isn't a lexicon database", async () => {
        const root = await fixture({ "notes.db": "Twas brillig" });

        await expect(
            sealLexicon(join(root, "notes.db"), join(root, "notes.db.gpg"), "jubjub bird"),
        ).rejects.toThrow();
        expect(existsSync(join(root, "notes.db.gpg"))).toBe(false);
    });
});
