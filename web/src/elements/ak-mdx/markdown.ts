import {
    normalizeAdmonitionLabels,
    remarkAdmonition,
} from "#elements/ak-mdx/remark/remark-admonition";
import { remarkHeadings } from "#elements/ak-mdx/remark/remark-headings";
import { remarkLists } from "#elements/ak-mdx/remark/remark-lists";

import rehypeStringify from "rehype-stringify";
import remarkDirective from "remark-directive";
import remarkGFM from "remark-gfm";
import remarkParse from "remark-parse";
import remarkRehype from "remark-rehype";
import { unified } from "unified";

/**
 * Compile an admin-supplied markdown string to an HTML string in the
 * browser. The pipeline is a strict subset of the build-time one in
 * `bundler/mdx-plugin/compile.js`: no syntax highlighting, no anchor
 * rewriting, no mermaid — the output is plain HTML that the existing
 * `BrandedHTMLPolicy` (DOMPurify) sanitizes cleanly.
 *
 * The two pipelines share the remark transforms (admonitions, headings,
 * lists) but deliberately diverge on the rehype side: this one stays
 * minimal, whereas the build-time one emits custom elements
 * (`<ak-alert>`, `<ak-md-a>`, `<ak-diagram>`) that are preserved by the
 * URL-mode `CompiledMarkdownSanitizePolicy`. **If you add a transform
 * that should apply to both surfaces, update `bundler/mdx-plugin/`
 * too** — the shared remark plugins live in `#elements/ak-mdx/remark/*`
 * and are mirrored there to keep drift easy to spot.
 *
 * Unlike `@mdx-js/mdx`'s `evaluate` / `run`, none of the `unified`,
 * `remark-*`, or `rehype-*` packages execute the input as JavaScript:
 * they are pure tree transformers. This is what lets us drop
 * `'unsafe-eval'` from the page CSP.
 */
export async function compileRuntimeMarkdown(source: string): Promise<string> {
    if (!source.trim()) return "";

    // Translate Docusaurus's `:::name Title` syntax to `:::name[Title]`
    // before remark-directive parses it; otherwise it falls through as
    // plain text.
    const normalized = normalizeAdmonitionLabels(source);

    const file = await unified()
        .use(remarkParse)
        .use(remarkGFM)
        .use(remarkDirective)
        .use(remarkAdmonition)
        .use(remarkHeadings)
        .use(remarkLists)
        .use(remarkRehype, { allowDangerousHtml: false })
        .use(rehypeStringify)
        .process(normalized);

    return String(file);
}
