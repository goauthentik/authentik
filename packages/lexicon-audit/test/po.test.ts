import { join } from "node:path";

import { collect, fixture, po } from "#test/helpers";
import { readPO } from "#translation/po";
import { entryKey, entryVariant } from "#translation/shared";

import { describe, expect, it } from "vitest";

const CATALOG = po(
    "tok",
    `#: jabberwocky.py
msgid "Beware the Jabberwock"
msgstr "o lukin e monsuta"

msgctxt "poem"
msgid "Callooh!"
msgstr "pona a!"

msgid "One borogove"
msgid_plural "Many borogoves"
msgstr[0] "waso wan"
msgstr[1] "waso mute"

msgid ""
"All mimsy were\\n"
"the \\"borogoves\\""
msgstr ""
"waso li\\n"
"\\"ike\\" lili"

#, fuzzy
msgid "Frumious"
msgstr "pakala"

msgid "Untranslated"
msgstr ""

#~ msgid "Vorpal"
#~ msgstr "wawa"
`,
);

describe("readPO", () => {
    it("reads entries, contexts, plurals and multiline escaped strings", async () => {
        const dir = await fixture({ "tok/LC_MESSAGES/django.po": CATALOG });
        const entries = await collect(readPO(join(dir, "tok/LC_MESSAGES/django.po")));

        expect(
            entries.map((entry) => [
                entryKey(entry),
                entryVariant(entry),
                entry.source,
                entry.target,
            ]),
        ).toEqual([
            ["Beware the Jabberwock", "", "Beware the Jabberwock", "o lukin e monsuta"],
            ["poem\u0004Callooh!", "", "Callooh!", "pona a!"],
            ["One borogove", "0", "One borogove", "waso wan"],
            ["One borogove", "1", "Many borogoves", "waso mute"],
            [
                'All mimsy were\nthe "borogoves"',
                "",
                'All mimsy were\nthe "borogoves"',
                'waso li\n"ike" lili',
            ],
            ["Untranslated", "", "Untranslated", ""],
        ]);
    });

    it("reads the declared locale from the header", async () => {
        const dir = await fixture({ "a.po": CATALOG });
        const [first] = await collect(readPO(join(dir, "a.po")));

        expect(first?.locale).toBe("tok");
    });

    it("includes fuzzy and obsolete entries only when asked", async () => {
        const dir = await fixture({ "a.po": CATALOG });
        const entries = await collect(
            readPO(join(dir, "a.po"), { includeFuzzy: true, includeObsolete: true }),
        );
        const keys = entries.map(entryKey);

        expect(keys).toContain("Frumious");
        expect(keys).toContain("#~Vorpal");
    });

    it("records the line each entry starts on", async () => {
        const dir = await fixture({ "a.po": CATALOG });
        const entries = await collect(readPO(join(dir, "a.po")));
        const lines = CATALOG.split("\n");

        for (const entry of entries) {
            const block = lines.slice(entry.line - 1, entry.line + 3).join("\n");

            expect(block).toContain(JSON.stringify(entry.id.split("\n")[0]).slice(0, -1));
        }
    });
});
