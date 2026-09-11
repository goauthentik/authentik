import { sanitizeLocaleModule } from "../../scripts/unescape-locale-entities.mjs";

import { describe, expect, it } from "vitest";

const wrap = (entries: string[]): string =>
    `export const templates = {\n${entries.map((e) => "    " + e).join("\n")}\n};\n`;

describe("sanitizeLocaleModule", () => {
    it("decodes over-escaped XML entities inside str-tagged templates", () => {
        const input = wrap(["'sample': str`&amp;quot;${0}&amp;quot; bearbeiten`,"]);

        const { output, replacements } = sanitizeLocaleModule(input);

        expect(output).toContain("'sample': str`\"${0}\" bearbeiten`,");
        expect(replacements).toBe(4);
    });

    it("decodes over-escaped XML entities inside untagged template literals", () => {
        const input = wrap(["'sample': `(Versuche &amp;lt; 10^3)`,"]);

        const { output } = sanitizeLocaleModule(input);

        expect(output).toContain("'sample': `(Versuche < 10^3)`,");
    });

    it("leaves html-tagged templates singly-encoded so lit-html can parse them", () => {
        const input = wrap(["'sample': html`Beispielsweise <code>foo</code> &gt; bar.`,"]);

        const { output, replacements } = sanitizeLocaleModule(input);

        expect(output).toBe(input);
        expect(replacements).toBe(0);
    });

    it("strips one layer of doubled entity references from html-tagged templates", () => {
        const input = wrap(["'sample': html`Directory &amp;gt; Users`,"]);

        const { output } = sanitizeLocaleModule(input);

        expect(output).toContain("html`Directory &gt; Users`");
    });

    it("does not touch ${...} substitution holes", () => {
        const input = wrap(["'sample': str`a&amp;quot;${0}&amp;quot;b`,"]);

        const { output } = sanitizeLocaleModule(input);

        expect(output).toContain('str`a"${0}"b`');
    });

    it("collapses fully doubly-encoded entities in one pass", () => {
        const input = wrap(["'sample': str`&amp;amp;lt;foo&amp;amp;gt;`,"]);

        const { output } = sanitizeLocaleModule(input);

        expect(output).toContain("str`<foo>`");
    });

    it("preserves template literals that contain no entity references", () => {
        const input = wrap(["'sample': str`Hello ${0}!`,", "'plain': `nichts zu sehen`,"]);

        const { output, replacements } = sanitizeLocaleModule(input);

        expect(output).toBe(input);
        expect(replacements).toBe(0);
    });

    it("handles consecutive template literals across multiple entries", () => {
        const input = wrap([
            "'a': str`&amp;quot;${0}&amp;quot;`,",
            "'b': html`<code>${0}</code>`,",
            "'c': `(Avaa &amp;quot;${0}&amp;quot;)`,",
        ]);

        const { output } = sanitizeLocaleModule(input);

        expect(output).toContain('str`"${0}"`');
        expect(output).toContain("html`<code>${0}</code>`");
        expect(output).toContain('(Avaa "${0}")');
    });
});
