import { join } from "node:path";

import { collect, fixture, xliff12 } from "#test/helpers";
import { PLACEHOLDER, entryKey, entryVariant } from "#translation/shared";
import { readXLIFF } from "#translation/xliff";

import { describe, expect, it } from "vitest";

describe("readXLIFF", () => {
    it("reads XLIFF 1.2 units, replacing inline markup with placeholders", async () => {
        const dir = await fixture({
            "tok.xlf": xliff12(
                "tok",
                `<trans-unit id="jabberwock">
  <source>Beware the <x id="0" equiv-text="&lt;b class=&quot;slithy&quot;&gt;"/>Jabberwock<x id="1" equiv-text="&lt;/b&gt;"/></source>
  <target>o lukin e <x id="0" equiv-text="&lt;b class=&quot;slithy&quot;&gt;"/>monsuta<x id="1" equiv-text="&lt;/b&gt;"/> &amp; jan</target>
</trans-unit>
<trans-unit id="untranslated">
  <source>Brillig</source>
</trans-unit>
<trans-unit id="frozen" translate="no">
  <source>Vorpal</source>
  <target>Vorpal</target>
</trans-unit>`,
            ),
        });

        const entries = await collect(readXLIFF(join(dir, "tok.xlf")));

        expect(
            entries.map((entry) => [entryKey(entry), entry.locale, entry.source, entry.target]),
        ).toEqual([
            [
                "jabberwock",
                "tok",
                `Beware the ${PLACEHOLDER}Jabberwock${PLACEHOLDER}`,
                `o lukin e ${PLACEHOLDER}monsuta${PLACEHOLDER} & jan`,
            ],
            ["untranslated", "tok", "Brillig", ""],
        ]);
    });

    it("reads XLIFF 2.0 segments as separate variants", async () => {
        const dir = await fixture({
            "tok.xlf": `<?xml version="1.0"?>
<xliff xmlns="urn:oasis:names:tc:xliff:document:2.0" version="2.0" srcLang="en" trgLang="tok">
  <file id="f">
    <unit id="poem">
      <segment id="s1"><source>Twas brillig</source><target>tenpo <ph id="1"/> pona</target></segment>
      <segment id="s2"><source>and the <pc id="2">slithy</pc> toves</source><target>en <pc id="2">soweli</pc> lili<cp hex="1F409"/></target></segment>
    </unit>
  </file>
</xliff>`,
        });

        const entries = await collect(readXLIFF(join(dir, "tok.xlf")));

        expect(
            entries.map((entry) => [entryKey(entry), entryVariant(entry), entry.target]),
        ).toEqual([
            ["poem", "s1", `tenpo ${PLACEHOLDER} pona`],
            ["poem", "s2", "en soweli lili\u{1F409}"],
        ]);
    });

    it("records the line each unit starts on", async () => {
        const units = Array.from(
            { length: 3 },
            (_, i) =>
                `<trans-unit id="u${i}">\n  <source>a</source>\n  <target>b</target>\n</trans-unit>`,
        ).join("\n");
        const content = xliff12("tok", units);
        const dir = await fixture({ "tok.xlf": content });
        const lines = content.split("\n");

        for (const entry of await collect(readXLIFF(join(dir, "tok.xlf")))) {
            expect(lines[entry.line - 1]).toContain(`id="${entry.id}"`);
        }
    });

    it("rejects unsupported versions", async () => {
        const dir = await fixture({ "a.xlf": `<xliff version="1.1"><file/></xliff>` });

        await expect(collect(readXLIFF(join(dir, "a.xlf")))).rejects.toThrow(
            'unsupported XLIFF version "1.1"',
        );
    });
});
