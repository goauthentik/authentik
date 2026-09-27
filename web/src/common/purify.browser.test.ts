import { CompiledMarkdownSanitizePolicy } from "#common/purify";

import { describe, expect, it } from "vitest";

const sanitize = (html: string) => String(CompiledMarkdownSanitizePolicy.createHTML(html));

describe("CompiledMarkdownSanitizePolicy", () => {
    it("keeps the new-tab attributes the anchor pipeline emits", () => {
        // `rehypeAnchors` pairs `target` with `rel` on every external link.
        // DOMPurify's default attribute list carries `rel` but not `target`,
        // so dropping it here silently defeats the build-time transform.
        const result = sanitize(
            `<ak-md-a><a href="https://oauth.net/2/" target="_blank" rel="noopener noreferrer">OAuth 2.0</a></ak-md-a>`,
        );

        expect(result).toContain(`target="_blank"`);
        expect(result).toContain(`rel="noopener noreferrer"`);
    });

    it("keeps the custom elements and parts the pipeline emits", () => {
        const result = sanitize(`<ak-alert level="warning"><p part="body">Careful</p></ak-alert>`);

        expect(result).toContain("ak-alert");
        expect(result).toContain(`level="warning"`);
        expect(result).toContain(`part="body"`);
    });

    it("still strips script handlers spliced in by a replacer", () => {
        const result = sanitize(`<a href="#x" onclick="alert(1)">x</a><script>alert(2)</script>`);

        expect(result).not.toContain("onclick");
        expect(result).not.toContain("<script");
    });
});
