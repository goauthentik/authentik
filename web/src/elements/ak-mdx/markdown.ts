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
 * browser. The pipeline is a strict subset of the build-time one: no
 * syntax highlighting, no anchor rewriting — the output is plain HTML
 * that the existing `BrandedHTMLPolicy` (DOMPurify) sanitizes cleanly.
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
