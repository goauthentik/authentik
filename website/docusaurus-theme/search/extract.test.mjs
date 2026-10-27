import assert from "node:assert/strict";
import { test } from "node:test";

import { extractRecords } from "./extract.mjs";

/**
 * @param {string} body
 * @param {Partial<import("./extract.mjs").ExtractOptions>} [overrides]
 */
function extract(body, overrides = {}) {
    return extractRecords(body, {
        site: "Documentation",
        url: "/docs/page/",
        category: "Reference",
        title: "Fallback title",
        filePath: "/nonexistent/page.mdx",
        ...overrides,
    });
}

test("starts a record at each heading and aggregates the text below it", () => {
    const records = extract("# Decoder\n\nIntro text.\n\n## Objective\n\nFirst.\n\n- Second.\n");

    assert.deepEqual(
        records.map((record) => [record.level, record.anchor, record.content]),
        [
            [1, "", "Intro text."],
            [2, "objective", "First. Second."],
        ],
    );

    assert.deepEqual(records[1]?.hierarchy, [
        "Reference",
        "Decoder",
        "Objective",
        null,
        null,
        null,
        null,
    ]);
    assert.deepEqual(
        records.map((record) => record.position),
        [0, 1],
    );
});

test("uses the frontmatter title for a page whose body holds no h1", () => {
    const records = extract("Intro.\n\n## Part\n\nText.\n");

    assert.deepEqual(
        records.map((record) => record.hierarchy[1]),
        ["Fallback title", "Fallback title"],
    );
    assert.equal(records[0]?.content, "Intro.");
});

test("computes anchors as Docusaurus does, including the {#custom-id} syntax", () => {
    const records = extract(
        "# A\n\n## Set up your instance\n\n## Set up your instance\n\n## For code contributors {#code-contributors}\n",
    );

    assert.deepEqual(
        records.map((record) => record.anchor),
        ["", "set-up-your-instance", "set-up-your-instance-1", "code-contributors"],
    );
    assert.equal(records[3]?.hierarchy[2], "For code contributors");
});

test("yields one level-5 record per named table row, under the enclosing heading", () => {
    const records = extract(
        "# Coverage\n\n## Rows\n\n| Name | Note | Status |\n| --- | --- | --- |\n| Norway | ignored middle | Elected |\n| Sweden | x | Refused |\n",
    );

    const rows = records.filter((record) => record.level === 5);

    assert.deepEqual(
        rows.map((record) => [record.hierarchy[5], record.content, record.anchor]),
        [
            ["Norway", "Elected", "rows"],
            ["Sweden", "Refused", "rows"],
        ],
    );
    assert.deepEqual(rows[0]?.hierarchy.slice(0, 3), ["Reference", "Coverage", "Rows"]);
});

test("joins a table row keyed by a number to the section instead of making it a record", () => {
    const records = extract(
        "# Tiers\n\n## Tiers\n\n| Tier | Meaning |\n| --- | --- |\n| 1 | Trained, with a regression bar. |\n| Norway | Elected |\n",
    );

    assert.deepEqual(
        records.filter((record) => record.level === 5).map((record) => record.hierarchy[5]),
        ["Norway"],
    );
    assert.equal(records[1]?.content, "1 Trained, with a regression bar.");
});

test("resets deeper hierarchy entries when a shallower heading follows", () => {
    const records = extract("# A\n\n## B\n\n### C\n\n## D\n");

    assert.deepEqual(records.at(-1)?.hierarchy, ["Reference", "A", "D", null, null, null, null]);
});

test("keeps at most 4,000 characters of a section's text", () => {
    const records = extract(`# A\n\n${"word ".repeat(2000)}\n`);

    assert.equal(records[0]?.content.length, 4000);
});

test("folds a heading deeper than h4 into the section above it", () => {
    const records = extract("# A\n\n## Changes\n\n##### GET /outposts/\n\nReturns outposts.\n");

    assert.deepEqual(
        records.map((record) => [record.level, record.content]),
        [
            [1, ""],
            [2, "GET /outposts/ Returns outposts."],
        ],
    );
});

test("reads text through admonitions, JSX containers and inline code, and skips code blocks", () => {
    const records = extract(
        '# A\n\n:::info\nInside the note.\n:::\n\n<Tabs>\n<TabItem value="x">\nIn a tab with `inline-code`.\n</TabItem>\n</Tabs>\n\n```bash\nnot indexed\n```\n',
    );

    assert.equal(records[0]?.content, "Inside the note. In a tab with inline-code.");
});

test("drops HTML comments, imports and expressions", () => {
    const records = extract(
        '# A\n\nimport X from "./x";\n\n<!-- hidden -->\n\nShown. {someExpression}\n',
    );

    assert.equal(records[0]?.content, "Shown.");
});

test("the fallback reader keeps the text of a tag and drops a script, a comment and an expression", () => {
    /** @type {string[]} */
    const fallbacks = [];

    const records = extract(
        "# A\n\nText <b title='>'>bold</b> <!-- gone --> <script>alert(1)</script> {gone} where 1 < 2.\n",
        { onFallback: (filePath) => void fallbacks.push(filePath) },
    );

    assert.equal(fallbacks.length, 1);
    assert.equal(records[0]?.content, "Text bold where 1 < 2.");
});

test("falls back to plain Markdown when the MDX parser refuses the page", () => {
    /** @type {string[]} */
    const fallbacks = [];

    const records = extract("# A\n\nA <b>broken tag and 1 < 2 is {not an expression.\n", {
        onFallback: (filePath) => {
            fallbacks.push(filePath);
        },
    });

    assert.deepEqual(fallbacks, ["/nonexistent/page.mdx"]);
    assert.equal(records.length, 1);
    assert.match(records[0]?.content ?? "", /broken tag/);
});

test("gives distinct ids to headings that share text and the same id across builds", () => {
    const first = extract("# A\n\n## x\n\n## x\n\none\n");
    const changed = extract("# A\n\n## x\n\n## x\n\ntwo\n");

    assert.equal(new Set(first.map((record) => record.id)).size, first.length);
    assert.deepEqual(
        changed.map((record) => record.id),
        first.map((record) => record.id),
    );
});

test("yields no record for a Related, See also or Next link list", () => {
    const records = extract(
        "# Deploy\n\nRun it.\n\n## Related\n\n- [Docker](/a)\n\n## See also\n\n- [B](/b)\n\n## Next\n\n- [C](/c)\n",
    );

    assert.deepEqual(
        records.map((record) => record.anchor),
        [""],
    );
    assert.equal(records[0]?.content, "Run it.");
});
